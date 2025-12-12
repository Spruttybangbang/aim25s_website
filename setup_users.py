#!/usr/bin/env python
"""
Setup users for Railway deployment
- Change admin username and password
- Create student account for classmates
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_companies_admin.settings')
# Set Railway DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:KZkUibmeAwylbYHGcocWHqTqXClSRQDC@interchange.proxy.rlwy.net:44541/railway'
django.setup()

from django.contrib.auth.models import User

def setup_users():
    print("\n" + "="*60)
    print("USER SETUP FOR RAILWAY")
    print("="*60 + "\n")

    # 1. Change admin account to linuslord
    print("1️⃣  Updating admin account...")
    try:
        admin = User.objects.get(username='admin')
        admin.username = 'linuslord'
        admin.set_password('T0pstudent!')
        admin.save()
        print("   ✅ Admin account updated:")
        print(f"      Username: linuslord")
        print(f"      Password: T0pstudent!")
        print(f"      Is superuser: {admin.is_superuser}")
        print(f"      Is staff: {admin.is_staff}")
    except User.DoesNotExist:
        # Admin doesn't exist, check if linuslord already exists
        try:
            admin = User.objects.get(username='linuslord')
            admin.set_password('T0pstudent!')
            admin.save()
            print("   ✅ Password updated for existing linuslord account")
        except User.DoesNotExist:
            # Create new superuser
            admin = User.objects.create_superuser(
                username='linuslord',
                email='',
                password='T0pstudent!'
            )
            print("   ✅ Created new superuser account:")
            print(f"      Username: linuslord")
            print(f"      Password: T0pstudent!")

    print()

    # 2. Create student account
    print("2️⃣  Setting up student account...")
    try:
        student = User.objects.get(username='ai-student')
        student.set_password('pythonrocks!')
        student.is_staff = False
        student.is_superuser = False
        student.save()
        print("   ✅ Student account updated:")
        print(f"      Username: ai-student")
        print(f"      Password: pythonrocks!")
        print(f"      Is superuser: {student.is_superuser}")
        print(f"      Is staff: {student.is_staff}")
    except User.DoesNotExist:
        student = User.objects.create_user(
            username='ai-student',
            email='',
            password='pythonrocks!'
        )
        student.is_staff = False
        student.is_superuser = False
        student.save()
        print("   ✅ Student account created:")
        print(f"      Username: ai-student")
        print(f"      Password: pythonrocks!")
        print(f"      Is superuser: {student.is_superuser}")
        print(f"      Is staff: {student.is_staff}")

    print()
    print("="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print()
    print("📝 Login credentials:")
    print()
    print("Admin (full access):")
    print("  Username: linuslord")
    print("  Password: T0pstudent!")
    print("  Access: /admin/ and /companies/")
    print()
    print("Student (view only):")
    print("  Username: ai-student")
    print("  Password: pythonrocks!")
    print("  Access: /companies/ (public view)")
    print()
    print("="*60)
    print()

if __name__ == '__main__':
    setup_users()
