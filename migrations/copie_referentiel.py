"""Copie le référentiel alimentaire d'une base PostgreSQL vers une autre.

Contexte : les tables `foods`, `ingredients`, `dishes` et `dish_ingredients`
avaient été peuplées dans une base de développement locale (`nutrition_westaf`)
par `fao_data_processor.py` et `extract_dishes.py`. La migration vers le
docker-compose repart d'un volume neuf : plutôt que de rejouer l'extraction —
qui régénère des UUID et perd les plats ajoutés à la main — on recopie
l'existant.

Ne copie **que** le référentiel. Les profils utilisateurs, maladies et
allergènes ne sont pas touchés : ils appartiennent à la base cible.

    python migrations/copie_referentiel.py --source postgresql://... [--dry-run]

La cible est lue dans DATABASE_URL.
"""

import argparse
import os
import sys

import psycopg2
from psycopg2.extras import execute_values, register_default_jsonb

# Ordre imposé par les clés étrangères
TABLES = [
    ("foods", ["id", "local_name", "scientific_name", "category",
               "nutritional_values", "glycemic_index", "sodium_content",
               "potassium_content", "origin"]),
    ("ingredients", ["id", "name", "food_id"]),
    ("dishes", ["id", "name", "description", "method", "meal_type", "cuisine_origin"]),
    ("dish_ingredients", ["dish_id", "ingredient_id", "quantity", "unit"]),
]


def dsn_psycopg2(url):
    return url.replace("postgresql+psycopg2://", "postgresql://")


def message_lisible(erreur):
    """libpq parle la langue de Windows ; psycopg2 le décode en UTF-8 et
    s'étrangle sur les accents. On récupère le message réel."""
    if isinstance(erreur, UnicodeDecodeError):
        return erreur.object.decode("cp1252", "replace")
    return str(erreur)


def copier(source_dsn, cible_dsn, dry_run=False):
    src = psycopg2.connect(source_dsn)
    dst = psycopg2.connect(cible_dsn)
    src.set_client_encoding("UTF8")
    dst.set_client_encoding("UTF8")
    # Par défaut psycopg2 transforme le JSONB lu en dict, qu'il ne sait pas
    # réinsérer tel quel. On le laisse sous forme de texte : il repart en jsonb
    # sans conversion ni perte.
    register_default_jsonb(conn_or_curs=src, loads=lambda valeur: valeur)

    total = {}
    try:
        with src.cursor() as cs, dst.cursor() as cd:
            for table, colonnes in TABLES:
                liste = ", ".join(colonnes)
                cs.execute(f"SELECT {liste} FROM {table}")
                lignes = cs.fetchall()

                cd.execute(f"SELECT COUNT(*) FROM {table}")
                avant = cd.fetchone()[0]

                if not dry_run and lignes:
                    # ON CONFLICT DO NOTHING : la copie est rejouable
                    conflit = "(dish_id, ingredient_id)" if table == "dish_ingredients" else "(id)"
                    execute_values(
                        cd,
                        f"INSERT INTO {table} ({liste}) VALUES %s "
                        f"ON CONFLICT {conflit} DO NOTHING",
                        lignes,
                        page_size=500,
                    )

                cd.execute(f"SELECT COUNT(*) FROM {table}")
                apres = cd.fetchone()[0]
                total[table] = (len(lignes), avant, apres)
                print(f"  {table:20} source {len(lignes):>5}   cible {avant:>5} -> {apres:>5}")

        if dry_run:
            dst.rollback()
            print("\n(dry-run : rien n'a été écrit)")
        else:
            dst.commit()
            print("\nCopie validée.")
    finally:
        src.close()
        dst.close()
    return total


def main():
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--source", required=True, help="DSN PostgreSQL de la base d'origine")
    parseur.add_argument("--cible", default=os.environ.get("DATABASE_URL"),
                         help="DSN de la base cible (défaut : DATABASE_URL)")
    parseur.add_argument("--dry-run", action="store_true", help="compte sans écrire")
    args = parseur.parse_args()

    if not args.cible:
        parseur.error("aucune cible : passer --cible ou définir DATABASE_URL")

    print(f"Copie du référentiel alimentaire{' (simulation)' if args.dry_run else ''}\n")
    try:
        copier(dsn_psycopg2(args.source), dsn_psycopg2(args.cible), args.dry_run)
    except Exception as erreur:  # noqa: BLE001
        print(f"\nÉchec : {message_lisible(erreur)}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
