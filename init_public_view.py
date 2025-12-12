#!/usr/bin/env python3
"""
Script för att initialisera standardkolumner för den publika vyn
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_companies_admin.settings')
django.setup()

from companies.models import PublicViewConfiguration

def init_default_columns():
    """Skapar standardkolumner för den publika vyn"""

    print("Initialiserar standardkolumner för publik vy...")

    # Ta bort eventuella existerande konfigurationer
    existing_count = PublicViewConfiguration.objects.count()
    if existing_count > 0:
        print(f"Hittade {existing_count} existerande kolumnkonfigurationer.")
        response = input("Vill du ersätta dem med standardkolumner? (j/n): ")
        if response.lower() != 'j':
            print("Avbryter...")
            return

        PublicViewConfiguration.objects.all().delete()
        print(f"Raderade {existing_count} existerande konfigurationer.")

    # Skapa standardkonfigurationer - Enkel tabell med 4 kolumner
    default_configs = [
        # Alla kolumner visas på både desktop och mobil
        {'column_name': 'name', 'show_on_desktop': True, 'show_on_mobile': True, 'display_order': 0},
        {'column_name': 'bransch', 'show_on_desktop': True, 'show_on_mobile': True, 'display_order': 1},
        {'column_name': 'ai_capabilities', 'show_on_desktop': True, 'show_on_mobile': True, 'display_order': 2},
        {'column_name': 'location_city', 'show_on_desktop': True, 'show_on_mobile': True, 'display_order': 3},
    ]

    created_count = 0
    for config in default_configs:
        PublicViewConfiguration.objects.create(**config)
        created_count += 1
        print(f"  ✓ Skapade kolumn: {config['column_name']}")

    print(f"\n✅ Initialisering klar! Skapade {created_count} standardkolumner.")
    print("\nDu kan nu:")
    print("  1. Gå till Django Admin (/admin)")
    print("  2. Öppna 'Publik vy - kolumnkonfigurationer'")
    print("  3. Redigera vilka kolumner som ska visas på desktop vs mobil")
    print("  4. Ändra ordning genom att justera 'Visningsordning'")
    print("\nFör att lägga till fler kolumner, använd admin-action 'Skapa alla kolumner'")

if __name__ == '__main__':
    init_default_columns()
