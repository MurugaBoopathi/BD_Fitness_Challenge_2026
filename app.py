# app.py
import streamlit as st
from datetime import datetime, date
import pandas as pd
import plotly.express as px
from firebase_config import db
from utils.activity_utils import calculate_points, calculate_calories
from utils.auth_utils import (
    authenticate_user, create_user_account, initialize_session, 
    clear_session, is_authenticated, require_authentication, 
    get_current_user, change_password, is_admin, get_all_users, 
    AuthenticationError
)


# --- Enhanced Custom CSS for fitness theme ---
st.markdown(
    """
    <style>
    body {
        background-image: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1500&q=80');
        background-size: cover;
        background-attachment: fixed;
    }
    .stApp {
        background: linear-gradient(135deg, rgba(255,255,255,0.97) 60%, #e3f2fd 100%);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 4px 32px rgba(0,0,0,0.13);
    }
    .stButton>button {
        background: linear-gradient(90deg, #43cea2 0%, #185a9d 100%);
        color: white;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1em;
        padding: 0.5em 1.5em;
        margin: 0.5em 0;
        transition: background 0.2s;
        box-shadow: 0 2px 8px rgba(67,206,162,0.15);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #185a9d 0%, #43cea2 100%);
    }
    .stDataFrame, .stTable {
        background: rgba(255,255,255,0.98);
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(67,206,162,0.10);
        border: 2px solid #43cea2;
    }
    .stMetric {
        background: linear-gradient(90deg, #f7971e 0%, #ffd200 100%);
        border-radius: 12px;
        padding: 0.7em 0.7em;
        margin-bottom: 0.7em;
        color: #222;
        font-weight: bold;
        box-shadow: 0 1px 6px rgba(255,215,0,0.10);
    }
    .stSidebar {
        background: #f5f5f5;
        border-radius: 14px;
        border: 2px solid #43cea2;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #185a9d !important;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .stSubheader, .stHeader, .stMarkdown>div>p {
        color: #185a9d !important;
        font-weight: 600;
    }
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.set_page_config(page_title="BD Fitness Challenge 2026 🌊", layout="wide")

# ----------------- Utilities -----------------
def get_or_create_user(full_name: str):
    users_ref = db.collection("users")
    try:
        q = users_ref.where("full_name", "==", full_name).stream()
        doc = next(iter(q), None)
        if doc is None:
            new_ref = users_ref.document()
            new_ref.set({
                "full_name": full_name,
                "height": 0,
                "weight": 0,
                "created_at": datetime.now().isoformat()
            })
            return new_ref.id
        return doc.id
    except Exception as e:
        st.error(f"Error accessing user data: {e}")
        return None

def fetch_user_logs(uid: str):
    coll = db.collection("activities").document(uid).collection("logs")
    docs = list(coll.stream())
    records = []
    for d in docs:
        rec = d.to_dict()
        rec["_id"] = d.id
        # ensure fields exist
        rec.setdefault("activity_type", "")
        rec.setdefault("distance", 0.0)
        rec.setdefault("duration", 0)
        rec.setdefault("points", 0)
        rec.setdefault("calories", 0)
        rec.setdefault("date", "")
        records.append(rec)
    return records

def save_activity(uid, activity_type, distance, duration, date_str, doc_id=None, attachment_url=None):
    points = float(calculate_points(activity_type, distance, duration))
    calories = float(calculate_calories(activity_type, duration))
    payload = {
        "activity_type": activity_type,
        "distance": float(distance),
        "duration": int(duration),
        "points": round(points,3),
        "calories": round(calories,1),
        "date": date_str,
        "updated_at": datetime.now().isoformat()
    }
    if attachment_url:
        payload["attachment_url"] = attachment_url
    coll = db.collection("activities").document(uid).collection("logs")
    if doc_id:
        coll.document(doc_id).update(payload)
    else:
        coll.add(payload)
    return payload

def delete_activity(uid, doc_id):
    db.collection("activities").document(uid).collection("logs").document(doc_id).delete()

# ----------------- Leaderboard helpers -----------------
def monthly_aggregates():
    """Return dataframe with Name, Points, ActiveDays, TotalKM, TotalMins for current month"""
    current_month = datetime.now().strftime("%Y-%m")
    users = list(db.collection("users").stream())
    rows = []
    for u in users:
        uid = u.id
        user = u.to_dict()
        logs = db.collection("activities").document(uid).collection("logs").stream()
        pts = 0.0
        kms = 0.0
        mins = 0
        active_dates = set()
        for l in logs:
            rec = l.to_dict()
            d = rec.get("date","")
            if d.startswith(current_month):
                pts += float(rec.get("points",0) or 0)
                kms += float(rec.get("distance",0) or 0)
                mins += int(rec.get("duration",0) or 0)
                active_dates.add(d)
        rows.append({
            "uid": uid,
            "Name": user.get("full_name","Unknown"),
            "Points": round(pts,3),
            "ActiveDays": len(active_dates),
            "TotalKM": round(kms,2),
            "TotalMins": mins
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values(["Points","ActiveDays"], ascending=False).reset_index(drop=True)
    df.index += 1
    df.insert(0, "Rank", df.index)
    return df

# ----------------- Heatmap helpers -----------------
def heatmap_month(df_logs, year:int, month:int, value_col="points"):
    """Create days x weekday heatmap matrix for a given year-month.
       Returns a DataFrame indexed by weekday (Mon..Sun) columns are week numbers with sums."""
    # filter
    df = df_logs.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df['date'].dt.year==year) & (df['date'].dt.month==month)]
    if df.empty:
        return None
    df['day'] = df['date'].dt.day
    df['weekday'] = df['date'].dt.weekday  # Mon=0
    # get week of month (1..)
    df['weeknum'] = ((df['date'].dt.day - 1) // 7) + 1
    pivot = df.groupby(['weekday','weeknum'])[value_col].sum().unstack(fill_value=0)
    # reorder weekdays to Mon..Sun index 0..6
    pivot = pivot.reindex(index=[0,1,2,3,4,5,6]).fillna(0)
    pivot.index = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    return pivot

def heatmap_year(df_logs, year:int, value_col="points"):
    """Return matrix month vs day-of-month aggregated by value_col for a year for heatmap-like visualization"""
    df = df_logs.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.year==year]
    if df.empty:
        return None
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    pivot = df.groupby(['month','day'])[value_col].sum().unstack(fill_value=0)
    # ensure months 1..12 present
    pivot = pivot.reindex(index=range(1,13), fill_value=0)
    pivot.index = [datetime(year, m, 1).strftime('%b') for m in pivot.index]
    return pivot

# ----------------- UI: main -----------------

# --- Authentication Gate: Show login/registration if not authenticated ---
if not is_authenticated():
    st.markdown(
        """
        <style>
        /* Clean professional background */
        .stApp {
            background: linear-gradient(to bottom right, #e8f5e9 0%, #ffffff 50%, #e3f2fd 100%);
        }
        
        /* Centered container */
        .auth-wrapper {
            max-width: 650px;
            margin: 2em auto;
        }
        
        /* Top header section */
        .auth-header {
            background: white;
            padding: 2.5em 2em;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 1.5em;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5em;
        }
        
        .auth-side-icon {
            width: 90px;
            height: 90px;
            object-fit: contain;
        }
        
        .auth-center-content {
            flex: 1;
        }
        
        .auth-logo {
            font-size: 3em;
            margin-bottom: 0.2em;
        }
        
        .auth-title {
            color: #2e7d32 !important;
            font-size: 1.9em !important;
            font-weight: 700 !important;
            margin: 0 0 0.2em 0 !important;
        }
        
        .auth-subtitle {
            color: #757575 !important;
            font-size: 0.95em !important;
            margin: 0 !important;
        }
        
        /* Form section */
        .auth-form-wrapper {
            max-width: 450px;
            margin: 0 auto;
        }
        
        /* Tab buttons */
        .stRadio {
            margin-bottom: 1.5em;
        }
        
        .stRadio > div {
            justify-content: center;
            gap: 1em;
        }
        
        .stRadio > div > label {
            padding: 0.7em 3em !important;
            background: white !important;
            border: 2px solid #e0e0e0 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            color: #616161 !important;
            transition: all 0.2s !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .stRadio > div > label:hover {
            border-color: #2e7d32 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(46,125,50,0.15);
        }
        
        .stRadio input:checked + label {
            background: #2e7d32 !important;
            border-color: #2e7d32 !important;
            color: white !important;
        }
        
        /* Form card */
        .stForm {
            background: white;
            padding: 2em;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        
        /* Input labels */
        .stTextInput label,
        .stSelectbox label {
            color: #424242 !important;
            font-weight: 600 !important;
            font-size: 0.9em !important;
        }
        
        /* Input fields */
        .stTextInput > div > div > input {
            border: 2px solid #e0e0e0 !important;
            border-radius: 8px !important;
            padding: 0.7em 0.9em !important;
            font-size: 0.95em !important;
            background: #fafafa !important;
            transition: all 0.2s !important;
            color: #333333 !important;
        }
        
        /* Selectbox styling - comprehensive fix */
        .stSelectbox > div > div {
            border: 2px solid #e0e0e0 !important;
            border-radius: 8px !important;
            background: white !important;
        }
        
        .stSelectbox * {
            color: #333333 !important;
        }
        
        .stSelectbox [data-baseweb="select"] {
            background: white !important;
        }
        
        .stSelectbox [data-baseweb="select"] > div {
            background: white !important;
            color: #333333 !important;
        }
        
        .stSelectbox [data-baseweb="select"] > div > div {
            color: #333333 !important;
        }
        
        .stSelectbox svg {
            fill: #333333 !important;
        }
        
        /* Dropdown menu options */
        [data-baseweb="menu"] {
            background: white !important;
        }
        
        [data-baseweb="menu"] li {
            color: #333333 !important;
            background: white !important;
        }
        
        [data-baseweb="menu"] li:hover {
            background: #f0f0f0 !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div:focus {
            border-color: #2e7d32 !important;
            background: white !important;
            box-shadow: 0 0 0 3px rgba(46,125,50,0.1) !important;
        }
        
        /* Submit button */
        .stButton > button {
            width: 100%;
            background: #2e7d32 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75em !important;
            font-weight: 600 !important;
            font-size: 1em !important;
            margin-top: 1em !important;
            transition: all 0.2s !important;
        }
        
        .stButton > button:hover {
            background: #1b5e20 !important;
            box-shadow: 0 4px 12px rgba(46,125,50,0.3);
            transform: translateY(-1px);
        }
        
        /* Info messages */
        .stAlert {
            border-radius: 8px !important;
            font-size: 0.9em !important;
        }
        
        /* Hide default subheaders */
        h3 {
            display: none !important;
        }
        
        /* Text styling */
        .stMarkdown p {
            font-size: 0.85em !important;
            color: #757575 !important;
            margin: 0.5em 0 !important;
        }
        
        /* Column spacing */
        [data-testid="column"] {
            padding: 0 0.4em !important;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .auth-side-icon {
                display: none;
            }
            .auth-header {
                padding: 2em 1.5em;
            }
        }
        </style>
        <div class="auth-wrapper">
            <div class="auth-header">
                <img src="https://cdn-icons-png.flaticon.com/512/2548/2548482.png" alt="Running" class="auth-side-icon">
                <div class="auth-center-content">
                    <div class="auth-logo">🏋️‍♂️</div>
                    <h1 class="auth-title">BD Fitness Challenge</h1>
                    <p class="auth-subtitle">Track your journey, achieve your goals</p>
                </div>
                <img src="https://cdn-icons-png.flaticon.com/512/2936/2936886.png" alt="Cycling" class="auth-side-icon">
            </div>
            <div class="auth-form-wrapper">
        """,
        unsafe_allow_html=True
    )
    
    # Tab selection for Login/Register
    auth_tab = st.radio("", ["Login", "Register"], horizontal=True, label_visibility="collapsed")
    
    if auth_tab == "Login":
        st.subheader("🔐 Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                try:
                    with st.spinner("Authenticating..."):
                        user_data = authenticate_user(email, password)
                        initialize_session(user_data)
                        st.success(f"Welcome back, {user_data['full_name']}! 🎉")
                        st.rerun()
                except AuthenticationError as e:
                    st.error(str(e))
        
        st.info("Don't have an account? Switch to Register tab above.")
    
    else:  # Register tab
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name", placeholder="John Doe")
            with col2:
                email = st.text_input("Email", placeholder="your.email@example.com")
            
            # Department dropdown
            department_options = ["BD/SWD-BEA9", "BD/SWD-BEA10", "BD/SWD-FSB5", "BD/SWD-FSB6"]
            department = st.selectbox("Department", department_options, help="Select your department")
            
            col3, col4 = st.columns(2)
            with col3:
                password = st.text_input("Password", type="password", placeholder="Min 8 chars")
            with col4:
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter")
            
            st.markdown("**Requirements:** 8+ chars, uppercase, lowercase, number")
            
            submit = st.form_submit_button("Create Account", use_container_width=True)
        
        if submit:
            if not all([full_name, email, password, confirm_password, department]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    with st.spinner("Creating your account..."):
                        user_data = create_user_account(email, password, full_name, department)
                        initialize_session(user_data)
                        st.success(f"Account created successfully! Welcome, {full_name}! 🎉")
                        st.balloons()
                        st.rerun()
                except AuthenticationError as e:
                    st.error(str(e))
        
        st.info("Already have an account? Switch to Login tab above.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- After login, show standard layout ---
st.title("🏋️ BD Fitness Challenge 2026 - Activity Tracker")

# Get authenticated user details
uid = st.session_state["uid"]
full_name = st.session_state["user_name"]

activities = [
        "Walking","Jogging","Running","Cycling","Trekking","Badminton","Pickle Ball","Volley Ball",
        "Gym","Yoga/Meditation","Dance","Swimming","Table Tennis","Tennis","Cricket","Football"
    ]

# Sidebar navigation with logout
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2764/2764434.png", width=100)
st.sidebar.markdown(f"**Hello, {full_name}** 👋")
if st.session_state.get('is_admin', False):
    st.sidebar.markdown("⭐ **Admin User**")
st.sidebar.markdown("---")

# Build menu items based on admin status
menu_items = ["Leaderboard","Log Activity","Edit / Delete Activities","My History","Profile"]
if st.session_state.get('is_admin', False):
    menu_items.insert(0, "🔧 Admin Dashboard")

menu = st.sidebar.radio("Navigate", menu_items)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    clear_session()
    st.rerun()

# ---------- Admin Dashboard ----------
if menu == "🔧 Admin Dashboard":
    if not st.session_state.get('is_admin', False):
        st.error("⛔ Access Denied: Admin privileges required")
        st.stop()
    
    st.header("🔧 Admin Dashboard")
    st.markdown("**Administrative tools and oversight**")
    
    # Tab layout for different admin sections
    admin_tab = st.tabs(["📊 Overview", "🔍 Review Activities", "➕ Add Activity for User", "👥 User Management", "📈 Statistics"])
    
    # Tab 1: Overview
    with admin_tab[0]:
        st.subheader("📊 System Overview")
        
        # Get all users and activities
        all_users = get_all_users()
        total_users = len(all_users)
        active_users = len([u for u in all_users if u.get('last_login')])
        admin_users = len([u for u in all_users if u.get('is_admin', False)])
        
        # Get total activities across all users
        total_activities = 0
        total_points = 0
        total_distance = 0
        
        for user in all_users:
            user_logs = fetch_user_logs(user['uid'])
            total_activities += len(user_logs)
            for log in user_logs:
                total_points += log.get('points', 0)
                total_distance += log.get('distance', 0)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Users", total_users)
        col2.metric("Active Users", active_users)
        col3.metric("Total Activities", total_activities)
        col4.metric("Admin Users", admin_users)
        
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Total Points", round(total_points, 2))
        col6.metric("Total KM", round(total_distance, 2))
        col7.metric("Avg Activities/User", round(total_activities / max(total_users, 1), 1))
        col8.metric("Avg Points/User", round(total_points / max(total_users, 1), 1))
        
        st.divider()
        
        # Recent activity summary
        st.subheader("📅 Recent Activity Summary")
        recent_logs = []
        for user in all_users:
            user_logs = fetch_user_logs(user['uid'])
            for log in user_logs:
                log['user_name'] = user.get('full_name', 'Unknown')
                recent_logs.append(log)
        
        if recent_logs:
            recent_df = pd.DataFrame(recent_logs)
            recent_df['date'] = pd.to_datetime(recent_df['date'])
            recent_df = recent_df.sort_values('date', ascending=False).head(20)
            
            display_df = recent_df[['date', 'user_name', 'activity_type', 'distance', 'duration', 'points']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No activities recorded yet")
    
    # Tab 2: Review Activities
    with admin_tab[1]:
        st.subheader("🔍 Review All Activities")
        st.markdown("**View and manage activities from all users**")
        
        # User filter
        all_users = get_all_users()
        user_names = ["All Users"] + [u.get('full_name', 'Unknown') for u in all_users]
        selected_user = st.selectbox("Filter by User", user_names)
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", value=date.today().replace(day=1))
        with col2:
            end_date = st.date_input("To Date", value=date.today())
        
        # Activity type filter
        activity_types = ["All Types"] + activities
        selected_activity = st.selectbox("Filter by Activity Type", activity_types)
        
        # Fetch and filter activities
        all_activities = []
        users_to_check = all_users if selected_user == "All Users" else [u for u in all_users if u.get('full_name') == selected_user]
        
        for user in users_to_check:
            user_logs = fetch_user_logs(user['uid'])
            for log in user_logs:
                log['user_name'] = user.get('full_name', 'Unknown')
                log['user_uid'] = user['uid']
                all_activities.append(log)
        
        if all_activities:
            activities_df = pd.DataFrame(all_activities)
            activities_df['date'] = pd.to_datetime(activities_df['date'])
            
            # Apply filters
            activities_df = activities_df[
                (activities_df['date'].dt.date >= start_date) & 
                (activities_df['date'].dt.date <= end_date)
            ]
            
            if selected_activity != "All Types":
                activities_df = activities_df[activities_df['activity_type'] == selected_activity]
            
            # Display count
            st.markdown(f"**Found {len(activities_df)} activities**")
            
            if len(activities_df) > 0:
                # Sort by date
                activities_df = activities_df.sort_values('date', ascending=False)
                
                # Display in expandable format for detailed review
                for idx, row in activities_df.iterrows():
                    # Check if added by admin
                    admin_badge = " 🔧 Admin Added" if row.get('added_by_admin', False) else ""
                    with st.expander(f"📅 {row['date'].strftime('%Y-%m-%d')} | 👤 {row['user_name']} | 🏃 {row['activity_type']} | ⭐ {row['points']} pts{admin_badge}"):
                        col1, col2, col3 = st.columns(3)
                        col1.write(f"**Distance:** {row['distance']} km")
                        col2.write(f"**Duration:** {row['duration']} mins")
                        col3.write(f"**Calories:** {row.get('calories', 0)} kcal")
                        
                        # Show if added by admin
                        if row.get('added_by_admin', False):
                            admin_name = row.get('admin_name', 'Admin')
                            st.info(f"🔧 This activity was added by admin: **{admin_name}**")
                            if row.get('admin_notes'):
                                st.write(f"**Admin Notes:** {row.get('admin_notes')}")
                        
                        # Show attachment if exists
                        if row.get('attachment_url'):
                            st.image(row['attachment_url'], width=400, caption="Activity Attachment")
                        
                        # Admin actions - Edit and Delete
                        st.markdown("---")
                        st.markdown("**Admin Actions:**")
                        
                        # Edit section
                        with st.expander("✏️ Edit Activity"):
                            edit_col1, edit_col2 = st.columns(2)
                            with edit_col1:
                                edit_act = st.selectbox(
                                    "Activity Type", 
                                    activities, 
                                    index=activities.index(row['activity_type']) if row['activity_type'] in activities else 0,
                                    key=f"admin_edit_act_{row['_id']}"
                                )
                                edit_dist = st.number_input(
                                    "Distance (km)", 
                                    value=float(row['distance']), 
                                    min_value=0.0, 
                                    step=0.1,
                                    key=f"admin_edit_dist_{row['_id']}"
                                )
                            with edit_col2:
                                edit_dur = st.number_input(
                                    "Duration (mins)", 
                                    value=int(row['duration']), 
                                    min_value=0, 
                                    step=1,
                                    key=f"admin_edit_dur_{row['_id']}"
                                )
                                edit_date = st.date_input(
                                    "Date", 
                                    value=row['date'].date(),
                                    key=f"admin_edit_date_{row['_id']}"
                                )
                            
                            if st.button(f"💾 Save Changes", key=f"admin_save_{row['_id']}"):
                                save_activity(
                                    row['user_uid'], 
                                    edit_act, 
                                    edit_dist, 
                                    edit_dur, 
                                    edit_date.strftime("%Y-%m-%d"), 
                                    doc_id=row['_id']
                                )
                                st.success("Activity updated successfully!")
                                st.rerun()
                        
                        # Delete button
                        if st.button(f"🗑️ Delete Activity", key=f"admin_del_{row['_id']}"):
                            delete_activity(row['user_uid'], row['_id'])
                            st.success("Activity deleted")
                            st.rerun()
            else:
                st.info("No activities found matching the filters")
        else:
            st.info("No activities to review")
    
    # Tab 3: Add Activity for User
    with admin_tab[2]:
        st.subheader("➕ Add Activity for User")
        st.markdown("**Add activity entries on behalf of any associate**")
        
        # Get all users for dropdown
        all_users_for_add = get_all_users()
        user_options = [(u.get('full_name', 'Unknown'), u['uid']) for u in all_users_for_add]
        user_names_for_add = [u[0] for u in user_options]
        
        if user_names_for_add:
            selected_user_for_activity = st.selectbox(
                "Select Associate", 
                user_names_for_add,
                key="admin_add_activity_user"
            )
            
            # Get the UID for the selected user
            selected_user_uid = next((u[1] for u in user_options if u[0] == selected_user_for_activity), None)
            
            if selected_user_uid:
                st.info(f"📝 Adding activity for: **{selected_user_for_activity}**")
                
                with st.form("admin_add_activity_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        admin_act = st.selectbox("Activity Type", activities, key="admin_activity_type")
                        admin_dist = st.number_input("Distance (km)", min_value=0.0, step=0.1, format="%.2f", key="admin_distance")
                    
                    with col2:
                        admin_dur = st.number_input("Duration (mins)", min_value=0, step=1, key="admin_duration")
                        admin_date = st.date_input("Activity Date", date.today(), key="admin_date")
                    
                    # Optional attachment
                    admin_attachment = st.file_uploader(
                        "Attachment (screenshot, Strava, etc.)", 
                        type=["png", "jpg", "jpeg"], 
                        key="admin_activity_attachment"
                    )
                    
                    # Additional notes field for admin
                    admin_notes = st.text_area(
                        "Admin Notes (optional)", 
                        placeholder="E.g., 'Activity logged by admin on behalf of user'",
                        key="admin_notes"
                    )
                    
                    admin_submit = st.form_submit_button("➕ Add Activity", use_container_width=True)
                
                if admin_submit:
                    if admin_dur == 0:
                        st.error("Please enter a valid duration")
                    else:
                        admin_attachment_url = None
                        if admin_attachment:
                            import os
                            from uuid import uuid4
                            img_folder = "activity_attachments"
                            os.makedirs(img_folder, exist_ok=True)
                            img_name = f"{selected_user_uid}_{uuid4()}.{admin_attachment.name.split('.')[-1]}"
                            img_path = os.path.join(img_folder, img_name)
                            with open(img_path, "wb") as f:
                                f.write(admin_attachment.getbuffer())
                            admin_attachment_url = img_path
                        
                        # Calculate points and calories
                        admin_points = float(calculate_points(admin_act, admin_dist, admin_dur))
                        admin_calories = float(calculate_calories(admin_act, admin_dur))
                        
                        # Prepare payload
                        admin_payload = {
                            "activity_type": admin_act,
                            "distance": float(admin_dist),
                            "duration": int(admin_dur),
                            "points": round(admin_points, 3),
                            "calories": round(admin_calories, 1),
                            "date": admin_date.strftime("%Y-%m-%d"),
                            "updated_at": datetime.now().isoformat(),
                            "added_by_admin": True,
                            "admin_uid": uid,
                            "admin_name": full_name
                        }
                        
                        if admin_attachment_url:
                            admin_payload["attachment_url"] = admin_attachment_url
                        
                        if admin_notes:
                            admin_payload["admin_notes"] = admin_notes
                        
                        # Save to database
                        db.collection("activities").document(selected_user_uid).collection("logs").add(admin_payload)
                        
                        st.success(f"✅ Activity added successfully for **{selected_user_for_activity}**!")
                        st.info(f"📊 {admin_act} — {admin_points:.2f} pts, {admin_calories:.1f} kcal")
                        st.balloons()
                
                # Show recent activities for the selected user
                st.divider()
                st.markdown(f"**📋 Recent Activities for {selected_user_for_activity}**")
                
                selected_user_logs = fetch_user_logs(selected_user_uid)
                if selected_user_logs:
                    selected_user_df = pd.DataFrame(selected_user_logs)
                    selected_user_df['date'] = pd.to_datetime(selected_user_df['date'])
                    selected_user_df = selected_user_df.sort_values('date', ascending=False).head(10)
                    
                    display_cols = ['date', 'activity_type', 'distance', 'duration', 'points', 'calories']
                    if 'added_by_admin' in selected_user_df.columns:
                        display_cols.append('added_by_admin')
                    
                    display_df = selected_user_df[display_cols].copy()
                    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Summary stats
                    total_user_pts = selected_user_df['points'].sum()
                    total_user_km = selected_user_df['distance'].sum()
                    st.markdown(f"**Recent 10 entries:** {total_user_pts:.2f} pts | {total_user_km:.2f} km")
                else:
                    st.info("No activities recorded for this user yet")
        else:
            st.warning("No users found in the system")
    
    # Tab 4: User Management
    with admin_tab[3]:
        st.subheader("👥 User Management")
        st.markdown("**Manage user accounts and permissions**")
        
        all_users = get_all_users()
        
        if all_users:
            users_df = pd.DataFrame(all_users)
            
            # Display user table
            display_columns = ['full_name', 'email', 'department', 'is_admin', 'is_active', 'created_at', 'last_login']
            available_columns = [col for col in display_columns if col in users_df.columns]
            
            # Format dates
            if 'created_at' in users_df.columns:
                users_df['created_at'] = pd.to_datetime(users_df['created_at']).dt.strftime('%Y-%m-%d')
            if 'last_login' in users_df.columns:
                users_df['last_login'] = pd.to_datetime(users_df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Fill missing columns
            if 'is_admin' not in users_df.columns:
                users_df['is_admin'] = False
            if 'is_active' not in users_df.columns:
                users_df['is_active'] = True
            
            st.dataframe(
                users_df[available_columns], 
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            
            # User details and actions
            st.subheader("User Details & Actions")
            selected_user_name = st.selectbox("Select User", [u.get('full_name', 'Unknown') for u in all_users])
            
            selected_user_data = next((u for u in all_users if u.get('full_name') == selected_user_name), None)
            
            if selected_user_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**User Information**")
                    st.write(f"**Name:** {selected_user_data.get('full_name')}")
                    st.write(f"**Email:** {selected_user_data.get('email')}")
                    st.write(f"**Department:** {selected_user_data.get('department', 'N/A')}")
                    st.write(f"**Status:** {'Active' if selected_user_data.get('is_active', True) else 'Inactive'}")
                    st.write(f"**Admin:** {'Yes' if selected_user_data.get('is_admin', False) else 'No'}")
                    st.write(f"**Created:** {selected_user_data.get('created_at', 'N/A')[:10]}")
                    st.write(f"**Last Login:** {selected_user_data.get('last_login', 'N/A')[:16]}")
                
                with col2:
                    st.markdown("**Activity Stats**")
                    user_logs = fetch_user_logs(selected_user_data['uid'])
                    total_acts = len(user_logs)
                    total_pts = sum([log.get('points', 0) for log in user_logs])
                    total_km = sum([log.get('distance', 0) for log in user_logs])
                    
                    st.write(f"**Total Activities:** {total_acts}")
                    st.write(f"**Total Points:** {round(total_pts, 2)}")
                    st.write(f"**Total Distance:** {round(total_km, 2)} km")
                
                st.divider()
                
                # Admin actions
                st.markdown("**Administrative Actions**")
                col_admin, col_status = st.columns(2)
                
                with col_admin:
                    current_admin = selected_user_data.get('is_admin', False)
                    if current_admin:
                        if st.button(f"🔓 Remove Admin Rights", key=f"remove_admin_{selected_user_data['uid']}"):
                            from utils.auth_utils import set_admin_status
                            set_admin_status(selected_user_data['uid'], False)
                            st.success("Admin rights removed")
                            st.rerun()
                    else:
                        if st.button(f"⭐ Grant Admin Rights", key=f"grant_admin_{selected_user_data['uid']}"):
                            from utils.auth_utils import set_admin_status
                            set_admin_status(selected_user_data['uid'], True)
                            st.success("Admin rights granted")
                            st.rerun()
                
                with col_status:
                    current_status = selected_user_data.get('is_active', True)
                    if current_status:
                        if st.button(f"🚫 Deactivate Account", key=f"deactivate_{selected_user_data['uid']}"):
                            db.collection("users").document(selected_user_data['uid']).update({"is_active": False})
                            st.warning("Account deactivated")
                            st.rerun()
                    else:
                        if st.button(f"✅ Activate Account", key=f"activate_{selected_user_data['uid']}"):
                            db.collection("users").document(selected_user_data['uid']).update({"is_active": True})
                            st.success("Account activated")
                            st.rerun()
                
                st.divider()
                
                # Password Reset Section
                st.markdown("**🔑 Password Reset**")
                st.info(f"Reset password for: **{selected_user_data.get('full_name')}** ({selected_user_data.get('email')})")
                
                with st.form(key=f"reset_password_form_{selected_user_data['uid']}"):
                    new_password = st.text_input("New Password", type="password", 
                                                  placeholder="Enter new password (min 8 chars)")
                    confirm_new_password = st.text_input("Confirm New Password", type="password",
                                                          placeholder="Re-enter new password")
                    
                    st.markdown("**Password Requirements:** 8+ characters, uppercase, lowercase, number")
                    
                    reset_btn = st.form_submit_button("🔄 Reset Password", use_container_width=True)
                    
                    if reset_btn:
                        if not new_password or not confirm_new_password:
                            st.error("Please fill in both password fields")
                        elif new_password != confirm_new_password:
                            st.error("Passwords do not match")
                        else:
                            try:
                                from utils.auth_utils import admin_reset_password, AuthenticationError
                                admin_reset_password(selected_user_data['uid'], new_password)
                                st.success(f"✅ Password reset successfully for {selected_user_data.get('full_name')}!")
                                st.info("The user can now login with the new password.")
                            except AuthenticationError as e:
                                st.error(str(e))
                            except Exception as e:
                                st.error(f"Error resetting password: {str(e)}")
        else:
            st.info("No users found")
    
    # Tab 5: Statistics
    with admin_tab[4]:
        st.subheader("📈 Detailed Statistics")
        
        all_users = get_all_users()
        all_activities_list = []
        
        for user in all_users:
            user_logs = fetch_user_logs(user['uid'])
            for log in user_logs:
                log['user_name'] = user.get('full_name', 'Unknown')
                all_activities_list.append(log)
        
        if all_activities_list:
            stats_df = pd.DataFrame(all_activities_list)
            stats_df['date'] = pd.to_datetime(stats_df['date'])
            
            # Activity type distribution
            st.markdown("**Activity Type Distribution**")
            activity_counts = stats_df['activity_type'].value_counts()
            fig_pie = px.pie(values=activity_counts.values, names=activity_counts.index, 
                            title="Activities by Type")
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Points by activity type
            st.markdown("**Points by Activity Type**")
            points_by_type = stats_df.groupby('activity_type')['points'].sum().sort_values(ascending=False)
            fig_bar = px.bar(x=points_by_type.index, y=points_by_type.values,
                           labels={'x': 'Activity Type', 'y': 'Total Points'},
                           title="Total Points by Activity Type")
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Activity trend over time
            st.markdown("**Activity Trend Over Time**")
            stats_df['month'] = stats_df['date'].dt.to_period('M').astype(str)
            monthly_counts = stats_df.groupby('month').size()
            fig_line = px.line(x=monthly_counts.index, y=monthly_counts.values,
                             labels={'x': 'Month', 'y': 'Number of Activities'},
                             title="Monthly Activity Trend")
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Top performers
            st.markdown("**Top 10 Performers (All Time)**")
            user_points = stats_df.groupby('user_name')['points'].sum().sort_values(ascending=False).head(10)
            fig_top = px.bar(x=user_points.values, y=user_points.index, orientation='h',
                           labels={'x': 'Total Points', 'y': 'User'},
                           title="Top 10 Users by Points")
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("No activity data available for statistics")

# ---------- Leaderboard ----------
elif menu == "Leaderboard":
    st.markdown(
        """
        <h2 style="color: #185a9d !important; 
                   font-size: 2em !important; 
                   font-weight: 700 !important;
                   margin-bottom: 0.3em !important;">
            🏆 Monthly Leaderboard
        </h2>
        <p style="color: #43cea2 !important; 
                  font-size: 1em !important;
                  font-weight: 500 !important;
                  margin-top: 0 !important;
                  margin-bottom: 1.5em !important;">
            Track top performers and department rankings for this month
        </p>
        """,
        unsafe_allow_html=True
    )
    
    df_lb = monthly_aggregates()
    if df_lb.empty:
        st.info("No activity data for this month yet.")
    else:
        # Highlight top 3 with truncated names (no department)
        import re
        def strip_department(name):
            return re.sub(r"\s*\([^)]*\)$", "", name).strip()
        top3 = df_lb.head(3)
        cols = st.columns(3)
        medals = ["🥇","🥈","🥉"]
        for i, (_, row) in enumerate(top3.iterrows()):
            short_name = strip_department(row['Name'])
            with cols[i]:
                st.markdown(f"### {medals[i]} {short_name}")
                st.metric("Points", row["Points"])
                st.write(f"Active Days: {row['ActiveDays']}")
                st.write(f"KM: {row['TotalKM']} | Mins: {row['TotalMins']}")

        # Department leaderboard

        import re
        # Use stored department from user data, fallback to extracting from name
        def get_user_department(uid):
            user_doc = db.collection("users").document(uid).get()
            if user_doc.exists:
                dept = user_doc.to_dict().get('department')
                if dept:
                    return dept
            # Fallback: extract from name
            user_data = user_doc.to_dict() if user_doc.exists else {}
            name = user_data.get('full_name', '')
            matches = re.findall(r'\(([^()]*)\)', name)
            if matches:
                return matches[-1].strip()
            return "Unknown"
        
        df_lb['Department'] = df_lb['uid'].apply(get_user_department)
        dept_agg = df_lb.groupby('Department').agg({
            'Points': 'sum',
            'ActiveDays': 'sum',
            'TotalKM': 'sum',
            'TotalMins': 'sum',
            'Name': 'count'
        }).rename(columns={'Name': 'Members'}).reset_index()
        dept_agg = dept_agg.sort_values('Points', ascending=False).reset_index(drop=True)
        dept_agg.index += 1
        dept_agg.insert(0, 'Rank', dept_agg.index)

        st.divider()
        st.subheader("Top Performing Departments (This Month)")
        top5_depts = dept_agg.head(5)
        import plotly.express as px

        # Show chart and table side by side, 50-50 split, with equal height and lollipop chart
        col_chart, col_table = st.columns([1, 1], gap="medium")
        import plotly.graph_objects as go
        # Gauge charts for top 3 departments with distinct colors
        top3_depts = dept_agg.head(3)
        gauge_colors = ["#636EFA", "#EF553B", "#00CC96"]  # vibrant blue, orange, green
        max_points = top3_depts["Points"].max() if not top3_depts.empty else 1
        gauge_height = 250
        gauge_width = 400
        gauge_cols = st.columns(len(top3_depts))
        for i, (idx, row) in enumerate(top3_depts.iterrows()):
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = row["Points"],
                delta = {"reference": max_points, "increasing": {"color": gauge_colors[i % len(gauge_colors)]}},
                gauge = {
                    "axis": {"range": [0, max_points], "tickwidth": 1, "tickcolor": gauge_colors[i % len(gauge_colors)]},
                    "bar": {"color": gauge_colors[i % len(gauge_colors)]},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "gray",
                },
                title = {"text": row["Department"], "font": {"size": 20, "color": gauge_colors[i % len(gauge_colors)], "family": "Arial Black, Arial, sans-serif"}},
                number = {"suffix": " pts", "font": {"color": gauge_colors[i % len(gauge_colors)], "size": 20}}
            ))
            fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=gauge_height, width=gauge_width)
            with gauge_cols[i]:
                st.plotly_chart(fig, use_container_width=False, height=gauge_height, width=gauge_width)

        # Table below gauges
        st.dataframe(
            top3_depts.head(3).reset_index(drop=True)[["Rank","Department","Points","ActiveDays","TotalKM","TotalMins","Members"]],
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.subheader("Full Leaderboard (This Month)")
        st.dataframe(df_lb[["Rank","Name","Points","ActiveDays","TotalKM","TotalMins"]], use_container_width=True)

# ---------- Log Activity ----------
elif menu == "Log Activity":
    st.header(f"📝 Log Activity — {full_name}")

    with st.form("log_form"):
        act = st.selectbox("Activity", activities)
        dist = st.number_input("Distance (km)", min_value=0.0, step=0.1, format="%.2f")
        dur = st.number_input("Duration (mins)", min_value=0, step=1)
        d = st.date_input("Date", date.today())
        attachment = st.file_uploader("Attachment (screenshot, Strava, etc.)", type=["png", "jpg", "jpeg"], key=f"log_activity_attachment_{uid}")
        submitted = st.form_submit_button("Save")
    attachment_url = None
    if submitted:
        if attachment:
            import os
            from uuid import uuid4
            img_folder = "activity_attachments"
            os.makedirs(img_folder, exist_ok=True)
            img_name = f"{uid}_{uuid4()}.{attachment.name.split('.')[-1]}"
            img_path = os.path.join(img_folder, img_name)
            with open(img_path, "wb") as f:
                f.write(attachment.getbuffer())
            attachment_url = img_path
        payload = save_activity(uid, act, dist, dur, d.strftime("%Y-%m-%d"), attachment_url=attachment_url)
        st.success(f"Saved: {act} — {payload['points']} pts, {payload['calories']} kcal")

# ---------- Edit / Delete Activities ----------
elif menu == "Edit / Delete Activities":
    st.header("✏️ Edit / Delete Your Activities")
    records = fetch_user_logs(uid)
    if not records:
        st.info("You have no activities to edit.")
    else:
        # show as table with index and small controls
        df = pd.DataFrame(records)
        df_display = df[["date","activity_type","distance","duration","points","calories","_id"]].sort_values("date", ascending=False)
        st.dataframe(df_display.drop(columns=["_id"]), use_container_width=True)

        st.markdown("**Click an entry below to edit or delete**")
        for rec in sorted(records, key=lambda x: x["date"], reverse=True):
            exp = st.expander(f"{rec['date']} — {rec['activity_type']} — {rec['points']} pts")
            with exp:
                col1, col2 = st.columns(2)
                with col1:
                    new_act = st.selectbox("Activity", options=activities, index=activities.index(rec["activity_type"]) if rec["activity_type"] in activities else 0, key=f"act_{rec['_id']}")
                    new_dist = st.number_input("Distance (km)", value=float(rec.get("distance",0.0)), key=f"dist_{rec['_id']}")
                with col2:
                    new_dur = st.number_input("Duration (mins)", value=int(rec.get("duration",0)), key=f"dur_{rec['_id']}")
                    new_date = st.date_input("Date", value=pd.to_datetime(rec.get("date")).date(), key=f"date_{rec['_id']}")
                col3, col4 = st.columns(2)
                if col3.button("Update", key=f"upd_{rec['_id']}"):
                    save_activity(uid, new_act, new_dist, new_dur, new_date.strftime("%Y-%m-%d"), doc_id=rec["_id"])
                    st.success("Updated successfully.")
                    st.rerun()
                if col4.button("Delete", key=f"del_{rec['_id']}"):
                    delete_activity(uid, rec["_id"])
                    st.warning("Deleted.")
                    st.rerun()

# ---------- My History (charts & heatmaps) ----------
elif menu == "My History":
    st.header("📈 My Activity History & Heatmaps")
    recs = fetch_user_logs(uid)
    if not recs:
        st.info("No activity records yet.")
    else:
        df = pd.DataFrame(recs)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # summary cards
        total_points = df['points'].sum()
        total_km = df['distance'].sum()
        total_mins = df['duration'].sum()
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Points", round(total_points,2))
        c2.metric("Total KM", round(total_km,2))
        c3.metric("Total Duration (mins)", int(total_mins))

        st.subheader("Points over time")
        st.line_chart(df.set_index('date')['points'])

        st.subheader("Points by activity type")
        agg = df.groupby('activity_type')['points'].sum().reset_index().sort_values('points', ascending=False)
        fig_bar = px.bar(agg, x='activity_type', y='points', title="Points by Activity")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Show attachments if available
        attachments = df[df['attachment_url'].notnull() & (df['attachment_url'] != '')] if 'attachment_url' in df.columns else pd.DataFrame()
        st.divider()
        st.subheader("Activity Attachments")
        if not attachments.empty:
            for idx, row in attachments.iterrows():
                st.markdown(f"**{row['date'].strftime('%Y-%m-%d')} — {row['activity_type']}**")
                st.image(row["attachment_url"], width=400)
        else:
            st.info("No attachments found.")

        # Monthly heatmap selector
        st.divider()
        st.subheader("Monthly Heatmap (days of month by weekday)")
        st.write("Select month and year to view day-by-week heatmap (intensity by points)")
        years = sorted(df['date'].dt.year.unique(), reverse=True)
        sel_year = st.selectbox("Year", years, index=0)
        months = sorted(df[df['date'].dt.year==sel_year]['date'].dt.month.unique(), reverse=True)
        sel_month = st.selectbox("Month (number)", months, index=0)

        pivot_m = heatmap_month(df, int(sel_year), int(sel_month), value_col="points")
        if pivot_m is None:
            st.info("No data for this month.")
        else:
            fig = px.imshow(pivot_m, labels=dict(x="Week of month", y="Weekday", color="Points"),
                            x=pivot_m.columns.astype(str), y=pivot_m.index, title=f"Heatmap: {sel_year}-{sel_month:02d}")
            st.plotly_chart(fig, use_container_width=True)

        # Yearly heatmap
        st.divider()
        st.subheader("Yearly Heatmap (month vs day)")
        year_for_heat = st.selectbox("Select year for yearly heatmap", years, index=0, key="yrheat")
        pivot_y = heatmap_year(df, int(year_for_heat), value_col="points")
        if pivot_y is None:
            st.info("No data for this year.")
        else:
            # plotly heatmap where y=month, x=day
            fig2 = px.imshow(pivot_y.fillna(0),
                             labels=dict(x="Day of month", y="Month", color="Points"),
                             x=pivot_y.columns.astype(str), y=pivot_y.index,
                             title=f"Yearly Heatmap: {year_for_heat}")
            st.plotly_chart(fig2, use_container_width=True)

        # Download full history
        st.divider()
        csv = df.drop(columns=['_id']).to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download full history (CSV)", csv, file_name=f"{full_name}_activity_history.csv", mime="text/csv")

# ---------- Profile ----------
elif menu == "Profile":
    st.header("🧑‍💻 My Profile")
    user_doc = db.collection("users").document(uid).get()
    data = user_doc.to_dict() if user_doc.exists else {}
    
    # Basic Profile Information
    st.subheader("Basic Information")
    with st.form("profile_form"):
        name = st.text_input("Full name", value=data.get("full_name", full_name))
        height = st.number_input("Height (cm)", value=float(data.get("height",0.0)))
        weight = st.number_input("Weight (kg)", value=float(data.get("weight",0.0)))
        submitted = st.form_submit_button("Update Profile")
    if submitted:
        db.collection("users").document(uid).update({
            "full_name": name,
            "height": float(height),
            "weight": float(weight)
        })
        st.success("Profile updated.")
        st.rerun()
    
    # Password Change Section
    st.markdown("---")
    st.subheader("🔒 Change Password")
    with st.form("password_change_form"):
        current_pwd = st.text_input("Current Password", type="password")
        new_pwd = st.text_input("New Password", type="password", help="Min 8 chars, 1 uppercase, 1 lowercase, 1 number")
        confirm_pwd = st.text_input("Confirm New Password", type="password")
        change_pwd_submit = st.form_submit_button("Change Password")
    
    if change_pwd_submit:
        if not all([current_pwd, new_pwd, confirm_pwd]):
            st.error("Please fill in all password fields")
        elif new_pwd != confirm_pwd:
            st.error("New passwords do not match")
        else:
            try:
                change_password(uid, current_pwd, new_pwd)
                st.success("Password changed successfully! ✅")
            except AuthenticationError as e:
                st.error(str(e))
    
    # Account Information
    st.markdown("---")
    st.subheader("📊 Account Information")
    st.write(f"**Email:** {data.get('email', 'N/A')}")
    st.write(f"**Account Created:** {data.get('created_at', 'N/A')[:10] if data.get('created_at') else 'N/A'}")
    st.write(f"**Last Login:** {data.get('last_login', 'N/A')[:10] if data.get('last_login') else 'N/A'}")
