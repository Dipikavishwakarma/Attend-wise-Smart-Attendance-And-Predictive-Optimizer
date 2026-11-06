"""
Attend-Wise: Smart Attendance & Predictive Optimizer
Main Streamlit Application Dashboard
"""

import os
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

# Import core modules
from src.predictor import (
    calculate_percentage,
    recovery_prediction,
    safe_bunk_buffer,
    get_status_zone,
    get_multi_target_matrix,
    simulate_scenario
)
from src.calendar_engine import (
    CalendarEngine,
    get_all_holidays,
    add_custom_holiday,
    remove_custom_holiday,
    get_custom_holiday_set,
    save_user_semester_config,
    load_user_semester_config
)
from src.auth import (
    render_auth_ui,
    logout_user,
    get_all_users
)
from src.attendance_engine import (
    get_user_records,
    get_user_daily_attendance,
    save_daily_lectures,
    delete_date_records,
    get_baseline_attendance,
    set_baseline_attendance,
    get_student_attendance_summary,
    seed_sample_attendance_for_user
)

# ---------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Attend-Wise | Smart Attendance Optimizer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# CUSTOM CSS STYLING
# ---------------------------------------------------------
CUSTOM_CSS = """
<style>
/* Global Dark Theme Settings */
.stApp {
    background: radial-gradient(circle at top right, #111827, #0B0F17 80%);
    color: #F3F4F6;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] .stMarkdown h2, 
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #F8FAFC !important;
}

/* Card Containers */
.custom-card {
    background: rgba(30, 41, 59, 0.65);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.custom-card:hover {
    border-color: rgba(148, 163, 184, 0.35);
}

/* Metric Display Cards */
.metric-box {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}
.metric-box .metric-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.metric-box .metric-val {
    font-size: 2.1rem;
    font-weight: 800;
    line-height: 1.1;
    color: #FFFFFF;
}
.metric-box .metric-sub {
    font-size: 0.8rem;
    color: #64748B;
    margin-top: 4px;
}

/* Zone Alerts */
.zone-alert-green {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.08));
    border: 1.5px solid #10B981;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    color: #ECFDF5;
}
.zone-alert-yellow {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.08));
    border: 1.5px solid #F59E0B;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    color: #FFFBEB;
}
.zone-alert-red {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.18), rgba(220, 38, 38, 0.08));
    border: 1.5px solid #EF4444;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    color: #FEF2F2;
}

/* Status Badges */
.badge-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.badge-green {
    background-color: rgba(16, 185, 129, 0.2);
    color: #34D399;
    border: 1px solid #10B981;
}
.badge-yellow {
    background-color: rgba(245, 158, 11, 0.2);
    color: #FBBF24;
    border: 1px solid #F59E0B;
}
.badge-red {
    background-color: rgba(239, 68, 68, 0.2);
    color: #F87171;
    border: 1px solid #EF4444;
}

/* Button & Form Controls Styling */
.stButton>button {
    background: linear-gradient(135deg, #1E293B, #0F172A) !important;
    color: #F8FAFC !important;
    border: 1px solid rgba(148, 163, 184, 0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #334155, #1E293B) !important;
    border-color: #38BDF8 !important;
    box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25) !important;
}

/* Highlight Primary Action Buttons */
div[data-testid="stForm"] .stButton>button {
    background: linear-gradient(135deg, #0284C7, #0369A1) !important;
    border-color: #38BDF8 !important;
}

/* Custom Table Polish */
div[data-testid="stDataFrame"] {
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.15);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# AUTHENTICATION CHECK
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    render_auth_ui()
    st.stop()


# ---------------------------------------------------------
# LOGGED IN USER CONTEXT
# ---------------------------------------------------------
username = st.session_state.get("username", "student")
user_info = st.session_state.get("user_info", {})
full_name = user_info.get("full_name") or username
roll_number = user_info.get("roll_number") or "N/A"
email = user_info.get("email") or "N/A"

# Load user semester config
sem_cfg = load_user_semester_config(username)
calendar_engine = CalendarEngine(
    start_date=sem_cfg["start_date"],
    end_date=sem_cfg["end_date"],
    daily_lectures=sem_cfg["daily_lectures"]
)
sem_stats = calendar_engine.get_semester_timeline()

# Load student attendance metrics
attendance_summary = get_student_attendance_summary(username)
total_a = attendance_summary["total_attended"]
total_c = attendance_summary["total_conducted"]
current_pct = attendance_summary["percentage"]
status_zone = get_status_zone(current_pct)


# ---------------------------------------------------------
# SIDEBAR NAVIGATION & PROFILE SUMMARY
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <div style="background: linear-gradient(135deg, #10B981, #06B6D4); border-radius: 10px; padding: 8px 12px; font-size: 22px;">
                🎯
            </div>
            <div>
                <h3 style="margin: 0; color: #FFFFFF; font-size: 1.2rem; font-weight: 700;">Attend-Wise</h3>
                <span style="font-size: 0.75rem; color: #94A3B8;">Predictive Attendance Optimizer</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # User Profile Card
    badge_class = "badge-green" if status_zone["zone"] == "Green" else ("badge-yellow" if status_zone["zone"] == "Yellow" else "badge-red")
    st.markdown(
        f"""
        <div class="custom-card" style="padding: 14px; margin-bottom: 18px; border-left: 4px solid {status_zone['color']};">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Student Profile</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-top: 2px;">{full_name}</div>
            <div style="font-size: 0.82rem; color: #CBD5E1;">🆔 Roll No: <code style="color: #38BDF8;">{roll_number}</code></div>
            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">👤 @{username}</div>
            <div style="margin-top: 8px;">
                <span class="badge-pill {badge_class}">{status_zone['badge_icon']} {current_pct}% ({status_zone['name']})</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 🧭 Navigation")
    menu_choice = st.radio(
        "Go To",
        options=[
            "📊 Dashboard & Optimizer",
            "📝 Daily Lecture Logger",
            "🎯 Multi-Target Matrix",
            "🔮 'What-If' Simulator",
            "📅 Semester Calendar & Holidays",
            "📜 Attendance History & Baseline"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    
    # Semester Timeline Mini-Card
    st.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 10px; padding: 12px; font-size: 0.82rem;">
            <div style="font-weight: 700; color: #F1F5F9; margin-bottom: 6px;">📅 Semester Progress</div>
            <div style="color: #94A3B8;">Start: <span style="color: #F8FAFC;">{sem_stats['start_date'].strftime('%d %b %Y')}</span></div>
            <div style="color: #94A3B8;">End: <span style="color: #F8FAFC;">{sem_stats['end_date'].strftime('%d %b %Y')}</span></div>
            <div style="color: #94A3B8;">Schedule: <span style="color: #38BDF8;">{sem_stats['daily_lectures']} lectures/day</span></div>
            <div style="color: #94A3B8; margin-top: 4px;">Remaining Working Days: <b style="color: #10B981;">{sem_stats['remaining_working_days']} days</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        logout_user()


# =========================================================
# 1. 📊 MAIN DASHBOARD & OPTIMIZER
# =========================================================
if menu_choice == "📊 Dashboard & Optimizer":
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 4px;">
                🎯 Attendance Optimizer Dashboard
            </h1>
            <p style="color: #94A3B8; margin-top: 0; font-size: 1rem;">
                Mathematical recovery predictions & safe bunk buffer analytics for <b>{full_name}</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Color-Coded Warning Banner
    if status_zone["zone"] == "Green":
        st.markdown(
            f"""
            <div class="zone-alert-green">
                <div style="font-size: 1.15rem; font-weight: 700;">🟢 {status_zone['name']} — {status_zone['summary']} ({current_pct}%)</div>
                <div style="font-size: 0.92rem; margin-top: 4px; opacity: 0.95;">{status_zone['description']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif status_zone["zone"] == "Yellow":
        st.markdown(
            f"""
            <div class="zone-alert-yellow">
                <div style="font-size: 1.15rem; font-weight: 700;">🟡 {status_zone['name']} — {status_zone['summary']} ({current_pct}%)</div>
                <div style="font-size: 0.92rem; margin-top: 4px; opacity: 0.95;">{status_zone['description']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="zone-alert-red">
                <div style="font-size: 1.15rem; font-weight: 700;">🔴 {status_zone['name']} — {status_zone['summary']} ({current_pct}%)</div>
                <div style="font-size: 0.92rem; margin-top: 4px; opacity: 0.95;">{status_zone['description']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Core Mathematical Predictor Calculations for standard 75%
    recovery_75 = recovery_prediction(total_a, total_c, 75.0)
    bunk_75 = safe_bunk_buffer(total_a, total_c, 75.0)

    # Top KPI Metrics Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(
            f"""
            <div class="metric-box" style="border-top: 4px solid {status_zone['color']};">
                <div class="metric-title">Current Attendance</div>
                <div class="metric-val" style="color: {status_zone['color']};">{current_pct}%</div>
                <div class="metric-sub">{status_zone['name']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="metric-box" style="border-top: 4px solid #10B981;">
                <div class="metric-title">Attended Lectures</div>
                <div class="metric-val" style="color: #34D399;">{total_a}</div>
                <div class="metric-sub">Present lectures logged</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="metric-box" style="border-top: 4px solid #38BDF8;">
                <div class="metric-title">Conducted Lectures</div>
                <div class="metric-val" style="color: #38BDF8;">{total_c}</div>
                <div class="metric-sub">Total delivered classes</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col4:
        if current_pct >= 75.0:
            st.markdown(
                f"""
                <div class="metric-box" style="border-top: 4px solid #10B981;">
                    <div class="metric-title">Safe Bunk Buffer (75%)</div>
                    <div class="metric-val" style="color: #10B981;">{bunk_75}</div>
                    <div class="metric-sub">Classes you can safely miss</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="metric-box" style="border-top: 4px solid #EF4444;">
                    <div class="metric-title">Recovery Needed (75%)</div>
                    <div class="metric-val" style="color: #EF4444;">{recovery_75}</div>
                    <div class="metric-sub">Consecutive classes to attend</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Strategy & Mathematical Action Card
    col_strat, col_gauge = st.columns([3, 2])

    with col_strat:
        st.markdown(
            """
            <div class="custom-card">
                <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    <span>📐</span> Exact Mathematical Strategy
                </div>
            """,
            unsafe_allow_html=True
        )
        if total_c == 0:
            st.info("No lectures have been logged yet. Head over to the 'Daily Lecture Logger' tab to record your classes.")
        elif current_pct >= 75.0:
            st.markdown(
                f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                    <h4 style="margin: 0 0 6px 0; color: #34D399;">🛡️ Safe Buffer Status</h4>
                    <p style="margin: 0; color: #E2E8F0; font-size: 0.95rem;">
                        You have an attendance surplus of <b>{round(current_pct - 75.0, 2)}%</b>. 
                        Using the mathematical floor buffer formula:
                    </p>
                    <code style="display: block; margin: 8px 0; padding: 6px; background: rgba(0,0,0,0.3); color: #38BDF8;">
                        y = Floor[(100 * {total_a} - 75 * {total_c}) / 75] = {bunk_75} lectures
                    </code>
                    <p style="margin: 0; color: #CBD5E1; font-size: 0.92rem;">
                        👉 You can safely miss up to <b>{bunk_75} consecutive lectures</b>. If you miss {bunk_75} classes, your attendance will be <b>{calculate_percentage(total_a, total_c + bunk_75)}%</b>, remaining safely above the 75% threshold!
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                    <h4 style="margin: 0 0 6px 0; color: #F87171;">⚡ Urgent Recovery Mandate</h4>
                    <p style="margin: 0; color: #E2E8F0; font-size: 0.95rem;">
                        You currently have an attendance deficit of <b>{round(75.0 - current_pct, 2)}%</b> below the required 75% line.
                        Using the algebraic recovery formula:
                    </p>
                    <code style="display: block; margin: 8px 0; padding: 6px; background: rgba(0,0,0,0.3); color: #FCA5A5;">
                        x = Ceil[(75 * {total_c} - 100 * {total_a}) / (100 - 75)] = {recovery_75} lectures
                    </code>
                    <p style="margin: 0; color: #CBD5E1; font-size: 0.92rem;">
                        👉 You must attend the next <b>{recovery_75} consecutive lectures</b> without missing any. 
                        Upon completing these {recovery_75} classes, your attendance will recover to <b>{calculate_percentage(total_a + recovery_75, total_c + recovery_75)}%</b>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Check if recovery is mathematically feasible before semester ends
        rem_lectures = sem_stats["remaining_lectures"]
        if current_pct < 75.0 and recovery_75 > 0:
            if recovery_75 > rem_lectures:
                st.error(f"🚨 Critical Feasibility Alert: You need {recovery_75} classes to recover, but only {rem_lectures} lectures remain scheduled this semester! Speak to your academic advisor immediately.")
            else:
                st.info(f"ℹ️ Semester Window: {rem_lectures} lectures remain scheduled. Your required {recovery_75} recovery classes will consume {round((recovery_75 / rem_lectures) * 100, 1)}% of remaining semester classes.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_gauge:
        # Semester Horizon & Ceiling/Floor Potentials
        max_possible_pct = calculate_percentage(total_a + rem_lectures, total_c + rem_lectures) if (total_c + rem_lectures) > 0 else 0.0
        min_possible_pct = calculate_percentage(total_a, total_c + rem_lectures) if (total_c + rem_lectures) > 0 else 0.0

        st.markdown(
            f"""
            <div class="custom-card">
                <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    <span>🔭</span> Semester End Projections
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 14px;">
                    Based on <b>{rem_lectures} remaining lectures</b> ({sem_stats['remaining_working_days']} working days) until semester end on {sem_stats['end_date'].strftime('%d %b %Y')}.
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                        <span style="color: #34D399; font-weight: 600;">Maximum Possible (100% Attendance)</span>
                        <span style="color: #34D399; font-weight: 700;">{max_possible_pct}%</span>
                    </div>
                    <div style="background: rgba(148, 163, 184, 0.2); border-radius: 999px; height: 8px; overflow: hidden;">
                        <div style="background: #10B981; width: {min(100.0, max_possible_pct)}%; height: 100%;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                        <span style="color: #F87171; font-weight: 600;">Minimum Possible (0% Remaining)</span>
                        <span style="color: #F87171; font-weight: 700;">{min_possible_pct}%</span>
                    </div>
                    <div style="background: rgba(148, 163, 184, 0.2); border-radius: 999px; height: 8px; overflow: hidden;">
                        <div style="background: #EF4444; width: {min(100.0, min_possible_pct)}%; height: 100%;"></div>
                    </div>
                </div>

                <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px; font-size: 0.82rem; color: #94A3B8;">
                    💡 <b>Attendance Cap:</b> Even if you attend every remaining class, your semester score cannot exceed <b>{max_possible_pct}%</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Quick Multi-Target Summary Snapshot
    st.markdown("### 🎯 Quick Multi-Target Snapshot")
    matrix_data = get_multi_target_matrix(total_a, total_c)
    m_cols = st.columns(len(matrix_data))
    for idx, item in enumerate(matrix_data):
        with m_cols[idx]:
            is_ok = item["is_achieved"]
            b_color = "#10B981" if is_ok else ("#F59E0B" if item["target"] < 75 else "#EF4444")
            st.markdown(
                f"""
                <div class="metric-box" style="border-top: 3px solid {b_color}; padding: 12px;">
                    <div style="font-size: 1.1rem; font-weight: 800; color: #FFFFFF;">{item['target_str']}</div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: {b_color}; margin-top: 2px;">
                        {'✅ ' + item['status'] if is_ok else '⚠️ ' + item['status']}
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 6px; min-height: 34px;">
                        {item['action']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# 2. 📝 INTERACTIVE DAILY LECTURE LOGGER
# =========================================================
elif menu_choice == "📝 Daily Lecture Logger":
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 4px;">
                📝 Daily Lecture Attendance Logger
            </h1>
            <p style="color: #94A3B8; margin-top: 0; font-size: 1rem;">
                Record daily lectures with instant 'Mark All Present' toggle, custom subjects, and status updates.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Date Selection Row
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        selected_date = st.date_input("📅 Select Date to Log", value=date.today(), key="logger_date")
    
    date_str = selected_date.isoformat()
    is_sat_sun = calendar_engine.is_weekend(selected_date)
    is_cust_holiday = calendar_engine.is_holiday(selected_date)

    with col_d2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if is_sat_sun:
            st.warning(f"⚠️ {selected_date.strftime('%A, %d %B %Y')} is a weekend (Saturday/Sunday). You can still log if extra lectures occurred.")
        elif is_cust_holiday:
            st.info(f"🏖️ {selected_date.strftime('%d %B %Y')} is marked as an academic holiday.")
        else:
            st.success(f"🏫 Regular Academic Working Day: {selected_date.strftime('%A, %d %B %Y')}")

    # Fetch existing entries for the chosen date
    existing_daily = get_user_daily_attendance(username, date_str)
    daily_lecture_count = sem_cfg["daily_lectures"]
    lecture_slots = calendar_engine.generate_lecture_slots()

    # Session state key for quick batch action
    batch_key = f"batch_mode_{date_str}"
    if batch_key not in st.session_state:
        st.session_state[batch_key] = None

    # Quick Batch Buttons Bar
    st.markdown("#### ⚡ Quick Actions")
    q_col1, q_col2, q_col3, q_col4 = st.columns([1, 1, 1, 2])
    with q_col1:
        if st.button("✅ Mark All Present", use_container_width=True):
            st.session_state[batch_key] = "Present"
            st.rerun()
    with q_col2:
        if st.button("❌ Mark All Absent", use_container_width=True):
            st.session_state[batch_key] = "Absent"
            st.rerun()
    with q_col3:
        if st.button("🟡 Mark All Leave", use_container_width=True):
            st.session_state[batch_key] = "Leave"
            st.rerun()
    with q_col4:
        if existing_daily:
            if st.button("🗑️ Reset / Clear Today's Records", use_container_width=True):
                ok, msg = delete_date_records(username, date_str)
                st.session_state[batch_key] = None
                st.toast(msg)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Form to input and review lectures
    with st.form("daily_lecture_form"):
        st.markdown(f"#### 📋 Lecture Schedule for {selected_date.strftime('%d %b %Y')} ({daily_lecture_count} Lectures)")
        
        form_entries = []
        for slot in lecture_slots:
            lec_num = slot["lecture_number"]
            slot_label = slot["label"]
            slot_time = slot["time_slot"]

            # Determine initial value:
            # 1. Batch override if user clicked a quick action button
            # 2. Existing database record if previously logged
            # 3. Default "Present"
            batch_val = st.session_state.get(batch_key)
            if batch_val:
                default_status = batch_val
            elif lec_num in existing_daily:
                default_status = existing_daily[lec_num].get("status", "Present")
            else:
                default_status = "Present"

            existing_subj = existing_daily.get(lec_num, {}).get("subject", "")

            # Form row
            l_col1, l_col2, l_col3 = st.columns([1.5, 2, 2.5])
            with l_col1:
                st.markdown(
                    f"""
                    <div style="padding-top: 10px;">
                        <b style="color: #FFFFFF; font-size: 0.95rem;">{slot_label}</b><br>
                        <span style="font-size: 0.78rem; color: #94A3B8;">🕒 {slot_time}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with l_col2:
                status_choice = st.radio(
                    f"Status for L{lec_num}",
                    options=["Present", "Absent", "Leave"],
                    index=["Present", "Absent", "Leave"].index(default_status) if default_status in ["Present", "Absent", "Leave"] else 0,
                    horizontal=True,
                    key=f"lec_status_{date_str}_{lec_num}",
                    label_visibility="collapsed"
                )
            with l_col3:
                subject_input = st.text_input(
                    f"Subject for L{lec_num}",
                    value=existing_subj,
                    placeholder="e.g. Data Structures / Lab",
                    key=f"lec_subj_{date_str}_{lec_num}",
                    label_visibility="collapsed"
                )

            form_entries.append({
                "lecture_number": lec_num,
                "status": status_choice,
                "subject": subject_input
            })
            st.markdown("<hr style='margin: 8px 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

        submit_save = st.form_submit_button("💾 Save Attendance Records", use_container_width=True)

        if submit_save:
            success, msg = save_daily_lectures(username, date_str, form_entries)
            st.session_state[batch_key] = None  # Reset batch override
            if success:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# =========================================================
# 3. 🎯 MULTI-TARGET PLAN SELECTOR MATRIX
# =========================================================
elif menu_choice == "🎯 Multi-Target Matrix":
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 4px;">
                🎯 Multi-Target Plan Selector Matrix
            </h1>
            <p style="color: #94A3B8; margin-top: 0; font-size: 1rem;">
                Compare required consecutive recovery classes and safe bunk allowances across standard thresholds (50%, 60%, 70%, 75%, 85%).
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="custom-card" style="margin-bottom: 20px; padding: 14px;">
            <span style="font-size: 0.95rem; color: #CBD5E1;">
                Current Benchmark Status: <b>{total_a} Attended</b> out of <b>{total_c} Conducted</b> = 
                <b style="color: {status_zone['color']}; font-size: 1.1rem;">{current_pct}%</b> ({status_zone['name']}).
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    targets = [50.0, 60.0, 70.0, 75.0, 85.0]
    matrix = get_multi_target_matrix(total_a, total_c, targets)

    # Detailed Table View
    table_rows = []
    for item in matrix:
        table_rows.append({
            "Target Threshold": item["target_str"],
            "Current Status": "✅ Eligible" if item["is_achieved"] else "⚠️ Shortage",
            "Difference": f"{item['difference']:+0.2f}%",
            "Consecutive Recovery Needed": f"{item['recovery_needed']} lectures" if item['recovery_needed'] > 0 else "0",
            "Safe Bunk Buffer": f"{item['safe_bunks']} lectures" if item['safe_bunks'] > 0 else "0",
            "Recommended Action": item["action"],
            "Projected %": f"{item['projected_percentage']}%"
        })

    df_matrix = pd.DataFrame(table_rows)
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🧩 Target Plan Detailed Breakdown Cards")

    card_cols = st.columns(len(matrix))
    for idx, item in enumerate(matrix):
        with card_cols[idx]:
            is_ok = item["is_achieved"]
            t_color = "#10B981" if is_ok else ("#F59E0B" if item["target"] < 75 else "#EF4444")
            
            st.markdown(
                f"""
                <div class="custom-card" style="border-top: 4px solid {t_color}; padding: 16px; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 800; color: #FFFFFF;">{item['target_str']}</div>
                    <div style="font-size: 0.85rem; font-weight: 700; color: {t_color}; margin: 4px 0 10px 0;">
                        {'🟢 ELIGIBLE' if is_ok else '🔴 SHORTAGE'}
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.7); border-radius: 8px; padding: 10px; margin-bottom: 10px;">
                        <div style="font-size: 0.75rem; color: #94A3B8;">Margin vs Target</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: {t_color};">{item['difference']:+0.2f}%</div>
                    </div>
                    <div style="font-size: 0.82rem; color: #E2E8F0; min-height: 48px;">
                        <b>{item['action']}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Custom Target Calculator
    with st.expander("🔍 Explore Custom Target Percentage (e.g., 80%, 90%)", expanded=False):
        c_col1, c_col2 = st.columns([1, 2])
        with c_col1:
            custom_t = st.number_input("Enter Target Percentage %", min_value=1.0, max_value=99.9, value=80.0, step=0.5)
        
        with c_col2:
            if current_pct >= custom_t:
                c_bunk = safe_bunk_buffer(total_a, total_c, custom_t)
                st.success(f"🎉 For **{custom_t}%**, you are already eligible! You can safely bunk up to **{c_bunk} lectures**.")
            else:
                c_rec = recovery_prediction(total_a, total_c, custom_t)
                st.error(f"⚡ For **{custom_t}%**, you need to attend **{c_rec} consecutive lectures** without missing.")


# =========================================================
# 4. 🔮 "WHAT-IF" SCENARIO SIMULATOR
# =========================================================
elif menu_choice == "🔮 'What-If' Simulator":
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 4px;">
                🔮 "What-If" Scenario Simulator
            </h1>
            <p style="color: #94A3B8; margin-top: 0; font-size: 1rem;">
                Dynamically project attendance percentage shifts when bunking upcoming classes or attending extra remedial lectures.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="custom-card" style="padding: 14px; margin-bottom: 20px;">
            <span style="color: #94A3B8;">Current Baseline:</span> 
            <b style="color: #FFFFFF;">{total_a} Attended</b> / <b style="color: #FFFFFF;">{total_c} Conducted</b> = 
            <span class="badge-pill {'badge-green' if status_zone['zone'] == 'Green' else ('badge-yellow' if status_zone['zone'] == 'Yellow' else 'badge-red')}">
                {status_zone['badge_icon']} {current_pct}% ({status_zone['name']})
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    sim_col1, sim_col2 = st.columns(2)

    with sim_col1:
        st.markdown(
            """
            <div class="custom-card">
                <h4 style="margin: 0 0 12px 0; color: #F87171;">🚫 Upcoming Missed Classes (Leaves / Bunks)</h4>
                <p style="font-size: 0.85rem; color: #94A3B8;">Simulate how many upcoming lectures you plan to miss or take leave for.</p>
            """,
            unsafe_allow_html=True
        )
        sim_leaves = st.slider("Number of Upcoming Classes to Bunk", min_value=0, max_value=30, value=2, step=1, key="slider_leaves")
        st.markdown("</div>", unsafe_allow_html=True)

    with sim_col2:
        st.markdown(
            """
            <div class="custom-card">
                <h4 style="margin: 0 0 12px 0; color: #34D399;">⚡ Upcoming Extra / Attended Classes</h4>
                <p style="font-size: 0.85rem; color: #94A3B8;">Simulate attending extra remedial lectures or upcoming regular classes consecutively.</p>
            """,
            unsafe_allow_html=True
        )
        sim_extra = st.slider("Number of Upcoming Classes to Attend", min_value=0, max_value=40, value=5, step=1, key="slider_extra")
        st.markdown("</div>", unsafe_allow_html=True)

    # Perform scenario simulation
    sim_result = simulate_scenario(total_a, total_c, upcoming_leaves=sim_leaves, upcoming_extra=sim_extra)
    new_pct = sim_result["new_percentage"]
    delta = sim_result["delta"]
    new_zone = sim_result["new_zone"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Simulation Outcomes")

    out_col1, out_col2, out_col3, out_col4 = st.columns(4)

    with out_col1:
        st.markdown(
            f"""
            <div class="metric-box" style="border-top: 4px solid {new_zone['color']};">
                <div class="metric-title">Projected Attendance</div>
                <div class="metric-val" style="color: {new_zone['color']};">{new_pct}%</div>
                <div class="metric-sub">{new_zone['name']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with out_col2:
        delta_color = "#10B981" if delta > 0 else ("#EF4444" if delta < 0 else "#94A3B8")
        st.markdown(
            f"""
            <div class="metric-box" style="border-top: 4px solid {delta_color};">
                <div class="metric-title">Percentage Shift (Δ)</div>
                <div class="metric-val" style="color: {delta_color};">{delta:+0.2f}%</div>
                <div class="metric-sub">From baseline {current_pct}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with out_col3:
        st.markdown(
            f"""
            <div class="metric-box" style="border-top: 4px solid #38BDF8;">
                <div class="metric-title">New Lecture Ratio</div>
                <div class="metric-val" style="color: #38BDF8; font-size: 1.7rem;">{sim_result['new_attended']} / {sim_result['new_conducted']}</div>
                <div class="metric-sub">Attended / Total Conducted</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with out_col4:
        if new_pct >= 75.0:
            st.markdown(
                f"""
                <div class="metric-box" style="border-top: 4px solid #10B981;">
                    <div class="metric-title">New Safe Bunks (75%)</div>
                    <div class="metric-val" style="color: #10B981;">{sim_result['safe_bunks_for_75']}</div>
                    <div class="metric-sub">Bunk allowance in new state</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="metric-box" style="border-top: 4px solid #EF4444;">
                    <div class="metric-title">New Recovery (75%)</div>
                    <div class="metric-val" style="color: #EF4444;">{sim_result['recovery_for_75']}</div>
                    <div class="metric-sub">Required consecutive classes</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Narrative Summary & Zone Shift Notice
    st.markdown(
        f"""
        <div class="custom-card" style="border-left: 4px solid {new_zone['color']};">
            <h4 style="margin: 0 0 8px 0; color: #FFFFFF;">Transition Assessment</h4>
            <p style="margin: 0 0 8px 0; color: #CBD5E1; font-size: 0.95rem;">
                Starting from <b>{total_a}/{total_c} ({current_pct}%)</b>, if you take <b>{sim_leaves} leaves</b> and attend <b>{sim_extra} classes</b>, 
                your ratio shifts to <b>{sim_result['new_attended']}/{sim_result['new_conducted']}</b> resulting in <b>{new_pct}%</b> attendance.
            </p>
            <div style="font-size: 0.9rem; color: #94A3B8;">
                Zone Migration: <span class="badge-pill {'badge-green' if status_zone['zone'] == 'Green' else ('badge-yellow' if status_zone['zone'] == 'Yellow' else 'badge-red')}">{status_zone['name']}</span> 
                ➔ <span class="badge-pill {'badge-green' if new_zone['zone'] == 'Green' else ('badge-yellow' if new_zone['zone'] == 'Yellow' else 'badge-red')}">{new_zone['name']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 5. 📅 SEMESTER CALENDAR & HOLIDAYS
# =========================================================
elif menu_choice == "📅 Semester Calendar & Holidays":
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 4px;">
                📅 Semester Calendar & Holiday Engine
            </h1>
            <p style="color: #94A3B8; margin-top: 0; font-size: 1rem;">
                Configure semester start/end dates, daily lecture counts (1-10/day), and manage college holidays with automatic weekend stripping.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    cal_col1, cal_col2 = st.columns([1, 1])

    with cal_col1:
        st.markdown(
            """
            <div class="custom-card">
                <h4 style="margin: 0 0 12px 0; color: #38BDF8;">⚙️ Semester Timeline & Timetable Settings</h4>
            """,
            unsafe_allow_html=True
        )

        with st.form("semester_config_form"):
            s_date = st.date_input("Semester Start Date", value=sem_cfg["start_date"], key="cfg_start_date")
            e_date = st.date_input("Semester End Date", value=sem_cfg["end_date"], key="cfg_end_date")
            d_lec = st.slider("Daily Lecture Count (1 to 10 lectures/day)", min_value=1, max_value=10, value=sem_cfg["daily_lectures"], step=1)
            
            submit_sem_cfg = st.form_submit_button("Save Semester Configuration", use_container_width=True)

            if submit_sem_cfg:
                if e_date <= s_date:
                    st.error("Semester End Date must be after Start Date.")
                else:
                    save_user_semester_config(username, s_date.isoformat(), e_date.isoformat(), d_lec)
                    st.success("Semester parameters saved successfully!")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with cal_col2:
        st.markdown(
            """
            <div class="custom-card">
                <h4 style="margin: 0 0 12px 0; color: #10B981;">📊 Calendar Engine Statistics</h4>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div style="font-size: 0.9rem; line-height: 1.8; color: #CBD5E1;">
                • <b>Total Academic Working Days:</b> <span style="color: #38BDF8;">{sem_stats['total_working_days']} days</span> (excluding Sat/Sun & holidays)<br>
                • <b>Total Semester Lectures:</b> <span style="color: #38BDF8;">{sem_stats['total_scheduled_lectures']} lectures</span> ({sem_stats['daily_lectures']} per day)<br>
                • <b>Working Days Elapsed:</b> <span style="color: #FBBF24;">{sem_stats['elapsed_working_days']} days</span> ({sem_stats['progress_percentage']}% completed)<br>
                • <b>Remaining Working Days:</b> <span style="color: #34D399;">{sem_stats['remaining_working_days']} days</span><br>
                • <b>Remaining Scheduled Lectures:</b> <span style="color: #34D399;">{sem_stats['remaining_lectures']} lectures</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Custom Holidays Management
    st.markdown("### 🏖️ Custom Academic Holidays & Festivals")
    h_col1, h_col2 = st.columns([1, 2])

    with h_col1:
        with st.form("add_holiday_form"):
            st.markdown("#### ➕ Add New Holiday")
            new_h_date = st.date_input("Holiday Date", value=date.today())
            new_h_name = st.text_input("Holiday Name", placeholder="e.g., College Fest / Diwali")
            new_h_type = st.selectbox("Type", ["National", "Festival", "College Event", "Other"])
            
            submit_h = st.form_submit_button("Add Holiday", use_container_width=True)
            if submit_h:
                if not new_h_name:
                    st.error("Please enter a holiday name.")
                else:
                    success, msg = add_custom_holiday(new_h_date, new_h_name, new_h_type)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with h_col2:
        st.markdown("#### 📋 Configured Academic Holidays")
        df_holidays = get_all_holidays()
        if df_holidays.empty:
            st.info("No custom holidays added yet.")
        else:
            df_holidays_sorted = df_holidays.sort_values(by="Date", ascending=True)
            st.dataframe(df_holidays_sorted, use_container_width=True, hide_index=True)
            
            # Delete holiday option
            del_date = st.selectbox("Select date to remove", options=df_holidays_sorted["Date"].tolist(), key="del_h_sel")
            if st.button("🗑️ Remove Selected Holiday"):
                ok, msg = remove_custom_holiday(del_date)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# =========================================================
# 6. 📜 ATTENDANCE HISTORY & BASELINE
# =========================================================
elif menu_choice == "📜 Attendance History & Baseline":
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #FFFFFF; font-size: 2rem; font-weight: 800; margin-bottom: 4px;">
                📜 Attendance History & Prior Baseline
            </h1>
            <p style="color: #94A3B8; margin-top: 0; font-size: 1rem;">
                View complete lecture logs, export attendance records, or set an initial historical baseline.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Initial Historical Baseline Expander
    with st.expander("⚙️ Set Prior Historical Baseline (For Mid-Semester Starters)", expanded=(total_c == 0)):
        st.markdown(
            """
            <p style="font-size: 0.9rem; color: #CBD5E1;">
                If you are starting to use Attend-Wise in the middle of a semester, you can enter your 
                prior cumulative attendance without backfilling old days individually.
            </p>
            """,
            unsafe_allow_html=True
        )
        base_a_curr, base_c_curr = get_baseline_attendance(username)
        
        with st.form("baseline_form"):
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                input_base_a = st.number_input("Prior Attended Lectures", min_value=0, max_value=500, value=base_a_curr)
            with b_col2:
                input_base_c = st.number_input("Prior Conducted Lectures", min_value=0, max_value=500, value=base_c_curr)
            
            submit_baseline = st.form_submit_button("Save Prior Baseline", use_container_width=True)
            if submit_baseline:
                if input_base_a > input_base_c:
                    st.error("Attended lectures cannot exceed conducted lectures.")
                else:
                    set_baseline_attendance(username, input_base_a, input_base_c)
                    st.success("Prior baseline updated successfully!")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Sample Data Demo Seeder
    user_records = get_user_records(username)
    if user_records.empty:
        st.markdown(
            """
            <div class="custom-card" style="text-align: center; padding: 24px;">
                <span style="font-size: 32px;">📊</span>
                <h4 style="color: #FFFFFF; margin: 8px 0 4px 0;">No Attendance Logs Yet</h4>
                <p style="color: #94A3B8; font-size: 0.92rem; max-width: 500px; margin: 0 auto 16px auto;">
                    You haven't logged any daily attendance records yet. You can log them day-by-day in the Daily Logger, or load realistic demo data to explore the optimizer right now!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("✨ Load Realistic Sample Data (42 Lectures, ~76% Attendance)"):
            seed_sample_attendance_for_user(username)
            st.success("Sample records loaded!")
            st.rerun()
    else:
        # Full Records Table and Export
        st.markdown("### 📋 Logged Lecture Entries")
        
        # Filter controls
        f_col1, f_col2 = st.columns([1, 1])
        with f_col1:
            status_filter = st.multiselect("Filter by Status", options=["Present", "Absent", "Leave"], default=["Present", "Absent", "Leave"])
        
        filtered_df = user_records[user_records["Status"].isin(status_filter)] if status_filter else user_records

        st.dataframe(
            filtered_df[["Date", "Lecture_Number", "Status", "Subject", "Timestamp"]],
            use_container_width=True,
            hide_index=True
        )

        csv_data = user_records.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Full Attendance Log to CSV",
            data=csv_data,
            file_name=f"attendwise_log_{username}_{date.today().isoformat()}.csv",
            mime="text/csv"
        )
