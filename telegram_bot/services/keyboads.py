from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard():
    """Menu principal"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Analyser plat", callback_data='action_analyze'),
            InlineKeyboardButton("⭐ Recommandations", callback_data='action_recommendations')
        ],
        [
            InlineKeyboardButton("🍽️ Liste plats", callback_data='action_dishes'),
            InlineKeyboardButton("👤 Mon profil", callback_data='action_profile')
        ],
        [
            InlineKeyboardButton("📊 Historique", callback_data='action_history'),
            InlineKeyboardButton("❓ Aide", callback_data='action_help')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def diseases_keyboard(selected: list = None):
    """Clavier sélection maladies"""
    selected = selected or []
    
    diseases = [
        ('Diabète Type 2', '6c6f38db-a11d-4077-9437-d0920e2820a3'),
        ('Hypertension arterielle', 'f8b080ed-1740-4895-845b-5449b532631e'),
        ('Maladie hépatique chronique', 'a33445f7-b18d-4c16-8ed8-e69bafa2778d'),
        ('Cancer (en traitement)', '3eefbe16-b811-4bef-9436-22141e6efaf0'),
        ('Insuffisance rénale chronique', 'c2209a0f-0276-4c45-a5b1-2bb20cdb41c5'),
        ('Aucune', 'none')
    ]
    # diseases_list = get_diseases_list()
    # diseases = [(d['name'], d['id']) for d in diseases_list or []]
    # diseases.append(('Aucune', 'none'))
    
    keyboard = []
    for name, callback in diseases:
        emoji = "✅" if callback in selected else "☐"
        keyboard.append([
            InlineKeyboardButton(f"{emoji} {name}", callback_data=callback)
        ])
    
    keyboard.append([
        InlineKeyboardButton("✅ Valider la sélection", callback_data='diseases_confirm')
    ])
    
    return InlineKeyboardMarkup(keyboard)

def allergens_keyboard(selected: list = None):
    """Clavier sélection allergènes"""
    selected = selected or []
    
    allergens = [
        ('Arachides', '94a8f70e-69c0-4c3c-9c5b-2e411f9cadf6'),
        ('Crustacés', '36463424-3eec-4348-a105-8ef0b67b57ab'),
        ('Gluten (blé)', '1d4b0887-d7da-4ae9-91ca-c5b259fa7509'),
        ('Lait (lactose)', '89bd3273-8266-4b8d-894c-ee66ef3bfc65'),
        ('Œufs', '724d4936-0c64-4b95-b879-d2f1461f04f3'),
        ('Poissons', 'c2ab4e01-e290-451c-a9cf-4591807a19b0'),
        ('Fruits à coque', '775020aa-1e41-41db-b0e4-7fc529c705b1'),
        ('Moutarde', 'c71d55a7-c3ca-458b-9570-f095ad1e77c0'),
        ('Soja', '9849596b-ead2-4524-a209-070f7955b705'),
        ('Sésame', '76857216-36b2-4170-9e73-b1d40f305e6a'),
        ('Aucune allergie', 'allergen_none')
    ]
    
    keyboard = []
    for name, callback in allergens:
        emoji = "✅" if callback in selected else "☐"
        keyboard.append([
            InlineKeyboardButton(f"{emoji} {name}", callback_data=callback)
        ])
    
    keyboard.append([
        InlineKeyboardButton("✅ Valider", callback_data='allergens_confirm')
    ])
    
    return InlineKeyboardMarkup(keyboard)

def meal_type_keyboard():
    """Clavier type de repas"""
    keyboard = [
        [
            InlineKeyboardButton("🌅 Petit-déjeuner", callback_data='meal_breakfast'),
            InlineKeyboardButton("☀️ Déjeuner", callback_data='meal_lunch')
        ],
        [
            InlineKeyboardButton("🌙 Dîner", callback_data='meal_dinner'),
            InlineKeyboardButton("📋 Tous", callback_data='meal_all')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
