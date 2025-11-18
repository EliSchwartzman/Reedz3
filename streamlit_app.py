import streamlit as st
from models import Role, AnswerType
import auth
import betting
import supabase_db
import datetime
import bcrypt

st.set_page_config(page_title="Reedz Betting Platform")

# Initialize session state keys safely
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = auth.login(username, password)
        if user:
            st.session_state.user = user
            st.session_state.page = "home"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Register Here"):
        st.session_state.page = "register"
        st.experimental_rerun()


def register_page():
    st.title("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    admin_code = st.text_input("Admin Code (optional)", type="password")

    if st.button("Register"):
        if not username or not email or not password:
            st.error("Please fill in all required fields.")
            return

        if supabase_db.get_user_by_username(username):
            st.error("Username already taken.")
            return

        role = Role.ADMIN if admin_code == "Reedz123" else Role.MEMBER
        password_hash = hash_password(password)

        user = supabase_db.insert_user(supabase_db.User(
            user_id=None,
            username=username,
            password_hash=password_hash,
            email=email,
            created_at=datetime.datetime.utcnow(),
            role=role,
            reedz=0
        ))
        st.success(f"User {username} created successfully as {role.value}!")
        st.session_state.user = supabase_db.get_user_by_username(username)
        st.session_state.page = "home"
        st.experimental_rerun()

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.experimental_rerun()


def member_home():
    st.title("Reedz Predictions")
    st.write(f"Welcome {st.session_state.user.username} ({st.session_state.user.role.value})")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "login"
        st.experimental_rerun()

    st.subheader("Open Bets")

    bets = supabase_db.client.table("bets").select("*").eq("is_closed", False).execute().data or []
    for bet in bets:
        st.write(f"**{bet['title']}** - {bet['description']} (Close at: {bet['close_at']})")
        with st.form(f"predict_{bet['bet_id']}"):
            pred = st.text_input(f"Your prediction for {bet['title']}", key=f"input_{bet['bet_id']}")
            submitted = st.form_submit_button("Place Prediction")
            if submitted:
                try:
                    betting.place_prediction(st.session_state.user, bet['bet_id'], pred)
                    st.success("Prediction placed!")
                except Exception as e:
                    st.error(str(e))


def admin_panel():
    st.title("Admin Panel")
    st.write(f"Welcome {st.session_state.user.username} (Admin)")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "login"
        st.experimental_rerun()

    st.subheader("Create Bet")
    with st.form("create_bet_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        answer_type = st.selectbox("Answer type", [AnswerType.NUMBER, AnswerType.TEXT])
        close_date = st.date_input("Close Date", value=datetime.date.today())
        close_time = st.time_input("Close Time", value=datetime.time(hour=23, minute=59))
        submitted = st.form_submit_button("Create Bet")
        if submitted:
            close_at = datetime.datetime.combine(close_date, close_time)
            try:
                betting.create_bet(st.session_state.user, title, description, answer_type, close_at)
                st.success("Bet created successfully.")
            except Exception as e:
                st.error(str(e))

    st.subheader("User Management")
    users = supabase_db.get_all_users()
    for user in users:
        st.write(f"{user.username} | Role: {user.role.value} | Reedz: {user.reedz}")
        # You can expand here with buttons for promote/demote, delete, and point adjustments


def main():
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    else:
        if st.session_state.user is None:
            st.session_state.page = "login"
            st.experimental_rerun()
        elif st.session_state.user.role == Role.ADMIN:
            admin_panel()
        else:
            member_home()


if __name__ == "__main__":
    main()
