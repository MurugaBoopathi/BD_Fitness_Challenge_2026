"""
Export Documentation Script
Copies all documentation files to a single folder for easy access and sharing

Usage:
    python export_documentation.py
"""

import os
import shutil
from datetime import datetime

def export_documentation():
    """Export all documentation files to a docs folder"""
    
    # Create export folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_folder = f"BD_Fitness_Challenge_Documentation_{timestamp}"
    
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)
    
    # List of documentation files to export
    doc_files = [
        "README.md",
        "AUTHENTICATION.md",
        "ADMIN_GUIDE.md",
        "QUICKSTART.md",
        "IMPLEMENTATION_SUMMARY.md"
    ]
    
    # Additional files that might be useful
    additional_files = [
        "requirements.txt",
        "app.py",
        "firebase_config.py",
        "migrate_users.py",
        "set_admin.py",
    ]
    
    print("=" * 70)
    print("BD Fitness Challenge - Documentation Export")
    print("=" * 70)
    print()
    
    # Copy documentation files
    print("📚 Copying Documentation Files...")
    copied_count = 0
    
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            shutil.copy2(doc_file, export_folder)
            print(f"  ✅ {doc_file}")
            copied_count += 1
        else:
            print(f"  ⚠️  {doc_file} - Not found")
    
    print()
    
    # Ask if user wants to include source files
    print("Would you like to include source code files as well?")
    include_code = input("Include source files? (yes/no): ").lower().strip()
    
    if include_code in ['yes', 'y']:
        print()
        print("📦 Copying Source Files...")
        
        # Create subdirectories
        utils_folder = os.path.join(export_folder, "utils")
        if not os.path.exists(utils_folder):
            os.makedirs(utils_folder)
        
        for code_file in additional_files:
            if os.path.exists(code_file):
                shutil.copy2(code_file, export_folder)
                print(f"  ✅ {code_file}")
                copied_count += 1
            else:
                print(f"  ⚠️  {code_file} - Not found")
        
        # Copy utils folder
        if os.path.exists("utils"):
            for file in os.listdir("utils"):
                if file.endswith(".py"):
                    src = os.path.join("utils", file)
                    dst = os.path.join(utils_folder, file)
                    shutil.copy2(src, dst)
                    print(f"  ✅ utils/{file}")
                    copied_count += 1
    
    print()
    print("=" * 70)
    print("✅ Export Complete!")
    print("=" * 70)
    print(f"📁 Location: {os.path.abspath(export_folder)}")
    print(f"📊 Total files copied: {copied_count}")
    print()
    print("You can now:")
    print("  • Share this folder with others")
    print("  • Zip it for email/transfer")
    print("  • Upload to cloud storage")
    print("  • Keep as backup")
    print()
    
    # Create a README in the export folder
    readme_content = f"""# BD Fitness Challenge - Documentation Package

**Exported on**: {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}
**Version**: 2.1.0 (with Admin Features)

## 📚 Documentation Files Included

### Main Documentation
- **README.md** - Complete project overview and features
- **AUTHENTICATION.md** - Authentication system details
- **ADMIN_GUIDE.md** - Admin features and management guide
- **QUICKSTART.md** - Quick start guide for users and admins
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation details

### Utility Scripts
- **migrate_users.py** - Migrate existing users to authentication
- **set_admin.py** - Manage admin privileges

### Configuration
- **requirements.txt** - Python dependencies

## 🚀 Quick Links

Start with:
1. **README.md** - Overview of the entire application
2. **QUICKSTART.md** - Get started quickly
3. **AUTHENTICATION.md** - Understand the auth system
4. **ADMIN_GUIDE.md** - If you're an administrator

## 📞 Support

For questions or issues, refer to the documentation files or contact your administrator.

---

**Project**: BD Fitness Challenge 2026
**Team**: BD/SWD
**Last Updated**: {datetime.now().strftime("%Y-%m-%d")}
"""
    
    with open(os.path.join(export_folder, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"📝 Created INDEX.md in {export_folder}")
    print()
    
    return export_folder


if __name__ == "__main__":
    try:
        folder = export_documentation()
        
        # Ask if user wants to open the folder
        print("Would you like to open the exported folder?")
        open_folder = input("Open folder? (yes/no): ").lower().strip()
        
        if open_folder in ['yes', 'y']:
            # Open folder in file explorer
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(folder)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', folder])
            else:  # Linux
                subprocess.Popen(['xdg-open', folder])
            
            print(f"✅ Opened {folder}")
        
        print()
        print("Thank you for using BD Fitness Challenge! 🎉")
        
    except KeyboardInterrupt:
        print("\n\n❌ Export cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during export: {e}")
