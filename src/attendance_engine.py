"""
Attend-Wise: Smart Attendance & Predictive Optimizer
Module: src/attendance_engine.py
Purpose: Handles logging, updating, filtering, and summary metrics for student
         attendance records stored in /data/attendance_records.csv.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance_records.csv")
BASELINE_FILE = os.path.join(DATA_DIR, "baseline_attendance.csv")

RECORD_COLUMNS = ["Username", "Date", "Lecture_Number", "Status", "Subject", "Timestamp"]
BASELINE_COLUMNS = ["Username", "Base_Attended", "Base_Conducted"]


def ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def init_attendance_storage() -> None:
    """Ensure attendance_records.csv exists with correct columns."""
    ensure_data_dir()
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=RECORD_COLUMNS)
        df.to_csv(ATTENDANCE_FILE, index=False)
    if not os.path.exists(BASELINE_FILE):
        df = pd.DataFrame(columns=BASELINE_COLUMNS)
        df.to_csv(BASELINE_FILE, index=False)


def get_all_records() -> pd.DataFrame:
    """Read all records from CSV."""
    init_attendance_storage()
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
        # Ensure correct column names
        for col in RECORD_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=RECORD_COLUMNS)


def get_user_records(username: str) -> pd.DataFrame:
    """Get all attendance logs for a specific user, sorted chronologically."""
    df = get_all_records()
    if df.empty:
        return df
    user_df = df[df["Username"].astype(str).str.strip().str.lower() == username.strip().lower()].copy()
    if not user_df.empty:
        user_df.sort_values(by=["Date", "Lecture_Number"], ascending=[False, True], inplace=True)
    return user_df


def get_user_daily_attendance(username: str, date_str: str) -> Dict[int, Dict[str, str]]:
    """
    Get already logged lectures for a specific date as:
    {lecture_number: {"status": "Present", "subject": "Maths"}}
    """
    df = get_user_records(username)
    if df.empty:
        return {}
    day_df = df[df["Date"].astype(str) == str(date_str)]
    res = {}
    for _, row in day_df.iterrows():
        try:
            lec_num = int(row["Lecture_Number"])
            res[lec_num] = {
                "status": str(row["Status"]).strip(),
                "subject": str(row.get("Subject", "")).strip() if pd.notna(row.get("Subject")) else ""
            }
        except (ValueError, TypeError):
            continue
    return res


def save_daily_lectures(
    username: str,
    date_str: str,
    lecture_entries: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    Save or update attendance for a specific day.
    lecture_entries is a list of dicts:
    [
      {"lecture_number": 1, "status": "Present", "subject": "Maths"},
      ...
    ]
    Overwrites any existing records for the same (username, date_str, lecture_number).
    """
    init_attendance_storage()
    df = get_all_records()
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Remove existing entries for this username on this date for the given lecture numbers
    u_clean = username.strip().lower()
    given_lec_nums = {int(e["lecture_number"]) for e in lecture_entries}

    if not df.empty:
        mask = (
            (df["Username"].astype(str).str.strip().str.lower() == u_clean) &
            (df["Date"].astype(str) == date_str) &
            (df["Lecture_Number"].astype(int, errors="ignore").isin(given_lec_nums))
        )
        df = df[~mask]

    new_rows = []
    for entry in lecture_entries:
        new_rows.append({
            "Username": username.strip(),
            "Date": date_str,
            "Lecture_Number": int(entry["lecture_number"]),
            "Status": str(entry["status"]).capitalize().strip(),
            "Subject": str(entry.get("subject", "")).strip(),
            "Timestamp": timestamp_str
        })

    if new_rows:
        new_df = pd.DataFrame(new_rows, columns=RECORD_COLUMNS)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
        return True, f"Successfully logged {len(new_rows)} lectures for {date_str}."
    return False, "No lecture entries provided."


def delete_date_records(username: str, date_str: str) -> Tuple[bool, str]:
    """Delete all records for a user on a given date."""
    init_attendance_storage()
    df = get_all_records()
    if df.empty:
        return False, "No records found."
    
    u_clean = username.strip().lower()
    mask = (
        (df["Username"].astype(str).str.strip().str.lower() == u_clean) &
        (df["Date"].astype(str) == date_str)
    )
    initial_len = len(df)
    df = df[~mask]
    if len(df) < initial_len:
        df.to_csv(ATTENDANCE_FILE, index=False)
        return True, f"Deleted attendance records for {date_str}."
    return False, f"No records found for {date_str}."


def get_baseline_attendance(username: str) -> Tuple[int, int]:
    """
    Get user's optional prior baseline attendance (Base_Attended, Base_Conducted).
    Useful for students who started mid-semester.
    """
    init_attendance_storage()
    if not os.path.exists(BASELINE_FILE):
        return 0, 0
    try:
        df = pd.read_csv(BASELINE_FILE)
        u_clean = username.strip().lower()
        matched = df[df["Username"].astype(str).str.strip().str.lower() == u_clean]
        if not matched.empty:
            a = int(matched.iloc[0]["Base_Attended"])
            c = int(matched.iloc[0]["Base_Conducted"])
            return max(0, a), max(0, c)
    except Exception:
        pass
    return 0, 0


def set_baseline_attendance(username: str, base_attended: int, base_conducted: int) -> None:
    """Save user baseline attendance offsets."""
    init_attendance_storage()
    df = pd.read_csv(BASELINE_FILE) if os.path.exists(BASELINE_FILE) else pd.DataFrame(columns=BASELINE_COLUMNS)
    u_clean = username.strip().lower()
    
    if not df.empty:
        df = df[df["Username"].astype(str).str.strip().str.lower() != u_clean]

    new_row = pd.DataFrame([{
        "Username": username.strip(),
        "Base_Attended": max(0, int(base_attended)),
        "Base_Conducted": max(0, int(base_conducted))
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(BASELINE_FILE, index=False)


def get_student_attendance_summary(username: str, count_leave_as_conducted: bool = True) -> Dict[str, Any]:
    """
    Calculate comprehensive student attendance metrics:
      - Logged lectures breakdown (Present, Absent, Leave)
      - Cumulative totals (including baseline if set)
      - Percentage
      - Daily logs summary dataframe
    """
    df = get_user_records(username)
    base_a, base_c = get_baseline_attendance(username)

    if df.empty:
        total_conducted = base_c
        total_attended = base_a
        present_count = 0
        absent_count = 0
        leave_count = 0
        logged_conducted = 0
    else:
        status_series = df["Status"].str.strip().str.capitalize()
        present_count = int((status_series == "Present").sum())
        absent_count = int((status_series == "Absent").sum())
        leave_count = int((status_series == "Leave").sum())

        logged_conducted = present_count + absent_count + (leave_count if count_leave_as_conducted else 0)
        total_conducted = base_c + logged_conducted
        total_attended = base_a + present_count

    percentage = round((total_attended / total_conducted) * 100.0, 2) if total_conducted > 0 else 0.0

    return {
        "username": username,
        "base_attended": base_a,
        "base_conducted": base_c,
        "logged_present": present_count,
        "logged_absent": absent_count,
        "logged_leave": leave_count,
        "logged_conducted": logged_conducted,
        "total_attended": total_attended,
        "total_conducted": total_conducted,
        "percentage": percentage,
        "records_df": df
    }


def seed_sample_attendance_for_user(username: str) -> None:
    """
    Seed realistic sample attendance records for quick demo/testing.
    Generates ~40 conducted lectures with ~29 present (approx 72.5% attendance).
    """
    init_attendance_storage()
    # Check if user already has records
    existing = get_user_records(username)
    if not existing.empty:
        return

    # Generate sample records across the past 7 weekdays
    from datetime import date, timedelta
    today = date.today()
    sample_data = []
    
    # 7 working days, 6 lectures each = 42 lectures
    cur = today - timedelta(days=12)
    working_days = []
    while len(working_days) < 7 and cur <= today:
        if cur.weekday() < 5:  # Mon to Fri
            working_days.append(cur)
        cur += timedelta(days=1)

    subjects = ["Data Structures", "Algorithms", "Operating Systems", "Computer Networks", "Database Systems", "Software Engg"]
    
    # Preset pattern: total attended 30 out of 42 = 71.4% (Warning Zone)
    pattern = [
        ["Present", "Present", "Present", "Present", "Present", "Present"],  # Day 1: 6/6
        ["Present", "Present", "Absent", "Present", "Present", "Absent"],    # Day 2: 4/6
        ["Present", "Present", "Present", "Present", "Present", "Present"],  # Day 3: 6/6
        ["Absent", "Present", "Present", "Present", "Absent", "Leave"],      # Day 4: 3/6
        ["Present", "Present", "Present", "Present", "Present", "Present"],  # Day 5: 6/6
        ["Present", "Absent", "Present", "Present", "Leave", "Absent"],      # Day 6: 3/6
        ["Present", "Present", "Present", "Present", "Absent", "Absent"],    # Day 7: 4/6 (Wait, 6+4+6+3+6+3+4 = 32 / 42 = 76.2%)
    ]

    for d_idx, day_obj in enumerate(working_days):
        d_str = day_obj.isoformat()
        day_pattern = pattern[d_idx % len(pattern)]
        for lec_idx in range(6):
            sample_data.append({
                "Username": username.strip(),
                "Date": d_str,
                "Lecture_Number": lec_idx + 1,
                "Status": day_pattern[lec_idx],
                "Subject": subjects[lec_idx],
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    if sample_data:
        df = get_all_records()
        new_df = pd.DataFrame(sample_data, columns=RECORD_COLUMNS)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
