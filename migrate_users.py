"""
Migration Script for BD Fitness Challenge
This script helps migrate existing users to the new authentication system.

Usage:
    python migrate_users.py

This script will:
1. Find all existing users without authentication credentials
2. Generate temporary credentials for them
3. Display the credentials (to be securely shared with users)
4. Users must change their password on first login
"""

import sys
from firebase_config import db
from utils.auth_utils import hash_password
import secrets


def migrate_users():
    """Migrate existing users to the authentication system"""
    
    print("=" * 60)
    print("BD Fitness Challenge - User Migration to Authentication")
    print("=" * 60)
    print()
    
    # Get all users
    users_ref = db.collection("users")
    all_users = list(users_ref.stream())
    
    print(f"Found {len(all_users)} user(s) in the database.\n")
    
    migrated_count = 0
    already_migrated = 0
    credentials_list = []
    
    for user_doc in all_users:
        user_data = user_doc.to_dict()
        uid = user_doc.id
        full_name = user_data.get("full_name", "Unknown")
        
        # Check if user already has authentication setup
        if user_data.get("password_hash") and user_data.get("email"):
            print(f"✓ {full_name}: Already migrated")
            already_migrated += 1
            continue
        
        # Generate email from name if not exists
        email = user_data.get("email")
        if not email:
            # Create email from name (replace spaces with dots, make lowercase)
            email_base = full_name.lower()
            # Remove department info in parentheses
            if "(" in email_base:
                email_base = email_base[:email_base.index("(")].strip()
            email_base = email_base.replace(" ", ".").replace("(", "").replace(")", "")
            email = f"{email_base}@bdchallenge.temp"
        
        # Generate a secure temporary password
        temp_password = secrets.token_urlsafe(12)
        
        # Hash the password
        hashed_pwd, salt = hash_password(temp_password)
        
        # Update user document
        users_ref.document(uid).update({
            "email": email.lower(),
            "password_hash": hashed_pwd,
            "password_salt": salt,
            "is_active": True,
            "requires_password_change": True,
            "migrated_at": __import__('datetime').datetime.now().isoformat()
        })
        
        credentials_list.append({
            "name": full_name,
            "email": email,
            "temp_password": temp_password
        })
        
        print(f"✓ {full_name}: Migrated successfully")
        migrated_count += 1
    
    print()
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total users: {len(all_users)}")
    print(f"Already migrated: {already_migrated}")
    print(f"Newly migrated: {migrated_count}")
    print()
    
    if credentials_list:
        print("=" * 60)
        print("TEMPORARY CREDENTIALS (Share securely with users)")
        print("=" * 60)
        print()
        print("NOTE: Users MUST change their password after first login!")
        print()
        
        for cred in credentials_list:
            print(f"Name: {cred['name']}")
            print(f"Email: {cred['email']}")
            print(f"Temporary Password: {cred['temp_password']}")
            print("-" * 60)
        
        # Optionally save to file
        save = input("\nSave credentials to file? (yes/no): ").lower()
        if save in ['yes', 'y']:
            with open("migrated_users_credentials.txt", "w") as f:
                f.write("BD Fitness Challenge - Migrated User Credentials\n")
                f.write("=" * 60 + "\n")
                f.write("NOTE: Users MUST change their password after first login!\n\n")
                
                for cred in credentials_list:
                    f.write(f"Name: {cred['name']}\n")
                    f.write(f"Email: {cred['email']}\n")
                    f.write(f"Temporary Password: {cred['temp_password']}\n")
                    f.write("-" * 60 + "\n")
            
            print("✓ Credentials saved to migrated_users_credentials.txt")
            print("⚠️  Please keep this file secure and delete after sharing!")
    
    print()
    print("Migration completed successfully!")


if __name__ == "__main__":
    try:
        confirm = input("This will migrate users to the new authentication system. Continue? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            migrate_users()
        else:
            print("Migration cancelled.")
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        sys.exit(1)
