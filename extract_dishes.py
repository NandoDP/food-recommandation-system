import pandas as pd
import json
import uuid
import psycopg2
import os

class CompleteDishesExtractor:
    """
    Extrait DISHES + crée INGREDIENTS + lie via DISH_INGREDIENTS
    Respecte le modèle: foods → ingredients → dish_ingredients ← dishes
    """
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df_dishes = None
        self.df_foods = None
        self.foods_map = {}  # code_wafct → food_data
        
    def load_all_foods(self):
        """Charge TOUS les aliments pour mapping"""
        try:
            self.df_foods = pd.read_excel(
                self.excel_path,
                sheet_name='05 NV_sum_57 (per 100g EP)',
                header=None
            )
            
            # Trouver en-tête
            header_row = None
            for idx in range(10):
                if 'Code' in str(self.df_foods.iloc[idx].values):
                    header_row = idx
                    break
            
            if header_row:
                self.df_foods.columns = self.df_foods.iloc[header_row]
                self.df_foods = self.df_foods[header_row + 1:].reset_index(drop=True)
            
            # Créer dictionnaire code → données
            for idx, row in self.df_foods.iterrows():
                code = str(row.iloc[0]).strip()
                if code and code not in ['', 'nan', 'Code']:
                    name_en = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ''
                    name_fr = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''
                    
                    self.foods_map[code] = {
                        'code': code,
                        'name_en': name_en,
                        'name_fr': name_fr,
                        'name': name_fr if name_fr != 'nan' else name_en
                    }
            
            print(f"✅ {len(self.foods_map)} codes WAFCT indexés pour mapping")
            return True
            
        except Exception as e:
            print(f"❌ Erreur chargement foods: {e}")
            return False
    
    def load_mixed_dishes(self):
        """Charge feuille '09 Mixed Dishes'"""
        try:
            self.df_dishes = pd.read_excel(
                self.excel_path,
                sheet_name='09 Mixed dishes',
                header=None
            )
            print(f"✅ Feuille Mixed Dishes chargée : {len(self.df_dishes)} lignes")
            return True
        except Exception as e:
            print(f"⚠️ Erreur Mixed Dishes: {e}")
            return False
    
    def extract_dishes_complete(self):
        """
        Extrait plats avec ingrédients mappés vers foods
        
        Retourne:
        - dishes: liste de plats pour table DISHES
        - ingredients: liste d'ingrédients pour table INGREDIENTS
        - dish_ingredients: liste de relations pour table DISH_INGREDIENTS
        """
        
        dishes = []
        ingredients_dict = {}  # code → ingredient_data
        dish_ingredients = []
        
        current_dish = None
        
        print("\n🍲 Extraction plats + ingrédients...\n")
        
        for idx, row in self.df_dishes.iterrows():
            obs_num = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            code = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
            name_en = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
            name_fr = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
            method = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ''
            
            # Ignorer en-têtes
            if code in ['', 'nan', 'Code'] or 'Cereals' in name_en:
                continue
            
            # NOUVELLE LIGNE DE PLAT (Observation# présent)
            if obs_num and obs_num.isdigit():
                if current_dish:
                    dishes.append(current_dish)
                
                dish_id = str(uuid.uuid4())
                current_dish = {
                    'id': dish_id,
                    'name': name_fr if name_fr != 'nan' else name_en,
                    'description': name_en if len(name_en) > len(name_fr) else name_fr,
                    'meal_type': self._guess_meal_type(name_en + name_fr),
                    'method': method,
                    'cuisine_origin': 'west_african'
                }
                
                # print(f"📌 Plat: {current_dish['name'][:50]}")
            
            # LIGNE D'INGRÉDIENT (Observation# vide, code présent)
            elif code and code != 'nan' and current_dish:
                quantity = self._safe_float(row.iloc[4]) if len(row) > 4 else None
                
                # CRÉER/RÉCUPÉRER INGREDIENT
                if code not in ingredients_dict:
                    # print(f'Code {code} not in ingredients_dict')
                    # Chercher dans foods_map
                    if code in self.foods_map:
                        food_data = self.foods_map[code]
                        ing_name = food_data['name']
                        found = True
                        status = "✅"
                        # print('Found:', code, ing_name)
                    else:
                        ing_name = name_fr if name_fr != 'nan' else name_en
                        found = False
                        status = "⚠️"
                        # print('Not found:', code, ing_name)
                    
                    ingredients_dict[code] = {
                        'id': str(uuid.uuid4()),
                        'name': ing_name,
                        'code_wafct': code,
                        'food_id': None,  # Sera rempli par SQL
                        'found_in_foods': found
                    }
                else:
                    status = "✅" if ingredients_dict[code]['found_in_foods'] else "⚠️"
                    # print(f'Code {code}: Status {status}')
                
                # CRÉER RELATION DISH_INGREDIENTS
                dish_ingredients.append({
                    'dish_id': current_dish['id'],
                    'ingredient_id': ingredients_dict[code]['id'],
                    'ingredient_code': code,
                    'quantity': quantity,
                    'unit': 'g'
                })
                
                print(f"   {status} {ingredients_dict[code]['name'][:35]} ({quantity}g)")
        
        # Dernier plat
        if current_dish:
            dishes.append(current_dish)
        
        ingredients_list = list(ingredients_dict.values())
        
        print(f"\n✅ Extraction terminée:")
        print(f"   - {len(dishes)} plats")
        print(f"   - {len(ingredients_list)} ingrédients uniques")
        print(f"   - {len(dish_ingredients)} relations")
        
        not_found = [ing for ing in ingredients_list if not ing['found_in_foods']]
        if not_found:
            print(f"\n⚠️ {len(not_found)} ingrédients non trouvés dans foods:")
            for ing in not_found[:5]:
                print(f"   - {ing['code_wafct']}: {ing['name']}")
        
        return dishes, ingredients_list, dish_ingredients
    
    def add_manual_senegalese_dishes(self):
        """Ajoute 6 plats sénégalais avec ingrédients manuels"""
        
        manual_dishes = []
        manual_ingredients = {}
        manual_dish_ingredients = []
        
        # Codes fictifs pour ingrédients manuels (préfixe SN_)
        senegalese_recipes = [
            {
                'name': 'Thiéboudienne',
                'description': 'Riz au poisson et légumes, plat national du Sénégal',
                'meal_type': 'lunch',
                'ingredients': [
                    ('SN_RICE_01', 'Riz brisé', 300),
                    ('SN_FISH_01', 'Thiof', 200),
                    ('SN_VEG_01', 'Tomate concentrée', 50),
                    ('SN_OIL_01', 'Huile arachide', 40),
                ]
            },
            {
                'name': 'Yassa Poulet',
                'description': 'Poulet mariné aux oignons et citron',
                'meal_type': 'lunch',
                'ingredients': [
                    ('SN_MEAT_01', 'Poulet', 400),
                    ('SN_VEG_02', 'Oignon', 300),
                    ('SN_FRUIT_01', 'Citron', 60),
                ]
            },
            {
                'name': 'Mafé',
                'description': 'Ragoût à la sauce arachide',
                'meal_type': 'lunch',
                'ingredients': [
                    ('SN_MEAT_02', 'Boeuf', 300),
                    ('SN_LEG_01', 'Pâte arachide', 150),
                    ('SN_VEG_03', 'Carotte', 100),
                ]
            },
            {
                'name': 'Thiéré',
                'description': 'Couscous de mil au lait caillé',
                'meal_type': 'breakfast',
                'ingredients': [
                    ('SN_CER_01', 'Mil (couscous)', 200),
                    ('SN_DAIRY_01', 'Lait caillé', 300),
                    ('SN_SUGAR_01', 'Sucre', 40),
                ]
            },
            {
                'name': 'Ndambé',
                'description': 'Haricots niébé en sauce',
                'meal_type': 'breakfast',
                'ingredients': [
                    ('SN_LEG_02', 'Niébé', 200),
                    ('SN_OIL_02', 'Huile palme', 30),
                    ('SN_VEG_02', 'Oignon', 60),
                ]
            },
            {
                'name': 'Thiakry',
                'description': 'Couscous de mil au yaourt',
                'meal_type': 'breakfast',
                'ingredients': [
                    ('SN_CER_01', 'Mil (couscous)', 150),
                    ('SN_DAIRY_02', 'Yaourt', 250),
                    ('SN_SUGAR_01', 'Sucre', 50),
                ]
            }
        ]
        
        for recipe in senegalese_recipes:
            dish_id = str(uuid.uuid4())
            
            manual_dishes.append({
                'id': dish_id,
                'name': recipe['name'],
                'description': recipe['description'],
                'meal_type': recipe['meal_type'],
                'cuisine_origin': 'senegalese'
            })
            
            for code, name, qty in recipe['ingredients']:
                if code not in manual_ingredients:
                    manual_ingredients[code] = {
                        'id': str(uuid.uuid4()),
                        'name': name,
                        'code_wafct': code,
                        'food_id': None,
                        'found_in_foods': False
                    }
                
                manual_dish_ingredients.append({
                    'dish_id': dish_id,
                    'ingredient_id': manual_ingredients[code]['id'],
                    'ingredient_code': code,
                    'quantity': qty,
                    'unit': 'g' if code != 'SN_DAIRY_01' and code != 'SN_DAIRY_02' else 'ml'
                })
        
        return manual_dishes, list(manual_ingredients.values()), manual_dish_ingredients
    
    def _guess_meal_type(self, name: str) -> str:
        name = name.lower()
        if any(k in name for k in ['porridge', 'bouillie', 'breakfast']):
            return 'breakfast'
        elif any(k in name for k in ['dinner', 'dîner']):
            return 'dinner'
        return 'lunch'
    
    def _safe_float(self, value):
        try:
            if pd.isna(value) or str(value).strip() in ['nan', '', '[0.7]']:
                return None
            return float(str(value).replace('[', '').replace(']', ''))
        except:
            return None
    
    def export_all_json(self, dishes, ingredients, dish_ingredients, 
                       filename='complete_dishes_data.json'):
        """Export JSON complet"""
        data = {
            'dishes': dishes,
            'ingredients': ingredients,
            'dish_ingredients': dish_ingredients
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ {filename} créé")
    
    def generate_complete_sql(self, dishes, ingredients, dish_ingredients,
                             filename='insert_complete_dishes.sql'):
        """Génère SQL complet pour les 3 tables"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("-- INSERTION COMPLÈTE: DISHES + INGREDIENTS + DISH_INGREDIENTS\n")
            f.write("-- Ordre: 1. INGREDIENTS, 2. DISHES, 3. DISH_INGREDIENTS\n\n")
            
            # 1. INGREDIENTS
            f.write("-- ============ TABLE INGREDIENTS ============\n\n")
            for ing in ingredients:
                name = ing['name'].replace("'", "''")
                code = ing['code_wafct']
                
                if ing['found_in_foods']:
                    # Lier avec foods via code WAFCT
                    f.write(f"""-- {name} ({code})
INSERT INTO ingredients (id, name, food_id)
SELECT '{ing['id']}', '{name}', id
FROM foods WHERE nutritional_values->>'code_wafct' = '{code}'
LIMIT 1;

""")
                else:
                    f.write(f"""-- ⚠️ {name} ({code}) - Non trouvé dans foods
INSERT INTO ingredients (id, name, food_id)
VALUES ('{ing['id']}', '{name}', NULL);

""")
            
            # 2. DISHES
            f.write("\n-- ============ TABLE DISHES ============\n\n")
            for dish in dishes:
                name = dish['name'].replace("'", "''")
                desc = dish['description'].replace("'", "''")
                
                f.write(f"""INSERT INTO dishes (id, name, description, meal_type, cuisine_origin)
VALUES ('{dish['id']}', '{name}', '{desc}', '{dish['meal_type']}', '{dish['cuisine_origin']}');

""")
            
            # 3. DISH_INGREDIENTS
            f.write("\n-- ============ TABLE DISH_INGREDIENTS ============\n\n")
            for di in dish_ingredients:
                qty = di['quantity'] if di['quantity'] else 0
                
                f.write(f"""INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, unit)
VALUES ('{di['dish_id']}', '{di['ingredient_id']}', {qty}, '{di['unit']}');

""")
        
        print(f"✅ {filename} créé")
    
    def insert_into_postgres(self, dishes, ingredients, dish_ingredients,
                            dbname='nutrition_westaf', user=None, password=None,
                            host='localhost', port=5432):
        """Insertion PostgreSQL complète"""
        
        user = user or os.environ.get('PGUSER', 'postgres')
        password = password or os.environ.get('PGPASSWORD')
        
        try:
            conn = psycopg2.connect(dbname=dbname, user=user, password=password, 
                                   host=host, port=port)
            cur = conn.cursor()
            print(f"\n🔌 Connecté à Postgres {user}@{host}:{port}/{dbname}")
            
            # 1. INGREDIENTS
            print("\n📝 Insertion INGREDIENTS...")
            for ing in ingredients:
                # Chercher food_id si trouvé
                food_id = None
                if ing['found_in_foods']:
                    cur.execute("""
                        SELECT id FROM foods 
                        WHERE nutritional_values->>'code_wafct' = %s
                        LIMIT 1
                    """, (ing['code_wafct'],))
                    result = cur.fetchone()
                    if result:
                        food_id = result[0]
                
                cur.execute("""
                    INSERT INTO ingredients (id, name, food_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (ing['id'], ing['name'], food_id))
            
            print(f"   ✅ {len(ingredients)} ingrédients insérés")
            
            # 2. DISHES
            print("\n🍲 Insertion DISHES...")
            for dish in dishes:
                cur.execute("""
                    INSERT INTO dishes (id, name, description, meal_type, method, cuisine_origin)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (dish['id'], dish['name'], dish['description'], 
                      dish['meal_type'], dish.get('method', ''), dish['cuisine_origin']))
            
            print(f"   ✅ {len(dishes)} plats insérés")
            
            # 3. DISH_INGREDIENTS
            print("\n🔗 Insertion DISH_INGREDIENTS...")
            for di in dish_ingredients:
                cur.execute("""
                    INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, unit)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (dish_id, ingredient_id) 
                    DO UPDATE SET quantity = EXCLUDED.quantity, unit = EXCLUDED.unit
                """, (di['dish_id'], di['ingredient_id'], 
                      di['quantity'], di['unit']))
            
            print(f"   ✅ {len(dish_ingredients)} relations insérées")
            
            conn.commit()
            print("\n✅ Transaction validée (COMMIT)")
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()


# === EXÉCUTION ===
if __name__ == "__main__":
    print("🍲 EXTRACTION COMPLÈTE DISHES + INGREDIENTS + RELATIONS\n")
    
    excel_path = "data/WAFCT_2019.xlsx"
    
    extractor = CompleteDishesExtractor(excel_path)
    
    # 1. Charger foods pour mapping
    if not extractor.load_all_foods():
        print("⚠️ Foods non chargés, mapping limité")
    
    # 2. Extraire plats WAFCT
    all_dishes = []
    all_ingredients = []
    all_dish_ingredients = []
    
    if extractor.load_mixed_dishes():
        wafct_dishes, wafct_ing, wafct_di = extractor.extract_dishes_complete()
        all_dishes.extend(wafct_dishes)
        all_ingredients.extend(wafct_ing)
        all_dish_ingredients.extend(wafct_di)
    
    # 3. Ajouter plats sénégalais manuels
    manual_dishes, manual_ing, manual_di = extractor.add_manual_senegalese_dishes()
    all_dishes.extend(manual_dishes)
    all_ingredients.extend(manual_ing)
    all_dish_ingredients.extend(manual_di)
    
    print(f"\n{'='*60}")
    print(f"📊 TOTAL:")
    print(f"   - {len(all_dishes)} plats")
    print(f"   - {len(all_ingredients)} ingrédients uniques")
    print(f"   - {len(all_dish_ingredients)} relations")
    print(f"{'='*60}")
    
    # 4. Export
    # extractor.export_all_json(all_dishes, all_ingredients, all_dish_ingredients)
    # extractor.generate_complete_sql(all_dishes, all_ingredients, all_dish_ingredients)
    
    # 5. Insertion PostgreSQL (optionnel)
    extractor.insert_into_postgres(all_dishes, all_ingredients, all_dish_ingredients,
                                   user='postgres', password='nando')
    
    print("\n✅ TERMINÉ!")
    # print("📁 Fichiers: complete_dishes_data.json, insert_complete_dishes.sql")





















# import pandas as pd
# import json
# import uuid
# import os
# import psycopg2

# class WAFCTDishesExtractor:
#     """
#     Extrait les plats composés de la feuille '09 Mixed Dishes'
#     Structure : 1 plat = plusieurs lignes (ligne principale + ingrédients)
#     """
    
#     def __init__(self, excel_path: str):
#         self.excel_path = excel_path
#         self.df = None
        
#     def load_mixed_dishes_sheet(self):
#         """Charge la feuille '09 Mixed Dishes'"""
#         try:
#             # Charger TOUTES les lignes sans header
#             self.df = pd.read_excel(
#                 self.excel_path,
#                 sheet_name='09 Mixed dishes',
#                 header=None
#             )
            
#             print(f"✅ Feuille '09 Mixed Dishes' chargée : {len(self.df)} lignes")
            
#             # Afficher les 20 premières lignes pour debug
#             print("\n🔍 Aperçu des 20 premières lignes :")
#             print(self.df.head(20).to_string())
            
#             return True
            
#         except Exception as e:
#             print(f"❌ Erreur : {e}")
#             return False
    
#     def extract_dishes_with_ingredients(self):
#         """
#         Extrait les plats avec leur structure multi-lignes
        
#         Structure attendue :
#         - Ligne plat : Observation#, Code plat, Nom EN, Nom FR, ..., Méthode
#         - Lignes ingrédients : vide, Code ingrédient, Nom EN, Nom FR, ..., Quantité, ...
#         """
        
#         dishes = []
#         current_dish = None
        
#         print("\n🍲 Extraction des plats...")
        
#         for idx, row in self.df.iterrows():
#             # Colonnes : A=Obs, B=Code, C=Name EN, D=Name FR, E=Weight, F=Yield, G=Method
#             obs_num = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
#             code = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
#             name_en = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
#             name_fr = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
            
#             # Ignorer lignes d'en-tête et sections
#             if code == 'Code' or code == 'nan' or 'Cereals' in name_en:
#                 continue
            
#             # CRITÈRE 1 : Nouvelle ligne de plat = Observation# non vide
#             if obs_num and obs_num != 'nan' and obs_num.isdigit():
#                 # Sauvegarder le plat précédent
#                 if current_dish:
#                     dishes.append(current_dish)
                
#                 # Créer nouveau plat
#                 current_dish = {
#                     'id': str(uuid.uuid4()),
#                     'observation_number': int(obs_num),
#                     'code': code,
#                     'name_en': name_en,
#                     'name_fr': name_fr,
#                     'local_name': name_fr if name_fr and name_fr != 'nan' else name_en,
#                     'description_en': name_en,
#                     'description_fr': name_fr,
#                     'weight_g': self._safe_float(row.iloc[4]) if len(row) > 4 else None,
#                     'yield_factor': self._safe_float(row.iloc[5]) if len(row) > 5 else None,
#                     'method_en': str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else '',
#                     'method_fr': str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else '',
#                     'meal_type': self._guess_meal_type(name_en + ' ' + name_fr),
#                     'cuisine_origin': 'west_african',
#                     'ingredients': []
#                 }
                
#                 print(f"   📌 Plat {obs_num}: {current_dish['local_name'][:60]}...")
            
#             # CRITÈRE 2 : Ligne d'ingrédient = Observation# vide + Code présent
#             elif code and code != 'nan' and current_dish is not None:
#                 ingredient = {
#                     'code': code,
#                     'name_en': name_en,
#                     'name_fr': name_fr,
#                     'name': name_fr if name_fr and name_fr != 'nan' else name_en,
#                     'weight_g': self._safe_float(row.iloc[4]) if len(row) > 4 else None,
#                     'quantity': self._safe_float(row.iloc[4]) if len(row) > 4 else None,
#                     'unit': 'g'  # Par défaut en grammes
#                 }
                
#                 current_dish['ingredients'].append(ingredient)
#                 print(f"      └─ {ingredient['name'][:40]} ({ingredient['quantity']}g)")
        
#         # Ajouter le dernier plat
#         if current_dish:
#             dishes.append(current_dish)
        
#         print(f"\n✅ {len(dishes)} plats extraits avec leurs ingrédients")
        
#         return dishes
    
#     def _guess_meal_type(self, name: str) -> str:
#         """Devine le type de repas"""
#         name = name.lower()
        
#         if any(k in name for k in ['porridge', 'bouillie', 'breakfast', 'petit-déjeuner']):
#             return 'breakfast'
#         elif any(k in name for k in ['lunch', 'déjeuner', 'midi']):
#             return 'lunch'
#         elif any(k in name for k in ['dinner', 'dîner', 'soir', 'souper']):
#             return 'dinner'
#         else:
#             return 'lunch'
    
#     def _safe_float(self, value):
#         """Conversion sécurisée en float"""
#         try:
#             if pd.isna(value) or value == '' or str(value).strip() in ['nan', '[0.7]']:
#                 return None
#             val_str = str(value).replace('[', '').replace(']', '').strip()
#             return float(val_str)
#         except:
#             return None
    
#     def create_senegalese_dishes(self):
#         """
#         Ajoute 20 plats sénégalais populaires (données manuelles)
#         """
        
#         senegalese_dishes = [
#             {
#                 'id': str(uuid.uuid4()),
#                 'code': 'SN_001',
#                 'name_en': 'Thieboudienne (Ceebu Jën)',
#                 'name_fr': 'Thiéboudienne',
#                 'local_name': 'Thiéboudienne',
#                 'description_en': 'Rice with fish and vegetables, national dish',
#                 'description_fr': 'Riz au poisson et légumes, plat national',
#                 'meal_type': 'lunch',
#                 'cuisine_origin': 'senegalese',
#                 'method_en': 'Cook rice with fish, tomato paste, and mixed vegetables',
#                 'method_fr': 'Cuire le riz avec poisson, concentré de tomate et légumes variés',
#                 'ingredients': [
#                     {'code': 'RICE_01', 'name_en': 'Broken rice', 'name_fr': 'Riz brisé', 'name': 'Riz brisé', 'quantity': 300, 'unit': 'g'},
#                     {'code': 'FISH_01', 'name_en': 'Thiof (grouper)', 'name_fr': 'Thiof (mérou)', 'name': 'Thiof', 'quantity': 200, 'unit': 'g'},
#                     {'code': 'VEG_01', 'name_en': 'Tomato paste', 'name_fr': 'Concentré de tomate', 'name': 'Tomate concentrée', 'quantity': 50, 'unit': 'g'},
#                     {'code': 'OIL_01', 'name_en': 'Peanut oil', 'name_fr': 'Huile d\'arachide', 'name': 'Huile arachide', 'quantity': 40, 'unit': 'ml'},
#                     {'code': 'VEG_02', 'name_en': 'Onion', 'name_fr': 'Oignon', 'name': 'Oignon', 'quantity': 100, 'unit': 'g'},
#                     {'code': 'VEG_03', 'name_en': 'Carrot', 'name_fr': 'Carotte', 'name': 'Carotte', 'quantity': 80, 'unit': 'g'},
#                     {'code': 'VEG_04', 'name_en': 'Cabbage', 'name_fr': 'Chou', 'name': 'Chou', 'quantity': 80, 'unit': 'g'},
#                     {'code': 'VEG_05', 'name_en': 'Eggplant', 'name_fr': 'Aubergine', 'name': 'Aubergine', 'quantity': 60, 'unit': 'g'},
#                     {'code': 'TUB_01', 'name_en': 'Cassava', 'name_fr': 'Manioc', 'name': 'Manioc', 'quantity': 100, 'unit': 'g'},
#                 ]
#             },
#             {
#                 'id': str(uuid.uuid4()),
#                 'code': 'SN_002',
#                 'name_en': 'Yassa Chicken',
#                 'name_fr': 'Yassa Poulet',
#                 'local_name': 'Yassa Poulet',
#                 'description_en': 'Marinated chicken with onions and lemon',
#                 'description_fr': 'Poulet mariné aux oignons et citron',
#                 'meal_type': 'lunch',
#                 'cuisine_origin': 'senegalese',
#                 'method_en': 'Marinate chicken, grill, then cook with caramelized onions',
#                 'method_fr': 'Mariner le poulet, griller, puis cuire avec oignons caramélisés',
#                 'ingredients': [
#                     {'code': 'MEAT_01', 'name_en': 'Chicken', 'name_fr': 'Poulet', 'name': 'Poulet', 'quantity': 400, 'unit': 'g'},
#                     {'code': 'VEG_02', 'name_en': 'Onion', 'name_fr': 'Oignon', 'name': 'Oignon', 'quantity': 300, 'unit': 'g'},
#                     {'code': 'FRUIT_01', 'name_en': 'Lemon juice', 'name_fr': 'Jus de citron', 'name': 'Citron', 'quantity': 60, 'unit': 'ml'},
#                     {'code': 'OIL_01', 'name_en': 'Oil', 'name_fr': 'Huile', 'name': 'Huile', 'quantity': 30, 'unit': 'ml'},
#                     {'code': 'COND_01', 'name_en': 'Mustard', 'name_fr': 'Moutarde', 'name': 'Moutarde', 'quantity': 20, 'unit': 'g'},
#                 ]
#             },
#             {
#                 'id': str(uuid.uuid4()),
#                 'code': 'SN_003',
#                 'name_en': 'Mafé (Peanut stew)',
#                 'name_fr': 'Mafé',
#                 'local_name': 'Mafé',
#                 'description_en': 'Meat stew with peanut sauce',
#                 'description_fr': 'Ragoût de viande à la sauce arachide',
#                 'meal_type': 'lunch',
#                 'cuisine_origin': 'senegalese',
#                 'method_en': 'Cook meat with peanut paste and vegetables',
#                 'method_fr': 'Cuire la viande avec pâte d\'arachide et légumes',
#                 'ingredients': [
#                     {'code': 'MEAT_02', 'name_en': 'Beef', 'name_fr': 'Boeuf', 'name': 'Boeuf', 'quantity': 300, 'unit': 'g'},
#                     {'code': 'LEG_01', 'name_en': 'Peanut paste', 'name_fr': 'Pâte d\'arachide', 'name': 'Pâte arachide', 'quantity': 150, 'unit': 'g'},
#                     {'code': 'VEG_01', 'name_en': 'Tomato paste', 'name_fr': 'Concentré de tomate', 'name': 'Tomate concentrée', 'quantity': 40, 'unit': 'g'},
#                     {'code': 'VEG_03', 'name_en': 'Carrot', 'name_fr': 'Carotte', 'name': 'Carotte', 'quantity': 100, 'unit': 'g'},
#                     {'code': 'TUB_02', 'name_en': 'Potato', 'name_fr': 'Pomme de terre', 'name': 'Pomme de terre', 'quantity': 150, 'unit': 'g'},
#                 ]
#             },
#             {
#                 'id': str(uuid.uuid4()),
#                 'code': 'SN_004',
#                 'name_en': 'Thiéré (Millet couscous)',
#                 'name_fr': 'Thiéré',
#                 'local_name': 'Thiéré',
#                 'description_en': 'Millet couscous with sour milk',
#                 'description_fr': 'Couscous de mil au lait caillé',
#                 'meal_type': 'breakfast',
#                 'cuisine_origin': 'senegalese',
#                 'method_en': 'Mix millet couscous with sour milk and sugar',
#                 'method_fr': 'Mélanger couscous de mil avec lait caillé et sucre',
#                 'ingredients': [
#                     {'code': 'CER_01', 'name_en': 'Millet couscous', 'name_fr': 'Couscous de mil', 'name': 'Mil (couscous)', 'quantity': 200, 'unit': 'g'},
#                     {'code': 'DAIRY_01', 'name_en': 'Sour milk', 'name_fr': 'Lait caillé', 'name': 'Lait caillé', 'quantity': 300, 'unit': 'ml'},
#                     {'code': 'SUGAR_01', 'name_en': 'Sugar', 'name_fr': 'Sucre', 'name': 'Sucre', 'quantity': 40, 'unit': 'g'},
#                 ]
#             },
#             {
#                 'id': str(uuid.uuid4()),
#                 'code': 'SN_005',
#                 'name_en': 'Thiakry',
#                 'name_fr': 'Thiakry',
#                 'local_name': 'Thiakry',
#                 'description_en': 'Millet couscous with vanilla yogurt',
#                 'description_fr': 'Couscous de mil au yaourt vanillé',
#                 'meal_type': 'breakfast',
#                 'cuisine_origin': 'senegalese',
#                 'method_en': 'Mix millet couscous with yogurt, sugar, and vanilla',
#                 'method_fr': 'Mélanger couscous de mil avec yaourt, sucre et vanille',
#                 'ingredients': [
#                     {'code': 'CER_01', 'name_en': 'Millet couscous', 'name_fr': 'Couscous de mil', 'name': 'Mil (couscous)', 'quantity': 150, 'unit': 'g'},
#                     {'code': 'DAIRY_02', 'name_en': 'Yogurt', 'name_fr': 'Yaourt', 'name': 'Yaourt', 'quantity': 250, 'unit': 'ml'},
#                     {'code': 'SUGAR_01', 'name_en': 'Sugar', 'name_fr': 'Sucre', 'name': 'Sucre', 'quantity': 50, 'unit': 'g'},
#                     {'code': 'COND_02', 'name_en': 'Vanilla', 'name_fr': 'Vanille', 'name': 'Vanille', 'quantity': 5, 'unit': 'ml'},
#                 ]
#             },
#             {
#                 'id': str(uuid.uuid4()),
#                 'code': 'SN_006',
#                 'name_en': 'Ndambé',
#                 'name_fr': 'Ndambé',
#                 'local_name': 'Ndambé',
#                 'description_en': 'Cowpea beans in sauce',
#                 'description_fr': 'Haricots niébé en sauce',
#                 'meal_type': 'breakfast',
#                 'cuisine_origin': 'senegalese',
#                 'method_en': 'Cook cowpeas with palm oil, onions, and tomatoes',
#                 'method_fr': 'Cuire les niébés avec huile de palme, oignons et tomates',
#                 'ingredients': [
#                     {'code': 'LEG_02', 'name_en': 'Cowpea', 'name_fr': 'Niébé', 'name': 'Niébé', 'quantity': 200, 'unit': 'g'},
#                     {'code': 'OIL_02', 'name_en': 'Palm oil', 'name_fr': 'Huile de palme', 'name': 'Huile palme', 'quantity': 30, 'unit': 'ml'},
#                     {'code': 'VEG_02', 'name_en': 'Onion', 'name_fr': 'Oignon', 'name': 'Oignon', 'quantity': 60, 'unit': 'g'},
#                     {'code': 'VEG_06', 'name_en': 'Tomato', 'name_fr': 'Tomate', 'name': 'Tomate', 'quantity': 80, 'unit': 'g'},
#                 ]
#             },
#         ]
        
#         return senegalese_dishes
    
#     def export_json(self, dishes: list, filename='dishes_with_ingredients.json'):
#         """Exporte en JSON avec structure complète"""
#         with open(filename, 'w', encoding='utf-8') as f:
#             json.dump(dishes, f, ensure_ascii=False, indent=2)
#         print(f"\n✅ {filename} créé ({len(dishes)} plats)")
    
#     def export_sql(self, dishes: list, filename='insert_dishes_complete.sql'):
#         """Génère SQL pour dishes ET dish_ingredients"""
        
#         with open(filename, 'w', encoding='utf-8') as f:
#             f.write("-- PLATS AVEC INGRÉDIENTS\n")
#             f.write("-- Structure bilingue (EN/FR)\n\n")
            
#             for dish in dishes:
#                 dish_id = dish['id']
#                 name = dish['local_name'].replace("'", "''")
#                 desc_en = dish.get('description_en', '').replace("'", "''")
#                 desc_fr = dish.get('description_fr', '').replace("'", "''")
                
#                 # INSERT dish
#                 f.write(f"\n-- {dish['local_name']}\n")
#                 f.write(f"INSERT INTO dishes (id, name, description, meal_type, cuisine_origin)\n")
#                 f.write(f"VALUES ('{dish_id}', '{name}', '{desc_fr}', '{dish['meal_type']}', '{dish['cuisine_origin']}');\n")
                
#                 # INSERT ingrédients (commentés - nécessite table ingredients)
#                 if dish.get('ingredients'):
#                     # f.write(f"\n-- Ingrédients:\n")
#                     for ing in dish['ingredients']:
#                         ing_name = ing['name'].replace("'", "''")
#                         # f.write(f"-- {ing['code']}: {ing_name} ({ing['quantity']} {ing['unit']})\n")
#                         f.write("\n")
#                         # SQL commenté (à décommenter après création table ingredients)
#                         f.write(f"INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, unit)\n")
#                         f.write(f"SELECT '{dish_id}', id, {ing['quantity']}, '{ing['unit']}'\n")
#                         f.write(f"FROM ingredients WHERE name = '{ing_name}' LIMIT 1;\n\n")
        
#         print(f"✅ {filename} créé")

#     def insert_into_postgres(self, dishes: list, dbname: str = 'nutrition_westaf', user: str = None, password: str = None, host: str = 'localhost', port: int = 5432):
#         """
#         Insère directement les `dishes` et `dish_ingredients` dans une base Postgres locale.

#         Paramètres:
#         - `dishes`: liste d'objets plats (structure utilisée par cette classe).
#         - `dbname`: nom de la base de données (défaut: 'nutrition_westaf').
#         - `user`, `password`, `host`, `port`: paramètres de connexion. Si `user`/`password` non fournis,
#           tente de lire `PGUSER`/`PGPASSWORD` depuis les variables d'environnement puis utilise `postgres` sans mot de passe.

#         Comportement:
#         - Insère chaque plat dans `dishes` (INSERT ... ON CONFLICT UPDATE).
#         - Pour chaque ingrédient : recherche par nom (insensible à la casse) dans `ingredients`; s'il n'existe pas, le crée.
#         - Insère/Met à jour la table `dish_ingredients` pour l'association plat/ingrédient.
#         - Opère dans une transaction globale (commit à la fin, rollback en cas d'erreur).
#         """
#         user = user or os.environ.get('PGUSER') or 'postgres'
#         password = password or os.environ.get('PGPASSWORD') or None

#         conn = None
#         try:
#             conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
#             cur = conn.cursor()
#             print(f"🔌 Connecté à Postgres {user}@{host}:{port}/{dbname}")

#             for dish in dishes:
#                 dish_id = dish['id']
#                 name = (dish.get('local_name') or dish.get('name_en') or '').strip()
#                 desc = (dish.get('description_fr') or dish.get('description_en') or '').strip()
#                 meal_type = dish.get('meal_type')
#                 cuisine = dish.get('cuisine_origin')

#                 # Insert or update dish
#                 cur.execute(
#                     """
#                     INSERT INTO dishes (id, name, description, meal_type, cuisine_origin)
#                     VALUES (%s, %s, %s, %s, %s)
#                     ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, meal_type = EXCLUDED.meal_type, cuisine_origin = EXCLUDED.cuisine_origin
#                     """,
#                     (dish_id, name, desc, meal_type, cuisine)
#                 )

#                 # Process ingredients
#                 for ing in dish.get('ingredients', []):
#                     ing_name = (ing.get('name') or ing.get('name_fr') or ing.get('name_en') or '').strip()
#                     if not ing_name:
#                         continue

#                     # Lookup existing ingredient by name (case-insensitive)
#                     cur.execute("SELECT id FROM ingredients WHERE lower(name) = lower(%s) LIMIT 1", (ing_name,))
#                     row = cur.fetchone()
#                     if row:
#                         ing_id = row[0]
#                     else:
#                         ing_id = str(uuid.uuid4())
#                         cur.execute("INSERT INTO ingredients (id, name, food_id) VALUES (%s, %s, %s)", (ing_id, ing_name, None))

#                     qty = ing.get('quantity')
#                     unit = ing.get('unit')

#                     # Insert or update dish_ingredients
#                     cur.execute(
#                         """
#                         INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, unit)
#                         VALUES (%s, %s, %s, %s)
#                         ON CONFLICT (dish_id, ingredient_id) DO UPDATE SET quantity = EXCLUDED.quantity, unit = EXCLUDED.unit
#                         """,
#                         (dish_id, ing_id, qty, unit)
#                     )

#             conn.commit()
#             print("✅ Insertions en base terminées et validées (commit).")

#         except Exception as e:
#             if conn:
#                 conn.rollback()
#             print("❌ Erreur lors de l'insertion en base:", e)
#             raise
#         finally:
#             if conn:
#                 conn.close()
    
#     def export_ingredients_list(self, dishes: list, filename='ingredients_from_dishes.json'):
#         """Extrait la liste unique des ingrédients utilisés"""
        
#         ingredients_set = {}
        
#         for dish in dishes:
#             if 'ingredients' in dish:
#                 for ing in dish['ingredients']:
#                     code = ing['code']
#                     if code not in ingredients_set:
#                         ingredients_set[code] = {
#                             'id': str(uuid.uuid4()),
#                             'code': code,
#                             'name_en': ing.get('name_en', ''),
#                             'name_fr': ing.get('name_fr', ''),
#                             'name': ing['name'],
#                             'used_in_dishes': []
#                         }
#                     ingredients_set[code]['used_in_dishes'].append(dish['local_name'])
        
#         ingredients_list = list(ingredients_set.values())
        
#         with open(filename, 'w', encoding='utf-8') as f:
#             json.dump(ingredients_list, f, ensure_ascii=False, indent=2)
        
#         print(f"✅ {filename} créé ({len(ingredients_list)} ingrédients uniques)")
        
#         return ingredients_list


# # === EXÉCUTION ===
# if __name__ == "__main__":
#     print("🍲 EXTRACTION COMPLÈTE DES PLATS\n")
    
#     extractor = WAFCTDishesExtractor("data/WAFCT_2019.xlsx")
    
#     all_dishes = []
    
#     # 1. Tenter extraction WAFCT
#     if extractor.load_mixed_dishes_sheet():
#         wafct_dishes = extractor.extract_dishes_with_ingredients()
#         all_dishes.extend(wafct_dishes)
    
#     # 2. Ajouter plats sénégalais manuels
#     senegalese_dishes = extractor.create_senegalese_dishes()
#     all_dishes.extend(senegalese_dishes)
    
#     print(f"\n" + "="*60)
#     print(f"📊 TOTAL : {len(all_dishes)} plats extraits")
#     print("="*60)
    
#     # Statistiques
#     breakfast_count = sum(1 for d in all_dishes if d['meal_type'] == 'breakfast')
#     lunch_count = sum(1 for d in all_dishes if d['meal_type'] == 'lunch')
#     dinner_count = sum(1 for d in all_dishes if d['meal_type'] == 'dinner')
    
#     print(f"\n📈 Répartition:")
#     print(f"   - Petit-déjeuner: {breakfast_count}")
#     print(f"   - Déjeuner: {lunch_count}")
#     print(f"   - Dîner: {dinner_count}")
    
#     extractor.insert_into_postgres(all_dishes, user='postgres', password='nando')