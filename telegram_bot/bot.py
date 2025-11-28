"""
CHATBOT TELEGRAM - NUTRISENEGAL BOT
Assistant nutrition personnalisé avec analyse de plats
"""

import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from config import TELEGRAM_TOKEN, API_BASE_URL

# ==================== CONFIGURATION ====================

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # filename='bot.log',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# États de conversation
(
    ONBOARDING_NAME,
    ONBOARDING_WEIGHT,
    ONBOARDING_DISEASES,
    ONBOARDING_ALLERGENS,
    ANALYZING_DISH,
    MODIFYING_PROFILE
) = range(6)


allergen_mapping = {
    '94a8f70e-69c0-4c3c-9c5b-2e411f9cadf6':	'Arachides',
    '36463424-3eec-4348-a105-8ef0b67b57ab':	'Crustacés',
    '1d4b0887-d7da-4ae9-91ca-c5b259fa7509':	'Gluten (blé)',
    '89bd3273-8266-4b8d-894c-ee66ef3bfc65':	'Lait (lactose)',
    '724d4936-0c64-4b95-b879-d2f1461f04f3':	'Œufs',
    'c2ab4e01-e290-451c-a9cf-4591807a19b0':	'Poissons',
    '775020aa-1e41-41db-b0e4-7fc529c705b1':	'Fruits à coque',
    'c71d55a7-c3ca-458b-9570-f095ad1e77c0':	'Moutarde',
    '9849596b-ead2-4524-a209-070f7955b705':	'Soja',
    '76857216-36b2-4170-9e73-b1d40f305e6a': 'Sésame',
    'allergen_none': 'Aucune allergie'
}

# Mapping callback → nom maladie
disease_mapping = {
    '6c6f38db-a11d-4077-9437-d0920e2820a3':	'Diabète Type 2',
    'f8b080ed-1740-4895-845b-5449b532631e':	'Hypertension arterielle',
    'a33445f7-b18d-4c16-8ed8-e69bafa2778d':	'Maladie hépatique chronique',
    '3eefbe16-b811-4bef-9436-22141e6efaf0':	'Cancer (en traitement)',
    'c2209a0f-0276-4c45-a5b1-2bb20cdb41c5':	'Insuffisance rénale chronique',
    'none': 'Aucune'
}

# ==================== HELPERS API ====================

def call_api(endpoint: str, method: str = 'GET', data: dict = None):
    """Appel à l'API backend"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        logger.info(f"🌐 API Call: {method} {url}")
        if data:
            logger.info(f"📤 Params/Data: {data}")
        
        if method == 'GET':
            response = requests.get(url, params=data, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=10)
        
        response.raise_for_status()
        
        result = response.json()
        
        # logger.info(f"✅ API Response: {len(str(result))} chars")
        # logger.info(f"📥 Keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
        
        # # Log détaillé
        # with open('api_log.txt', 'a', encoding='utf-8') as f:
        #     f.write(f'\n=== {method} {endpoint} ===\n')
        #     f.write(f'Response: {result}\n')
        
        return result
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API Error: {e}")
        return None

# def get_diseases_list():
#     """Récupère la liste des maladies disponibles"""
#     return call_api('/health-profiles/diseases', 'GET')

# def get_allergens_list():
#     """Récupère la liste des allergènes disponibles"""
#     return call_api('/health-profiles/allergens', 'GET')

def get_user_profile(user_id: str):
    """Récupère le profil santé d'un utilisateur"""
    return call_api(f'/health-profiles/{user_id}', 'GET')

def create_user_profile(profile_data: dict):
    """Crée un profil santé"""
    user_data = {
        'id': profile_data['user_id'],
        'first_name': profile_data.get('first_name', ''),
        'last_name': profile_data.get('last_name', ''),
        'weight': profile_data.get('weight', None)
    }
    try:
        # Créer l'utilisateur d'abord
        call_api('/users/register', 'POST', user_data)
        profile = call_api(f'/health-profiles', 'POST', {
            'user_id': profile_data['user_id'],
            'physical_activity_level': profile_data.get('physical_activity_level', 'moderate'),
        })
        for disease in profile_data.get('diseases', []):
            call_api(f'/health-profiles/{profile["id"]}/diseases', 'POST', {'disease_id': disease})
        for allergen in profile_data.get('allergens', []):
            call_api(f'/health-profiles/{profile["id"]}/allergens', 'POST', {'allergen_id': allergen})
        return profile
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

def analyze_dish(dish_id: str, user_id: str):
    """Analyse un plat"""
    return call_api('/analyze-dish', 'POST', {
        'dish_id': dish_id,
        'user_id': user_id
    })

def analyze_menu_text(menu_text: str, user_id: str):
    """Analyse un menu depuis texte"""
    return call_api('/analyze-menu', 'POST', {
        'menu_text': menu_text,
        'user_id': user_id
    })

def get_recommendations(user_id: str, meal_type: str = None):
    """Obtient des recommandations"""
    params = {'limit': 5}
    if meal_type:
        params['meal_type'] = meal_type
    
    result = call_api(f'/recommendations/{user_id}', 'GET', params)
    # with open('log.txt', 'a', encoding='utf-8') as f:
    #     f.write(str(result))
    
    return result

def get_dishes(meal_type: str = None, limit: int = 10):
    """Liste des plats disponibles"""
    params = {'limit': limit}
    if meal_type:
        params['meal_type'] = meal_type
    
    return call_api('/dishes', 'GET', params)

def get_alternatives(dish_id: str, user_id: str):
    """Obtient alternatives pour un plat"""
    return call_api(f'/alternatives/{dish_id}', 'POST', {
        'user_id': user_id
    })

# ==================== FORMATTERS ====================

def format_score_emoji(score: int) -> str:
    """Convertit score en emoji"""
    if score >= 75:
        return "🟢"
    elif score >= 50:
        return "🟠"
    elif score >= 25:
        return "🔴"
    else:
        return "⛔"

def format_alert_level(level: str) -> str:
    """Convertit niveau d'alerte en texte"""
    mapping = {
        'safe': '🟢 COMPATIBLE',
        'caution': '🟠 MODÉRATION',
        'danger': '🔴 NON RECOMMANDÉ',
        'critical': '⛔ INTERDIT'
    }
    return mapping.get(level, level.upper())

def format_analysis_result(analysis: dict) -> str:
    """Formate le résultat d'analyse"""
    
    score = analysis['score']
    alert_level = analysis['alert_level']
    
    message = f"""
🔍 **ANALYSE NUTRITIONNELLE**

🎯 **Score de compatibilité** : {score}/100 {format_score_emoji(score)}
🚦 **Niveau d'alerte** : {format_alert_level(alert_level)}
"""
    
    # Alertes
    if analysis['alerts']:
        message += "\n⚠️ **ALERTES** :\n"
        for alert in analysis['alerts'][:5]:  # Max 5 alertes
            message += f"• {alert['message']}\n"
    
    # Recommandations
    if analysis['recommendations']:
        message += "\n💡 **RECOMMANDATIONS** :\n"
        for rec in analysis['recommendations'][:3]:
            message += f"• {rec}\n"
    
    # Résumé nutritionnel
    nutr = analysis.get('nutritional_summary', {})
    if nutr:
        message += f"""
📊 **Valeurs nutritionnelles** :
• Énergie : {nutr.get('energy_kcal', 0):.0f} kcal
• Protéines : {nutr.get('protein_g', 0):.1f}g
• Glucides : {nutr.get('carbohydrate_g', 0):.1f}g
• Lipides : {nutr.get('fat_g', 0):.1f}g
• Fibres : {nutr.get('fiber_g', 0):.1f}g
• Sodium : {nutr.get('sodium_mg', 0):.0f}mg
"""
    
    return message

# ==================== KEYBOARDS ====================

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
    #     ('Arachides', 'allergen_peanut'),
    #     ('Gluten (blé)', 'allergen_gluten'),
    #     ('Lait (lactose)', 'allergen_lactose'),
    #     ('Œufs', 'allergen_eggs'),
    #     ('Poissons', 'allergen_fish'),
    #     ('Fruits à coque', 'allergen_nuts'),
    #     ('Aucune allergie', 'allergen_none')
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
    # allergens_list = get_allergens_list()
    # allergens = [(a['name'], a['id']) for a in allergens_list or []]
    # allergens.append(('Aucune allergie', 'allergen_none'))
    
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

def analysis_actions_keyboard(dish_id: str):
    """Actions après analyse"""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Voir alternatives", callback_data=f'alternatives_{dish_id}'),
            InlineKeyboardButton("📋 Détails complets", callback_data=f'details_{dish_id}')
        ],
        [
            InlineKeyboardButton("🔍 Analyser autre plat", callback_data='action_analyze'),
            InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start - Onboarding"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Vérifier si profil existe déjà
    profile = get_user_profile(user_id)
    
    if profile:
        # Utilisateur existant
        await update.message.reply_text(
            f"👋 Ravi de vous revoir {user.first_name} !\n\n"
            "Que souhaitez-vous faire ?",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Nouvel utilisateur - Onboarding
    await update.message.reply_text(
        f"🌟 Bienvenue {user.first_name} sur **NutriSénégal Bot** !\n\n"
        "Je suis votre assistant nutrition personnalisé pour vous aider à "
        "manger sainement selon vos besoins de santé.\n\n"
        "🎯 **Ce que je peux faire** :\n"
        "✅ Analyser la compatibilité d'un plat avec votre santé\n"
        "✅ Détecter les allergènes dangereux\n"
        "✅ Recommander des plats adaptés\n"
        "✅ Suggérer des alternatives plus saines\n\n"
        "Commençons par créer votre profil santé ! 👇\n\n"
        "📝 Quel est votre **prénom** ?\n"
        "(Tapez /cancel pour annuler)",
        parse_mode='Markdown'
    )
    
    return ONBOARDING_NAME

async def onboarding_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collecte du prénom"""
    first_name = update.message.text.strip()
    context.user_data['first_name'] = first_name
    
    await update.message.reply_text(
        f"Enchanté {first_name} ! 😊\n\n"
        "⚖️ Quel est votre **poids** (en kg) ?\n"
        "(Cela m'aidera à personnaliser les calculs)\n\n"
        "Exemple : 75"
    )
    
    return ONBOARDING_WEIGHT

async def onboarding_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collecte du poids"""
    try:
        weight = float(update.message.text.strip())
        if weight < 30 or weight > 300:
            raise ValueError
        
        context.user_data['weight'] = weight
        context.user_data['selected_diseases'] = []
        
        await update.message.reply_text(
            "🏥 **Avez-vous des maladies chroniques ?**\n\n"
            "Sélectionnez toutes celles qui s'appliquent :\n"
            "(Vous pouvez en sélectionner plusieurs)",
            reply_markup=diseases_keyboard(),
            parse_mode='Markdown'
        )
        
        return ONBOARDING_DISEASES
    
    except ValueError:
        await update.message.reply_text(
            "⚠️ Veuillez entrer un poids valide (entre 30 et 300 kg)\n"
            "Exemple : 75"
        )
        return ONBOARDING_WEIGHT

async def onboarding_diseases_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion sélection maladies"""
    query = update.callback_query
    await query.answer()
    
    selected = context.user_data.get('selected_diseases', [])
    
    
    # diseases_list = get_diseases_list()
    # disease_mapping = {d['id']: d['name'] for d in diseases_list or []}
    # disease_mapping['none'] = 'Aucune'
    
    data = query.data
    
    if data == 'diseases_confirm':
        # Validation
        context.user_data['diseases'] = selected
        context.user_data['selected_allergens'] = []
        
        await query.edit_message_text(
            "🚫 **Avez-vous des allergies alimentaires ?**\n\n"
            "Sélectionnez toutes celles qui s'appliquent :",
            reply_markup=allergens_keyboard(),
            parse_mode='Markdown'
        )
        
        return ONBOARDING_ALLERGENS
    
    else:
        # Toggle maladie
        # disease_name = disease_mapping.get(data)
        
        if data == 'none':
            selected = []
        else:
            if data in selected:
                selected.remove(data)
            else:
                selected.append(data)
                if 'none' in selected:
                    selected.remove('none')
        
        context.user_data['selected_diseases'] = selected
        
        await query.edit_message_reply_markup(
            reply_markup=diseases_keyboard(selected)
        )
        
        return ONBOARDING_DISEASES

async def onboarding_allergens_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion sélection allergènes"""
    query = update.callback_query
    await query.answer()
    
    selected = context.user_data.get('selected_allergens', [])
    
    
    # allergens_list = get_allergens_list()
    # allergen_mapping = {a['id']: a['name'] for a in allergens_list or []}
    # allergen_mapping['allergen_none'] = 'Aucune allergie'
    
    data = query.data
    
    if data == 'allergens_confirm':
        # Finalisation onboarding
        context.user_data['allergens'] = selected
        
        user_id = str(update.effective_user.id)
        
        # Créer profil dans l'API
        profile_data = {
            'user_id': user_id,
            'first_name': context.user_data.get('first_name'),
            'last_name': context.user_data.get('last_name', ''),
            'diseases': context.user_data.get('diseases', []),
            'allergens': context.user_data.get('allergens', []),
            'physical_activity_level': 'moderate',
            'weight': context.user_data.get('weight')
        }
        
        result = create_user_profile(profile_data)
        
        if result:
            # Récapitulatif
            diseases_text = ", ".join([disease_mapping.get(disease_id, '') for disease_id in context.user_data.get('diseases', [])]) or "Aucune"
            allergens_text = ", ".join([allergen_mapping.get(allergen_id, '') for allergen_id in context.user_data.get('allergens', [])]) or "Aucune"
            
            await query.edit_message_text(
                f"✅ **Profil créé avec succès !**\n\n"
                f"👤 Prénom : {context.user_data.get('first_name')}\n"
                f"⚖️ Poids : {context.user_data.get('weight')} kg\n"
                f"🏥 Maladies : {diseases_text}\n"
                f"🚫 Allergies : {allergens_text}\n\n"
                "Vous êtes prêt à utiliser NutriSénégal Bot ! 🎉\n\n"
                "Que souhaitez-vous faire ?",
                reply_markup=main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Erreur lors de la création du profil.\n"
                "Veuillez réessayer avec /start"
            )
        
        return ConversationHandler.END
    
    else:
        # Toggle allergène
        # allergen_name = allergen_mapping.get(data)
        
        if data == 'allergen_none':
            selected = []
        else:
            if data in selected:
                selected.remove(data)
            else:
                selected.append(data)
                if 'allergen_none' in selected:
                    selected.remove('allergen_none')
        
        context.user_data['selected_allergens'] = selected
        
        await query.edit_message_reply_markup(
            reply_markup=allergens_keyboard(selected)
        )
        
        return ONBOARDING_ALLERGENS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annuler l'opération en cours"""
    await update.message.reply_text(
        "❌ Opération annulée.\n\n"
        "Utilisez /start pour recommencer ou /help pour l'aide."
    )
    return ConversationHandler.END

# ==================== ACTION HANDLERS ====================

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion des callbacks du menu principal"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = str(update.effective_user.id)
    
    if data == 'main_menu':
        await query.edit_message_text(
            "🏠 **Menu Principal**\n\nQue souhaitez-vous faire ?",
            reply_markup=main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data == 'action_analyze':
        await query.edit_message_text(
            "🔍 **Analyser un plat**\n\n"
            "Vous pouvez :\n"
            "1️⃣ Décrire le plat en texte\n"
            "2️⃣ Choisir dans la liste des plats\n\n"
            "Comment voulez-vous procéder ?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✍️ Décrire en texte", callback_data='analyze_text'),
                    InlineKeyboardButton("📋 Choisir liste", callback_data='analyze_list')
                ],
                [InlineKeyboardButton("🏠 Retour", callback_data='main_menu')]
            ]),
            parse_mode='Markdown'
        )
    
    elif data == 'action_recommendations':
        await query.edit_message_text(
            "⭐ **Recommandations personnalisées**\n\n"
            "Pour quel type de repas ?",
            reply_markup=meal_type_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data == 'action_profile':
        profile = get_user_profile(user_id)
        
        if profile:
            diseases = ", ".join(profile.get('diseases', [])) or "Aucune"
            allergens = ", ".join(profile.get('allergens', [])) or "Aucune"
            
            await query.edit_message_text(
                f"👤 **Votre Profil Santé**\n\n"
                f"🏥 Maladies : {diseases}\n"
                f"🚫 Allergies : {allergens}\n"
                f"⚖️ Poids : {profile.get('weight', 'Non renseigné')} kg\n"
                f"🏃 Activité : {profile.get('physical_activity_level', 'Modérée')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Modifier profil", callback_data='modify_profile')],
                    [InlineKeyboardButton("🏠 Retour", callback_data='main_menu')]
                ]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Profil non trouvé.\n"
                "Utilisez /start pour créer votre profil."
            )
    
    elif data == 'action_help':
        await query.edit_message_text(
            "❓ **Aide - NutriSénégal Bot**\n\n"
            "**Commandes disponibles** :\n"
            "/start - Démarrer le bot\n"
            "/analyser - Analyser un plat\n"
            "/profil - Voir votre profil\n"
            "/recommandations - Plats recommandés\n"
            "/help - Afficher cette aide\n\n"
            "**Comment utiliser** :\n"
            "1️⃣ Créez votre profil santé\n"
            "2️⃣ Analysez des plats\n"
            "3️⃣ Suivez les recommandations\n\n"
            "Pour toute question : @votre_support",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ]),
            parse_mode='Markdown'
        )

async def analyze_text_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarrer analyse textuelle"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "✍️ **Analyse de plat par description**\n\n"
        "Décrivez le plat que vous souhaitez manger.\n\n"
        "**Exemple** :\n"
        "\"Thiéboudienne avec riz blanc, poisson et légumes\"\n"
        "\"Yassa poulet avec oignons et citron\"\n\n"
        "Tapez /cancel pour annuler.",
        parse_mode='Markdown'
    )
    
    return ANALYZING_DISH

async def analyze_dish_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Traite l'analyse textuelle"""
    menu_text = update.message.text
    user_id = str(update.effective_user.id)
    
    # Message d'attente
    waiting_msg = await update.message.reply_text("🔄 Analyse en cours...")
    
    # Appel API
    result = analyze_menu_text(menu_text, user_id)
    
    if result:
        # Formater et envoyer résultat
        message = format_analysis_result(result)
        
        await waiting_msg.edit_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Analyser autre plat", callback_data='action_analyze')],
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ]),
            parse_mode='Markdown'
        )
    else:
        await waiting_msg.edit_text(
            "❌ Erreur lors de l'analyse.\n"
            "Veuillez réessayer."
        )
    
    return ConversationHandler.END

def safe_md(text: str) -> str:
    """Échappe tout texte pour Markdown V2 sans rien casser."""
    if text is None:
        return ""
    return escape_markdown(text, version=2)

async def recommendations_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)

    meal_mapping = {
        'meal_breakfast': 'breakfast',
        'meal_lunch': 'lunch',
        'meal_dinner': 'dinner',
        'meal_all': None
    }

    meal_type = meal_mapping.get(query.data)

    await query.edit_message_text("🔄 Recherche de recommandations...")

    result = get_recommendations(user_id, meal_type)

    if result and result.get('recommendations'):
        recs = result['recommendations'][:5]
        tips = result.get('personalized_tips', [])

        message = "⭐ *VOS RECOMMANDATIONS*\n\n"
        
        for i, rec in enumerate(recs, 1):

            dish = safe_md(rec["dish_name"])
            reason = safe_md(rec["reason"])

            message += f"{i} *{dish}*\n"
            message += f"   Score : {rec['score']}/100 {format_score_emoji(rec['score'])}\n"
            message += f"   {reason}\n"

            if rec.get("nutritional_highlights"):
                highlight = safe_md(rec["nutritional_highlights"][0])
                message += f"   ✅ {highlight}\n"

            message += "\n"

        if tips:
            message += "💡 *CONSEILS* :\n"
            for tip in tips[:2]:
                safe_tip = safe_md(tip)
                message += f"{safe_tip}\n"

        with open('message.txt', 'a', encoding='utf-8') as f:
            f.write(str(message))
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ]),
            parse_mode='MarkdownV2'
        )

    else:
        await query.edit_message_text(
            "❌ Aucune recommandation disponible.\nVotre profil semble incomplet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ])
        )


# ==================== MAIN ====================

def main():
    """Démarre le bot"""
    
    # Créer l'application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Conversation Handler - Onboarding
    onboarding_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ONBOARDING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_name)],
            ONBOARDING_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_weight)],
            ONBOARDING_DISEASES: [CallbackQueryHandler(onboarding_diseases_callback)],
            ONBOARDING_ALLERGENS: [CallbackQueryHandler(onboarding_allergens_callback)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Conversation Handler - Analyse
    analyze_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(analyze_text_start, pattern='^analyze_text$')],
        states={
            ANALYZING_DISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_dish_text)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Ajouter handlers
    app.add_handler(onboarding_handler)
    app.add_handler(analyze_handler)
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(menu_callback, pattern='^(main_menu|action_|modify_)'))
    app.add_handler(CallbackQueryHandler(recommendations_callback, pattern='^meal_'))
    
    # Commandes simples
    app.add_handler(CommandHandler('help', lambda u, c: u.message.reply_text(
        "❓ Utilisez /start pour commencer\n"
        "Ou cliquez sur le menu ci-dessous",
        reply_markup=main_menu_keyboard()
    )))
    
    # Démarrer le bot
    logger.info("🤖 Bot démarré avec succès!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()










# from telegram import Update
# from telegram.ext import (
#     ApplicationBuilder,
#     CommandHandler,
#     MessageHandler,
#     ContextTypes,
#     filters,
# )
# import requests
# from services.health_api import get_user_health_profile, get_nutritional_recommendations
# from config import TELEGRAM_TOKEN


# # ----------------------
# # /start
# # ----------------------
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         "👋 Bienvenue dans le Bot de Recommandation Nutritionnelle !\n"
#         "Veuillez envoyer votre *ID utilisateur* pour commencer.",
#         parse_mode="Markdown"
#     )


# # ----------------------
# # Réception de l’ID utilisateur
# # ----------------------
# async def set_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_input = update.message.text.strip()

#     # On suppose que l’ID est un UUID → tu peux adapter
#     context.user_data["user_id"] = user_input

#     profile = get_user_health_profile(user_input)

#     if profile is None:
#         await update.message.reply_text("❌ ID invalide ou aucun profil santé trouvé.")
#         return

#     # Affichage résumé
#     diseases = ", ".join(profile["diseases"]) or "Aucune"
#     allergens = ", ".join(profile["allergens"]) or "Aucun"

#     await update.message.reply_text(
#         f"Profil santé trouvé ✔️\n\n"
#         f"🧬 Maladies : {diseases}\n"
#         f"⚠️ Allergies : {allergens}\n"
#         f"🍽 Tu peux maintenant poser des questions sur un aliment !\n\n"
#         f"Par ex :\n"
#         f"• *Est-ce que je peux manger du riz ?*\n"
#         f"• *Recommande-moi un plat sain*",
#         parse_mode="Markdown"
#     )


# # ----------------------
# # Toute autre question nutritionnelle
# # ----------------------
# async def nutrition_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = context.user_data.get("user_id", None)

#     if not user_id:
#         await update.message.reply_text(
#             "🔑 Avant tout, envoie ton ID utilisateur."
#         )
#         return

#     food_name = update.message.text

#     # Appel à ton API Flask
#     result = get_nutritional_recommendations(user_id, food_name)

#     await update.message.reply_text(
#         f"🍏 *Recommandation pour* : {food_name}\n\n"
#         f"{result.get('message', 'Aucune réponse')}",
#         parse_mode="Markdown"
#     )


# # ----------------------
# # Main
# # ----------------------
# if __name__ == "__main__":
#     app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

#     app.add_handler(CommandHandler("start", start))
    
#     # Si le texte ressemble à un ID → l'utiliser comme ID user
#     app.add_handler(MessageHandler(filters.Regex(r"^[0-9a-fA-F\-]{36}$"), set_user))

#     # Sinon → interprété comme question nutritionnelle
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, nutrition_query))

#     print("🤖 Bot Telegram nutritionnel en cours d’exécution...")
#     app.run_polling()
