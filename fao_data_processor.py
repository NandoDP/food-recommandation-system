import pandas as pd
import json
import uuid
import psycopg2
import os

class WAFCTFoodsExtractor:
    """
    Extrait les ALIMENTS DE BASE (table FOODS) depuis WAFCT 2019
    Feuille: '05 NV_sum_57 (per 100g EP)'
    """
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        
    def load_data(self):
        """Charge la feuille des aliments de base"""
        try:
            self.df = pd.read_excel(
                self.excel_path,
                sheet_name='05 NV_sum_57 (per 100g EP)',
                header=None
            )
            
            # Trouver l'en-tête (ligne contenant "Code")
            header_row = None
            for idx in range(10):
                if 'Code' in str(self.df.iloc[idx].values):
                    header_row = idx
                    break
            
            if header_row is not None:
                self.df.columns = self.df.iloc[header_row]
                self.df = self.df[header_row + 1:].reset_index(drop=True)
                print(f"✅ Feuille chargée : {len(self.df)} aliments")
                return True
            else:
                print("❌ En-têtes non trouvés")
                return False
                
        except Exception as e:
            print(f"❌ Erreur : {e}")
            return False
    
    def filter_priority_foods(self, extract_all=False):
        """
        Filtre les aliments prioritaires OU extrait TOUT
        
        Args:
            extract_all: Si True, extrait TOUS les aliments (pour mapping plats)
                        Si False, filtre les aliments sénégalais prioritaires
        """
        
        if extract_all:
            print("🌍 Extraction de TOUS les aliments WAFCT...")
            return self.df
        
        # Mots-clés pour aliments sénégalais prioritaires
        priority_keywords = [
            'riz', 'rice', 'mil', 'millet', 'maïs', 'maize', 'sorgho', 'sorghum',
            'fonio', 'manioc', 'cassava', 'patate', 'igname', 'yam', 'potato',
            'arachide', 'peanut', 'niébé', 'cowpea', 'haricot', 'bean',
            'tomate', 'tomato', 'oignon', 'onion', 'carotte', 'carrot',
            'chou', 'cabbage', 'gombo', 'okra', 'aubergine', 'eggplant',
            'mangue', 'mango', 'banane', 'banana', 'orange', 'citron', 'lemon',
            'poisson', 'fish', 'poulet', 'chicken', 'boeuf', 'beef', 'mouton',
            'lait', 'milk', 'huile', 'oil', 'sucre', 'sugar', 'sel', 'salt'
        ]
        
        # Filtrage
        mask = pd.Series([False] * len(self.df))
        name_cols = [self.df.columns[1], self.df.columns[2]]  # Colonnes B et C
        
        for col in name_cols:
            for keyword in priority_keywords:
                mask |= self.df[col].astype(str).str.lower().str.contains(
                    keyword, na=False, regex=False
                )
        
        filtered = self.df[mask]
        print(f"✅ {len(filtered)} aliments sénégalais prioritaires")
        
        return filtered
    
    def extract_foods_for_db(self, df_subset):
        """
        Extrait dans le format de la table FOODS
        
        Structure SQL:
        - id, local_name, scientific_name, category
        - nutritional_values (JSONB)
        - glycemic_index, sodium_content, potassium_content, origin
        """
        
        foods_data = []
        
        print("\n📦 Extraction vers table FOODS...")
        
        for idx, row in df_subset.iterrows():
            try:
                # Colonnes de base
                code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                name_en = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
                name_fr = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
                scientific = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None
                
                # Ignorer lignes invalides
                if code in ['', 'nan', 'Code']:
                    continue
                
                # Nom local (priorité français)
                local_name = name_fr if name_fr != 'nan' else name_en
                if not local_name or local_name == 'nan':
                    continue
                
                # Catégorie
                category = self._categorize_food(local_name + ' ' + name_en)
                
                # Valeurs nutritionnelles (colonnes I-M et suivantes)
                # Index réels dans le DataFrame après chargement
                energy = self._safe_float(row.iloc[9])
                water = self._safe_float(row.iloc[10])
                protein = self._safe_float(row.iloc[11])
                fat = self._safe_float(row.iloc[12])
                carbs = self._safe_float(row.iloc[13])
                fiber = self._safe_float(row.iloc[14])
                
                # Minéraux
                calcium = self._safe_float(row.iloc[17]) if len(row) > 17 else None
                iron = self._safe_float(row.iloc[18]) if len(row) > 18 else None
                magnesium = self._safe_float(row.iloc[19]) if len(row) > 19 else None
                phosphorus = self._safe_float(row.iloc[20]) if len(row) > 20 else None
                potassium = self._safe_float(row.iloc[21]) if len(row) > 21 else None
                sodium = self._safe_float(row.iloc[22]) if len(row) > 22 else None
                
                # JSONB nutritional_values
                nutritional_values = {
                    'energy_kcal': energy,
                    'water_g': water,
                    'protein_g': protein,
                    'fat_g': fat,
                    'carbohydrate_g': carbs,
                    'fiber_g': fiber,
                    'calcium_mg': calcium,
                    'iron_mg': iron,
                    'magnesium_mg': magnesium,
                    'phosphorus_mg': phosphorus,
                    'potassium_mg': potassium,
                    'sodium_mg': sodium,
                    'source': 'WAFCT 2019',
                    'code_wafct': code
                }
                
                # Estimation IG
                glycemic_index = self._estimate_gi(category, carbs, fiber)
                
                food_entry = {
                    'id': str(uuid.uuid4()),
                    'local_name': local_name[:200],
                    'scientific_name': scientific[:200] if scientific and scientific != 'nan' else None,
                    'category': category,
                    'nutritional_values': nutritional_values,
                    'glycemic_index': glycemic_index,
                    'sodium_content': int(sodium) if sodium else None,
                    'potassium_content': int(potassium) if potassium else None,
                    'origin': 'Afrique de l\'Ouest'
                }
                
                foods_data.append(food_entry)
                
            except Exception as e:
                print(f"⚠️ Erreur ligne {idx}: {e}")
                continue
        
        print(f"✅ {len(foods_data)} aliments extraits")
        return foods_data
    
    def _categorize_food(self, name: str) -> str:
        """Catégorisation automatique"""
        name = name.lower()
        
        categories = {
            'cereals': ['riz', 'rice', 'mil', 'millet', 'maïs', 'maize', 'sorgho', 
                       'sorghum', 'fonio', 'blé', 'wheat', 'pain', 'bread', 'farine', 'flour'],
            'legumes': ['haricot', 'bean', 'pois', 'pea', 'lentille', 'lentil', 
                       'niébé', 'cowpea', 'arachide', 'peanut', 'voandzou'],
            'vegetables': ['tomate', 'tomato', 'oignon', 'onion', 'carotte', 'carrot',
                          'chou', 'cabbage', 'gombo', 'okra', 'aubergine', 'eggplant',
                          'poivron', 'pepper', 'épinard', 'spinach'],
            'fruits': ['mangue', 'mango', 'banane', 'banana', 'papaye', 'papaya',
                      'orange', 'citron', 'lemon', 'pastèque', 'watermelon', 
                      'tamarin', 'tamarind', 'baobab'],
            'tubers': ['manioc', 'cassava', 'patate', 'potato', 'igname', 'yam'],
            'meat': ['poulet', 'chicken', 'boeuf', 'beef', 'mouton', 'mutton',
                    'chèvre', 'goat', 'viande', 'meat'],
            'fish': ['poisson', 'fish', 'thiof', 'yaboy', 'sardinelle', 'tilapia', 
                    'carpe', 'carp'],
            'dairy': ['lait', 'milk', 'yaourt', 'yogurt', 'fromage', 'cheese'],
            'oils_fats': ['huile', 'oil', 'beurre', 'butter', 'karité', 'shea', 'palme', 'palm'],
            'condiments': ['sel', 'salt', 'sucre', 'sugar', 'cube', 'bouillon']
        }
        
        for category, keywords in categories.items():
            if any(kw in name for kw in keywords):
                return category
        
        return 'other'
    
    def _estimate_gi(self, category: str, carbs: float, fiber: float) -> int:
        """Estimation Index Glycémique"""
        if not carbs or carbs < 5:
            return None
        
        fiber = fiber or 0
        
        if category in ['legumes', 'vegetables', 'fruits'] or fiber > 5:
            return 40
        elif category in ['cereals', 'tubers'] and fiber > 3:
            return 60
        else:
            return 70
    
    def _safe_float(self, value):
        """Conversion sécurisée float"""
        try:
            if pd.isna(value) or str(value).strip() in ['nan', '', '[0.7]']:
                return None
            return float(str(value).replace('[', '').replace(']', ''))
        except:
            return None
    
    def export_json(self, foods_data: list, filename='foods_wafct.json'):
        """Export JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(foods_data, f, ensure_ascii=False, indent=2)
        print(f"✅ {filename} créé")
    
    def generate_sql(self, foods_data: list, filename='insert_foods.sql'):
        """Génère SQL pour table FOODS"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("-- TABLE FOODS - Aliments de base WAFCT 2019\n")
            f.write("-- À exécuter après script.sql\n\n")
            
            for food in foods_data:
                name = food['local_name'].replace("'", "''")
                scientific = food['scientific_name'].replace("'", "''") if food['scientific_name'] else None
                category = food['category']
                nutr = json.dumps(food['nutritional_values'])
                gi = food['glycemic_index']
                sodium = food['sodium_content']
                potassium = food['potassium_content']
                origin = food['origin']
                
                f.write(f"""INSERT INTO foods (id, local_name, scientific_name, category, nutritional_values, glycemic_index, sodium_content, potassium_content, origin)
VALUES ('{food['id']}', '{name}', {f"'{scientific}'" if scientific else 'NULL'}, '{category}', '{nutr}'::jsonb, {gi if gi else 'NULL'}, {sodium if sodium else 'NULL'}, {potassium if potassium else 'NULL'}, '{origin}');

""")
        
        print(f"✅ {filename} créé")
    
    def insert_into_postgres(self, foods_data: list, dbname='nutrition_westaf', 
                            user=None, password=None, host='localhost', port=5432):
        """Insertion directe PostgreSQL"""
        
        user = user or os.environ.get('PGUSER', 'postgres')
        password = password or os.environ.get('PGPASSWORD')
        
        try:
            conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            cur = conn.cursor()
            print(f"🔌 Connecté à Postgres {user}@{host}:{port}/{dbname}")
            
            inserted = 0
            for food in foods_data:
                try:
                    cur.execute("""
                        INSERT INTO foods (id, local_name, scientific_name, category, 
                                         nutritional_values, glycemic_index, 
                                         sodium_content, potassium_content, origin)
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        food['id'],
                        food['local_name'],
                        food['scientific_name'],
                        food['category'],
                        json.dumps(food['nutritional_values']),
                        food['glycemic_index'],
                        food['sodium_content'],
                        food['potassium_content'],
                        food['origin']
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"⚠️ Erreur insertion {food['local_name']}: {e}")
            
            conn.commit()
            print(f"✅ {inserted} aliments insérés dans PostgreSQL")
            
        except Exception as e:
            print(f"❌ Erreur PostgreSQL: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()


# === EXÉCUTION ===
if __name__ == "__main__":
    print("🍎 EXTRACTION TABLE FOODS (aliments de base WAFCT)\n")
    
    excel_path = "C:/Users/maodo/Downloads/WAFCT_2019.xlsx"
    
    extractor = WAFCTFoodsExtractor(excel_path)
    
    if not extractor.load_data():
        exit(1)
    
    # CHOIX: Extraire TOUT ou filtrer prioritaires
    extract_all = True  # Mettre False pour filtrer seulement sénégalais
    
    filtered_df = extractor.filter_priority_foods(extract_all=extract_all)
    foods_data = extractor.extract_foods_for_db(filtered_df)
    
    print(f"\n📊 {len(foods_data)} aliments extraits")
    
    # Exemple
    if foods_data:
        print("\n🔍 Exemple:")
        ex = foods_data[0]
        print(f"   {ex['local_name']} ({ex['category']})")
        print(f"   IG: {ex['glycemic_index']}")
        print(f"   Sodium: {ex['sodium_content']} mg")
    
    # Export
    # extractor.export_json(foods_data)
    # extractor.generate_sql(foods_data)
    
    # Insertion directe (optionnel)
    extractor.insert_into_postgres(foods_data, user='postgres', password='nando')
    
    print("\n✅ TERMINÉ!")
    # print("📁 Fichiers: foods_wafct.json, insert_foods.sql")













# import pandas as pd
# import json
# import uuid
# from pathlib import Path

# class WAFCTDataProcessor:
#     """
#     Processeur pour la Table WAFCT 2019 (FAO West Africa Food Composition)
#     Extrait les données des feuilles '03 NV_sum_39' et '05 NV_sum_57'
#     """
    
#     def __init__(self, excel_path: str):
#         self.excel_path = excel_path
#         self.df = None
        
#     def load_data(self):
#         """Charge les feuilles Excel avec les bons en-têtes"""
#         try:
#             # Les vrais en-têtes sont à la ligne 3 (index 2)
#             self.df = pd.read_excel(
#                 self.excel_path, 
#                 sheet_name='05 NV_sum_57 (per 100g EP)',
#                 header=2,  # Ligne 3
#                 skiprows=0  # Ne pas sauter de lignes
#             )
            
#             # Afficher les vraies colonnes
#             print(f"✅ Feuille '05 NV_sum_57' chargée : {len(self.df)} aliments")
#             print(f"\n📊 Colonnes détectées ({len(self.df.columns)} colonnes):")
#             for i, col in enumerate(self.df.columns[:15]):
#                 print(f"   {i}: {col}")
            
#             # Afficher aperçu des données
#             print(f"\n🔍 Aperçu des 3 premières lignes :")
#             print(self.df[['Code', 'Food name in English', 'Food name in French']].head(3))
            
#             return True
            
#         except Exception as e:
#             print(f"❌ Erreur : {e}")
#             print("\n💡 Essai avec une autre méthode...")
            
#             # Plan B : Charger sans header et reconstruire
#             try:
#                 self.df = pd.read_excel(
#                     self.excel_path,
#                     sheet_name='05 NV_sum_57 (per 100g EP)',
#                     header=None
#                 )
                
#                 # Trouver la ligne d'en-tête (contient "Code")
#                 header_row = None
#                 for idx, row in self.df.head(10).iterrows():
#                     if 'Code' in str(row.values):
#                         header_row = idx
#                         break
                
#                 if header_row is not None:
#                     # Définir cette ligne comme en-tête
#                     self.df.columns = self.df.iloc[header_row]
#                     self.df = self.df[header_row + 1:].reset_index(drop=True)
#                     print(f"✅ En-têtes trouvés à la ligne {header_row + 1}")
#                     print(f"📊 {len(self.df)} aliments chargés")
#                     return True
#                 else:
#                     print("❌ Impossible de trouver les en-têtes")
#                     return False
                    
#             except Exception as e2:
#                 print(f"❌ Erreur Plan B : {e2}")
#                 return False
    
#     def filter_senegalese_foods(self, limit=50):
#         """
#         Filtre les aliments sénégalais/ouest-africains prioritaires
#         """
#         # Aliments prioritaires
#         priority_keywords = [
#             # Céréales
#             'riz', 'rice', 'mil', 'millet', 'maïs', 'maize', 'corn', 'sorgho', 'sorghum',
#             'fonio', 'couscous', 'pain', 'bread', 'thiakry',
#             # Tubercules
#             'manioc', 'cassava', 'patate', 'sweet potato', 'igname', 'yam',
#             'pomme de terre', 'potato',
#             # Légumineuses
#             'arachide', 'peanut', 'groundnut', 'niébé', 'cowpea', 'haricot', 'bean',
#             'pois', 'pea', 'lentille', 'lentil', 'voandzou', 'bambara',
#             # Légumes
#             'tomate', 'tomato', 'oignon', 'onion', 'carotte', 'carrot',
#             'chou', 'cabbage', 'aubergine', 'eggplant', 'gombo', 'okra',
#             'poivron', 'pepper', 'épinard', 'spinach', 'moringa',
#             # Fruits
#             'mangue', 'mango', 'banane', 'banana', 'papaye', 'papaya',
#             'pastèque', 'watermelon', 'orange', 'citron', 'lemon',
#             'bissap', 'hibiscus', 'baobab', 'ditakh', 'tamarin', 'tamarind',
#             # Poissons
#             'poisson', 'fish', 'thiof', 'yaboy', 'sardinelle', 'sardine',
#             'carpe', 'carp', 'tilapia', 'capitaine',
#             # Viandes
#             'poulet', 'chicken', 'boeuf', 'beef', 'mouton', 'mutton',
#             'chèvre', 'goat',
#             # Huiles
#             'huile', 'oil', 'arachide', 'palme', 'palm', 'karité', 'shea',
#             # Condiments
#             'nététou', 'soumbala', 'dawadawa', 'cube', 'bouillon'
#         ]
        
#         # Chercher dans les colonnes de noms
#         name_cols = []
#         for col in self.df.columns:
#             col_str = str(col).lower()
#             if 'food name' in col_str or 'nom' in col_str or 'aliment' in col_str:
#                 name_cols.append(col)
        
#         if not name_cols:
#             # Utiliser les 3 premières colonnes textuelles
#             name_cols = [self.df.columns[1], self.df.columns[2]]
        
#         print(f"\n🔍 Colonnes utilisées pour la recherche : {name_cols}")
        
#         # Créer un masque de filtrage
#         mask = pd.Series([False] * len(self.df))
#         for col in name_cols:
#             for keyword in priority_keywords:
#                 mask |= self.df[col].astype(str).str.lower().str.contains(
#                     keyword, na=False, regex=False
#                 )
        
#         filtered = self.df[mask]
#         # filtered = self.df[mask].head(limit)
#         print(f"✅ {len(filtered)} aliments sélectionnés")
        
#         return filtered
    
#     def extract_foods_for_db(self, df_subset):
#         """
#         Extrait les données dans le format de votre table 'foods'
#         """
#         foods_data = []
        
#         # Identifier les colonnes par position (plus fiable)
#         # A=0:Code, B=1:English, C=2:French, D=3:Scientific
#         # I=8:WATER, J=9:PROTCNT, K=10:FAT, L=11:CHOAVLDF, M=12:FIBTG
        
#         print(f"\n📊 Colonnes utilisées:")
#         print(f"   Code (A) : {df_subset.columns[0]}")
#         print(f"   English (B) : {df_subset.columns[1]}")
#         print(f"   French (C) : {df_subset.columns[2]}")
        
#         for idx, row in df_subset.iterrows():
#             try:
#                 # Extraire les noms
#                 code = str(row.iloc[0]) if pd.notna(row.iloc[0]) else 'Unknown'
#                 name_en = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ''
#                 name_fr = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
#                 scientific = str(row.iloc[3]) if pd.notna(row.iloc[3]) else None
                
#                 # Priorité au nom français
#                 local_name = name_fr if name_fr and name_fr != 'nan' else name_en
                
#                 # Nettoyer le nom
#                 if local_name.startswith('nan'):
#                     local_name = name_en
                
#                 # Déterminer la catégorie
#                 category = self._categorize_food(local_name + ' ' + name_en)
                
#                 # Valeurs nutritionnelles (colonnes I-M = indices 8-12)
#                 energy = self._safe_float(row.iloc[9]) if len(row) > 9 else None
#                 water = self._safe_float(row.iloc[10]) if len(row) > 10 else None
#                 protein = self._safe_float(row.iloc[11]) if len(row) > 11 else None
#                 fat = self._safe_float(row.iloc[12]) if len(row) > 12 else None
#                 carbs = self._safe_float(row.iloc[13]) if len(row) > 13 else None
#                 fiber = self._safe_float(row.iloc[14]) if len(row) > 14 else None
                
#                 calcium = self._safe_float(row.iloc[17]) if len(row) > 17 else None
#                 magnesium = self._safe_float(row.iloc[19]) if len(row) > 19 else None
#                 potassium = self._safe_float(row.iloc[21]) if len(row) > 21 else None
#                 sodium = self._safe_float(row.iloc[22]) if len(row) > 22 else None
                
#                 # # Calculer l'énergie
#                 # energy = None
#                 # if protein is not None and fat is not None and carbs is not None:
#                 #     energy = round((protein * 4) + (carbs * 4) + (fat * 9), 1)
                
#                 nutritional_values = {
#                     'water_g': water,
#                     'energy_kcal': energy,
#                     'protein_g': protein,
#                     'fat_g': fat,
#                     'carbohydrate_g': carbs,
#                     'fiber_g': fiber,
#                     'calcium_mg': calcium,
#                     'magnesium_mg': magnesium,
#                     'sodium_mg': sodium,
#                     'potassium_mg': potassium,
#                     'source': 'WAFCT 2019'
#                 }
                
#                 food_entry = {
#                     'id': str(uuid.uuid4()),
#                     'code_wafct': code[:50],
#                     'local_name': local_name[:200],
#                     'scientific_name': scientific[:200] if scientific and scientific != 'nan' else None,
#                     'category': category,
#                     'nutritional_values': nutritional_values,
#                     'glycemic_index': self._estimate_gi(category, nutritional_values),
#                     'origin': 'Afrique de l\'Ouest'
#                 }
                
#                 foods_data.append(food_entry)
                
#             except Exception as e:
#                 print(f"⚠️ Erreur ligne {idx}: {e}")
#                 continue
        
#         return foods_data
    
#     def _categorize_food(self, food_name: str) -> str:
#         """Catégorise automatiquement"""
#         food_name = food_name.lower()
        
#         categories = {
#             'cereals': ['riz', 'rice', 'mil', 'millet', 'maïs', 'maize', 'corn', 
#                        'sorgho', 'sorghum', 'fonio', 'blé', 'wheat', 'pain', 'bread'],
#             'legumes': ['haricot', 'bean', 'pois', 'pea', 'lentille', 'lentil', 
#                        'niébé', 'cowpea', 'arachide', 'peanut', 'voandzou', 'bambara'],
#             'vegetables': ['tomate', 'tomato', 'oignon', 'onion', 'carotte', 'carrot',
#                           'chou', 'cabbage', 'gombo', 'okra', 'aubergine', 'eggplant'],
#             'fruits': ['mangue', 'mango', 'banane', 'banana', 'papaye', 'papaya',
#                       'orange', 'citron', 'lemon', 'pastèque', 'watermelon'],
#             'tubers': ['manioc', 'cassava', 'patate', 'potato', 'igname', 'yam'],
#             'meat': ['poulet', 'chicken', 'boeuf', 'beef', 'mouton', 'mutton',
#                     'chèvre', 'goat', 'viande', 'meat'],
#             'fish': ['poisson', 'fish', 'thiof', 'yaboy', 'sardinelle', 'tilapia'],
#             'dairy': ['lait', 'milk', 'yaourt', 'yogurt', 'fromage', 'cheese'],
#             'oils_fats': ['huile', 'oil', 'beurre', 'butter', 'karité', 'shea'],
#             'nuts_seeds': ['noix', 'nut', 'arachide', 'peanut', 'sésame', 'sesame']
#         }
        
#         for category, keywords in categories.items():
#             if any(kw in food_name for kw in keywords):
#                 return category
        
#         return 'other'
    
#     def _estimate_gi(self, category: str, nutr_values: dict) -> int:
#         """Estime l'Index Glycémique"""
#         fiber = nutr_values.get('fiber_g', 0) or 0
#         carbs = nutr_values.get('carbohydrate_g', 0) or 0
        
#         if carbs < 5:
#             return None
        
#         if category in ['legumes', 'vegetables', 'fruits'] or fiber > 5:
#             return 40
        
#         if category in ['cereals', 'tubers'] and fiber > 3:
#             return 60
        
#         return 70
    
#     def _safe_float(self, value, default=None):
#         """Conversion sécurisée"""
#         try:
#             if pd.isna(value) or value == '' or str(value).strip() in ['[0.7]', 'nan']:
#                 return default
#             val_str = str(value).replace('[', '').replace(']', '').strip()
#             return float(val_str)
#         except:
#             return default
    
#     def generate_sql_insert(self, foods_data: list, output_file: str = './insert_foods.sql'):
#         """Génère les INSERT SQL"""
        
#         with open(output_file, 'w', encoding='utf-8') as f:
#             f.write("-- Insertion des aliments WAFCT 2019\n")
#             f.write("-- À exécuter après script.sql\n\n")
            
#             for food in foods_data:
#                 local_name = food['local_name'].replace("'", "''")
#                 scientific = food['scientific_name'].replace("'", "''") if food['scientific_name'] else None
                
#                 f.write(f"""INSERT INTO foods (
#     id, local_name, scientific_name, category, 
#     nutritional_values, glycemic_index, origin
# ) VALUES (
#     `{food['id']}`,
#     `{local_name}`,
#     {f"`{scientific}`" if scientific else 'NULL'},
#     `{food['category']}`,
#     `{json.dumps(food['nutritional_values'])}`::jsonb,
#     {food['glycemic_index'] if food['glycemic_index'] else 'NULL'},
#     `{food['origin']}`
# );

# """)
        
#         print(f"\n✅ {output_file} créé ({len(foods_data)} aliments)")
    
#     def export_to_json(self, foods_data: list, output_file: str = './foods_extracted.json'):
#         """Export JSON"""
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(foods_data, f, ensure_ascii=False, indent=2)
        
#         print(f"✅ {output_file} créé")


# # ========== UTILISATION ==========
# if __name__ == "__main__":
#     print("🚀 Extraction données WAFCT 2019\n")
    
#     excel_path = "C:/Users/maodo/Downloads/WAFCT_2019.xlsx"
    
#     processor = WAFCTDataProcessor(excel_path)
    
#     # 1. Charger
#     if not processor.load_data():
#         exit(1)
    
#     # 2. Filtrer (50 aliments sénégalais)
#     senegalese_df = processor.filter_senegalese_foods(limit=50)
    
#     # 3. Extraire
#     foods_data = processor.extract_foods_for_db(senegalese_df)
    
#     print(f"\n📊 Extraction réussie : {len(foods_data)} aliments")
    
#     # Afficher exemple
#     if foods_data:
#         print(f"\n🔍 Exemple d'aliment extrait:")
#         example = foods_data[0]
#         print(f"   Nom : {example['local_name']}")
#         print(f"   Catégorie : {example['category']}")
#         print(f"   IG estimé : {example['glycemic_index']}")
#         print(f"   Nutriments : {example['nutritional_values']}")
    
#     # 4. Exporter
#     # processor.export_to_json(foods_data)
#     processor.generate_sql_insert(foods_data)
    
#     print("\n" + "="*60)
#     print("✅ TERMINÉ!")
#     print("="*60)
#     print("\n📁 Fichiers générés :")
#     print("   1. foods_extracted.json")
#     print("   2. insert_foods.sql")
#     print("\n📝 Prochaine étape : Vérifier foods_extracted.json")
