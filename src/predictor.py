"""
Attend-Wise: Smart Attendance & Predictive Optimizer
Module: src/predictor.py
Purpose: Core algebraic prediction engine for exact recovery lectures
         and safe bunk buffers using strict Ceil and Floor formulations.
"""

import math
from typing import Dict, List, Any


def calculate_percentage(attended: int, conducted: int) -> float:
    """
    Calculate the attendance percentage rounded to 2 decimal places.
    If no lectures have been conducted (C = 0), returns 0.0.
    """
    if conducted <= 0:
        return 0.0
    return round((attended / conducted) * 100.0, 2)


def recovery_prediction(attended: int, conducted: int, target_percent: float) -> int:
    """
    Recovery Prediction Formula (When Current Attendance % < Target T%):
    Formula: x = Ceil[ (T * C - 100 * A) / (100 - T) ]
    Where:
      A = Attended Lectures
      C = Conducted Lectures
      T = Target Percentage (e.g., 75.0)

    Uses math.ceil to guarantee strict eligibility compliance.
    Returns 0 if current attendance already meets or exceeds target.
    If target is 100% and any lecture was missed (A < C), returns -1 (impossible).
    """
    if target_percent <= 0:
        return 0
    if target_percent >= 100:
        if conducted == 0:
            return 0
        if attended >= conducted:
            return 0
        # Once a class is missed, 100% can never be mathematically reached
        return -1

    # If already at or above target, no recovery classes needed
    current_pct = calculate_percentage(attended, conducted)
    if conducted > 0 and current_pct >= target_percent:
        return 0

    numerator = (target_percent * conducted) - (100.0 * attended)
    denominator = 100.0 - target_percent

    if numerator <= 0:
        return 0

    x = math.ceil(numerator / denominator)
    return max(0, x)


def safe_bunk_buffer(attended: int, conducted: int, target_percent: float) -> int:
    """
    Safe Bunk Buffer Formula (When Current Attendance % >= Target T%):
    Formula: y = Floor[ (100 * A - T * C) / T ]
    Where:
      A = Attended Lectures
      C = Conducted Lectures
      T = Target Percentage (e.g., 75.0)

    Uses math.floor to ensure students do not cross below the detention risk line.
    Returns 0 if current attendance is below target.
    """
    if target_percent <= 0:
        return 999999  # Arbitrarily large safe buffer if target is 0%
    if conducted <= 0:
        return 0

    current_pct = calculate_percentage(attended, conducted)
    if current_pct < target_percent:
        return 0

    numerator = (100.0 * attended) - (target_percent * conducted)
    denominator = target_percent

    if numerator < 0:
        return 0

    y = math.floor(numerator / denominator)
    return max(0, y)


def get_status_zone(percentage: float) -> Dict[str, Any]:
    """
    Classify attendance percentage into standard color-coded warning zones:
      - Green (Safe Zone): >= 75.0%
      - Yellow (Warning Zone): 65.0% to 74.99%
      - Red (Critical Zone): < 65.0%
    """
    if percentage >= 75.0:
        return {
            "zone": "Green",
            "name": "Safe Zone",
            "color": "#10B981",          # Emerald Green
            "bg_color": "rgba(16, 185, 129, 0.12)",
            "border_color": "#10B981",
            "badge_icon": "🟢",
            "summary": "Eligible & Secure",
            "description": "Your attendance meets or exceeds university norms (75%+). Maintain your buffer!",
            "status_code": "SAFE"
        }
    elif percentage >= 65.0:
        return {
            "zone": "Yellow",
            "name": "Warning Zone",
            "color": "#F59E0B",          # Amber
            "bg_color": "rgba(245, 158, 11, 0.12)",
            "border_color": "#F59E0B",
            "badge_icon": "🟡",
            "summary": "Borderline / Medical Criteria",
            "description": "Attendance is between 65% and 75%. You risk exam debarment without condonation/medical certificates.",
            "status_code": "WARNING"
        }
    else:
        return {
            "zone": "Red",
            "name": "Critical Zone",
            "color": "#EF4444",          # Crimson Red
            "bg_color": "rgba(239, 68, 68, 0.12)",
            "border_color": "#EF4444",
            "badge_icon": "🔴",
            "summary": "Detention Risk",
            "description": "Attendance is below 65%. High risk of course detention! Immediate recovery plan needed.",
            "status_code": "CRITICAL"
        }


def get_multi_target_matrix(attended: int, conducted: int, targets: List[float] = None) -> List[Dict[str, Any]]:
    """
    Generate the multi-target plan selector matrix for benchmarks:
    Default targets: [50.0, 60.0, 70.0, 75.0, 85.0]
    """
    if targets is None:
        targets = [50.0, 60.0, 70.0, 75.0, 85.0]

    current_pct = calculate_percentage(attended, conducted)
    results = []

    for t in sorted(targets):
        is_achieved = (conducted > 0) and (current_pct >= t)
        
        if is_achieved:
            bunks = safe_bunk_buffer(attended, conducted, t)
            # Test percentage if student bunks 'bunks' lectures
            new_conducted = conducted + bunks
            projected_pct = calculate_percentage(attended, new_conducted) if new_conducted > 0 else current_pct
            action_text = f"Can safely bunk {bunks} lecture{'s' if bunks != 1 else ''}"
            recovery_needed = 0
            safe_bunks = bunks
        else:
            recovery = recovery_prediction(attended, conducted, t)
            if recovery == -1:
                action_text = "Target mathematically unreachable (100%)"
                projected_pct = current_pct
            else:
                new_attended = attended + recovery
                new_conducted = conducted + recovery
                projected_pct = calculate_percentage(new_attended, new_conducted) if new_conducted > 0 else current_pct
                action_text = f"Must attend {recovery} consecutive lecture{'s' if recovery != 1 else ''}"
            recovery_needed = recovery
            safe_bunks = 0

        diff = round(current_pct - t, 2)
        results.append({
            "target": t,
            "target_str": f"{int(t) if t.is_integer() else t}%",
            "is_achieved": is_achieved,
            "status": "Eligible" if is_achieved else "Shortage",
            "difference": diff,
            "recovery_needed": recovery_needed,
            "safe_bunks": safe_bunks,
            "action": action_text,
            "projected_percentage": projected_pct
        })

    return results


def simulate_scenario(attended: int, conducted: int, upcoming_leaves: int = 0, upcoming_extra: int = 0) -> Dict[str, Any]:
    """
    Simulate "What-If" scenarios:
      - upcoming_leaves: lectures conducted that student will miss
      - upcoming_extra: extra/upcoming lectures student will attend without missing
    """
    base_pct = calculate_percentage(attended, conducted)
    new_attended = attended + upcoming_extra
    new_conducted = conducted + upcoming_leaves + upcoming_extra

    new_pct = calculate_percentage(new_attended, new_conducted)
    delta = round(new_pct - base_pct, 2)
    old_zone = get_status_zone(base_pct)
    new_zone = get_status_zone(new_pct)

    return {
        "base_attended": attended,
        "base_conducted": conducted,
        "base_percentage": base_pct,
        "new_attended": new_attended,
        "new_conducted": new_conducted,
        "new_percentage": new_pct,
        "delta": delta,
        "old_zone": old_zone,
        "new_zone": new_zone,
        "recovery_for_75": recovery_prediction(new_attended, new_conducted, 75.0),
        "safe_bunks_for_75": safe_bunk_buffer(new_attended, new_conducted, 75.0)
    }
