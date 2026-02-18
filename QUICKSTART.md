# Quick Start Guide - Authentication Setup

## 🎯 For Administrators

### Step 1: Understand What Changed
The app now requires users to login with email/password instead of just selecting their name.

### Step 2: Migrate Existing Users (If Any)

If you have existing users in the database, run the migration script:

```bash
python migrate_users.py
```

This will:
- Generate temporary credentials for all existing users
- Display the credentials on screen
- Optionally save them to `migrated_users_credentials.txt`

**⚠️ IMPORTANT**: Keep these credentials secure! Share them privately with each user.

### Step 3: Share Credentials with Users

Send each user their temporary login details:
```
Email: [their.email@bdchallenge.temp]
Temporary Password: [generated_password]
```

**Instruct users to**:
1. Login with temporary credentials
2. Immediately change their password via Profile → Change Password

### Step 4: Test the System

1. Try registering a new account
2. Try logging in
3. Test password change
4. Test logout
5. Verify all features work after login

### Step 5: Set Up Admin Users (Recommended)

Grant admin privileges to yourself or designated administrators:

**Interactive mode:**
```bash
python set_admin.py
```

**Command line:**
```bash
python set_admin.py --grant admin@example.com
```

**For admin features, see [ADMIN_GUIDE.md](ADMIN_GUIDE.md)**

## 🎯 For New Users

### Creating an Account

1. Open the application
2. Click "Register" tab
3. Fill in:
   - Full Name: Your complete name
   - Email: Your email address
   - Password: Must have:
     - At least 8 characters
     - 1 uppercase letter (A-Z)
     - 1 lowercase letter (a-z)
     - 1 number (0-9)
4. Click "Create Account"
5. You're logged in! Start using the app

### Logging In

1. Open the application
2. Click "Login" tab (default)
3. Enter your email and password
4. Click "Login"

### Using the App

After login, you can:
- **Log Activity**: Record your fitness activities
- **View Leaderboard**: See rankings and compete
- **Edit/Delete Activities**: Manage your logged activities
- **My History**: View charts and statistics
- **Profile**: Update info and change password
- **Logout**: Click logout button in sidebar

**For Admin Users:**
- **Admin Dashboard**: Access comprehensive oversight tools (see [ADMIN_GUIDE.md](ADMIN_GUIDE.md))

## 🔄 For Migrated Users

If you're an existing user who was migrated:

1. **Login with Temporary Credentials**
   - Use the email and password provided by admin
   - Usually: `firstname.lastname@bdchallenge.temp`

2. **Change Your Password Immediately**
   - Click "Profile" in sidebar
   - Scroll to "Change Password" section
   - Enter:
     - Current Password: Your temporary password
     - New Password: Your chosen secure password
     - Confirm New Password: Same as new password
   - Click "Change Password"

3. **Update Your Email (Optional)**
   - If you want to use your real email instead of the temporary one
   - Contact administrator to update

## 🛠️ Troubleshooting

### Can't Login
- Double-check your email (it's case-insensitive but must be exact)
- Verify password is correct
- Ensure account exists (try Register if new user)

### Forgot Password
- Currently: Contact administrator for password reset
- Future: Password reset feature will be added

### Account Locked
- Contact administrator
- Check if account is marked as `is_active: false`

## 📋 Security Reminders

✅ **DO**:
- Use strong, unique passwords
- Change temporary passwords immediately
- Logout when done (especially on shared computers)
- Keep credentials private

❌ **DON'T**:
- Share your password with others
- Use simple/common passwords
- Leave app logged in on shared devices
- Reuse passwords from other sites

## 🚀 Running the Application

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📞 Getting Help

If you encounter issues:
1. Check error messages carefully
2. Review the AUTHENTICATION.md documentation
3. Contact your administrator
4. Check Firebase console (admins only)

## ✅ Quick Checklist for Admins

Before rolling out:
- [ ] Run `migrate_users.py` if existing users
- [ ] Save/distribute temporary credentials securely
- [ ] Test login/registration yourself
- [ ] Verify all features work after authentication
- [ ] Set up admin users with `set_admin.py`
- [ ] Test admin dashboard functionality
- [ ] Brief users on how to change passwords
- [ ] Set up support channel for questions
- [ ] Delete `migrated_users_credentials.txt` after distribution

## 🎉 Ready to Go!

Once authentication is set up:
1. Users register/login
2. All existing features work normally
3. Data remains secure
4. Ready for wider deployment

---

**Need Help?** Contact the application administrator or refer to:
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for admin features
- [AUTHENTICATION.md](AUTHENTICATION.md) for detailed documentation
