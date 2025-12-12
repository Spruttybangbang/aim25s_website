#!/bin/bash

echo "🔍 Kontrollerar DATABASE_URL format..."
echo ""

if [ -z "$1" ]; then
    echo "❌ Ingen DATABASE_URL angiven!"
    echo ""
    echo "Användning:"
    echo "  ./check_database_url.sh 'postgresql://user:pass@host:port/db'"
    exit 1
fi

URL="$1"

# Kontrollera om det är en komplett PostgreSQL URL
if [[ $URL =~ ^postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
    echo "✅ URL ser korrekt ut!"
    echo ""
    echo "   Username: ${BASH_REMATCH[1]}"
    echo "   Password: ***skjult***"
    echo "   Host:     ${BASH_REMATCH[3]}"
    echo "   Port:     ${BASH_REMATCH[4]}"
    echo "   Database: ${BASH_REMATCH[5]}"
    echo ""
    echo "📋 Kör nu detta kommando:"
    echo "DATABASE_URL='$URL' ./run_railway_setup.sh"
else
    echo "❌ URL är ofullständig eller felaktig!"
    echo ""
    echo "Din URL: $URL"
    echo ""
    echo "Ska vara format: postgresql://user:pass@host:port/database"
    echo "Exempel: postgresql://postgres:abc123@web-production-f430b.up.railway.app:5432/railway"
    echo ""
    echo "Hittade du hela DATABASE_URL i Railway Variables?"
fi
