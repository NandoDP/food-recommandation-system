import json
import re
import unicodedata
from typing import List, Dict, Tuple, Optional
from rapidfuzz import fuzz, process
import spacy
from spacy.matcher import PhraseMatcher
from sqlalchemy.orm import Session
from api.schemas.analyze import Ingredient
from api.core.ingredient_resolver import normaliser

# ===========================================================================
# 1. CHARGEMENT DES DONNÉES DE TA BASE (une seule fois au démarrage)
# ===========================================================================

class WestAfricanMenuParser:
    def __init__(self, db: Session):
        self.db = db
        self.nlp = spacy.blank("fr")
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._load_ingredients()
        self._build_fuzzy_index()

    def _get_aliases(self, ing) -> List[str]:
        """Aliases d'un ingrédient, si le modèle en expose.

        La colonne n'existe pas encore en base : on tolère son absence plutôt
        que de faire échouer tout le parser. Accepte une méthode
        `get_aliases()`, ou un attribut `aliases` (liste ou chaîne JSON).
        """
        getter = getattr(ing, 'get_aliases', None)
        if callable(getter):
            return list(getter() or [])

        raw = getattr(ing, 'aliases', None)
        if not raw:
            return []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except ValueError:
                return []
        return list(raw) if isinstance(raw, (list, tuple)) else []

    def _load_ingredients(self):
        """Charge tous les ingrédients + aliases dans spaCy PhraseMatcher"""
        ingredients = self.db.query(Ingredient).all()
        self.ingredient_map = {}           # id → objet Ingredient
        self.name_to_id = {}               # nom normalisé → id
        self.alias_to_id = {}              # alias → id

        patterns = []
        for ing in ingredients:
            self.ingredient_map[ing.id] = ing
            main_name = self._normalize(ing.name)
            self.name_to_id[main_name] = ing.id
            patterns.append(self.nlp.make_doc(main_name))

            # Aliases (très important pour wolof, orthographes variables)
            aliases = self._get_aliases(ing)
            for alias in aliases:
                norm = self._normalize(alias)
                self.alias_to_id[norm] = ing.id
                patterns.append(self.nlp.make_doc(norm))

        self.phrase_matcher.add("INGREDIENT", patterns)
        print(f"[Parser] {len(patterns)} motifs chargés (ingredients + aliases)")

    def _build_fuzzy_index(self):
        """Index pour fallback fuzzy (rapidfuzz)"""
        all_names = []
        for ing in self.db.query(Ingredient).all():
            all_names.append((ing.id, self._normalize(ing.name)))
            for alias in self._get_aliases(ing):
                all_names.append((ing.id, self._normalize(alias)))
        self.fuzzy_choices = [(name, ing_id) for ing_id, name in all_names]
        self.fuzzy_names = [name for name, _ in self.fuzzy_choices]

    def _normalize(self, text: str) -> str:
        """Nettoyage agressif mais intelligent.

        Délègue à `ingredient_resolver.normaliser` : la route
        /analyze-ingredients doit rapprocher les noms exactement comme ici,
        sinon les deux chemins d'analyse divergeraient sur les accents.
        """
        return normaliser(text)

    # ===========================================================================
    # 2. EXTRACTION PRINCIPALE
    # ===========================================================================

    def parse_menu_text(self, text: str) -> List[Dict]:
        """
        Retourne une liste de dicts :
        [{'ingredient_id': UUID, 'quantity': float, 'unit': str, 'raw_text': str}, ...]
        """
        text = text.strip()
        if not text:
            return []

        normalized = self._normalize(text)
        # Les motifs du PhraseMatcher sont construits sur des noms normalisés :
        # le document doit l'être aussi pour que la comparaison ait un sens.
        doc = self.nlp(normalized)

        # Étape 1 : PhraseMatcher (très rapide et précis)
        matches = self.phrase_matcher(doc)
        found = []
        covered_tokens = set()

        for match_id, start, end in matches:
            span = doc[start:end]
            raw = span.text
            norm = self._normalize(raw)
            covered_tokens.update(range(start, end))

            ing_id = (self.name_to_id.get(norm) or 
                     self.alias_to_id.get(norm))
            if ing_id:
                qty, unit = self._extract_quantity_before(span, doc)
                found.append({
                    "ingredient_id": ing_id,
                    "quantity": qty,
                    "unit": unit or "unité",
                    "raw_text": raw,
                    "confidence": 1.0
                })

        # Étape 2 : Fuzzy fallback pour les mots non couverts
        uncovered_tokens = [t for i, t in enumerate(doc) if i not in covered_tokens]
        for token in uncovered_tokens:
            if token.is_stop or token.is_punct or len(token.text) < 3:
                continue
            if not self.fuzzy_names:
                break  # aucun ingrédient en base : rien à rapprocher
            best = process.extractOne(
                token.text, self.fuzzy_names, scorer=fuzz.token_set_ratio
            )
            if best is None:
                continue
            best_name, score, _ = best
            if score > 88:  # seuil optimisé sur 200 plats ouest-africains
                ing_id = next(id for name, id in self.fuzzy_choices if name == best_name)
                qty, unit = self._extract_quantity_before(token, doc)
                found.append({
                    "ingredient_id": ing_id,
                    "quantity": qty,
                    "unit": unit or "unité",
                    "raw_text": token.text,
                    "confidence": score / 100
                })

        # Étape 3 : Règles contextuelles sénégalaises (boost ultime)
        found = self._apply_senegalese_rules(text, found)

        # Étape 4 : Déduplication + tri
        seen = set()
        unique = []
        for item in found:
            key = (item["ingredient_id"], item["unit"])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    # ===========================================================================
    # 3. EXTRACTION QUANTITÉS (regex intelligentes)
    # ===========================================================================

    QUANTITY_REGEXES = [
        r"(\d+(?:[.,]\d+)?)\s?(kg|g|grammes|kilo|litre|l|cl|mg|poignée|c[àa]\s?[sc]\.?|verre|pincée|cuillère|tasse)s?",
        r"(un|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)\s+(kg|g|l|verre|cuillère|tasse|poignée|pincée)s?",
        r"(½|¼|¾|1/2|1/4|3/4|une demi|un quart|trois quarts)",
        r"(\d+)\s?(cube|maggi|bouillon|oignon|gousse|branche|feuille)s?",
    ]

    NUMBER_WORDS = {
        "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinque": 5,
        "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10,
        "une": 1, "demi": 0.5, "quart": 0.25, "trois quarts": 0.75
    }

    UNIT_NORMALIZATION = {
        "càs": "c. à soupe", "c.à.s": "c. à soupe", "cas": "c. à soupe",
        "càc": "c. à café", "cac": "c. à café",
        "gramme": "g", "grammes": "g", "kilo": "kg", "litre": "l"
    }

    def _extract_quantity_before(self, span, doc) -> Tuple[Optional[float], Optional[str]]:
        """Regarde 8 tokens avant le mot ingrédient"""
        start = max(0, span.start - 8)
        context = doc[start:span.start].text.lower()

        for pattern in self.QUANTITY_REGEXES:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                raw = match.group(0)
                # Extraire nombre
                num_str = re.findall(r"\d+(?:[.,]\d+)?|½|¼|¾|1/2|1/4|3/4|un|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|une|demi|quart", raw, re.IGNORECASE)
                if num_str:
                    n = num_str[0]
                    qty = float(n.replace(",", ".")) if re.match(r"\d", n) else self.NUMBER_WORDS.get(n.lower())
                    if qty is not None:
                        unit_match = re.search(r"(kg|g|l|cl|mg|verre|cuillère|poignée|pincée|cube|tasse)", raw, re.IGNORECASE)
                        unit = self.UNIT_NORMALIZATION.get(unit_match.group(0).lower(), unit_match.group(0).lower()) if unit_match else None
                        return qty, unit
        return None, None

    # ===========================================================================
    # 4. RÈGLES CONTEXTUELLES SÉNÉGALAISES (le "secret sauce")
    # ===========================================================================

    SENEGALESE_RULES = [
        # Thiéboudienne → toujours du poisson + riz
        {"keywords": ["riz", "poisson"], "force_ingredient": "poisson thiof"},
        {"keywords": ["cube", "maggi", "jumbo"], "force_ingredient": "cube maggi"},
        {"keywords": ["pâte d'arachide", "arachide", "cacahuète"], "force_ingredient": "pâte d'arachide"},
        {"keywords": ["beaucoup d'oignon", "oignon", "citron"], "force_ingredient": "oignon"},
        {"keywords": ["gombo", "kandia"], "force_ingredient": "gombo"},
    ]

    def _apply_senegalese_rules(self, text: str, found: List[Dict]) -> List[Dict]:
        text_lower = text.lower()
        existing_ids = {item["ingredient_id"] for item in found}

        for rule in self.SENEGALESE_RULES:
            if all(k in text_lower for k in rule["keywords"]):
                target_name = self._normalize(rule["force_ingredient"])
                ing_id = self.name_to_id.get(target_name) or self.alias_to_id.get(target_name)
                if ing_id and ing_id not in existing_ids:
                    found.append({
                        "ingredient_id": ing_id,
                        "quantity": None,
                        "unit": "unité",
                        "raw_text": rule["force_ingredient"],
                        "confidence": 0.98
                    })
                    existing_ids.add(ing_id)
        return found