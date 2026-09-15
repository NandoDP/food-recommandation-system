#!/usr/bin/env python3
"""Contrôle les workflows de `workflows/` avant de les importer dans n8n.

`n8n import:workflow` valide **tout le lot** avant d'en écrire un seul : une
seule référence cassée et rien n'est importé, y compris les workflows sains.
Le message ne dit pas quel fichier est en cause, seulement le nom du nœud.

Le cas qui se produit vraiment : on remplace un nœud « X à brancher » par
l'appel au sous-workflow, on renomme, et un autre nœud continue de citer
l'ancien nom comme cible de connexion.

    python n8n/valider_workflows.py

Sortie 0 si tout est cohérent, 1 sinon, avec le fichier et la ligne du problème.
"""
import json
import sys
from pathlib import Path

DOSSIER = Path(__file__).parent / "workflows"


def charger(chemin: Path):
    try:
        return json.loads(chemin.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"JSON illisible ligne {e.lineno} : {e.msg}"


def controler(workflow: dict, identifiants_connus: set) -> list:
    """Renvoie la liste des problèmes trouvés dans un workflow."""
    problemes = []

    noms = [n.get("name") for n in workflow.get("nodes", [])]
    doublons = {n for n in noms if noms.count(n) > 1}
    if doublons:
        problemes.append(f"noms de nœuds en double : {', '.join(sorted(doublons))}")
    connus = set(noms)

    for source, sorties in workflow.get("connections", {}).items():
        if source not in connus:
            problemes.append(f"connexion depuis un nœud inexistant : « {source} »")
        for index, sortie in enumerate(sorties.get("main", [])):
            for lien in sortie:
                cible = lien.get("node")
                if cible not in connus:
                    problemes.append(
                        f"« {source} » sortie {index} pointe sur « {cible} », qui n'existe pas"
                    )

    # Un Execute Sub-workflow qui vise un identifiant absent s'importe sans
    # broncher, puis échoue à l'exécution : autant le voir ici.
    for noeud in workflow.get("nodes", []):
        if noeud.get("type") != "n8n-nodes-base.executeWorkflow":
            continue
        vise = (noeud.get("parameters", {}).get("workflowId") or {}).get("value")
        if vise and vise not in identifiants_connus:
            problemes.append(
                f"« {noeud['name']} » appelle le workflow « {vise} », absent de {DOSSIER.name}/"
            )

    # Un nœud isolé est le plus souvent un oubli de câblage, pas un choix.
    atteints = set()
    for source, sorties in workflow.get("connections", {}).items():
        atteints.add(source)
        for sortie in sorties.get("main", []):
            atteints.update(lien.get("node") for lien in sortie)
    for noeud in workflow.get("nodes", []):
        if noeud["type"] in ("n8n-nodes-base.stickyNote", "n8n-nodes-base.errorTrigger"):
            continue
        if noeud["name"] not in atteints:
            problemes.append(f"« {noeud['name']} » n'est relié à rien")

    return problemes


def main() -> int:
    fichiers = sorted(DOSSIER.glob("*.json"))
    if not fichiers:
        print(f"Aucun workflow dans {DOSSIER}")
        return 1

    charges = {}
    en_echec = False
    for chemin in fichiers:
        workflow, erreur = charger(chemin)
        if erreur:
            print(f"ERREUR  {chemin.name} : {erreur}")
            en_echec = True
        else:
            charges[chemin] = workflow

    identifiants = {w.get("id") for w in charges.values()}

    for chemin, workflow in charges.items():
        problemes = controler(workflow, identifiants)
        if problemes:
            en_echec = True
            print(f"ERREUR  {chemin.name}")
            for probleme in problemes:
                print(f"    {probleme}")
        else:
            print(f"ok      {chemin.name} : {len(workflow.get('nodes', []))} noeuds")

    if en_echec:
        print("\nn8n refuserait le lot entier : corriger avant d'importer.")
        return 1

    print(f"\n{len(charges)} workflows cohérents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
