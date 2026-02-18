# Admin Features Documentation

## 🔧 Admin Dashboard Overview

The BD Fitness Challenge application now includes a comprehensive Admin Dashboard that allows designated administrators to oversee and manage the entire platform.

## ⭐ Admin Capabilities

### 📊 System Overview
- View total users, active users, and admin count
- Monitor total activities, points, and distance across all users
- Track average activities and points per user
- See recent activity summary from all users (last 20 activities)

### 🔍 Review All Activities
Admins can:
- **View all activities** from all users in one place
- **Filter activities** by:
  - User (select specific user or view all)
  - Date range (from/to dates)
  - Activity type (Walking, Running, Cycling, etc.)
- **Review activity details**:
  - Distance, duration, calories
  - View uploaded attachments/screenshots
  - See which user posted each activity
- **Delete activities** if needed (with single click)

### 👥 User Management
Comprehensive user account management:
- **View all users** with details:
  - Name, email, admin status, active status
  - Account creation date
  - Last login time
- **View individual user stats**:
  - Total activities logged
  - Total points earned
  - Total distance covered
- **Grant/Remove admin rights** to any user
- **Activate/Deactivate accounts** as needed

### 📈 Detailed Statistics
Advanced analytics across all users:
- **Activity Type Distribution** (pie chart)
  - See which activities are most popular
- **Points by Activity Type** (bar chart)
  - Identify which activities generate the most points
- **Activity Trend Over Time** (line chart)
  - Monitor monthly activity trends
- **Top 10 Performers** (horizontal bar chart)
  - All-time leaderboard with total points

## 🚀 Setting Up Admin Users

### Method 1: Using the Interactive Script (Recommended)

1. **Run the admin setup script**:
   ```bash
   python set_admin.py
   ```

2. **Follow the interactive menu**:
   ```
   Options:
   1. Grant admin privileges to a user
   2. Remove admin privileges from a user
   3. Show current admin users only
   4. Exit
   ```

3. **Grant admin to a user**:
   - Select option 1
   - Enter the user number from the list
   - Confirm the action
   - User will have admin access on next login

### Method 2: Using Command Line

**Grant admin rights:**
```bash
python set_admin.py --grant user@example.com
```

**Remove admin rights:**
```bash
python set_admin.py --revoke user@example.com
```

**List current admins:**
```bash
python set_admin.py --list
```

**View help:**
```bash
python set_admin.py --help
```

### Method 3: Directly in Firebase (Advanced)

1. Open Firebase Console
2. Go to Firestore Database
3. Navigate to `users` collection
4. Select the user document
5. Add/Update field: `is_admin: true`
6. User will have admin access on next login

### Method 4: Within the App (Admin-to-Admin)

If you're already an admin, you can grant admin to others:
1. Login as admin
2. Go to "Admin Dashboard"
3. Click "User Management" tab
4. Select a user
5. Click "Grant Admin Rights" button

## 🎯 Accessing Admin Dashboard

### For Admin Users:

1. **Login** to the application with your credentials
2. Look for the **⭐ Admin User** badge in the sidebar
3. See **🔧 Admin Dashboard** as the first menu option
4. Click to access all admin features

### Visual Indicators:
- Sidebar shows "⭐ **Admin User**" badge
- Admin Dashboard appears at top of navigation menu
- Access to 4 tabs: Overview, Review Activities, User Management, Statistics

## 🔐 Admin Security

### Access Control:
- ✅ Only users with `is_admin: true` can access admin features
- ✅ Non-admin users see "Access Denied" if they try to access admin routes
- ✅ Admin status checked on every page load
- ✅ Admin privileges stored securely in Firebase

### Best Practices:
1. **Limit Admin Users**: Only grant admin to trusted individuals
2. **Regular Audits**: Periodically review who has admin access
3. **Document Changes**: Keep track of who was granted admin and when
4. **Monitor Activities**: Check the admin dashboard regularly
5. **Revoke When Needed**: Remove admin rights when no longer required

## 📋 Admin Use Cases

### Use Case 1: Monitoring Platform Health
**Scenario**: Weekly check of platform activity
1. Go to Admin Dashboard → Overview
2. Check total users and active users ratio
3. Review recent activity summary
4. Identify any drop in engagement

### Use Case 2: Reviewing Suspicious Activities
**Scenario**: A user reported an unusually high point entry
1. Go to Admin Dashboard → Review Activities
2. Filter by the specific user
3. Sort by points (highest first)
4. Review activity details and attachments
5. Delete if fraudulent

### Use Case 3: Granting Admin to Team Lead
**Scenario**: New team lead needs admin access
1. Option A: Use set_admin.py script
   ```bash
   python set_admin.py --grant teamlead@company.com
   ```
2. Option B: Use Admin Dashboard
   - Go to User Management
   - Select the team lead
   - Click "Grant Admin Rights"

### Use Case 4: Monthly Report Generation
**Scenario**: Need statistics for monthly meeting
1. Go to Admin Dashboard → Statistics
2. Review all charts and metrics
3. Take screenshots or export data
4. Note top performers for recognition

### Use Case 5: User Account Issues
**Scenario**: User can't access their account
1. Go to Admin Dashboard → User Management
2. Search for the user
3. Check their active status
4. Click "Activate Account" if deactivated
5. Verify last login time

## 🎨 Admin Dashboard Tabs Explained

### Tab 1: 📊 Overview
**Purpose**: Quick health check of the platform
- **Metrics displayed**:
  - User counts (total, active, admins)
  - Activity counts and totals
  - Aggregated statistics
- **Recent activities**: Last 20 activities across all users
- **Best for**: Daily/weekly monitoring

### Tab 2: 🔍 Review Activities
**Purpose**: Deep dive into user activities
- **Filtering options**:
  - By user (dropdown)
  - By date range (from/to)
  - By activity type
- **Actions available**:
  - View full details
  - See attachments
  - Delete activities
- **Best for**: Investigating specific activities, quality control

### Tab 3: 👥 User Management
**Purpose**: Manage user accounts and permissions
- **View user list**: All users with key info
- **User details**: Select any user for deep dive
- **Actions available**:
  - Grant/remove admin rights
  - Activate/deactivate accounts
  - View activity statistics per user
- **Best for**: Account management, permission changes

### Tab 4: 📈 Statistics
**Purpose**: Platform-wide analytics and insights
- **Charts provided**:
  - Activity type distribution (pie)
  - Points by activity (bar)
  - Monthly trend (line)
  - Top performers (horizontal bar)
- **Best for**: Reports, trend analysis, recognition programs

## 🚨 Common Admin Tasks

### Task: Find and Review a Specific Activity
```
1. Admin Dashboard → Review Activities
2. Select the user from dropdown
3. Set date range if known
4. Click on the activity expander
5. Review details and attachment
6. Delete if necessary
```

### Task: Grant Admin to Multiple Users
```
Option 1: Interactive (for multiple at once)
1. Run: python set_admin.py
2. For each user:
   - Select option 1
   - Enter user number
   - Confirm

Option 2: Command line (for batch)
python set_admin.py --grant user1@example.com
python set_admin.py --grant user2@example.com
python set_admin.py --grant user3@example.com
```

### Task: Generate Monthly Report
```
1. Admin Dashboard → Statistics
2. Screenshot each chart
3. Admin Dashboard → Overview
4. Note key metrics
5. Compile in report document
```

### Task: Investigate High Activity User
```
1. Admin Dashboard → Review Activities
2. Filter by specific user
3. Sort by recent or by points
4. Check if attachments are valid
5. Contact user if suspicious
6. Delete fraudulent activities
```

## 📊 Admin Metrics Explained

| Metric | Description | Found In |
|--------|-------------|----------|
| Total Users | All registered accounts | Overview |
| Active Users | Users who have logged in | Overview |
| Total Activities | Sum of all logged activities | Overview |
| Admin Users | Users with admin privileges | Overview |
| Total Points | Aggregated points across all users | Overview |
| Total KM | Aggregated distance across all users | Overview |
| Avg Activities/User | Total activities ÷ total users | Overview |
| Avg Points/User | Total points ÷ total users | Overview |

## 🔄 Admin Workflow Examples

### Weekly Monitoring Workflow
```
Monday Morning Routine:
1. Login as admin
2. Check Overview → Review key metrics
3. Compare with last week
4. Check Statistics → Review trends
5. Note any anomalies
6. Review Activities if needed
```

### New Admin Onboarding Workflow
```
When adding new admin:
1. Verify they need admin access
2. Run: python set_admin.py --grant their@email.com
3. Notify them of new privileges
4. Send them this documentation
5. Schedule a walkthrough session
6. Add to admin list in your records
```

### Activity Audit Workflow
```
Monthly audit:
1. Review Activities → Set date range for month
2. Filter by "All Users"
3. Sort by points (highest)
4. Review top 20 activities
5. Check attachments
6. Verify legitimacy
7. Take action if needed
```

## ⚠️ Important Notes

### Admin Responsibilities:
- **Data Privacy**: Admins can see all user data - handle responsibly
- **Fair Review**: Review activities objectively and consistently
- **Communication**: Inform users before deleting their activities
- **Documentation**: Keep records of admin actions taken
- **Security**: Never share admin credentials

### Limitations:
- Admins cannot edit activities (only delete)
- Admins cannot change user passwords directly
- Activity deletion is permanent (no undo)
- Admin changes take effect on next page load/login

### Things Admins CANNOT Do:
- ❌ Directly edit someone's activity details
- ❌ Reset user passwords (users must do this themselves)
- ❌ Create activities on behalf of users
- ❌ Modify historical data in bulk
- ❌ Export all data (feature not implemented)

### Things Admins CAN Do:
- ✅ View all activities across all users
- ✅ Delete inappropriate or fraudulent activities
- ✅ Activate/deactivate user accounts
- ✅ Grant/revoke admin privileges
- ✅ Monitor platform statistics
- ✅ Review activity attachments

## 🆘 Troubleshooting

### "Access Denied" when accessing Admin Dashboard
**Solution**: Verify your account has `is_admin: true` in database
```bash
python set_admin.py --list
```
If not listed, ask another admin to grant you access.

### Admin Dashboard menu not showing
**Solution**: Logout and login again. Admin status loads at login.

### Can't grant admin to a user
**Solution**: 
1. Verify you are an admin
2. Check user exists in database
3. Try command line method:
   ```bash
   python set_admin.py --grant user@email.com
   ```

### Statistics not loading
**Solution**: 
1. Check if there are any activities in database
2. Refresh the page
3. Check Firebase connection

## 📚 Additional Resources

- **Main Documentation**: [README.md](README.md)
- **Authentication Guide**: [AUTHENTICATION.md](AUTHENTICATION.md)
- **Quick Start Guide**: [QUICKSTART.md](QUICKSTART.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## 🎉 Summary

The Admin Dashboard provides comprehensive oversight and management capabilities:
- ✅ Monitor platform health and engagement
- ✅ Review and moderate user activities
- ✅ Manage user accounts and permissions
- ✅ Analyze trends and generate reports
- ✅ Ensure data quality and platform integrity

**Admin access is powerful - use it wisely and responsibly!**

---

**Last Updated**: February 18, 2026
**Version**: 2.1.0 (with admin features)
