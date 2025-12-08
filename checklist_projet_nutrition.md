# CHECKLIST COMPLÈTE - SYSTÈME DE RECOMMANDATION ALIMENTAIRE
## Projet Master 1 - 2 Semaines

---

## 📋 PHASE PRÉPARATOIRE (Jour 0)

### Documentation Préliminaire
- [x] Définir les objectifs SMART du projet
- [x] Lister les contraintes (temps, budget, compétences)
- [x] Identifier les outils/technologies à utiliser
- [x] Créer le repository Git/GitHub
- [x] Préparer l'environnement de développement

### Recherche Documentaire
- [x] Rechercher 5-8 articles scientifiques sur nutrition et maladies chroniques
- [x] Consulter recommandations OMS sur diabète/cancer/maladies hépatiques
- [ ] Documenter les statistiques locales (Sénégal) sur ces maladies
- [ ] Identifier applications similaires existantes
- [ ] Noter les points forts/faibles des solutions existantes

---

## 🗂️ SEMAINE 1 : BACKEND & BASE DE DONNÉES

### JOUR 1-2 : Conception & Modélisation

#### Modèle de Données
- [x] Créer le diagramme Entité-Relations (ERD)
- [x] Définir les 8-10 tables principales
- [x] Établir les relations entre entités
- [x] Définir les clés primaires et étrangères
- [x] Créer le dictionnaire de données (description de chaque champ)
- [ ] Valider le modèle avec un encadreur/pair

#### Base de Connaissances Nutritionnelles
- [-] Lister 50 aliments de base sénégalais prioritaires
- [x] Collecter valeurs nutritionnelles (calories, glucides, protéines, lipides, fibres)
- [x] Rechercher index glycémique des aliments (diabète)
- [x] Identifier teneur en sodium (problèmes hépatiques/HTA)
- [-] Documenter 30-40 plats locaux typiques (thiébou, yassa, mafé, etc.)
- [x] Lister ingrédients de chaque plat

#### Règles Métier - Diabète
- [x] Définir seuils glycémiques (IG < 55 faible, 55-70 moyen, >70 élevé)
- [x] Établir limites glucides par repas (45-60g)
- [x] Lister aliments interdits/limités/recommandés
- [x] Définir portions recommandées

#### Règles Métier - Allergies
- [x] Lister 14 allergènes majeurs (arachide, gluten, lactose, etc.)
- [x] Créer matrice allergène-aliment
- [x] Définir niveaux d'alerte (critique, attention, traces)
- [ ] Documenter allergies croisées (ex: latex-banane)

#### Règles Métier - Problèmes Hépatiques
- [x] Définir limite sodium (< 2000mg/jour)
- [x] Lister aliments hépatotoxiques
- [x] Établir restrictions protéines selon stade
- [x] Documenter aliments détoxifiants

#### Règles Métier - Cancer
- [x] Identifier aliments anti-inflammatoires
- [x] Lister aliments à éviter (ultra-transformés)
- [ ] Documenter interactions avec traitements
- [x] Définir besoins caloriques augmentés

#### Système de Scoring
- [x] Créer formule de calcul score compatibilité (0-100)
- [x] Définir pondération des critères
- [x] Établir code couleur (vert/orange/rouge)
- [ ] Tester avec 10 cas d'exemple

### JOUR 3-4 : Implémentation Base de Données

#### Setup Technique
- [x] Choisir SGBD (PostgreSQL recommandé / MongoDB si NoSQL)
- [x] Installer et configurer localement
- [x] Créer la base de données principale
- [x] Configurer utilisateurs et permissions

#### Création des Tables
- [x] Table `users` avec champs de base
- [x] Table `health_profiles` (profils santé)
- [x] Table `diseases` (maladies)
- [x] Table `allergens` (allergènes)
- [x] Table `foods` (aliments)
- [x] Table `ingredients` (ingrédients)
- [x] Table `dishes` (plats/menus)
- [x] Table `dish_ingredients` (composition)
- [x] Table `disease_food_restrictions` (restrictions)
- [x] Table `allergen_food_mapping` (correspondances)
- [x] Table `user_meal_history` (historique)

#### Indexation & Optimisation
- [ ] Créer index sur `user_id`
- [ ] Créer index sur `disease_id`, `allergen_id`
- [ ] Créer index full-text sur noms d'aliments
- [ ] Tester performances requêtes

#### Peuplement Initial
- [x] Insérer 5 maladies principales
- [x] Insérer 14 allergènes majeurs
- [x] Insérer 50 aliments de base
- [x] Insérer 30 plats locaux
- [ ] Insérer règles restrictions (minimum 50 règles)
- [ ] Vérifier intégrité des données

#### Scripts & Backup
- [x] Créer script de migration
- [ ] Créer script de seed (données initiales)
- [ ] Créer script de backup
- [ ] Documenter procédures dans README

### JOUR 5-7 : API Backend & Logique Métier

#### Setup Backend
- [x] Choisir framework (FastAPI/Python ou Express/Node.js)
- [x] Créer structure projet (MVC ou équivalent)
- [x] Configurer connexion base de données
- [x] Installer dépendances (ORM, validation, etc.)
- [x] Configurer variables d'environnement (.env)

#### API Endpoints - Gestion Utilisateurs
- [x] `POST /api/users/register` - Inscription
- [ ] `POST /api/users/login` - Connexion (optionnel pour MVP)
- [x] `GET /api/users/:id/profile` - Récupérer profil
- [ ] `PUT /api/users/:id/profile` - Modifier profil
- [ ] `DELETE /api/users/:id` - Supprimer compte

#### API Endpoints - Profil Santé
- [x] `POST /api/health-profiles` - Créer profil santé
- [x] `GET /api/health-profiles/:userId` - Récupérer profil
- [x] `PUT /api/health-profiles/:id` - Mettre à jour
- [x] `POST /api/health-profiles/:id/diseases` - Ajouter maladie
- [x] `POST /api/health-profiles/:id/allergens` - Ajouter allergène
- [x] `DELETE /api/health-profiles/:id/diseases/:diseaseId` - Retirer maladie

#### API Endpoints - Analyse de Menu
- [x] `POST /api/analyze-menu` - Analyser un menu (texte)
- [x] `POST /api/analyze-dish` - Analyser un plat spécifique
- [x] `GET /api/recommendations/:userId` - Obtenir recommandations
- [x] `POST /api/alternatives/:dishId` - Suggérer alternatives

#### API Endpoints - Base de Données Aliments
- [ ] `GET /api/foods` - Liste aliments (avec pagination)
- [ ] `GET /api/foods/:id` - Détails aliment
- [x] `GET /api/foods/search?q=` - Recherche aliment
- [x] `GET /api/dishes` - Liste plats
- [x] `GET /api/dishes/:id` - Détails plat avec ingrédients

#### Logique Métier - Module Analyse
- [ ] Fonction `extractIngredients(menuText)` - Extraire ingrédients du texte
- [x] Fonction `identifyAllergens(ingredients)` - Détecter allergènes
- [ ] Fonction `calculateGlycemicLoad(dish)` - Calculer charge glycémique
- [ ] Fonction `checkRestrictions(dish, healthProfile)` - Vérifier restrictions
- [x] Fonction `calculateCompatibilityScore(dish, healthProfile)` - Score 0-100
- [x] Fonction `generateAlerts(analysis)` - Générer alertes colorées
- [x] Fonction `suggestAlternatives(dish, restrictions)` - Alternatives

#### Intégration IA/NLP
- [ ] Choisir API NLP (Claude API, OpenAI, ou Hugging Face)
- [ ] Créer compte et obtenir clé API
- [ ] Implémenter fonction `analyzeMenuWithAI(text)`
- [ ] Créer prompt efficace pour extraction ingrédients
- [ ] Tester avec 10-15 descriptions de plats
- [ ] Gérer cas d'erreurs API
- [ ] Implémenter cache pour réduire coûts

#### Tests API
- [ ] Tester chaque endpoint avec Postman/Insomnia
- [ ] Créer collection de tests
- [ ] Valider codes de retour HTTP
- [ ] Tester cas d'erreur (données invalides)
- [ ] Documenter l'API (Swagger/OpenAPI optionnel)

#### Sécurité & Validation
- [ ] Valider entrées utilisateur
- [ ] Protéger contre injections SQL
- [ ] Implémenter rate limiting (optionnel)
- [ ] Gérer erreurs proprement
- [ ] Logger les requêtes importantes

---

## 💬 SEMAINE 2 : INTERFACES & INTÉGRATION

### JOUR 8-10 : Chatbot

#### Choix de Plateforme
- [x] Décider priorité : Telegram (plus simple) ou WhatsApp
- [x] Créer compte développeur sur plateforme choisie
- [x] Lire documentation officielle

#### Telegram Bot (Recommandé pour MVP)
- [x] Créer bot via @BotFather
- [x] Obtenir token API
- [x] Installer SDK/bibliothèque (python-telegram-bot ou node-telegram-bot-api)
- [x] Configurer webhook ou polling
- [x] Tester connexion basique

<!-- #### WhatsApp Bot (Alternative)
- [ ] S'inscrire à Twilio ou WhatsApp Business API
- [ ] Obtenir numéro test
- [ ] Configurer webhook
- [ ] Vérifier limitations free tier -->

#### Flux de Conversation - Onboarding
- [x] Message de bienvenue `/start`
- [x] Demander nom/prénom
- [-] Demander âge/genre (optionnel)
- [x] Questionnaire maladies chroniques (menu à choix)
- [x] Questionnaire allergies (menu à choix)
- [x] Confirmation profil créé
- [x] Sauvegarder dans base de données

#### Flux de Conversation - Analyse Menu
- [x] Commande `/analyser` ou message direct
- [x] Demander description du menu
- [x] Envoyer texte à API backend
- [x] Afficher résultat avec emojis (🟢🟠🔴)
- [ ] Lister ingrédients détectés
- [x] Afficher alertes si nécessaire
- [x] Proposer alternatives si menu incompatible

#### Flux de Conversation - Commandes Utiles
- [x] `/profil` - Voir son profil santé
- [x] `/modifier` - Modifier profil
- [x] `/aide` - Menu d'aide
- [ ] `/historique` - Voir dernières analyses (optionnel)
- [x] `/recommandations` - Idées de menus

#### Gestion des États Conversation
- [x] Implémenter machine à états (onboarding, idle, analyzing)
- [x] Gérer contexte utilisateur
- [ ] Timeout si inactivité
- [ ] Gérer erreurs utilisateur (commandes invalides)

#### Interface Utilisateur Chatbot
- [x] Utiliser boutons interactifs (inline keyboard)
- [x] Créer menus de navigation clairs
- [x] Ajouter emojis pour clarté
- [x] Formatter messages proprement (Markdown/HTML)
- [ ] Limiter longueur des messages

#### Tests Chatbot
- [ ] Tester onboarding complet
- [ ] Tester 10 scénarios d'analyse
- [ ] Tester modification profil
- [ ] Tester comportement erreurs
- [ ] Tester avec plusieurs utilisateurs simultanés

### JOUR 11-12 : Interface Web (MVP)

#### Setup Frontend
- [ ] Choisir framework (React recommandé / Vue.js)
- [ ] Créer projet avec Vite/Create React App
- [ ] Installer Tailwind CSS pour styling
- [ ] Configurer Axios/Fetch pour appels API
- [ ] Créer structure dossiers (components, pages, utils)

#### Pages Principales
- [ ] Page d'accueil/Landing
- [ ] Page inscription/connexion (simple)
- [ ] Page profil santé (formulaire)
- [ ] Page analyse de menu (principale)
- [ ] Page résultats d'analyse
- [ ] Page historique (optionnel)

#### Composants - Profil Santé
- [ ] Formulaire informations personnelles
- [ ] Sélecteur multi-choix maladies (checkboxes)
- [ ] Sélecteur multi-choix allergènes (checkboxes)
- [ ] Bouton sauvegarder
- [ ] Affichage profil actuel
- [ ] Option modifier/supprimer

#### Composants - Analyse Menu
- [ ] Zone de texte pour description menu
- [ ] Bouton "Analyser"
- [ ] Loader pendant analyse
- [ ] Carte de résultats avec score coloré
- [ ] Liste ingrédients détectés
- [ ] Section alertes (rouge/orange/jaune)
- [ ] Section recommandations/alternatives
- [ ] Bouton "Nouvelle analyse"

#### Composants - Résultats Visuels
- [ ] Badge score avec couleur (vert/orange/rouge)
- [ ] Graphique radar nutritionnel (optionnel mais valorisant)
- [ ] Liste avec icônes pour allergènes détectés
- [ ] Cartes alternatives suggérées
- [ ] Explications pédagogiques

#### Design & UX
- [ ] Design responsive (mobile-first)
- [ ] Palette de couleurs cohérente
- [ ] Typographie lisible
- [ ] Espacement suffisant
- [ ] Feedback visuel sur actions (toasts/notifications)
- [ ] Accessibilité (contraste, labels)

#### Connexion Backend
- [ ] Configurer URL API (variable d'environnement)
- [ ] Implémenter appels API pour chaque fonctionnalité
- [ ] Gérer tokens/sessions (si auth)
- [ ] Gérer erreurs réseau
- [ ] Afficher messages d'erreur utilisateur-friendly

#### Tests Interface Web
- [ ] Tester sur Chrome/Firefox/Safari
- [ ] Tester responsive (mobile/tablette/desktop)
- [ ] Tester formulaires (validation)
- [ ] Tester flux complet utilisateur
- [ ] Corriger bugs UI

### JOUR 13 : Déploiement

#### Backend Deployment
- [ ] Choisir plateforme (Railway, Render, Heroku)
- [ ] Créer compte
- [ ] Configurer variables d'environnement
- [ ] Déployer API backend
- [ ] Tester endpoints en production
- [ ] Configurer domaine (optionnel)

#### Base de Données Production
- [ ] Provisionner base de données cloud (Railway/Supabase)
- [ ] Migrer schéma
- [ ] Importer données initiales
- [ ] Tester connexion depuis backend
- [ ] Configurer backups automatiques

#### Frontend Deployment
- [ ] Choisir plateforme (Vercel, Netlify)
- [ ] Connecter repository GitHub
- [ ] Configurer build
- [ ] Déployer
- [ ] Tester site en production
- [ ] Configurer domaine custom (optionnel)

#### Chatbot Deployment
- [ ] Configurer webhook en production (si nécessaire)
- [ ] Mettre à jour token bot avec URL production
- [ ] Tester bot en conditions réelles
- [ ] Configurer monitoring (optionnel)

#### Tests Post-Déploiement
- [ ] Tester toute la chaîne bout-en-bout
- [ ] Vérifier performances/temps de réponse
- [ ] Tester avec données réelles
- [ ] Inviter 3-5 utilisateurs bêta
- [ ] Collecter premiers retours

### JOUR 14 : Documentation & Préparation Soutenance

#### Documentation Technique
- [ ] README.md complet (installation, utilisation)
- [ ] Diagrammes d'architecture (système, séquence)
- [ ] Documentation API (endpoints, paramètres, réponses)
- [ ] Schéma base de données
- [ ] Guide de déploiement
- [ ] Difficultés rencontrées et solutions

#### Documentation Utilisateur
- [ ] Guide d'utilisation chatbot (avec captures)
- [ ] Guide d'utilisation interface web
- [ ] FAQ (questions fréquentes)
- [ ] Vidéo démo 2-3 minutes (optionnel mais valorisant)

#### Rapport Académique
- [ ] Page de garde
- [ ] Résumé/Abstract (français/anglais)
- [ ] Introduction (problématique, objectifs)
- [ ] État de l'art (revue littérature)
- [ ] Méthodologie (conception, technologies)
- [ ] Implémentation (choix techniques justifiés)
- [ ] Résultats (captures, tests, statistiques)
- [ ] Discussion (limites, perspectives)
- [ ] Conclusion
- [ ] Bibliographie (normes APA/IEEE)
- [ ] Annexes (code snippets, questionnaires)

#### Préparation Présentation
- [ ] Créer slides PowerPoint/Google Slides (15-20 slides)
- [ ] Structure : Contexte → Problème → Solution → Démo → Résultats → Perspectives
- [ ] Inclure captures écrans/vidéos
- [ ] Préparer démonstration live
- [ ] Préparer plan B (vidéo) si problème réseau
- [ ] Répéter présentation (15-20 min)
- [ ] Anticiper questions jury

#### Tests Finaux
- [ ] Tests utilisateurs (5-10 personnes)
- [ ] Collecter retours qualitatifs
- [ ] Mesurer temps de réponse
- [ ] Calculer taux de précision recommandations
- [ ] Documenter bugs connus

---

## 📸 RECONNAISSANCE D'IMAGES (Intégré au MVP)

### JOUR 10-11 : Module Reconnaissance Visuelle

#### Choix Stack Vision AI
- [ ] Choisir API Vision (Google Cloud Vision, Clarifai, ou Claude API)
- [ ] Créer compte et obtenir clés API
- [ ] Vérifier quotas/limites gratuites
- [ ] Tester avec 10 images de test

#### Préparation Données Visuelles
- [ ] Collecter 50-100 photos de plats sénégalais
- [ ] Photographier plats locaux typiques
- [ ] Télécharger images libres de droits
- [ ] Créer dataset d'entraînement (optionnel)
- [ ] Organiser par catégories de plats

#### Backend - Endpoints Image
- [ ] `POST /api/analyze-image` - Upload et analyse d'image
- [ ] `POST /api/identify-dish-from-image` - Identification plat
- [ ] `GET /api/image-history/:userId` - Historique photos
- [ ] Support formats (JPEG, PNG, WebP)
- [ ] Limite taille fichier (5-10 MB)

#### Logique Reconnaissance
- [ ] Fonction `uploadImage(file)` - Validation et stockage temporaire
- [ ] Fonction `analyzeImageWithAI(imageData)` - Appel API Vision
- [ ] Fonction `extractDishName(visionResults)` - Extraire nom du plat
- [ ] Fonction `matchDishInDatabase(dishName)` - Correspondance BDD
- [ ] Fonction `combineVisionAndNutrition(dish, healthProfile)` - Analyse complète
- [ ] Gestion des images non reconnues (fallback vers saisie manuelle)

#### Intégration Chatbot
- [ ] Telegram : Support envoi photo
- [ ] Recevoir image de l'utilisateur
- [ ] Compresser image si nécessaire
- [ ] Envoyer à API backend
- [ ] Afficher résultat identification + analyse
- [ ] Option "Ce n'est pas ça" → correction manuelle

#### Intégration Web
- [ ] Composant upload image (drag & drop)
- [ ] Prévisualisation image
- [ ] Bouton "Analyser cette photo"
- [ ] Loader pendant traitement
- [ ] Affichage plat identifié avec confiance (%)
- [ ] Option caméra (mobile web)

#### Amélioration Précision
- [ ] Créer mapping noms détectés → plats BDD
- [ ] Gérer variations noms (thiéboudienne/ceebu jën/tiep)
- [ ] Détecter ingrédients visibles (tomates, poisson, riz)
- [ ] Combiner détection objet + reconnaissance plat
- [ ] Logger erreurs pour amélioration future

#### Tests Reconnaissance
- [ ] Tester avec 20 plats différents
- [ ] Mesurer taux de précision (objectif >70%)
- [ ] Tester éclairages différents
- [ ] Tester angles de prise de vue
- [ ] Tester plats mixtes/composés

#### Application Mobile Native
- [ ] Citer frameworks (React Native, Flutter)
- [ ] Justifier avantages (notifications, offline)
- [ ] Proposer roadmap 6 mois

#### Fonctionnalités Avancées
- [ ] Planification de menus hebdomadaires
- [ ] Suivi glycémique intégré
- [ ] Communauté/partage recettes
- [ ] Intégration wearables (glucomètres)
- [ ] Téléconsultation nutritionniste

#### Machine Learning Avancé
- [ ] Recommandations personnalisées (historique)
- [ ] Prédiction besoins nutritionnels
- [ ] Détection automatique anomalies alimentaires

---

## ✅ CRITÈRES DE SUCCÈS

### Critères Techniques
- [ ] Système fonctionne sans crash majeur
- [ ] Base de données contient minimum 50 aliments, 30 plats
- [ ] API répond en < 3 secondes
- [ ] Chatbot répond à 80%+ des requêtes valides
- [ ] Interface web responsive et intuitive

### Critères Académiques
- [ ] Rapport 30-50 pages structuré
- [ ] 5-8 références scientifiques
- [ ] Diagrammes techniques clairs
- [ ] Présentation 15-20 minutes fluide
- [ ] Démonstration convaincante

### Critères Fonctionnels
- [ ] Détecte correctement 90%+ des allergènes communs
- [ ] Recommandations pertinentes pour diabétiques
- [ ] Score de compatibilité cohérent
- [ ] Alternatives proposées réalistes

---

## 📦 LIVRABLES FINAUX

### Code Source
- [ ] Repository GitHub/GitLab propre
- [ ] Code commenté
- [ ] .gitignore configuré
- [ ] Branches organisées (main, develop)
- [ ] Commits réguliers avec messages clairs

### Documentation
- [ ] README détaillé
- [ ] Rapport académique PDF
- [ ] Présentation PowerPoint/PDF
- [ ] Vidéo de démonstration (optionnel)

### Système Déployé
- [ ] API backend accessible
- [ ] Interface web en ligne
- [ ] Chatbot fonctionnel (au moins Telegram)
- [ ] Liens partagés avec jury

---

## ⏰ RÉCAPITULATIF CHRONOLOGIQUE

**Jour 1-2** : Modélisation + Collecte données nutritionnelles  
**Jour 3-4** : Création base de données + Peuplement  
**Jour 5-7** : Développement API backend + Logique métier  
**Jour 8-10** : Chatbot (Telegram priorité)  
**Jour 11-12** : Interface web MVP  
**Jour 13** : Déploiement complet  
**Jour 14** : Documentation + Préparation soutenance  

---

## 🎯 CONSEILS DE PRIORISATION

### MUST HAVE (Obligatoire)
- Base de données fonctionnelle
- API backend opérationnelle
- Chatbot Telegram basique
- Documentation technique minimale
- Rapport académique

### SHOULD HAVE (Important)
- Interface web responsive
- Système de scoring sophistiqué
- Tests utilisateurs
- Vidéo démo

### COULD HAVE (Nice to have)
- Graphiques nutritionnels
- Historique détaillé
- Intégration WhatsApp
- Déploiement domaine custom

### WON'T HAVE (Reporter)
- Reconnaissance d'images
- Application mobile
- Machine learning avancé
- Paiements/abonnements

---

**BONNE CHANCE ! 🍀**

*Conseil final : Commitez votre code quotidiennement, testez régulièrement, et n'hésitez pas à simplifier si vous prenez du retard. Un MVP fonctionnel vaut mieux qu'un système complexe incomplet.*