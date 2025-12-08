from telegram.helpers import escape_markdown

def safe_md(text: str) -> str:
    """Échappe tout texte pour Markdown V2 sans rien casser."""
    if text is None:
        return ""
    # text = text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')
    text = text.replace('´', '\'')
    return escape_markdown(text, version=2)


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
🍲 **Plat** : {safe_md(analysis.get('name', 'Inconnu'))}

🎯 **Score de compatibilité** : {score}/100 {format_score_emoji(score)}
🚦 **Niveau d'alerte** : {format_alert_level(alert_level)}
"""
    
    # Alertes
    if analysis['allergen_alerts']:
        message += "\n⚠️ **ALERTES** :\n"
        for alert in analysis['allergen_alerts'][:3]:  # Max 5 alertes
            message += f"• {alert['message']}\n"
    if analysis['disease_alerts']:
        message += "\n⚠️ **ALERTES** :\n"
        for alert in analysis['disease_alerts'][:3]:  # Max 5 alertes
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
