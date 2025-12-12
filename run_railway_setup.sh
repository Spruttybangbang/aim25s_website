#!/bin/bash

# Kontrollera att DATABASE_URL är satt
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL är inte satt!"
    echo "Kör scriptet så här:"
    echo "DATABASE_URL='postgresql://user:pass@host:port/db' ./run_railway_setup.sh"
    exit 1
fi

echo "🔗 Ansluter till Railway PostgreSQL..."
echo ""

echo "📊 Initialiserar public view configuration..."
DATABASE_URL="$DATABASE_URL" python init_public_view.py

echo ""
echo "👤 Skapar superuser..."
DATABASE_URL="$DATABASE_URL" python manage.py createsuperuser

echo ""
echo "✅ Setup klar!"
