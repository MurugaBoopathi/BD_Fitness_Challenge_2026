# BD Fitness Challenge 2026 🏋️

A comprehensive fitness tracking application with secure authentication, activity logging, leaderboards, and detailed analytics.

## 🌟 Features

### � Admin Dashboard (NEW!)
- **System Overview**: Monitor total users, activities, and platform statistics
- **Review All Activities**: View, filter, and manage activities from all users
- **User Management**: Grant/revoke admin rights, activate/deactivate accounts
- **Detailed Statistics**: Charts and analytics for platform-wide insights
- See [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for complete admin documentation

### 🔐 Secure Authentication
- **User Registration**: Email-based account creation with strong password requirements
- **Login System**: Secure authentication with password hashing
- **Session Management**: Persistent login sessions with secure logout
- **Password Management**: Change password functionality
- **Profile Management**: Update personal information and view account details

### 🏃 Activity Tracking
- Log multiple activity types (Walking, Running, Cycling, Swimming, Gym, Sports, and more)
- Track distance, duration, and calories
- Automatic points calculation
- Upload activity screenshots/attachments
- Edit or delete logged activities

### 🏆 Leaderboard & Competition
- **Monthly Leaderboard**: Real-time rankings by points
- **Department Rankings**: Team-based competition
- **Statistics**: Active days, total kilometers, total minutes
- **Top Performers**: Highlighted top 3 users with medals

### 📊 Analytics & Insights
- **Activity History**: View all your logged activities
- **Charts**: Points over time, activity type breakdown
- **Heatmaps**: Monthly and yearly activity visualization
- **Summary Metrics**: Total points, distance, and duration
- **Export Data**: Download activity history as CSV

### 👤 User Profile
- Personal information management
- Height and weight tracking
- Password change
- Account information display

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Firebase account with Firestore and Storage enabled
- Firebase service account key (JSON file)

### Installation

1. **Clone the repository**
   ```bash
   cd BD-Fitness-Challenge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Firebase**
   - Place your Firebase service account key as `bd-fitness-challenge-2026.json` in the project root
   - Or set the `FIREBASE_CREDENTIALS` environment variable with the JSON content

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the app**
   - Open your browser to `http://localhost:8501`
   - Register a new account or login

## 📖 Documentation

- **[Admin Guide](ADMIN_GUIDE.md)** - Complete admin features documentation
- **[Authentication Guide](AUTHENTICATION.md)** - Detailed authentication system documentation
- **[Quick Start Guide](QUICKSTART.md)** - Quick start for admins and users
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

## 🔐 Security

This application implements enterprise-grade security:
- **Password Hashing**: SHA-256 with unique salt per user
- **Strong Password Policy**: Minimum 8 characters, mixed case, numbers
- **Session Management**: Secure session handling with proper cleanup
- **Email Validation**: Format validation and uniqueness enforcement
- **No Plain Text**: Passwords never stored in plain text

## 👥 User Management

### For New Users
1. Click "Register" on the login page
2. Enter your full name, email, and password
3. Click "Create Account"
4. Start logging activities!

### For Existing Users (Migration)
If you have existing users without authentication:
1. Run the migration script: `python migrate_users.py`
2. Distribute temporary credentials to users
3. Users login and change their password immediately

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## 🎯 Activity Types Supported

- Walking
- Jogging
- Running
- Cycling
- Trekking
- Badminton
- Pickle Ball
- Volley Ball
- Gym
- Yoga/Meditation
- Dance
- Swimming
- Table Tennis
- Tennis
- Cricket
- Football

## 📊 Points System

Activities are automatically scored based on:
- Activity type
- Distance covered
- Duration
- Intensity level

Points are calculated using the `calculate_points()` function in [utils/activity_utils.py](utils/activity_utils.py).

## 🏗️ Project Structure

```
BD-Fitness-Challenge/
├── app.py                          # Main Streamlit application
├── firebase_config.py              # Firebase initialization
├── migrate_users.py                # User migration script
├── requirements.txt                # Python dependencies
├── bd-fitness-challenge-2026.json  # Firebase credentials (not in repo)
├── utils/
│   ├── activity_utils.py          # Activity calculations
│   └── auth_utils.py              # Authentication utilities
├── activity_attachments/           # Uploaded activity screenshots
└── docs/
    ├── AUTHENTICATION.md           # Auth documentation
    ├── QUICKSTART.md               # Quick start guide
    └── IMPLEMENTATION_SUMMARY.md   # Implementation details
```

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.8+
- **Database**: Firebase Firestore
- **Storage**: Firebase Storage
- **Authentication**: Custom implementation with password hashing
- **Charts**: Plotly Express
- **Data Processing**: Pandas

## 🔧 Configuration

### Environment Variables
- `FIREBASE_CREDENTIALS` (optional): Firebase service account JSON as string

### Firebase Requirements
- Firestore database enabled
- Storage bucket configured
- Service account with appropriate permissions

## 📝 Requirements

See [requirements.txt](requirements.txt) for complete list:
- streamlit
- firebase-admin
- pandas
- plotly

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Production Deployment
1. Set up environment variables
2. Configure Firebase credentials
3. Run migration script if needed
4. Deploy to your hosting platform (Streamlit Cloud, Heroku, etc.)
5. Configure HTTPS for secure communication

See [AUTHENTICATION.md](AUTHENTICATION.md) for complete deployment checklist.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
1. Check the documentation (AUTHENTICATION.md, QUICKSTART.md)
2. Review error messages
3. Contact the administrator
4. Open an issue on GitHub

## 🔄 Version History

### Version 2.1.0 (Current)
- ✅ Added Admin Dashboard with comprehensive oversight tools
- ✅ Activity review and management for admins
- ✅ User management (grant/revoke admin, activate/deactivate)
- ✅ Platform-wide statistics and analytics
- ✅ Admin setup utility script

### Version 2.0.0
- ✅ Added secure authentication system
- ✅ User registration and login
- ✅ Session management
- ✅ Password management
- ✅ User migration support
- ✅ Enhanced profile page

### Version 1.0.0
- Initial release
- Activity tracking
- Leaderboards
- Analytics and heatmaps
- Basic profile management

## 📜 License

This project is proprietary and confidential.

## 🎉 Acknowledgments

- BD/SWD Team members for participation
- Firebase for backend infrastructure
- Streamlit for the awesome web framework

## ⚠️ Important Notes

1. **First Time Setup**: New users must register before using the app
2. **Existing Users**: Run migration script to enable authentication
3. **Password Security**: Use strong passwords and change temporary ones immediately
4. **Data Privacy**: All user data is stored securely in Firebase
5. **Session Timeout**: Sessions persist until logout

## 🔮 Roadmap

Future enhancements:
- [x] Admin dashboard for activity oversight
- [x] User management for admins
- [ ] Email verification
- [ ] Password reset via email
- [ ] Two-factor authentication
- [ ] Social login (Google, Microsoft)
- [ ] Mobile app
- [ ] Push notifications
- [ ] Team challenges
- [ ] Achievement badges
- [ ] Bulk data export for admins

---

**Maintained by**: BD Fitness Challenge Team
**Last Updated**: February 18, 2026
**Version**: 2.1.0

For detailed technical documentation, see [AUTHENTICATION.md](AUTHENTICATION.md), [ADMIN_GUIDE.md](ADMIN_GUIDE.md), and [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md).
