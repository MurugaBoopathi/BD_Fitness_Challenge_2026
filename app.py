# app.py
import streamlit as st
from datetime import datetime, date
import pandas as pd
import plotly.express as px
from firebase_config import db
from utils.activity_utils import calculate_points, calculate_calories


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

# --- Show attractive home page only when user not logged in ---
if "user_name" not in st.session_state:
    st.markdown(
        """
        <style>
        .bd-hero-container {
            max-width: 900px;
            margin: 1em auto;
            background: linear-gradient(135deg, #ffffff 0%, #e3f2fd 100%);
            border-radius: 24px;
            box-shadow: 0 12px 48px rgba(67,206,162,0.20);
            overflow: hidden;
            position: relative;
        }
        .bd-hero-top {
            background: linear-gradient(90deg, #43cea2 0%, #185a9d 100%);
            padding: 1.2em 2em;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .bd-hero-logo {
            display: flex;
            align-items: center;
            gap: 0.8em;
        }
        .bd-hero-logo-img {
            width: 55px;
            height: 55px;
            border-radius: 50%;
            box-shadow: 0 4px 16px rgba(255,255,255,0.3);
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .bd-hero-logo-text h1 {
            color: #fff !important;
            font-size: 1.7em !important;
            margin: 0 !important;
            font-weight: 800 !important;
            letter-spacing: 1px !important;
        }
        .bd-hero-logo-text p {
            color: rgba(255,255,255,0.95) !important;
            font-size: 1em !important;
            margin: 0.2em 0 0 0 !important;
            font-weight: 600 !important;
        }
        .bd-hero-badge {
            background: rgba(255,255,255,0.25);
            color: #fff;
            padding: 0.4em 1em;
            border-radius: 16px;
            font-size: 0.95em;
            font-weight: 700;
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255,255,255,0.3);
        }
        .bd-hero-content {
            display: flex;
            flex-direction: row;
            gap: 1.5em;
            padding: 1.5em 2em 1.3em 2em;
            justify-content: center;
        }
        .bd-hero-left {
            flex: 1;
            max-width: 600px;
        }
        .bd-hero-welcome {
            font-size: 1.3em;
            color: #185a9d;
            font-weight: 700;
            margin-bottom: 0.4em;
        }
        .bd-hero-desc {
            font-size: 0.95em;
            color: #444;
            margin-bottom: 0.8em;
            line-height: 1.5;
        }
        .bd-hero-features {
            display: flex;
            flex-direction: row;
            gap: 0.6em;
            margin-bottom: 0.8em;
            flex-wrap: wrap;
        }
        .bd-hero-feature {
            display: flex;
            align-items: center;
            gap: 0.5em;
            background: rgba(67,206,162,0.08);
            padding: 0.5em 0.7em;
            border-radius: 8px;
            border-left: 3px solid #43cea2;
            flex: 1;
            min-width: 120px;
        }
        .bd-hero-feature-icon {
            font-size: 1.3em;
        }
        .bd-hero-feature-text {
            font-size: 0.9em;
            color: #185a9d;
            font-weight: 600;
        }
        .bd-hero-quote {
            font-size: 0.95em;
            color: #43cea2;
            font-weight: 600;
            font-style: italic;
            text-align: center;
            margin: 0.6em 0;
            padding: 0.6em;
            background: rgba(67,206,162,0.08);
            border-radius: 8px;
        }
        .bd-hero-right {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .bd-hero-illustration {
            width: 100%;
            max-width: 400px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(67,206,162,0.25);
            margin-bottom: 1.5em;
        }
        .bd-hero-stats {
            display: flex;
            gap: 1.5em;
            justify-content: center;
            flex-wrap: wrap;
        }
        .bd-hero-stat {
            background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
            color: #fff;
            padding: 1em 1.5em;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(67,206,162,0.25);
            min-width: 100px;
        }
        .bd-hero-stat-value {
            font-size: 2em;
            font-weight: 700;
        }
        .bd-hero-stat-label {
            font-size: 0.9em;
            opacity: 0.95;
            margin-top: 0.3em;
        }
        .bd-hero-form-container {
            display: flex;
            justify-content: center;
            padding: 0 2em 1.5em 2em;
        }
        .bd-hero-form {
            background: rgba(67,206,162,0.10);
            padding: 1.2em;
            border-radius: 12px;
            border: 2px solid #43cea2;
            box-shadow: 0 4px 16px rgba(67,206,162,0.15);
            width: 100%;
            max-width: 700px;
        }
        .bd-hero-form-container .stSelectbox,
        .bd-hero-form-container .stTextInput {
            max-width: 700px;
            margin: 0 auto;
        }
        .bd-hero-form-container .stButton {
            display: flex;
            justify-content: center;
        }
        .bd-hero-form-container .stButton>button {
            max-width: 200px;
        }
        .bd-hero-form-title {
            font-size: 1em;
            color: #185a9d;
            font-weight: 700;
            margin-bottom: 0.5em;
            text-align: center;
        }
        .bd-hero-form-desc {
            font-size: 0.85em;
            color: #444;
            margin-bottom: 0.7em;
            text-align: center;
        }
        </style>
        <div class="bd-hero-container">
            <div class="bd-hero-top">
                <div class="bd-hero-logo">
                    <img class="bd-hero-logo-img" src="https://cdn-icons-png.flaticon.com/512/1048/1048953.png" alt="Fitness">
                    <div class="bd-hero-logo-text">
                        <h1>BD Fitness Challenge 2026</h1>
                        <p>Transform Your Health Journey</p>
                    </div>
                </div>
                <div class="bd-hero-badge">🏆 Join the Challenge!</div>
            </div>
            <div class="bd-hero-content">
                <div class="bd-hero-left">
                    <div class="bd-hero-welcome">Welcome, Fitness Champion! 💪</div>
                    <div class="bd-hero-desc">
                        Track your daily activities, compete with your team, and achieve your fitness goals together!
                    </div>
                    <div class="bd-hero-features">
                        <div class="bd-hero-feature">
                            <div class="bd-hero-feature-icon">📊</div>
                            <div class="bd-hero-feature-text">Track Activities</div>
                        </div>
                        <div class="bd-hero-feature">
                            <div class="bd-hero-feature-icon">🏅</div>
                            <div class="bd-hero-feature-text">Compete</div>
                        </div>
                        <div class="bd-hero-feature">
                            <div class="bd-hero-feature-icon">📈</div>
                            <div class="bd-hero-feature-text">Progress</div>
                        </div>
                    </div>
                    <div class="bd-hero-quote">
                        "The only bad workout is the one you didn't do."
                    </div>
                </div>
            </div>
            <div class="bd-hero-form-container">
                <div class="bd-hero-form">
                    <div class="bd-hero-form-title">🎯 Select Your Name to Continue</div>
                    <div class="bd-hero-form-desc">Pick your name from the list below or type a new one</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Name selection (pre-populated list)
    names_list = [
        "Remya Rajaratnam (BD/SWD-BEA9)","Lokhsundar Balasubramaniam (BD/SWD-BEA9)",
        "Madhanreyan V (BD/SWD-BEA9)","Paulin Nancy Pradeepa Prabhu (BD/SWD-BEA9)",
        "Thamarai Govindasamy (BD/SWD-FSB6)","Prito Thamizh Selvan M (BD/SWD-BEA10)",
        "Murugaboopathi Pillaiyar (BD/SWD-FSB6)","Nagaraj Pandian (BD/SWD-BEA9)",
        "Divya Bharathi Rathnavel Pandian (BD/SWD-BEA10)","Pavithra Muralidharan (BD/SWD-BEA9)",
        "Meenakshi Sundaram Prabhu (BD/SWD-BEA10)","Jayavelu Kola Arumugam (BD/SWD-BEA9)",
        "Karpagam Vigginaraj (BD/SWD-BEA9)","EXTERNAL Velusamy Muthukumar (KGIS, BD/SWD-FSB6)",
        "Vediappan P Raj (BD/SWD-BEA10)","Sri Dhanalakshmi Kamaraj (BD/SWD-BEA9)"
    ]
    # Allow custom name by typing "Other"
    choice = st.selectbox("Pick your name (or type a new name below)", names_list + ["Other"])
    if choice == "Other":
        full_name = st.text_input("Enter your name")
    else:
        full_name = choice

    if full_name and st.button("Continue"):
        with st.spinner("Checking/creating user..."):
            uid = get_or_create_user(full_name.strip())
        if uid:
            st.session_state["user_name"] = full_name.strip()
            st.session_state["uid"] = uid
            st.rerun()
        else:
            st.error("Could not find or create user. Please try again or contact support.")
    st.stop()

# --- After login, show standard layout ---
st.title("🏋️ BD Fitness Challenge 2026 - Activity Tracker")
st.markdown("**Quick select your name and start logging / editing activities.**")

# Name selection (available on all screens to switch users)
names_list = [
    "Remya Rajaratnam (BD/SWD-BEA9)","Lokhsundar Balasubramaniam (BD/SWD-BEA9)",
    "Madhanreyan V (BD/SWD-BEA9)","Paulin Nancy Pradeepa Prabhu (BD/SWD-BEA9)",
    "Thamarai Govindasamy (BD/SWD-FSB6)","Prito Thamizh Selvan M (BD/SWD-BEA10)",
    "Murugaboopathi Pillaiyar (BD/SWD-FSB6)","Nagaraj Pandian (BD/SWD-BEA9)",
    "Divya Bharathi Rathnavel Pandian (BD/SWD-BEA10)","Pavithra Muralidharan (BD/SWD-BEA9)",
    "Meenakshi Sundaram Prabhu (BD/SWD-BEA10)","Jayavelu Kola Arumugam (BD/SWD-BEA9)",
    "Karpagam Vigginaraj (BD/SWD-BEA9)","EXTERNAL Velusamy Muthukumar (KGIS, BD/SWD-FSB6)",
    "Vediappan P Raj (BD/SWD-BEA10)","Sri Dhanalakshmi Kamaraj (BD/SWD-BEA9)"
]

# Get current selection from session state
current_selection = st.session_state.get("user_name", names_list[0])
current_index = names_list.index(current_selection) if current_selection in names_list else 0

# Allow user to switch between associates
choice = st.selectbox("Pick your name (or type a new name below)", names_list + ["Other"], index=current_index, key="user_selector")
if choice == "Other":
    selected_name = st.text_input("Enter your name")
else:
    selected_name = choice

# Update session if selection changed
if selected_name and selected_name != st.session_state.get("user_name"):
    if st.button("Switch User"):
        with st.spinner("Switching user..."):
            uid = get_or_create_user(selected_name.strip())
        if uid:
            st.session_state["user_name"] = selected_name.strip()
            st.session_state["uid"] = uid
            st.rerun()
        else:
            st.error("Could not find or create user. Please try again or contact support.")

activities = [
        "Walking","Jogging","Running","Cycling","Trekking","Badminton","Pickle Ball","Volley Ball",
        "Gym","Yoga/Meditation","Dance","Swimming","Table Tennis","Tennis","Cricket","Football"
    ]

uid = st.session_state["uid"]
full_name = st.session_state["user_name"]

# Sidebar navigation
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2764/2764434.png", width=100)
st.sidebar.markdown(f"**Hello, {full_name}**")
menu = st.sidebar.radio("Navigate", ["Leaderboard","Log Activity","Edit / Delete Activities","My History","Profile"])

# ---------- Leaderboard ----------
if menu == "Leaderboard":
    st.header("🏆 Monthly Leaderboard")
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
        def extract_department(name):
            # Extract the last parenthetical group as department
            matches = re.findall(r'\(([^()]*)\)', name)
            if matches:
                return matches[-1].strip()
            return "Unknown"
        df_lb['Department'] = df_lb['Name'].apply(extract_department)
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
