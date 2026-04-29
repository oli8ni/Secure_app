#!/bin/bash
# Script de lancement rapide pour développement local

echo "🛡️  SecureAlert - Lancement local"
echo "=================================="

# Vérifier que streamlit est installé
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit non trouvé. Installation..."
    pip install -r requirements.txt
fi

# Lancer l'application
cd app
echo "🚀 Démarrage de l'application..."
streamlit run streamlit_app.py
