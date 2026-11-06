"""
Attend-Wise: Smart Attendance & Predictive Optimizer
Module: src/calendar_engine.py
Purpose: Handles date range selection, automatic Saturday-Sunday exclusion,
         custom holiday management, and daily lecture counts (1-10 per day).
"""

import os
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
HOLIDAYS_FILE = os.path.join(DATA_DIR, "holidays.csv")
SEMESTER_CONFIG_FILE = os.path.join(DATA_DIR, "semester_settings.csv")


def ensure_data_dir() -> None:
    """Ensure data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def init_holidays_storage() -> None:
    """Initialize holidays.csv if it does not exist."""
    ensure_data_dir()
    if not os.path.exists(HOLIDAYS_FILE):
        df = pd.DataFrame(columns=["Date", "Name", "Type"])
        # Seed with a few standard academic holidays
        sample_holidays = [
            {"Date": f"{date.today().year}-01-26", "Name": "Republic Day", "Type": "National"},
            {"Date": f"{date.today().year}-08-15", "Name": "Independence Day", "Type": "National"},
            {"Date": f"{date.today().year}-10-02", "Name": "Gandhi Jayanti", "Type": "National"},
            {"Date": f"{date.today().year}-12-25", "Name": "Christmas Day", "Type": "Festival"},
        ]
        df = pd.DataFrame(sample_holidays)
        df.to_csv(HOLIDAYS_FILE, index=False)


def get_all_holidays() -> pd.DataFrame:
    """Load all custom holidays from CSV."""
    init_holidays_storage()
    try:
        df = pd.read_csv(HOLIDAYS_FILE)
        if "Date" not in df.columns:
            df["Date"] = []
        if "Name" not in df.columns:
            df["Name"] = []
        if "Type" not in df.columns:
            df["Type"] = []
        return df
    except Exception:
        return pd.DataFrame(columns=["Date", "Name", "Type"])


def add_custom_holiday(holiday_date: date, name: str, holiday_type: str = "Custom") -> Tuple[bool, str]:
    """Add a new custom holiday."""
    init_holidays_storage()
    df = get_all_holidays()
    date_str = holiday_date.isoformat()
    
    if not df.empty and date_str in df["Date"].astype(str).values:
        return False, f"Holiday on {date_str} already exists ({name})."
    
    new_entry = pd.DataFrame([{"Date": date_str, "Name": name.strip(), "Type": holiday_type}])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(HOLIDAYS_FILE, index=False)
    return True, f"Holiday '{name}' on {date_str} added successfully."


def remove_custom_holiday(date_str: str) -> Tuple[bool, str]:
    """Remove a custom holiday by date string."""
    init_holidays_storage()
    df = get_all_holidays()
    if df.empty or date_str not in df["Date"].astype(str).values:
        return False, "Holiday date not found."
    
    df = df[df["Date"].astype(str) != date_str]
    df.to_csv(HOLIDAYS_FILE, index=False)
    return True, f"Holiday on {date_str} removed."


def get_custom_holiday_set() -> Set[date]:
    """Return a set of date objects for fast holiday lookup."""
    df = get_all_holidays()
    holidays_set = set()
    for d_val in df["Date"].dropna():
        try:
            holidays_set.add(datetime.strptime(str(d_val).strip(), "%Y-%m-%d").date())
        except (ValueError, TypeError):
            continue
    return holidays_set


class CalendarEngine:
    """
    Core semester calendar and working days calculation engine.
    """
    def __init__(
        self,
        start_date: date,
        end_date: date,
        daily_lectures: int = 6,
        custom_holidays: Optional[Set[date]] = None
    ):
        if end_date < start_date:
            raise ValueError("Semester end date cannot precede start date.")
        
        self.start_date = start_date
        self.end_date = end_date
        # Daily lectures strictly constrained between 1 and 10
        self.daily_lectures = max(1, min(10, int(daily_lectures)))
        self.custom_holidays = custom_holidays if custom_holidays is not None else get_custom_holiday_set()

    def is_weekend(self, target_date: date) -> bool:
        """Check if date is Saturday (5) or Sunday (6)."""
        return target_date.weekday() in (5, 6)

    def is_holiday(self, target_date: date) -> bool:
        """Check if date is in custom holidays set."""
        return target_date in self.custom_holidays

    def is_working_day(self, target_date: date) -> bool:
        """A working day is neither a weekend (Sat/Sun) nor a custom holiday."""
        return not self.is_weekend(target_date) and not self.is_holiday(target_date)

    def get_working_days(self, range_start: Optional[date] = None, range_end: Optional[date] = None) -> List[date]:
        """
        Return list of all academic working days between range_start and range_end (inclusive),
        automatically stripping Saturdays, Sundays, and custom holidays.
        """
        s = range_start or self.start_date
        e = range_end or self.end_date
        working_days = []
        cur = s
        while cur <= e:
            if self.is_working_day(cur):
                working_days.append(cur)
            cur += timedelta(days=1)
        return working_days

    def count_working_days(self, range_start: Optional[date] = None, range_end: Optional[date] = None) -> int:
        """Return the count of academic working days in the range."""
        return len(self.get_working_days(range_start, range_end))

    def get_semester_timeline(self, as_of_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculate complete semester statistics and forward projections:
          - Total academic days
          - Total scheduled lectures
          - Elapsed days and scheduled lectures up to as_of_date
          - Remaining days and scheduled lectures
        """
        ref_date = as_of_date or date.today()
        all_working_days = self.get_working_days(self.start_date, self.end_date)
        total_working_days = len(all_working_days)
        total_scheduled_lectures = total_working_days * self.daily_lectures

        # Elapsed working days (up to min(ref_date, end_date))
        if ref_date < self.start_date:
            elapsed_days = 0
        else:
            clamped_ref = min(ref_date, self.end_date)
            elapsed_days = len([d for d in all_working_days if d <= clamped_ref])

        elapsed_lectures = elapsed_days * self.daily_lectures
        remaining_days = max(0, total_working_days - elapsed_days)
        remaining_lectures = remaining_days * self.daily_lectures

        # Semester progress percentage
        progress_pct = round((elapsed_days / total_working_days) * 100.0, 1) if total_working_days > 0 else 0.0

        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "daily_lectures": self.daily_lectures,
            "total_working_days": total_working_days,
            "total_scheduled_lectures": total_scheduled_lectures,
            "elapsed_working_days": elapsed_days,
            "elapsed_scheduled_lectures": elapsed_lectures,
            "remaining_working_days": remaining_days,
            "remaining_lectures": remaining_lectures,
            "progress_percentage": progress_pct,
            "reference_date": ref_date
        }

    def generate_lecture_slots(self) -> List[Dict[str, str]]:
        """
        Generate default lecture schedule labels and timings for the daily lecture count (1 to 10).
        """
        default_times = [
            ("09:00 AM", "10:00 AM"),
            ("10:00 AM", "11:00 AM"),
            ("11:15 AM", "12:15 PM"),
            ("12:15 PM", "01:15 PM"),
            ("02:00 PM", "03:00 PM"),
            ("03:00 PM", "04:00 PM"),
            ("04:15 PM", "05:15 PM"),
            ("05:15 PM", "06:15 PM"),
            ("06:30 PM", "07:30 PM"),
            ("07:30 PM", "08:30 PM")
        ]
        
        slots = []
        for i in range(1, self.daily_lectures + 1):
            idx = i - 1
            start_t, end_t = default_times[idx] if idx < len(default_times) else (f"Slot {i}", f"End {i}")
            slots.append({
                "lecture_number": i,
                "label": f"Lecture {i}",
                "time_slot": f"{start_t} - {end_t}"
            })
        return slots


def save_user_semester_config(username: str, start_date_str: str, end_date_str: str, daily_lectures: int) -> None:
    """Save user-specific semester parameters to CSV."""
    ensure_data_dir()
    cols = ["Username", "Start_Date", "End_Date", "Daily_Lectures"]
    if os.path.exists(SEMESTER_CONFIG_FILE):
        try:
            df = pd.read_csv(SEMESTER_CONFIG_FILE)
        except Exception:
            df = pd.DataFrame(columns=cols)
    else:
        df = pd.DataFrame(columns=cols)

    # Clean / sanitize columns
    for col in cols:
        if col not in df.columns:
            df[col] = []

    # Update or insert
    df = df[df["Username"] != username]
    new_row = pd.DataFrame([{
        "Username": username,
        "Start_Date": start_date_str,
        "End_Date": end_date_str,
        "Daily_Lectures": max(1, min(10, int(daily_lectures)))
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(SEMESTER_CONFIG_FILE, index=False)


def load_user_semester_config(username: str) -> Dict[str, Any]:
    """Load user-specific semester parameters or return sensible defaults."""
    ensure_data_dir()
    today = date.today()
    default_start = today.replace(month=max(1, today.month - 2), day=1) if today.month > 2 else today.replace(month=1, day=1)
    default_end = default_start + timedelta(days=120)
    
    defaults = {
        "start_date": default_start,
        "end_date": default_end,
        "daily_lectures": 6
    }
    
    if not os.path.exists(SEMESTER_CONFIG_FILE):
        return defaults

    try:
        df = pd.read_csv(SEMESTER_CONFIG_FILE)
        user_row = df[df["Username"] == username]
        if not user_row.empty:
            row = user_row.iloc[0]
            s_date = datetime.strptime(str(row["Start_Date"]), "%Y-%m-%d").date()
            e_date = datetime.strptime(str(row["End_Date"]), "%Y-%m-%d").date()
            d_lectures = int(row["Daily_Lectures"])
            return {
                "start_date": s_date,
                "end_date": e_date,
                "daily_lectures": max(1, min(10, d_lectures))
            }
    except Exception:
        pass
    
    return defaults
