# Stack Technique

## Backend

Framework : Python + FastAPI
ORM : SQLAlchemy
Validation : Pydantic

## Base de Données

SGBD : PostgreSQL (production) + dbeaver
Cache : Redis (optionnel, pour images déjà analysées)

## APIs IA/ML

#### Pour NLP (Analyse de Texte)

- Option 1 : Claude API (Anthropic) - Excellent pour comprendre contexte et nuances
- Option 2 : OpenAI GPT-4 - Très performant
- Option 3 : Hugging Face (gratuit mais moins précis)

#### Pour Vision (Reconnaissance d'Images) ⭐

- TensorFlow/PyTorch + MobileNet
- Fine-tuné sur plats sénégalais
- Plus complexe mais précis


## Stockage Images

Cloud : Cloudinary (gratuit 25GB) ou AWS S3
Temporaire : Système de fichiers local puis suppression après analyse

## Chatbot

Telegram : python-telegram-bot / node-telegram-bot-api
WhatsApp : Twilio API (payant après essai)

## Frontend Web

Framework : React.js + Vite
Styling : Tailwind CSS
Upload Images : react-dropzone ou input HTML5
Caméra : react-webcam (pour photo directe)
HTTP Client : Axios

## Déploiement

Backend : Railway.app ou Render.com (support images)
Frontend : Vercel ou Netlify
Base de Données : Railway PostgreSQL ou Supabase
Stockage Images : Cloudinary (CDN intégré)

