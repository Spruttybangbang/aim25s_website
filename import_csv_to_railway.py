#!/usr/bin/env python
"""
CSV Import Script for Railway PostgreSQL
Imports company data from import_data.csv to Railway database
"""
import os
import sys
import csv
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_companies_admin.settings')
# Set Railway DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:KZkUibmeAwylbYHGcocWHqTqXClSRQDC@interchange.proxy.rlwy.net:44541/railway'
django.setup()

from companies.models import AICompany
from django.db import transaction

def parse_boolean(value):
    """Convert string to boolean"""
    if not value or value == '':
        return None
    true_values = ['TRUE', '1', 'YES', 'JA', 'Y', 'J', 'True', 'true', 'SANT']
    return str(value).strip() in true_values

def import_csv(csv_file='import_data.csv'):
    """Import companies from CSV file to Railway database"""

    print(f"\n{'='*60}")
    print("CSV IMPORT TO RAILWAY POSTGRESQL")
    print(f"{'='*60}\n")

    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"❌ Error: {csv_file} not found!")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in current directory: {os.listdir('.')}")
        return

    # Read CSV
    print(f"📖 Reading {csv_file}...")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"✓ Found {len(rows)} rows in CSV\n")

    # Get all valid field names from AICompany model
    valid_fields = {f.name for f in AICompany._meta.get_fields()}

    # Also include db_column names
    db_column_map = {}
    for field in AICompany._meta.get_fields():
        if hasattr(field, 'db_column') and field.db_column:
            db_column_map[field.db_column] = field.name

    print(f"Model fields: {len(valid_fields)}")
    print(f"DB column mappings: {len(db_column_map)}\n")

    # Confirm before proceeding
    print("This will:")
    print("  1. Delete existing test company (ID 9999)")
    print(f"  2. Import {len(rows)} companies to Railway PostgreSQL")
    print()

    # Check for --auto-confirm flag
    auto_confirm = '--auto-confirm' in sys.argv

    if not auto_confirm:
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Import cancelled")
            return
    else:
        print("Auto-confirm enabled, proceeding with import...")

    print("\n📦 Starting import...\n")

    created = 0
    updated = 0
    errors = []

    try:
        with transaction.atomic():
            # Delete test company
            AICompany.objects.filter(id=9999).delete()
            print("✓ Deleted test company (ID 9999)")

            # Import companies
            for i, row in enumerate(rows, 1):
                try:
                    # Extract ID
                    company_id = int(row['id']) if row.get('id') else None
                    if not company_id:
                        errors.append(f"Row {i}: Missing ID")
                        continue

                    # Build company data dict
                    company_data = {'id': company_id}

                    for csv_column, value in row.items():
                        if csv_column == 'id':
                            continue  # Already handled

                        # Skip empty values
                        if value == '' or value is None:
                            value = None

                        # Map db_column names to field names
                        if csv_column in db_column_map:
                            field_name = db_column_map[csv_column]
                        else:
                            field_name = csv_column

                        # Only include valid fields
                        if field_name not in valid_fields:
                            continue  # Skip unknown columns

                        # Handle boolean fields
                        if field_name == 'STORSTOCKHOLM':
                            value = parse_boolean(value)

                        company_data[field_name] = value

                    # Create or update company
                    company, was_created = AICompany.objects.update_or_create(
                        id=company_id,
                        defaults=company_data
                    )

                    if was_created:
                        created += 1
                    else:
                        updated += 1

                    # Progress indicator
                    if i % 50 == 0:
                        print(f"  Processed {i}/{len(rows)} companies...")

                except Exception as e:
                    error_msg = f"Row {i} (ID {row.get('id', 'unknown')}): {str(e)}"
                    errors.append(error_msg)
                    print(f"  ⚠️  {error_msg}")

            print(f"\n{'='*60}")
            print("IMPORT COMPLETE")
            print(f"{'='*60}")
            print(f"✓ Created: {created} companies")
            print(f"✓ Updated: {updated} companies")

            if errors:
                print(f"\n⚠️  Errors: {len(errors)}")
                for error in errors[:10]:  # Show first 10 errors
                    print(f"  - {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")

            # Verify total count
            total = AICompany.objects.count()
            print(f"\n📊 Total companies in database: {total}")

            # Show sample
            sample = AICompany.objects.exclude(id=9999).first()
            if sample:
                print(f"\n📝 Sample company:")
                print(f"  ID: {sample.id}")
                print(f"  Name: {sample.NAMN}")
                print(f"  AI capabilities: {sample.AI_FÖRMÅGA_V2}")
                print(f"  Industry: {sample.BRANSCHKLUSTER_V2}")

            print(f"\n{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Import failed: {str(e)}")
        raise

if __name__ == '__main__':
    import_csv()
