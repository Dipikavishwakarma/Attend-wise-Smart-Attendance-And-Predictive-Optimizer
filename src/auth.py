"""
Attend-Wise: Smart Attendance & Predictive Optimizer
Module: src/auth.py
Purpose: Handles user registration, login, and SHA-256 password hashing
         storing user credentials in /data/users.csv.
"""

import os
import re
import hashlib
import pandas as pd
import streamlit as st
from typing import Tuple, Optional, Dict, Any


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
ROOT_USERS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "users.csv"))

COLUMNS = ["Full Name", "Email", "Roll Number", "Username", "Password_Hash"]


def make_hashes(password: str) -> str:
    """Generate SHA-256 hash of password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_users_csv() -> None:
    """
    Ensure /data/users.csv exists with correct columns.
    Migrate legacy root users.csv if found.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(USERS_FILE):
        # Check if legacy users.csv exists in root directory
        if os.path.exists(ROOT_USERS_FILE):
            try:
                legacy_df = pd.read_csv(ROOT_USERS_FILE)
                # Map old headers to new headers if present
                migrated_rows = []
                for _, row in legacy_df.iterrows():
                    u = str(row.get("username", "")).strip()
                    p = str(row.get("password", "")).strip()
                    n = str(row.get("name", u)).strip()
                    e = str(row.get("email", "")).strip()
                    r = str(row.get("roll_no", "")).strip()
                    
                    # If password wasn't hashed (length < 64), hash it
                    if len(p) != 64 and p:
                        p = make_hashes(p)
                    
                    migrated_rows.append({
                        "Full Name": n if n else u,
                        "Email": e,
                        "Roll Number": r,
                        "Username": u,
                        "Password_Hash": p
                    })
                df = pd.DataFrame(migrated_rows, columns=COLUMNS)
                df.to_csv(USERS_FILE, index=False)
                return
            except Exception:
                pass
        
        # Create empty with default sample student account for instant testing
        demo_user = pd.DataFrame([{
            "Full Name": "Student Demo",
            "Email": "demo@college.edu",
            "Roll Number": "2026-CS-001",
            "Username": "student",
            "Password_Hash": make_hashes("password123")
        }], columns=COLUMNS)
        demo_user.to_csv(USERS_FILE, index=False)
    else:
        # Validate columns
        try:
            df = pd.read_csv(USERS_FILE)
            dirty = False
            for c in COLUMNS:
                if c not in df.columns:
                    # check lowercase or alternative
                    matched = False
                    for col_name in df.columns:
                        if col_name.strip().lower() == c.lower().replace("_", "").replace(" ", ""):
                            df.rename(columns={col_name: c}, inplace=True)
                            matched = True
                            dirty = True
                            break
                    if not matched:
                        df[c] = ""
                        dirty = True
            if dirty:
                df[COLUMNS].to_csv(USERS_FILE, index=False)
        except Exception:
            pd.DataFrame(columns=COLUMNS).to_csv(USERS_FILE, index=False)


def get_all_users() -> pd.DataFrame:
    """Load all users from data/users.csv."""
    init_users_csv()
    try:
        return pd.read_csv(USERS_FILE, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=COLUMNS)


def check_login(username: str, password: str) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Verify user credentials against data/users.csv.
    Returns (True, user_dict) if valid, otherwise (False, None).
    """
    init_users_csv()
    df = get_all_users()
    if df.empty or "Username" not in df.columns:
        return False, None

    u_clean = username.strip().lower()
    pw_hash = make_hashes(password)

    matched = df[df["Username"].str.strip().str.lower() == u_clean]
    if not matched.empty:
        stored_hash = str(matched.iloc[0]["Password_Hash"]).strip()
        # Direct match or backward compatibility check
        if stored_hash == pw_hash or stored_hash == password:
            user_info = {
                "full_name": str(matched.iloc[0]["Full Name"]).strip(),
                "email": str(matched.iloc[0]["Email"]).strip(),
                "roll_number": str(matched.iloc[0]["Roll Number"]).strip(),
                "username": str(matched.iloc[0]["Username"]).strip(),
            }
            return True, user_info
    return False, None


def register_user(full_name: str, email: str, roll_number: str, username: str, password: str) -> Tuple[bool, str]:
    """
    Register a new student with SHA-256 hashed password.
    Enforces format validations and username uniqueness.
    """
    init_users_csv()
    df = get_all_users()

    # Field validations
    full_name = full_name.strip()
    email = email.strip()
    roll_number = roll_number.strip()
    username = username.strip()

    if not full_name or not email or not roll_number or not username or not password:
        return False, "Please fill in all the required registration fields."

    if len(username) < 3:
        return False, "Username must be at least 3 characters long."

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Please enter a valid email address (e.g., student@college.edu)."

    if len(password) < 4:
        return False, "Password should be at least 4 characters long."

    # Check for existing username (case-insensitive)
    if not df.empty and "Username" in df.columns:
        existing_users = df["Username"].astype(str).str.strip().str.lower().values
        if username.lower() in existing_users:
            return False, f"Username '{username}' is already taken. Please choose another."

    # Save to CSV
    new_user = pd.DataFrame([{
        "Full Name": full_name,
        "Email": email,
        "Roll Number": roll_number,
        "Username": username,
        "Password_Hash": make_hashes(password)
    }], columns=COLUMNS)

    new_user.to_csv(USERS_FILE, mode="a", header=False, index=False)
    return True, "Account registered successfully! You can now log in."


def logout_user() -> None:
    """Clear session state and trigger a rerun."""
    for key in ["logged_in", "username", "user_info"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["logged_in"] = False
    st.rerun()


def render_auth_ui() -> None:
    """
    Render clean, polished authentication UI (Login & Registration)
    matching Attend-Wise styling.
    """
    init_users_csv()

    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; padding: 12px 18px; border-radius: 50%; background: linear-gradient(135deg, #10B981, #06B6D4); margin-bottom: 12px; box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);">
                <span style="font-size: 32px;">🎯</span>
            </div>
            <h1 style="color: #FFFFFF; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px; letter-spacing: -0.5px;">
                Attend-Wise
            </h1>
            <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0;">
                Smart Attendance & Predictive Optimizer for College Students
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create New Account"])

        # ------------------ LOGIN TAB ------------------
        with tab_login:
            st.markdown("<p style='color: #CBD5E1; font-size: 0.95rem; margin-bottom: 16px;'>Enter your credentials to access your predictive attendance dashboard.</p>", unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("👤 Username", placeholder="Enter your username", key="login_username")
                password = st.text_input("🔑 Password", type="password", placeholder="Enter your password", key="login_password")
                submit_login = st.form_submit_button("Sign In to Dashboard", use_container_width=True)

                if submit_login:
                    if not username or not password:
                        st.error("Please enter both username and password.")
                    else:
                        is_valid, user_data = check_login(username, password)
                        if is_valid:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = user_data["username"]
                            st.session_state["user_info"] = user_data
                            st.success(f"Welcome back, {user_data.get('full_name') or username}!")
                            st.rerun()
                        else:
                            st.error("Invalid Username or Password. Please try again or create an account.")

            # Quick Demo Hint
            st.markdown(
                """
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 12px; margin-top: 16px; font-size: 0.85rem; color: #94A3B8;">
                    💡 <b>Instant Demo Access:</b> Username: <code style="color: #38BDF8;">student</code> | Password: <code style="color: #38BDF8;">password123</code>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ------------------ REGISTRATION TAB ------------------
        with tab_register:
            st.markdown("<p style='color: #CBD5E1; font-size: 0.95rem; margin-bottom: 16px;'>Create your personal student profile to track semester attendance and safe bunk buffers.</p>", unsafe_allow_html=True)
            
            with st.form("register_form", clear_on_submit=True):
                full_name = st.text_input("📝 Full Name", placeholder="e.g., Alex Mercer")
                email = st.text_input("📧 College / Personal Email", placeholder="e.g., alex@college.edu")
                roll_number = st.text_input("🆔 Roll Number / Scholar ID", placeholder="e.g., 2026-CS-042")
                
                reg_username = st.text_input("👤 Choose Username", placeholder="e.g., alex_mercer")
                reg_password = st.text_input("🔑 Choose Password", type="password", placeholder="At least 4 characters")
                
                submit_reg = st.form_submit_button("Create Account", use_container_width=True)

                if submit_reg:
                    success, msg = register_user(full_name, email, roll_number, reg_username, reg_password)
                    if success:
                        st.success(f"✅ {msg}")
                        st.info("You can now switch to the 'Sign In' tab above to log in.")
                    else:
                        st.error(f"❌ {msg}")
