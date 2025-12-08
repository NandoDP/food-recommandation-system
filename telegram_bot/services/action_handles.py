import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)
from telegram_bot.services.health_api import (
    get_user_profile,
    create_user_profile,
    analyze_dish,
    analyze_menu_text,
    get_recommendations,
    get_alternatives,
    get_dishes,
    get_dish_details,
    add_list_allergens_to_profile,
    add_list_diseases_to_profile
)
from telegram_bot.services.keyboads import (
    main_menu_keyboard,
    diseases_keyboard,
    allergens_keyboard,
    meal_type_keyboard
)
from telegram_bot.services.formatters import (
    safe_md, format_analysis_result, format_score_emoji
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
        parse_mode='MarkdownV2'
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
            parse_mode='MarkdownV2'
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
            parse_mode='MarkdownV2'
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
                parse_mode='MarkdownV2'
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
            parse_mode='MarkdownV2'
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
            parse_mode='MarkdownV2'
        )
    
    elif data == 'action_recommendations':
        await query.edit_message_text(
            "⭐ **Recommandations personnalisées**\n\n"
            "Pour quel type de repas ?",
            reply_markup=meal_type_keyboard(),
            parse_mode='MarkdownV2'
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
                    [
                        InlineKeyboardButton("🏥 Gérer maladies", callback_data='manage_diseases'),
                        InlineKeyboardButton("🚫 Gérer allergies", callback_data='manage_allergens')
                    ],
                    [
                        InlineKeyboardButton("⚖️ Modifier poids", callback_data='modify_weight'),
                        InlineKeyboardButton("🗑️ Supprimer profil", callback_data='delete_profile')
                    ],
                    [InlineKeyboardButton("🏠 Retour", callback_data='main_menu')]
                ]),
                parse_mode='MarkdownV2'
            )
        else:
            await query.edit_message_text(
                "❌ Profil non trouvé.\n"
                "Utilisez /start pour créer votre profil."
            )
    
    elif data == 'action_dishes':
        await query.edit_message_text(
            "🍽️ **Liste des plats disponibles**\n\n"
            "Choisissez un type de repas pour voir les plats :",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🌅 Petit-déjeuner", callback_data='dishes_breakfast'),
                    InlineKeyboardButton("☀️ Déjeuner", callback_data='dishes_lunch')
                ],
                [
                    InlineKeyboardButton("🌙 Dîner", callback_data='dishes_dinner'),
                    InlineKeyboardButton("📋 Tous les plats", callback_data='dishes_all')
                ],
                [InlineKeyboardButton("🏠 Retour", callback_data='main_menu')]
            ]),
            parse_mode='MarkdownV2'
        )
        
    elif data == 'action_help':
        await query.edit_message_text(
            escape_markdown("❓ **Aide - NutriSénégal Bot**\n\n"
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
            "Pour toute question : @votre_support", version=2),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ]),
            parse_mode='MarkdownV2'
        )

async def dishes_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion de la liste des plats par type"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    
    # Extraire meal_type
    meal_mapping = {
        'dishes_breakfast': 'breakfast',
        'dishes_lunch': 'lunch',
        'dishes_dinner': 'dinner',
        'dishes_all': None
    }
    
    meal_type = meal_mapping.get(query.data)
    meal_label = {
        'breakfast': '🌅 Petit-déjeuner',
        'lunch': '☀️ Déjeuner',
        'dinner': '🌙 Dîner',
        None: '📋 Tous les plats'
    }.get(meal_type)
    
    # Message d'attente
    await query.edit_message_text("🔄 Chargement des plats...")
    
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Récupérer les plats
        dishes = await loop.run_in_executor(
            None,
            lambda: get_dishes(meal_type, limit=10)
        )
        
        if dishes:
            # dishes = result['dishes']
            
            message = f"🍽️ **{meal_label}**\n\n"
            message += f"📊 {len(dishes)} plat(s) disponible(s)\n\n"
            
            # Créer keyboard avec les plats
            keyboard = []
            
            for i, dish in enumerate(dishes[:8], 1):  # Max 8 plats
                dish_id = dish['id']
                dish_name = dish['name']
                
                # Bouton pour chaque plat
                keyboard.append([
                    InlineKeyboardButton(
                        f"{i}. {dish_name[:35]}", 
                        callback_data=f'dish_view_{dish_id}'
                    )
                ])
            
            # Boutons de navigation
            keyboard.append([
                InlineKeyboardButton("🔄 Changer type", callback_data='action_dishes'),
                InlineKeyboardButton("🏠 Menu", callback_data='main_menu')
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='MarkdownV2'
            )
        
        else:
            await query.edit_message_text(
                f"❌ Aucun plat trouvé pour {meal_label}.\n\n"
                "Vérifiez que la base de données contient des plats.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Réessayer", callback_data='action_dishes')],
                    [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
                ])
            )
    
    except Exception as e:
        logger.error(f"❌ Error in dishes_list_callback: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Erreur lors du chargement des plats.\n"
            f"Détails: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
            ])
        )

async def dish_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les détails d'un plat et propose l'analyse"""
    query = update.callback_query
    await query.answer()
    
    # Extraire dish_id
    dish_id = query.data.replace('dish_view_', '')
    user_id = str(update.effective_user.id)
    
    await query.edit_message_text("🔄 Chargement des détails...")
    
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Analyser le plat
        result = await loop.run_in_executor(
            None,
            lambda: analyze_dish(dish_id, user_id)
        )
        
        if result:
            # Formater l'analyse
            message = format_analysis_result(result)
            
            # Ajouter actions
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Voir alternatives", callback_data=f'alternatives_{dish_id}'),
                    InlineKeyboardButton("📋 Détails", callback_data=f'details_{dish_id}')
                ],
                [
                    InlineKeyboardButton("◀️ Retour liste", callback_data='action_dishes'),
                    InlineKeyboardButton("🏠 Menu", callback_data='main_menu')
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='MarkdownV2'
            )
        else:
            await query.edit_message_text(
                "❌ Erreur lors de l'analyse du plat.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Retour", callback_data='action_dishes')]
                ])
            )
    
    except Exception as e:
        logger.error(f"❌ Error in dish_view_callback: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Erreur: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Retour", callback_data='action_dishes')]
            ])
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
        parse_mode='MarkdownV2'
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
            parse_mode='MarkdownV2'
        )
    else:
        await waiting_msg.edit_text(
            "❌ Erreur lors de l'analyse.\n"
            "Veuillez réessayer."
        )
    
    return ConversationHandler.END

async def details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les détails nutritionnels d'un plat"""
    query = update.callback_query
    await query.answer()
    
    # Extraire dish_id
    dish_id = query.data.replace('details_', '')
    # user_id = str(update.effective_user.id)
    
    await query.edit_message_text("🔄 Chargement des détails de préparation du plat...")
    
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Analyser le plat
        result = await loop.run_in_executor(
            None,
            lambda: get_dish_details(dish_id)
        )
        
        # Afficher les details d'un plat: nom, methode de preparation, liste des ingredients avec quantité, etc
        if result:
            dish_name = safe_md(result.get('name', 'Inconnu'))
            preparation_method = safe_md(result.get('method', 'Non spécifié'))
            ingredients = result.get('ingredients', [])
            
            message = f"🍏 **Détails du Plat : {dish_name}**\n\n"
            message += f"**Méthode de Préparation** : {preparation_method}\n\n"
            message += "**Ingrédients** :\n"
            for ingredient in ingredients:
                ing_name = safe_md(ingredient.get('name', 'Inconnu'))
                quantity = safe_md(str(ingredient.get('quantity', 'N/A')))
                unit = safe_md(ingredient.get('unit', ''))
                message += f"• {ing_name} : {quantity}{unit}\n"
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Retour plat", callback_data=f'dish_view_{dish_id}')],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
                ]),
                parse_mode='MarkdownV2'
            )
        
        else:
            await query.edit_message_text(
                "❌ Détails nutritionnels non disponibles pour ce plat.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Retour plat", callback_data=f'dish_view_{dish_id}')],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
                ])
            )
    
    except Exception as e:
        logger.error(f"❌ Error in details_callback: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Erreur lors du chargement des détails.\n"
            f"Détails: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ])
        )

async def alternatives_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Propose des alternatives plus saines pour un plat donné"""
    query = update.callback_query
    await query.answer()
    
    # Extraire dish_id
    dish_id = query.data.replace('alternatives_', '')
    user_id = str(update.effective_user.id)
    
    await query.edit_message_text("🔄 Recherche d'alternatives...")
    
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Récupérer alternatives
        result = await loop.run_in_executor(
            None,
            lambda: get_alternatives(dish_id, user_id)
        )
        
        if result and result.get('alternatives'):
            alternatives = result['alternatives'][:1]  # Limiter à 3 alternatives
            
            message = "🍽️ **Alternatives plus saines**\n\n"
            
            keyword = []
            for i, alt in enumerate(alternatives, 1):
                dish_name = safe_md(alt['dish_name'])
                reason = safe_md(alt['reason'])
                
                message += f"{i}• *{dish_name}*\n"
                message += f"   {reason}\n\n"
                
                keyword.append([
                    InlineKeyboardButton(
                        f"{i}• {alt['dish_name'][:35]}", 
                        callback_data=f'dish_view_{alt["dish_id"]}'
                    )
                ])
            
            # with open('message.txt', 'a', encoding='utf-8') as f:
            #     f.write('\n\n=== Alternative Dish ===\n')
            #     f.write(message)
            keyword.append([
                InlineKeyboardButton("◀️ Retour plat", callback_data=f'dish_view_{dish_id}'),
                InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyword),
                parse_mode='MarkdownV2'
            )
        
        else:
            await query.edit_message_text(
                "❌ Aucune alternative disponible pour ce plat.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Retour plat", callback_data=f'dish_view_{dish_id}')],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
                ])
            )
    
    except Exception as e:
        logger.error(f"❌ Error in alternatives_callback: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Erreur lors de la recherche d'alternatives.\n"
            f"Détails: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ])
        )

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
        recs = result['recommendations'][:3]  # Limiter à 3 recommandations
        tips = result.get('personalized_tips', [])

        message = "⭐ *VOS RECOMMANDATIONS*\n\n"
        
        keyword = []
        for i, rec in enumerate(recs, 1):

            dish = safe_md(rec["dish_name"])
            reason = safe_md(rec["reason"])

            message += f"{i} *{dish}*\n"
            message += f"   Score : {rec['score']}/100 {format_score_emoji(rec['score'])}\n"
            message += f"   {reason}\n"

            if rec.get("nutritional_highlights"):
                for h in rec["nutritional_highlights"]:
                    highlight = safe_md(h)
                    message += f"   ✅ {highlight}\n"

            message += "\n"
            
            keyword.append([
                InlineKeyboardButton(
                    f"{i}• {rec['dish_name'][:35]}", 
                    callback_data=f'dish_view_{rec["dish_id"]}'
                )
            ])

        if tips:
            message += "💡 *CONSEILS* :\n"
            for tip in tips[:2]:
                safe_tip = safe_md(tip)
                message += f"{safe_tip}\n"

        # with open('message.txt', 'a', encoding='utf-8') as f:
        #         f.write('\n\n=== Recommendation Dish ===\n')
        #         f.write(message)
        keyword.append([
            InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')
        ])
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyword),
            parse_mode='MarkdownV2'
        )

    else:
        await query.edit_message_text(
            "❌ Aucune recommandation disponible.\nVotre profil semble incomplet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu principal", callback_data='main_menu')]
            ])
        )

async def manage_diseases_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion des maladies du profil"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    
    # Récupérer profil actuel
    profile = get_user_profile(user_id)
    
    if not profile:
        await query.edit_message_text("❌ Profil non trouvé.")
        return
    
    current_diseases = profile.get('diseases', [])
    
    # Stocker dans context pour modifications
    context.user_data['editing_diseases'] = current_diseases.copy()
    
    await query.edit_message_text(
        "🏥 **Gestion des Maladies**\n\n"
        "Sélectionnez vos maladies chroniques :\n"
        "(Cliquez pour ajouter/retirer)",
        reply_markup=diseases_keyboard(current_diseases),
        parse_mode='MarkdownV2'
    )

async def manage_diseases_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle maladie on/off"""
    query = update.callback_query
    await query.answer()
    
    current = context.user_data.get('editing_diseases', [])
    
    data = query.data
    logger.info(data)
    
    if data == 'diseases_confirm':
        # Sauvegarder les modifications
        user_id = str(update.effective_user.id)
        # new_diseases = context.user_data.get('editing_diseases', [])
        
        # Récupérer profil actuel
        profile = get_user_profile(user_id)
        result = add_list_diseases_to_profile(profile['id'], current)
        
        if result:
            await query.edit_message_text(
                "✅ **Maladies mises à jour !**\n\n"
                f"Nouvelles maladies : {', '.join(current) or 'Aucune'}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Voir profil", callback_data='action_profile')],
                    [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
                ]),
                parse_mode='MarkdownV2'
            )
        else:
            await query.edit_message_text(
                "❌ Erreur lors de la mise à jour.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Réessayer", callback_data='manage_diseases')],
                    [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
                ])
            )
    
    else:
        # Toggle disease
        # disease_name = disease_mapping.get(data)
        # current = context.user_data.get('editing_diseases', [])
        
        if data == 'none':
            current = []
        else:
            if data in current:
                current.remove(data)
            else:
                current.append(data)
                if 'none' in current:
                    current.remove('none')
        
        context.user_data['editing_diseases'] = current
        
        await query.edit_message_reply_markup(
            reply_markup=diseases_keyboard(current)
        )

async def manage_allergens_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestion des allergies du profil"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    
    # Récupérer profil actuel
    profile = get_user_profile(user_id)
    
    if not profile:
        await query.edit_message_text("❌ Profil non trouvé.")
        return
    
    current_allergens = profile.get('allergens', [])
    
    # Stocker dans context
    context.user_data['editing_allergens'] = current_allergens.copy()
    context.user_data['editing_diseases'] = profile.get('diseases', [])
    
    await query.edit_message_text(
        "🚫 **Gestion des Allergies**\n\n"
        "Sélectionnez vos allergies alimentaires :\n"
        "(Cliquez pour ajouter/retirer)",
        reply_markup=allergens_keyboard(current_allergens),
        parse_mode='MarkdownV2'
    )

async def manage_allergens_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle allergie on/off"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'allergens_confirm':
        # Sauvegarder les modifications
        user_id = str(update.effective_user.id)
        new_allergens = context.user_data.get('editing_allergens', [])
        new_diseases = context.user_data.get('editing_diseases', [])
        
        # Appel API
        # result = update_user_profile(user_id, {
        #     'user_id': user_id,
        #     'diseases': new_diseases,
        #     'allergens': new_allergens,
        #     'physical_activity_level': 'moderate'
        # })
        # Récupérer profil actuel
        profile = get_user_profile(user_id)
        result = add_list_allergens_to_profile(profile['id'], new_allergens)
        
        if result:
            await query.edit_message_text(
                "✅ **Allergies mises à jour !**\n\n"
                f"Nouvelles allergies : {', '.join(new_allergens) or 'Aucune'}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 Voir profil", callback_data='action_profile')],
                    [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
                ]),
                parse_mode='MarkdownV2'
            )
        else:
            await query.edit_message_text(
                "❌ Erreur lors de la mise à jour.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Réessayer", callback_data='manage_allergens')],
                    [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
                ])
            )
    
    else:
        # Toggle allergen
        # allergen_name = allergen_mapping.get(data)
        current = context.user_data.get('editing_allergens', [])
        
        if data == 'allergen_none':
            current = []
        else:
            if data in current:
                current.remove(data)
            else:
                current.append(data)
                if 'allergen_none' in current:
                    current.remove('allergen_none')
        
        context.user_data['editing_allergens'] = current
        
        await query.edit_message_reply_markup(
            reply_markup=allergens_keyboard(current)
        )

# async def modify_weight_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Demande nouveau poids"""
#     query = update.callback_query
#     await query.answer()
    
#     await query.edit_message_text(
#         "⚖️ **Modification du poids**\n\n"
#         "Entrez votre nouveau poids en kg :\n\n"
#         "Exemple : 75\n\n"
#         "Tapez /cancel pour annuler.",
#         parse_mode='MarkdownV2'
#     )
    
#     return MODIFYING_PROFILE

# async def modify_weight_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Traite le nouveau poids"""
#     try:
#         new_weight = float(update.message.text.strip())
        
#         if new_weight < 30 or new_weight > 300:
#             raise ValueError
        
#         user_id = str(update.effective_user.id)
        
#         # Récupérer profil actuel
#         profile = get_user_profile(user_id)
        
#         if profile:
#             # Mise à jour avec nouveau poids
#             result = update_user_profile(user_id, {
#                 'user_id': user_id,
#                 'diseases': profile.get('diseases', []),
#                 'allergens': profile.get('allergens', []),
#                 'physical_activity_level': profile.get('physical_activity_level', 'moderate'),
#                 'weight': new_weight
#             })
            
#             if result:
#                 await update.message.reply_text(
#                     f"✅ **Poids mis à jour !**\n\n"
#                     f"Nouveau poids : {new_weight} kg",
#                     reply_markup=InlineKeyboardMarkup([
#                         [InlineKeyboardButton("👤 Voir profil", callback_data='action_profile')],
#                         [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
#                     ]),
#                     parse_mode='MarkdownV2'
#                 )
#             else:
#                 await update.message.reply_text(
#                     "❌ Erreur lors de la mise à jour du poids.",
#                     reply_markup=main_menu_keyboard()
#                 )
#         else:
#             await update.message.reply_text(
#                 "❌ Profil non trouvé.",
#                 reply_markup=main_menu_keyboard()
#             )
        
#         return ConversationHandler.END
    
#     except ValueError:
#         await update.message.reply_text(
#             "⚠️ Veuillez entrer un poids valide (entre 30 et 300 kg)\n"
#             "Exemple : 75"
#         )
#         return MODIFYING_PROFILE

# async def delete_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Confirmation suppression profil"""
#     query = update.callback_query
#     await query.answer()
    
#     await query.edit_message_text(
#         "⚠️ **Suppression du profil**\n\n"
#         "Êtes-vous sûr de vouloir supprimer votre profil ?\n"
#         "Cette action est irréversible.\n\n"
#         "⚠️ Toutes vos données seront perdues.",
#         reply_markup=InlineKeyboardMarkup([
#             [
#                 InlineKeyboardButton("✅ Oui, supprimer", callback_data='confirm_delete'),
#                 InlineKeyboardButton("❌ Annuler", callback_data='action_profile')
#             ]
#         ]),
#         parse_mode='MarkdownV2'
#     )

# async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Supprime le profil"""
#     query = update.callback_query
#     await query.answer()
    
#     user_id = str(update.effective_user.id)
    
#     result = delete_user_profile(user_id)
    
#     if result:
#         await query.edit_message_text(
#             "✅ **Profil supprimé**\n\n"
#             "Votre profil a été supprimé avec succès.\n\n"
#             "Utilisez /start pour créer un nouveau profil.",
#             parse_mode='MarkdownV2'
#         )
#     else:
#         await query.edit_message_text(
#             "❌ Erreur lors de la suppression du profil.",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🏠 Menu", callback_data='main_menu')]
#             ])
#         )

