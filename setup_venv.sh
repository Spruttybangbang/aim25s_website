#!/bin/bash
# Setup-script för att skapa virtual environment och installera beroenden

set -e  # Avsluta vid fel

echo "======================================"
echo "  AI Companies Admin - Setup"
echo "======================================"
echo ""

# Kontrollera om .venv redan finns
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment (.venv) finns redan!"
    echo ""
    read -p "Vill du ta bort och skapa om den? (j/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        echo "Tar bort .venv..."
        rm -rf .venv
    else
        echo "Avbryter. Använd 'source .venv/bin/activate' för att aktivera befintlig .venv"
        exit 0
    fi
fi

echo "1. Skapar virtual environment (.venv)..."
python3 -m venv .venv

echo "2. Aktiverar .venv..."
source .venv/bin/activate

echo "3. Uppgraderar pip..."
pip install --upgrade pip

echo "4. Installerar beroenden från requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Setup klart!"
echo ""
echo "======================================"
echo "  Nästa steg:"
echo "======================================"
echo ""
echo "1. Aktivera virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Placera din databas (om du har en):"
echo "   cp /sökväg/till/ai_companies.db ."
echo "   python manage.py migrate --fake-initial"
echo ""
echo "3. Eller skapa test-data:"
echo "   python create_sample_data.py"
echo ""
echo "4. Starta servern:"
echo "   python manage.py runserver"
echo ""
echo "5. Öppna: http://127.0.0.1:8000/admin"
echo "   Användarnamn: admin"
echo "   Lösenord: admin123"
echo ""
echo "======================================"
