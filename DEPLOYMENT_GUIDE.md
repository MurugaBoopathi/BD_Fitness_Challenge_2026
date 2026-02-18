# BD Fitness Challenge - Deployment Guide

## Setting Admin Rights in Production

### Option 1: First User Auto-Admin ✅ (Recommended)
**Status:** Now implemented in the code!

The first user who registers in your application **automatically becomes an admin**. This is perfect for deployment on Render or any cloud platform.

**How it works:**
- When a user registers, the system checks if any users exist in the database
- If no users exist, the new user gets `is_admin: true` automatically
- All subsequent users are regular users by default

**Steps:**
1. Deploy your app to Render
2. Register yourself as the first user
3. You'll automatically have admin privileges
4. Grant admin rights to others via Admin Dashboard → User Management

---

### Option 2: Run set_admin.py Locally (Works Anytime)
Even after deployment, you can run the admin script from your local machine since it connects directly to Firebase.

**Command:**
```bash
python set_admin.py --grant your.email@example.com
```

**Why this works:**
- The script connects to Firebase using your credentials
- Firebase is cloud-based, so local script = deployed app = same database
- No need to access the Render server

---

### Option 3: Firebase Console (Manual)
Access Firebase directly to edit user data:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `bd-fitness-challenge-2026`
3. Navigate to: **Firestore Database** → **users** collection
4. Find your user document
5. Click **Edit**
6. Add field: `is_admin` = `true` (boolean)
7. Save changes

---

## Deploying to Render

### Prerequisites
- Firebase project with Firestore enabled
- Firebase service account JSON file
- GitHub repository (optional but recommended)

### Step 1: Prepare Environment Variables
In Render dashboard, add these environment variables:

```env
FIREBASE_CREDENTIALS=<paste entire contents of bd-fitness-challenge-2026.json here>
```

**Important:** Copy the entire JSON content as a single-line string or multi-line value.

### Step 2: Create requirements.txt
Ensure your `requirements.txt` includes:
```txt
streamlit==1.31.0
firebase-admin==6.3.0
pandas==2.1.4
plotly==5.18.0
```

### Step 3: Configure Render Service

1. **Create New Web Service**
   - Connect your GitHub repository
   - Or use Render's Git integration

2. **Build Settings**
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

3. **Environment Variables**
   - Add `FIREBASE_CREDENTIALS` with your JSON content

4. **Instance Type**
   - Free tier is sufficient for testing
   - Upgrade to paid tier for production (better performance)

### Step 4: Deploy
- Click **Create Web Service**
- Wait for deployment (usually 2-5 minutes)
- Access your app at: `https://your-app-name.onrender.com`

### Step 5: Register as First User
- Open your deployed app
- Click **Register**
- Fill in your details
- You'll automatically become admin (first user privilege)

### Step 6: Verify Admin Access
- Login to your deployed app
- Check sidebar for "⭐ Admin User" badge
- Access "🔧 Admin Dashboard" from menu

---

## Troubleshooting

### Firebase Connection Issues
**Problem:** App can't connect to Firebase

**Solution:**
1. Verify `FIREBASE_CREDENTIALS` environment variable is set correctly
2. Ensure the JSON is valid (use a JSON validator)
3. Check Firebase project permissions
4. Verify service account has Firestore access

### First User Not Getting Admin
**Problem:** Registered as first user but not admin

**Solution:**
1. Check Firestore console - ensure users collection is empty before registration
2. Use Option 2 or 3 to manually grant admin rights
3. Verify `is_admin` field appears in user document

### Port Binding Issues
**Problem:** Streamlit not starting on Render

**Solution:**
Ensure start command includes port binding:
```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## Security Best Practices

### 1. Protect Firebase Credentials
- Never commit `bd-fitness-challenge-2026.json` to Git
- Use environment variables for credentials
- Add `.json` files to `.gitignore`

### 2. Admin Access Control
- First user auto-admin only triggers when database is empty
- Regularly audit admin users in Admin Dashboard
- Revoke admin rights when users leave the organization

### 3. Database Security
- Configure Firebase Security Rules
- Limit read/write access to authenticated users
- Enable Firebase Authentication (optional enhancement)

### Example Security Rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth.uid == userId;
    }
    match /activities/{userId}/logs/{logId} {
      allow read, write: if request.auth.uid == userId;
    }
  }
}
```

---

## Monitoring & Maintenance

### Check Application Health
- Monitor Render logs for errors
- Track Firebase usage in Firebase Console
- Review admin dashboard statistics regularly

### Backup Strategy
- Firebase automatic backups (depends on plan)
- Export user data via Admin Dashboard
- Periodic manual backups via Firebase Console

### Updates & Maintenance
1. Test changes locally first
2. Push to GitHub (if using Git deployment)
3. Render auto-deploys on push (if configured)
4. Monitor deployment logs

---

## Alternative Platforms

### Deploy to Streamlit Cloud
```bash
# streamlit_app.py (if required)
# No changes needed to app.py

# Deploy via Streamlit Cloud dashboard
# Add FIREBASE_CREDENTIALS to Secrets
```

### Deploy to Heroku
```bash
# Procfile
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0

# Deploy
heroku create bd-fitness-challenge
git push heroku main
heroku config:set FIREBASE_CREDENTIALS='<json_content>'
```

### Deploy to AWS/GCP/Azure
- Use container deployment (Docker)
- Or deploy as serverless function
- Configure environment variables in respective platform

---

## Support & Resources

- **Render Documentation:** https://render.com/docs
- **Streamlit Deployment:** https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app
- **Firebase Setup:** https://firebase.google.com/docs/firestore
- **Your Firebase Console:** https://console.firebase.google.com/project/bd-fitness-challenge-2026

---

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Grant admin locally | `python set_admin.py --grant email@example.com` |
| List admins | `python set_admin.py --list` |
| Remove admin | `python set_admin.py --revoke email@example.com` |
| Check deployment logs | Render Dashboard → Logs |
| Access Firebase | console.firebase.google.com |
| Export users | Admin Dashboard → User Management |

---

**Last Updated:** February 18, 2026
**Version:** 2.2.0
