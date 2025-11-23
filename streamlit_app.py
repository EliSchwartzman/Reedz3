import streamlit as st
from models import User
from auth import hash_password, authenticate, is_admin
import supabase_db
from betting import create_bet, close_bet, resolve_bet, place_prediction, get_bet_overview
from scoring import distribute_reedz_on_resolution
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re

load_dotenv()
ADMIN_CODE = os.getenv("ADMIN_CODE")
st.set_page_config(page_title="Reedz Betting", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "home"

def auth_panel():
    st.header("Reedz: Login / Register")
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Reset Password"])
    # Login
    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type='password', key="login_password")
        if st.button("Login"):
            user = authenticate(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Logged in as {user.username}, role {user.role}")
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Login failed")
    # Register
    with tab2:
        username = st.text_input("New Username", key="reg_username")
        password = st.text_input("New Password", type='password', key="reg_password")
        email = st.text_input("Email", key="reg_email")
        role = st.selectbox("Role", ["Member", "Admin"], key="reg_role")
        admin_code = ""
        if role == "Admin":
            admin_code = st.text_input("Admin Verification Code", type="password", key="reg_code")
            if st.button("Register"):
                if not username.strip() or not password or not email.strip():
                    st.error("Username, password, and email are required and cannot be blank.")
                elif not re.match(r'^[A-Za-z0-9]+$', username):
                    st.error("Username must contain only letters and numbers—no spaces or special characters allowed.")
                elif role == "Admin" and admin_code != ADMIN_CODE:
                    st.error("Incorrect admin verification code.")
                elif role not in ["Admin", "Member"]:
                    st.error("Role must be Admin or Member.")
                else:
                    hashed = hash_password(password)
                    u = User(user_id=None, username=username.strip(), password=hashed, email=email.strip(), reedz_balance=0, role=role, created_at=datetime.now())
                    try:
                        supabase_db.create_user(u)
                        st.success("Registration successful. Please login.")
                    except Exception as e:
                        msg = str(e)
                        if "unique" in msg.lower() or "already exists" in msg.lower():
                            st.error("Username or email already exists. Try again with different values.")
                        elif "null" in msg.lower() or "not-null" in msg.lower():
                            st.error("Fields cannot be null.")
                        else:
                            st.error(f"Failed to register: {e}")
    # Password reset
    with tab3:
        email = st.text_input("Enter your email address (for reset)", key="reset_email")
        new_password = st.text_input("Enter your new password", type='password', key="reset_new")
        confirm_password = st.text_input("Confirm new password", type='password', key="reset_confirm")
        if st.button("Reset Password"):
            found_user = supabase_db.get_user_by_email(email)
            if not found_user:
                st.error("No user found for this email.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                hashed = hash_password(new_password)
                ok = supabase_db.update_user_password(found_user.user_id, hashed)
                if ok:
                    st.success("Password reset. You may login.")
                else:
                    st.error("Password reset failed.")

def leaderboard_panel():
    st.header("Leaderboard")
    leaderboard = supabase_db.get_leaderboard()
    if leaderboard:
        st.table([
            {"Rank": idx + 1, "Username": entry["username"], "Reedz": entry["reedz_balance"]}
            for idx, entry in enumerate(leaderboard)
        ])
    else:
        st.info("No users found.")

def bets_panel():
    st.header("All Bets Overview")
    open_bets = get_bet_overview("open")
    closed_bets = get_bet_overview("closed")
    resolved_bets = get_bet_overview("resolved")
    with st.expander("Open Bets", expanded=True):
        if open_bets:
            for bet in open_bets:
                st.write(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
        else:
            st.info("No open bets.")
    with st.expander("Closed Bets"):
        if closed_bets:
            for bet in closed_bets:
                st.write(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
        else:
            st.info("No closed bets.")
    with st.expander("Resolved Bets"):
        if resolved_bets:
            for bet in resolved_bets:
                ans_str = f", Answer: {bet['correct_answer']}" if bet.get('correct_answer') else ""
                st.write(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}{ans_str}")
        else:
            st.info("No resolved bets.")

def predictions_panel():
    st.header("View Predictions for a Bet")
    all_bets = get_bet_overview("")
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in all_bets}
    opt = st.selectbox("Select a bet", list(bet_titles.keys()))
    bet_id = bet_titles[opt]
    predictions = supabase_db.get_predictions_for_bet(bet_id)
    if predictions:
        data = []
        for pred in predictions:
            pred_user = supabase_db.get_user_by_username(pred.user_id)
            username = pred_user.username if pred_user else f"UserID {pred.user_id}"
            data.append({"User": username, "Prediction": pred.prediction})
        st.table(data)
    else:
        st.info("No predictions for this bet.")

def create_bet_panel(user):
    st.header("Create a Bet")
    title = st.text_input("Bet Title")
    description = st.text_area("Bet Description")
    answer_type = st.selectbox("Answer Type", ["number", "text"])
    close_days = st.number_input("Days until bet closes", min_value=1, max_value=30, value=1)
    if st.button("Create Bet"):
        close_at = datetime.now() + timedelta(days=close_days)
        try:
            create_bet(user, title, description, answer_type, close_at)
            st.success("Bet created.")
        except Exception as e:
            st.error(f"Failed to create bet: {e}")

def place_prediction_panel(user):
    st.header("Place Prediction")
    open_bets = get_bet_overview("open")
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in open_bets}
    if not bet_titles:
        st.info("No open bets for prediction.")
        return
    opt = st.selectbox("Select bet to predict on", list(bet_titles.keys()))
    bet_id = bet_titles[opt]
    pred_val = st.text_input("Your Prediction (number or text)")
    if st.button("Place Prediction"):
        try:
            place_prediction(user, bet_id, pred_val)
            st.success("Prediction placed.")
        except Exception as e:
            st.error(str(e))

def close_bet_panel(user):
    st.header("Close Bet")
    open_bets = get_bet_overview("open")
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in open_bets}
    if not bet_titles:
        st.info("No open bets to close.")
        return
    opt = st.selectbox("Select bet to close", list(bet_titles.keys()))
    bet_id = bet_titles[opt]
    if st.button("Close Bet"):
        try:
            close_bet(user, bet_id)
            st.success("Bet closed.")
        except Exception as e:
            st.error(str(e))

def resolve_bet_panel(user):
    st.header("Resolve Bet")
    closed_bets = get_bet_overview("closed")
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in closed_bets}
    if not bet_titles:
        st.info("No bets available to resolve.")
        return
    opt = st.selectbox("Select bet to resolve", list(bet_titles.keys()))
    bet_id = bet_titles[opt]
    answer = st.text_input("Correct Answer")
    if st.button("Resolve Bet"):
        try:
            resolve_bet(user, bet_id, answer)
            st.success("Bet resolved and Reedz distributed.")
        except Exception as e:
            st.error(str(e))

def user_management_panel():
    st.header("Admin: User Management")
    sub_menu = st.radio("Choose action", ["List users", "Promote/Demote", "Change Reedz", "Delete user"])
    if sub_menu == "List users":
        users = supabase_db.list_all_users()
        # Include email column here!
        user_rows = [
            {
                "UserID": u["user_id"], 
                "Username": u["username"], 
                "Email": u.get("email",""), 
                "Role": u["role"], 
                "Reedz": u["reedz_balance"]
            }
            for u in users
        ]
        st.table(user_rows)
    elif sub_menu == "Promote/Demote":
        users = supabase_db.list_all_users()
        user_map = {f"{u['username']} (ID {u['user_id']}) - {u['role']}": u['user_id'] for u in users}
        opt = st.selectbox("Pick user to modify", list(user_map.keys()))
        uid = user_map[opt]
        new_role = st.selectbox("New Role", ["Admin", "Member"])
        admin_code = ""
        if new_role == "Admin":
            admin_code = st.text_input("Admin Verification Code", type="password")
            if admin_code != ADMIN_CODE:
                st.error("Incorrect admin code.")
                return
        if st.button("Promote/Demote"):
            try:
                supabase_db.change_role(uid, new_role)
                st.success("Role updated.")
            except Exception as e:
                st.error(str(e))
    elif sub_menu == "Change Reedz":
        users = supabase_db.list_all_users()
        user_map = {f"{u['username']} (ID {u['user_id']}) - {u['reedz_balance']} Reedz": u for u in users}
        opt = st.selectbox("Pick user", list(user_map.keys()))
        uid = user_map[opt]['user_id']
        reedz = st.number_input("New Reedz balance", min_value=0, value=user_map[opt]['reedz_balance'])
        if st.button("Update Reedz"):
            delta = reedz - user_map[opt]['reedz_balance']
            try:
                supabase_db.add_reedz(uid, delta)
                st.success("Reedz updated.")
            except Exception as e:
                st.error(str(e))
    elif sub_menu == "Delete user":
        users = supabase_db.list_all_users()
        user_map = {f"{u['username']} (ID {u['user_id']})": u['user_id'] for u in users}
        opt = st.selectbox("Pick user to delete", list(user_map.keys()))
        uid = user_map[opt]
        if st.button("Confirm Delete"):
            try:
                supabase_db.delete_user(uid)
                st.success("User deleted.")
            except Exception as e:
                st.error(str(e))

def main_panel():
    user = st.session_state.user
    st.sidebar.write(f"Logged in as: {user.username}, Role: {user.role}, Reedz: {user.reedz_balance}")
    st.sidebar.write(" ")
    pages = ["Leaderboard", "All Bets", "Place Prediction", "View Predictions for a Bet"]
    if is_admin(user):
        pages = ["Create Bet", "Close Bet", "Resolve Bet", "User Management"] + pages
    page = st.sidebar.radio("Navigation", pages)
    if is_admin(user) and page == "Create Bet":
        create_bet_panel(user)
    elif is_admin(user) and page == "Close Bet":
        close_bet_panel(user)
    elif is_admin(user) and page == "Resolve Bet":
        resolve_bet_panel(user)
    elif is_admin(user) and page == "User Management":
        user_management_panel()
    elif page == "Leaderboard":
        leaderboard_panel()
    elif page == "All Bets":
        bets_panel()
    elif page == "Place Prediction":
        place_prediction_panel(user)
    elif page == "View Predictions for a Bet":
        predictions_panel()
    st.sidebar.write("")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "home"
        st.success("Logged out. Please log in/register again.")
        st.rerun()

def run_app():
    if st.session_state.user is None:
        auth_panel()
    else:
        main_panel()

if __name__ == "__main__" or st._is_running_with_streamlit:
    run_app()
