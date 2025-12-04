import streamlit as st
import re
from models import User
from auth import hash_password, authenticate, is_admin
import supabase_db
from betting import create_bet, close_bet, resolve_bet, place_prediction, get_bet_overview
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import time_utils  # ADD THIS LINE
import os
from dotenv import load_dotenv
import random
import string
from email_sender import send_password_reset_email

load_dotenv()


load_dotenv() # Load environment variables from .env file
ADMIN_CODE = os.getenv("ADMIN_CODE") # Admin verification code from environment variables

st.set_page_config(page_title="Reedz Betting", layout="wide") # Set Streamlit page configuration

# Initalize session state variables for the user and home page which are used to track login status and the current page
if "user" not in st.session_state: 
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "home"

# Generates a random numeric reset code of length 6
def generate_reset_code(length=6): 
    return ''.join(random.choices(string.digits, k=length)) 
# Generates a random password reset code
def set_reset_code_for_email(email):
    code = generate_reset_code()
    expiry = datetime.now() + timedelta(minutes=5) # Code will expire in 5 minutes
    supabase_db.set_user_reset_code(email, code, expiry) # Store the reset code in the database and its expiration time
    success, error_msg = send_password_reset_email(email, code) # Send the reset code via email
    return success, error_msg 

# Renders the authentication panel for login, registration, and password reset
# This is the first page the user sees when the load the webpage if they are not already logged in
def auth_panel():
    st.title("Reedz Betting")
    st.divider()
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Reset Password"])

    with tab1:
        st.subheader("Login")
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.success(f"Logged in as {user.username} ({user.role})")
                    st.session_state.page = "main"
                    st.rerun()
                else:
                    st.error("Login failed")

    with tab2:
        st.subheader("Register")
        with st.form("register_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("New Username")
                password = st.text_input("New Password", type="password")
            with col2:
                email = st.text_input("Email")
                role = st.selectbox("Role", ["Member", "Admin"])
            admin_code = ""
            if role == "Admin":
                admin_code = st.text_input("Admin Verification Code", type="password")
            reg_button = st.form_submit_button("Register", use_container_width=True)
            if reg_button:
                if not username.strip() or not password or not email.strip():
                    st.error("All fields are required.")
                elif not re.match(r'^[A-Za-z0-9]+$', username):
                    st.error("Username must be letters/numbers only with no spaces.")
                elif role == "Admin" and admin_code != ADMIN_CODE:
                    st.error("Incorrect admin verification code.")
                elif role not in ["Admin", "Member"]:
                    st.error("Role must be Admin or Member.")
                else:
                    hashed = hash_password(password)
                    u = User(
                        user_id=None,
                        username=username.strip(),
                        password=hashed,
                        email=email.strip(),
                        reedz_balance=0,
                        role=role,
                        created_at=datetime.now()
                    )
                    try:
                        supabase_db.create_user(u)
                        st.success("Registration successful! Please log in.")
                    except Exception as e:
                        msg = str(e)
                        if "unique" in msg.lower() or "already exists" in msg.lower():
                            st.error("Username or email already exists.")
                        elif "null" in msg.lower() or "not-null" in msg.lower() or "empty" in msg.lower():
                            st.error("All fields must be non-null/non-empty.")
                        else:
                            st.error(f"Failed to register: {e}")

    with tab3:
        st.subheader("Password Reset")
        if "sent_reset_email" not in st.session_state:
            st.session_state["sent_reset_email"] = False
            st.session_state["reset_email_val"] = ""
            st.session_state["reset_code_sent_to"] = ""
        with st.form("reset_form", clear_on_submit=False):
            email = st.text_input("Enter your email address", value=st.session_state.get("reset_email_val", ""))
            send_code_clicked = st.form_submit_button("Send Reset Code")
            if send_code_clicked:
                found_user = supabase_db.get_user_by_email(email)
                if not found_user:
                    st.error("No user found for this email.")
                    st.session_state["sent_reset_email"] = False
                else:
                    success, error_msg = set_reset_code_for_email(email)
                    if success:
                        st.session_state["sent_reset_email"] = True
                        st.session_state["reset_email_val"] = email
                        st.session_state["reset_code_sent_to"] = email
                        st.success("A reset code has been sent to your email.")
                    else:
                        st.session_state["sent_reset_email"] = False
                        st.error(f"Failed to send reset email: {error_msg}")

        if st.session_state["sent_reset_email"]:
            with st.form("change_pw_form", clear_on_submit=False):
                code = st.text_input("Enter reset code from email", max_chars=6)
                new_password = st.text_input("Enter your new password", type="password", key="reset_new")
                confirm_password = st.text_input("Confirm new password", type="password", key="reset_confirm")
                col1, col2 = st.columns(2)
                change_pw = col1.form_submit_button("Change My Password")
                cancel = col2.form_submit_button("Cancel & Start Over")
                if change_pw:
                    if not new_password or not confirm_password:
                        st.error("Please enter your new password twice.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif not supabase_db.check_reset_code(st.session_state["reset_email_val"], code):
                        st.error("Invalid or expired reset code.")
                    else:
                        hashed = hash_password(new_password)
                        ok = supabase_db.update_user_password_by_email(st.session_state["reset_email_val"], hashed)
                        supabase_db.clear_reset_code(st.session_state["reset_email_val"])
                        if ok:
                            st.success("Password reset successful. You may now log in.")
                            st.session_state["sent_reset_email"] = False
                            st.session_state["reset_email_val"] = ""
                            st.session_state["reset_code_sent_to"] = ""
                        else:
                            st.error("Password reset failed.")
                if cancel:
                    st.session_state["sent_reset_email"] = False
                    st.session_state["reset_email_val"] = ""
                    st.session_state["reset_code_sent_to"] = ""

def leaderboard_panel():
    st.subheader("Leaderboard")
    leaderboard = supabase_db.get_leaderboard()
    if leaderboard:
        st.dataframe([
            {"Rank": idx + 1, "Username": entry["username"], "Reedz": entry["reedz_balance"]}
            for idx, entry in enumerate(leaderboard)
        ], use_container_width=True)
    else:
        st.info("No users found.")

def bets_panel():
    st.subheader("All Bets Overview")
    open_bets = get_bet_overview("open")
    closed_bets = get_bet_overview("closed")
    resolved_bets = get_bet_overview("resolved")

    with st.expander("Open Bets", expanded=True):
        if open_bets:
            for bet in open_bets:
                st.write(f"**ID {bet['bet_id']}** | {bet['title']} (closes {time_utils.format_et(bet['close_at'])})")
        else:
            st.info("No open bets.")

    with st.expander("Closed Bets"):
        if closed_bets:
            for bet in closed_bets:
                st.write(f"**ID {bet['bet_id']}** | {bet['title']} (closed {time_utils.format_et(bet['close_at'])})")
        else:
            st.info("No closed bets.")

    with st.expander("Resolved Bets"):
        if resolved_bets:
            for bet in resolved_bets:
                ans_str = f" | Answer: {bet['correct_answer']}" if bet.get('correct_answer') else ""
                st.write(f"**ID {bet['bet_id']}** | {bet['title']}{ans_str}")
        else:
            st.info("No resolved bets.")


def predictions_panel():
    st.subheader("View Predictions for a Bet")
    all_bets = get_bet_overview("open") + get_bet_overview("closed") + get_bet_overview("resolved")
    if not all_bets:
        st.info("No bets available.")
        return
    
    bet_titles = {f"ID {b['bet_id']} - {b['title'][:50]}...": b['bet_id'] for b in all_bets}
    opt = st.selectbox("Select a bet", list(bet_titles.keys()))
    
    if not opt:
        st.info("No bet selected.")
        return
    
    bet_id = bet_titles[opt]
    predictions = supabase_db.get_predictions_for_bet(bet_id)
    
    if predictions:
        user_cache = {}
        pred_data = []
        for p in predictions:
            user_id = p["user_id"]
            if user_id not in user_cache:
                user = supabase_db.get_user_by_id(user_id)
                user_cache[user_id] = user.username if user else f"ID {user_id}"
            
            pred_data.append({
                "User": user_cache[user_id],
                "Prediction": p["prediction"],
                "Created": time_utils.format_et(p["created_at"])  # FIXED
            })
        
        st.dataframe(pred_data, use_container_width=True)
    else:
        st.info("No predictions for this bet.")


def create_bet_panel(user):
    st.subheader("Create a Bet")
    with st.expander("Create New Bet", expanded=True):
        title = st.text_input("Bet Title")
        description = st.text_area("Bet Description")
        answer_type = st.selectbox("Answer Type", ["number", "text"])
        close_days = st.number_input("Days until bet closes", min_value=1, max_value=30, value=1)
        if st.button("Create Bet", use_container_width=True):
            close_at = datetime.now() + timedelta(days=close_days)
            try:
                create_bet(user, title, description, answer_type, close_at)
                st.success("Bet created.")
            except Exception as e:
                st.error(f"Failed to create bet: {e}")

def place_prediction_panel(user):
    st.subheader("Place Prediction")
    open_bets = get_bet_overview("open")
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in open_bets}
    if not bet_titles:
        st.info("No open bets for prediction.")
        return
    opt = st.selectbox("Select bet to predict on", list(bet_titles.keys()))
    bet_id = bet_titles.get(opt)
    if not bet_id:
        st.info("No bet selected.")
        return
    pred_val = st.text_input("Your Prediction (number or text)")
    if st.button("Place Prediction", use_container_width=True):
        try:
            place_prediction(user, bet_id, pred_val)
            st.success("Prediction placed.")
        except Exception as e:
            st.error(str(e))

def close_bet_panel(user):
    st.subheader("Close Bet")
    open_bets = get_bet_overview("open")
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in open_bets}
    if not bet_titles:
        st.info("No open bets to close.")
        return
    opt = st.selectbox("Select bet to close", list(bet_titles.keys()))
    bet_id = bet_titles.get(opt)
    if not bet_id:
        st.info("No bet selected.")
        return
    if st.button("Close Bet", use_container_width=True):
        try:
            close_bet(user, bet_id)
            st.success("Bet closed.")
        except Exception as e:
            st.error(str(e))

def resolve_bet_panel(user):
    st.subheader("Resolve Bet")
    closed_bets = get_bet_overview("closed")
    bet_titles = {f"ID {b['bet_id']}: {b['title']}": b['bet_id'] for b in closed_bets}
    if not bet_titles:
        st.info("No bets available to resolve.")
        return
    opt = st.selectbox("Select bet to resolve", list(bet_titles.keys()))
    bet_id = bet_titles.get(opt)
    if not bet_id:
        st.info("No bet selected.")
        return
    answer = st.text_input("Correct Answer")
    if st.button("Resolve Bet", use_container_width=True):
        try:
            resolve_bet(user, bet_id, answer)
            st.success("Bet resolved and Reedz distributed.")
        except Exception as e:
            st.error(str(e))

def user_management_panel():
    st.subheader("Admin: User Management")
    sub_menu = st.radio("Choose action", ["List users", "Promote/Demote", "Change Reedz", "Delete user"])
    if sub_menu == "List users":
        users = supabase_db.list_all_users()
        st.dataframe([
            {
                "UserID": u["user_id"],
                "Username": u["username"],
                "Email": u.get("email", ""),
                "Role": u["role"],
                "Reedz": u["reedz_balance"]
            }
            for u in users
        ], use_container_width=True)
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

def profile_panel(user):
    st.subheader("My Profile")
    user_db = supabase_db.get_user_by_id(user.user_id)
    if user_db:
        st.write(f"**Username:** {user_db.username}")
        st.write(f"**Email:** {user_db.email}")
        st.write(f"**Reedz Balance:** {user_db.reedz_balance}")
    else:
        st.error("Could not retrieve user profile.")

def main_panel():
    user = st.session_state.user
    st.sidebar.title("Reedz Betting Menu")
    st.sidebar.markdown(
        f"**Username:** {user.username}\n\n **Role:** {user.role}"
        )
    st.sidebar.divider()
    pages = [
        "My Profile", "Leaderboard", "All Bets",
        "Place Prediction", "View Predictions for a Bet"
    ]
    if is_admin(user):
        admin_pages = ["Create Bet", "Close Bet", "Resolve Bet", "User Management"]
        pages = admin_pages + pages
    page = st.sidebar.radio("Navigation", pages)
    if page == "My Profile":
        profile_panel(user)
    elif is_admin(user) and page == "Create Bet":
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
        
if st.sidebar.checkbox("Test time_utils"):
    test_time = time_utils.format_et("2025-12-04T19:30:00Z")
    st.write(f"Test: {test_time}")  # Should show "2025-12-04 2:30 PM ET"

if __name__ == "__main__" or st._is_running_with_streamlit:
    run_app()
