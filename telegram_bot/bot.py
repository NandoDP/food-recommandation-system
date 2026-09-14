"""
CHATBOT TELEGRAM - NUTRISENEGAL BOT
Assistant nutrition personnalisé avec analyse de plats
"""

import logging
from telegram import Update
# from telegram.helpers import escape_markdown
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
# ==================== HELPERS API ====================
from telegram_bot.services.action_handles import (
    start,
    onboarding_name,
    onboarding_weight,
    onboarding_diseases_callback,
    onboarding_allergens_callback,
    analyze_text_start,
    analyze_dish_text,
    menu_callback,
    recommendations_callback,
    alternatives_callback,
    dishes_list_callback,
    dish_view_callback,
    details_callback,
    manage_diseases_callback,
    manage_diseases_toggle,
    manage_allergens_callback,
    manage_allergens_toggle,
    cancel,
    main_menu_keyboard,
    ONBOARDING_NAME,
    ONBOARDING_WEIGHT,
    ONBOARDING_DISEASES,
    ONBOARDING_ALLERGENS,
    ANALYZING_DISH
)

from telegram_bot.config import settings

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # filename='bot.log',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



# ==================== MAIN ====================

def main():
    """Démarre le bot"""
    
    if not settings.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN n'est pas défini dans les variables d'environnement.")
        return
    
    # Créer l'application
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    
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
    app.add_handler(CallbackQueryHandler(dishes_list_callback, pattern='^analyze_list$'))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(menu_callback, pattern='^(main_menu|action_|modify_)'))
    app.add_handler(CallbackQueryHandler(recommendations_callback, pattern='^meal_'))
    app.add_handler(CallbackQueryHandler(alternatives_callback, pattern='^alternatives_'))
    app.add_handler(CallbackQueryHandler(dishes_list_callback, pattern='^dishes_'))
    app.add_handler(CallbackQueryHandler(dish_view_callback, pattern='^dish_view_'))
    app.add_handler(CallbackQueryHandler(details_callback, pattern='^details_'))
    app.add_handler(CallbackQueryHandler(manage_diseases_callback, pattern='^manage_diseases$'))
    app.add_handler(CallbackQueryHandler(manage_diseases_toggle, pattern='^(disease_|diseases_confirm)$'))
    app.add_handler(CallbackQueryHandler(manage_allergens_callback, pattern='^manage_allergens$'))
    app.add_handler(CallbackQueryHandler(manage_allergens_toggle, pattern='^(allergen_|allergens_confirm)$'))
    # app.add_handler(CallbackQueryHandler(modify_weight_callback, pattern='^modify_weight$'))
    # app.add_handler(CallbackQueryHandler(delete_profile_callback, pattern='^delete_profile$'))
    
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