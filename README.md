# 🎯 Attend-Wise: Smart Attendance & Predictive Optimizer

A multi-user predictive attendance management and optimization system for college students built with **Python**, **Streamlit**, and **Pandas**. Attend-Wise replaces guesswork with exact algebraic models to compute required consecutive recovery classes and safe bunk buffers before exam debarment thresholds are breached.

---
## 🌐 Live Prototype & Access

* **Live Interactive Demo:** [Attend-Wise Web Application](https://attend-wise-smart-attendance-and-predictive-optimizer-d2xl6cw8.streamlit.app/)
* **Local Run:** `streamlit run app.py` (Localhost: `http://localhost:8501`)

## 📐 Mathematical & Prediction Engine (`src/predictor.py`)

Attend-Wise implements strict algebraic formulations without random heuristics or approximations:

### 1. Recovery Prediction (When Current Attendance % < Target $T\%$)
To determine the exact number of future consecutive lectures ($x$) a student must attend to reach or exceed target percentage $T$:

$$\frac{A + x}{C + x} \ge \frac{T}{100} \implies x = \left\lceil \frac{T \cdot C - 100 \cdot A}{100 - T} \right\rceil$$

Where:
- $A$ = Attended Lectures
- $C$ = Conducted Lectures
- $T$ = Target Percentage (e.g., $75\%$)
- Strict eligibility compliance is guaranteed using `math.ceil`.

### 2. Safe Bunk Buffer (When Current Attendance % $\ge$ Target $T\%$)
To determine the maximum number of future consecutive lectures ($y$) a student can safely miss without falling below target percentage $T$:

$$\frac{A}{C + y} \ge \frac{T}{100} \implies y = \left\lfloor \frac{100 \cdot A - T \cdot C}{T} \right\rfloor$$

- Strict detention avoidance is guaranteed using `math.floor`.

### 3. Color-Coded Warning Zones
- 🟢 **Safe Zone ($\ge 75\%$)**: Examination eligible. Safe bunk buffers active.
- 🟡 **Warning Zone ($65\% - 74.99\%$)**: Borderline / condonation criteria. Detention risk if classes are missed.
- 🔴 **Critical Zone ($< 65\%$)**: Serious shortage. Immediate attendance recovery mandate.

---

## 📁 Repository Structure

```text
Attendwise_project/
├── data/
│   ├── users.csv               # User profiles & SHA-256 hashed passwords
│   ├── attendance_records.csv  # Detailed student attendance logs
│   ├── holidays.csv            # Configurable college holidays & events
│   └── semester_settings.csv   # Semester timeline & timetable parameters
├── src/
│   ├── __init__.py
│   ├── auth.py                 # Multi-user registration, SHA-256 hashing & login
│   ├── calendar_engine.py      # Working days, weekend stripping & timetable (1-10/day)
│   ├── predictor.py            # Exact algebraic recovery & bunk buffer formulas
│   └── attendance_engine.py   # Daily logging, historical baselines & aggregation
├── app.py                      # Production Streamlit UI with custom CSS styling
├── test_suite.py               # Automated unit & integration test suite
├── requirements.txt            # Dependency requirements
└── README.md                   # Complete documentation & usage guide
```

---

## 🚀 Quick Setup & Execution

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
streamlit run app.py
```
The application will launch in your browser at `http://localhost:8501`.

---

## 🔑 Default Demo Accounts

You can register a new account on the registration tab, or sign in immediately using:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Demo Student** | `student` | `password123` | Pre-loaded with realistic attendance logs (~76%) |
| **Admin** | `admin` | `1234` | System administrator account |

---

## 🌟 Key Application Features

1. **Dashboard & Optimizer**:
   - Hero KPI cards for current attendance %, attended lectures, conducted lectures, and safe bunks/recovery classes.
   - Semester horizon projections: Maximum possible attendance cap (if 100% attended till semester end) and minimum attendance floor.

2. **Interactive Daily Lecture Logger**:
   - Date picker with automatic weekend and holiday alerts.
   - Quick one-click action buttons: **"Mark All Present"**, **"Mark All Absent"**, **"Mark All Leave"**.
   - Per-lecture period timings, status selector (`Present`, `Absent`, `Leave`), and subject tags.

3. **Multi-Target Plan Selector Matrix**:
   - Benchmarks matrix for **50%**, **60%**, **70%**, **75%**, and **85%**.
   - Displays exact margin, consecutive recovery needed, safe bunk allowances, and recommended actions.
   - Interactive custom target calculator for exploring any percentage (e.g. 80%, 90%).

4. **"What-If" Scenario Simulator**:
   - Dual interactive sliders to simulate upcoming leaves vs extra classes attended.
   - Real-time percentage delta ($\Delta$) and dynamic zone migration preview.

5. **Semester Calendar & Holiday Engine**:
   - Configurable semester start and end dates.
   - Timetable scale from 1 to 10 lectures/day.
   - Automatic exclusion of Saturdays and Sundays.
   - Add and remove custom college holidays.

6. **Historical Baseline & CSV Export**:
   - Support for mid-semester starters to input prior cumulative attendance without backfilling old dates.
   - Export full attendance history to CSV at any time.
