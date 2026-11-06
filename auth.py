"""
Attend-Wise: Root Compatibility Bridge
Re-exports src.auth for seamless backward compatibility.
All core authentication logic is centralized in src/auth.py.
"""

from src.auth import (
    make_hashes,
    init_users_csv,
    get_all_users,
    check_login,
    register_user,
    logout_user,
    render_auth_ui
)

# Backward-compatibility alias
login_ui = render_auth_ui
