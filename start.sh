#!/bin/bash
# Snabbstart-script för AI Companies Admin

# Kontrollera om vi är i virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  VARNING: Virtual environment är inte aktiverad!"
    echo ""
    echo "Rekommendation:"
    echo "  1. Aktivera .venv: source .venv/bin/activate"
    echo "  2. Kör detta script igen"
    echo ""
    read -p "Fortsätt ändå? (j/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
        exit 1
    fi
    PYTHON_CMD="python3"
else
    echo "✅ Virtual environment aktiverad: $VIRTUAL_ENV"
    PYTHON_CMD="python"
fi

echo "======================================"
echo "  AI Companies Admin - Snabbstart"
echo "======================================"
echo ""
echo "Startar Django development server..."
echo ""
echo "Admin-gränssnitt: http://127.0.0.1:8000/admin"
echo "Användarnamn: admin"
echo "Lösenord: admin123"
echo ""
echo "Tryck Ctrl+C för att stoppa servern"
echo "======================================"
echo ""

$PYTHON_CMD manage.py runserver
