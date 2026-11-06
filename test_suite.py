"""
Attend-Wise Verification & Test Suite
"""

import sys
import math
from datetime import date

def test_predictor():
    print("Testing src.predictor...")
    from src.predictor import (
        calculate_percentage,
        recovery_prediction,
        safe_bunk_buffer,
        get_status_zone,
        get_multi_target_matrix,
        simulate_scenario
    )

    # Test 1: Percentages
    assert calculate_percentage(0, 0) == 0.0
    assert calculate_percentage(18, 24) == 75.0
    assert calculate_percentage(28, 40) == 70.0
    assert calculate_percentage(32, 40) == 80.0

    # Test 2: Recovery Formula: x = Ceil[(T * C - 100 * A) / (100 - T)]
    # C = 40, A = 28 (70%), Target T = 75%:
    # num = 75 * 40 - 100 * 28 = 3000 - 2800 = 200
    # den = 100 - 75 = 25
    # x = Ceil[200 / 25] = 8
    rec = recovery_prediction(28, 40, 75.0)
    assert rec == 8, f"Expected 8, got {rec}"
    # Verify that attending 8 makes it >= 75%: (28+8)/(40+8) = 36/48 = 0.75 (75.0%)
    assert calculate_percentage(28 + rec, 40 + rec) >= 75.0
    # Verify that attending 7 makes it < 75%: (28+7)/(40+7) = 35/47 = 74.47%
    assert calculate_percentage(28 + rec - 1, 40 + rec - 1) < 75.0

    # Test 3: Safe Bunk Buffer Formula: y = Floor[(100 * A - T * C) / T]
    # C = 40, A = 32 (80%), Target T = 75%:
    # num = 100 * 32 - 75 * 40 = 3200 - 3000 = 200
    # den = 75
    # y = Floor[200 / 75] = 2
    bunk = safe_bunk_buffer(32, 40, 75.0)
    assert bunk == 2, f"Expected 2, got {bunk}"
    # Verify that bunking 2 keeps it >= 75%: 32 / (40+2) = 32/42 = 76.19% >= 75%
    assert calculate_percentage(32, 40 + bunk) >= 75.0
    # Verify that bunking 3 drops it < 75%: 32 / (40+3) = 32/43 = 74.42% < 75%
    assert calculate_percentage(32, 40 + bunk + 1) < 75.0

    # Test 4: Status Zones
    assert get_status_zone(80.0)["zone"] == "Green"
    assert get_status_zone(75.0)["zone"] == "Green"
    assert get_status_zone(74.9)["zone"] == "Yellow"
    assert get_status_zone(65.0)["zone"] == "Yellow"
    assert get_status_zone(64.9)["zone"] == "Red"
    assert get_status_zone(50.0)["zone"] == "Red"

    # Test 5: Multi-target matrix targets: [50, 60, 70, 75, 85]
    matrix = get_multi_target_matrix(28, 40)
    targets_found = [m["target"] for m in matrix]
    assert targets_found == [50.0, 60.0, 70.0, 75.0, 85.0]

    # Test 6: Simulator
    sim = simulate_scenario(28, 40, upcoming_leaves=2, upcoming_extra=6)
    # A' = 28 + 6 = 34, C' = 40 + 2 + 6 = 48 -> 34/48 = 70.83%
    assert sim["new_attended"] == 34
    assert sim["new_conducted"] == 48
    assert sim["new_percentage"] == 70.83

    print("✅ src.predictor passed all tests!")


def test_calendar():
    print("Testing src.calendar_engine...")
    from src.calendar_engine import CalendarEngine, add_custom_holiday, remove_custom_holiday

    # Test weekend stripping
    eng = CalendarEngine(date(2026, 11, 2), date(2026, 11, 8), daily_lectures=5)
    # Nov 2 (Mon) to Nov 8 (Sun) 2026: Mon, Tue, Wed, Thu, Fri = 5 days, Sat and Sun excluded
    working_days = eng.get_working_days()
    assert len(working_days) == 5, f"Expected 5 working days, got {len(working_days)}"
    for d in working_days:
        assert d.weekday() < 5, f"Date {d} is a weekend day!"

    # Test custom holiday
    test_h_date = date(2026, 11, 4) # Wednesday
    add_custom_holiday(test_h_date, "Test College Day", "College Event")
    eng_with_h = CalendarEngine(date(2026, 11, 2), date(2026, 11, 8), daily_lectures=5)
    working_days_h = eng_with_h.get_working_days()
    assert len(working_days_h) == 4, f"Expected 4 working days with holiday, got {len(working_days_h)}"
    remove_custom_holiday(test_h_date.isoformat())

    # Test daily lectures constraint 1 to 10
    eng_low = CalendarEngine(date(2026, 11, 2), date(2026, 11, 6), daily_lectures=0)
    assert eng_low.daily_lectures == 1
    eng_high = CalendarEngine(date(2026, 11, 2), date(2026, 11, 6), daily_lectures=15)
    assert eng_high.daily_lectures == 10

    print("✅ src.calendar_engine passed all tests!")


def test_auth_and_storage():
    print("Testing src.auth and data storage...")
    from src.auth import init_users_csv, get_all_users, register_user, check_login
    init_users_csv()
    users_df = get_all_users()
    assert "Full Name" in users_df.columns
    assert "Email" in users_df.columns
    assert "Roll Number" in users_df.columns
    assert "Username" in users_df.columns
    assert "Password_Hash" in users_df.columns

    # Test registration of a test user
    test_u = "test_student_xyz"
    test_p = "secure_pass_123"
    reg_ok, msg = register_user("Test Student", "test@college.edu", "ROLL-999", test_u, test_p)
    assert reg_ok, f"Registration failed: {msg}"

    # Verify duplicate prevention
    dup_ok, dup_msg = register_user("Test Student 2", "test2@college.edu", "ROLL-998", test_u, "other_pass")
    assert not dup_ok, "Duplicate username registration should fail!"

    # Verify login
    login_ok, u_data = check_login(test_u, test_p)
    assert login_ok, "Login verification failed!"
    assert u_data["full_name"] == "Test Student"

    # Verify wrong password fails
    wrong_ok, _ = check_login(test_u, "wrong_password")
    assert not wrong_ok, "Wrong password should not authenticate!"

    print("✅ src.auth and data storage passed all tests!")


def test_attendance():
    print("Testing src.attendance_engine...")
    from src.attendance_engine import (
        save_daily_lectures,
        get_user_records,
        get_student_attendance_summary,
        delete_date_records
    )
    test_u = "test_student_xyz"
    test_d = "2026-11-03"

    entries = [
        {"lecture_number": 1, "status": "Present", "subject": "Maths"},
        {"lecture_number": 2, "status": "Present", "subject": "Physics"},
        {"lecture_number": 3, "status": "Absent", "subject": "Chemistry"},
        {"lecture_number": 4, "status": "Present", "subject": "Programming"},
    ]
    ok, msg = save_daily_lectures(test_u, test_d, entries)
    assert ok, f"Save daily failed: {msg}"

    recs = get_user_records(test_u)
    assert len(recs) == 4

    summary = get_student_attendance_summary(test_u)
    assert summary["total_conducted"] == 4
    assert summary["total_attended"] == 3
    assert summary["percentage"] == 75.0

    # Clean up
    delete_date_records(test_u, test_d)
    print("✅ src.attendance_engine passed all tests!")

if __name__ == "__main__":
    test_predictor()
    test_calendar()
    test_auth_and_storage()
    test_attendance()
    print("\n🎉 ALL UNIT AND INTEGRATION TESTS PASSED SUCCESSFULLY!")
