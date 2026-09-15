"""Résolution de noms d'ingrédients vers les lignes de la table `ingredients`.

Sert la route `POST /api/analyze-ingredients` (ARCHITECTURE_V2.md §6.2), qui
reçoit des ingrédients **déjà extraits et normalisés en français** par le LLM :
il n'y a donc plus de phrase à analyser, seulement des noms à rapprocher du
référentiel. Pas de spaCy ici — `WestAfricanMenuParser` reste le chemin pour le
texte libre, et le repli hors ligne (décision 4 du §11).

La normalisation est volontairement identique à celle du parser : les deux
routes doivent rapprocher « Thiéboudienne » et « thieboudienne » de la même
façon. `WestAfricanMenuParser._normalize` délègue à `normaliser` ci-dessous.
"""

import json
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from api.schemas.analyze import Ingredient

# Au-dessus de ce score, un nom approchant est accepté. Le parser utilise 88
# sur des tokens isolés ; ici les noms viennent du LLM, déjà propres, donc on
# peut être un peu plus strict sans perdre de rappel.
SEUIL_APPROCHANT = 90


def normaliser(texte: str) -> str:
    """Minuscules, sans diacritiques ni ponctuation, espaces réduits."""
    if not texte:
        return ""
    texte = texte.lower()
    texte = unicodedata.normalize("NFKD", texte)
    # Retirer les diacritiques décomposés : sans cela la regex ci-dessous
    # les remplace par une espace ("thiéboudienne" -> "thie boudienne").
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = re.sub(r"[^\w\s]", " ", texte)
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte


def alias_de(ingredient) -> List[str]:
    """Alias d'un ingrédient, si le modèle en expose.

    La colonne `aliases` n'existe pas encore en base (elle arrive avec le wolof,
    §6.1) : on tolère son absence plutôt que de faire échouer la résolution.
    """
    getter = getattr(ingredient, "get_aliases", None)
    if callable(getter):
        return list(getter() or [])

    brut = getattr(ingredient, "aliases", None)
    if not brut:
        return []
    if isinstance(brut, str):
        try:
            brut = json.loads(brut)
        except (ValueError, TypeError):
            return []
    return [a for a in brut if isinstance(a, str)]


def construire_index(db: Session) -> List[Tuple[str, str]]:
    """[(nom normalisé, ingredient_id)] pour les noms et leurs alias."""
    index: List[Tuple[str, str]] = []
    for ingredient in db.query(Ingredient).all():
        index.append((normaliser(ingredient.name), ingredient.id))
        for alias in alias_de(ingredient):
            index.append((normaliser(alias), ingredient.id))
    return [(nom, ident) for nom, ident in index if nom]


def resoudre(
    entrees: List[Dict],
    db: Session,
    seuil: int = SEUIL_APPROCHANT,
) -> Tuple[List[Dict], List[str]]:
    """Rapproche des ingrédients nommés du référentiel.

    Args:
        entrees: [{"name": "riz", "quantity": 200, "unit": "g"}, ...]
        db: session SQLAlchemy
        seuil: score minimal pour accepter un rapprochement approchant

    Returns:
        (items, non_resolus) où `items` a la forme attendue par
        `calculate_dish_nutrition_from_items` et `non_resolus` liste les noms
        restés sans correspondance — c'est cette liste qui doit déclencher une
        demande de confirmation côté bot plutôt qu'une analyse silencieusement
        incomplète (§7).
    """
    index = construire_index(db)
    exact = {nom: ident for nom, ident in index}
    noms_connus = [nom for nom, _ in index]

    items: List[Dict] = []
    non_resolus: List[str] = []
    deja_vus = set()

    for entree in entrees:
        brut = (entree.get("name") or "").strip()
        if not brut:
            continue

        norme = normaliser(brut)
        ingredient_id: Optional[str] = exact.get(norme)
        confiance = 1.0

        if ingredient_id is None and noms_connus:
            meilleur = process.extractOne(norme, noms_connus, scorer=fuzz.token_set_ratio)
            if meilleur and meilleur[1] >= seuil:
                ingredient_id = exact[meilleur[0]]
                confiance = meilleur[1] / 100

        if ingredient_id is None:
            non_resolus.append(brut)
            continue

        # Un même ingrédient cité deux fois ne doit pas compter double
        if ingredient_id in deja_vus:
            continue
        deja_vus.add(ingredient_id)

        items.append({
            "ingredient_id": ingredient_id,
            "quantity": entree.get("quantity"),
            "unit": entree.get("unit") or "unité",
            "raw_text": brut,
            "confidence": confiance,
        })

    return items, non_resolus
