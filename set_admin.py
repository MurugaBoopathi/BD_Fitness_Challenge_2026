"""
Admin Privileges Management Script
Set or remove admin privileges for users in the BD Fitness Challenge app

Usage:
    python set_admin.py
"""

import sys
from firebase_config import db
from utils.auth_utils import set_admin_status, get_all_users


def display_users():
    """Display all users with their admin status"""
    users = get_all_users()
    
    if not users:
        print("No users found in the database.")
        return []
    
    print("\n" + "=" * 80)
    print("All Users")
    print("=" * 80)
    print(f"{'#':<4} {'Name':<40} {'Email':<30} {'Admin':<6}")
    print("-" * 80)
    
    for idx, user in enumerate(users, 1):
        name = user.get('full_name', 'Unknown')
        email = user.get('email', 'N/A')
        is_admin = "Yes" if user.get('is_admin', False) else "No"
        print(f"{idx:<4} {name:<40} {email:<30} {is_admin:<6}")
    
    print("=" * 80)
    return users


def set_admin_interactive():
    """Interactive mode to set admin privileges"""
    while True:
        users = display_users()
        
        if not users:
            return
        
        print("\nOptions:")
        print("1. Grant admin privileges to a user")
        print("2. Remove admin privileges from a user")
        print("3. Show current admin users only")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            # Grant admin
            user_num = input(f"\nEnter user number to grant admin (1-{len(users)}): ").strip()
            try:
                user_idx = int(user_num) - 1
                if 0 <= user_idx < len(users):
                    selected_user = users[user_idx]
                    
                    if selected_user.get('is_admin', False):
                        print(f"\n⚠️  {selected_user['full_name']} is already an admin!")
                    else:
                        confirm = input(f"\nGrant admin rights to {selected_user['full_name']}? (yes/no): ")
                        if confirm.lower() in ['yes', 'y']:
                            set_admin_status(selected_user['uid'], True)
                            print(f"\n✅ Admin rights granted to {selected_user['full_name']}")
                        else:
                            print("\n❌ Cancelled")
                else:
                    print("\n❌ Invalid user number")
            except ValueError:
                print("\n❌ Invalid input")
        
        elif choice == "2":
            # Remove admin
            user_num = input(f"\nEnter user number to remove admin (1-{len(users)}): ").strip()
            try:
                user_idx = int(user_num) - 1
                if 0 <= user_idx < len(users):
                    selected_user = users[user_idx]
                    
                    if not selected_user.get('is_admin', False):
                        print(f"\n⚠️  {selected_user['full_name']} is not an admin!")
                    else:
                        confirm = input(f"\nRemove admin rights from {selected_user['full_name']}? (yes/no): ")
                        if confirm.lower() in ['yes', 'y']:
                            set_admin_status(selected_user['uid'], False)
                            print(f"\n✅ Admin rights removed from {selected_user['full_name']}")
                        else:
                            print("\n❌ Cancelled")
                else:
                    print("\n❌ Invalid user number")
            except ValueError:
                print("\n❌ Invalid input")
        
        elif choice == "3":
            # Show admins only
            admin_users = [u for u in users if u.get('is_admin', False)]
            
            print("\n" + "=" * 80)
            print("Current Admin Users")
            print("=" * 80)
            
            if admin_users:
                print(f"{'#':<4} {'Name':<40} {'Email':<30}")
                print("-" * 80)
                for idx, user in enumerate(admin_users, 1):
                    name = user.get('full_name', 'Unknown')
                    email = user.get('email', 'N/A')
                    print(f"{idx:<4} {name:<40} {email:<30}")
                print("=" * 80)
                print(f"\nTotal: {len(admin_users)} admin user(s)")
            else:
                print("No admin users found!")
                print("=" * 80)
        
        elif choice == "4":
            print("\nExiting...")
            break
        
        else:
            print("\n❌ Invalid option")
        
        input("\nPress Enter to continue...")
        print("\n" * 2)


def set_admin_by_email(email: str, grant: bool):
    """Set admin status for a user by email (command line mode)"""
    users = get_all_users()
    user = next((u for u in users if u.get('email', '').lower() == email.lower()), None)
    
    if not user:
        print(f"❌ User with email '{email}' not found")
        return False
    
    current_status = user.get('is_admin', False)
    
    if grant and current_status:
        print(f"⚠️  {user['full_name']} is already an admin")
        return False
    
    if not grant and not current_status:
        print(f"⚠️  {user['full_name']} is not an admin")
        return False
    
    set_admin_status(user['uid'], grant)
    
    if grant:
        print(f"✅ Admin rights granted to {user['full_name']} ({email})")
    else:
        print(f"✅ Admin rights removed from {user['full_name']} ({email})")
    
    return True


if __name__ == "__main__":
    print("=" * 80)
    print("BD Fitness Challenge - Admin Management")
    print("=" * 80)
    print()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("Usage:")
            print("  python set_admin.py                    # Interactive mode")
            print("  python set_admin.py --grant <email>    # Grant admin to user")
            print("  python set_admin.py --revoke <email>   # Remove admin from user")
            print("  python set_admin.py --list             # List all admin users")
            print()
        elif sys.argv[1] == '--grant' and len(sys.argv) > 2:
            email = sys.argv[2]
            set_admin_by_email(email, True)
        elif sys.argv[1] == '--revoke' and len(sys.argv) > 2:
            email = sys.argv[2]
            set_admin_by_email(email, False)
        elif sys.argv[1] == '--list':
            users = get_all_users()
            admin_users = [u for u in users if u.get('is_admin', False)]
            
            print("Current Admin Users:")
            print("-" * 80)
            if admin_users:
                for user in admin_users:
                    print(f"  • {user.get('full_name', 'Unknown')} ({user.get('email', 'N/A')})")
                print(f"\nTotal: {len(admin_users)} admin user(s)")
            else:
                print("  No admin users found")
        else:
            print("Invalid arguments. Use --help for usage information.")
    else:
        # Interactive mode
        try:
            set_admin_interactive()
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
