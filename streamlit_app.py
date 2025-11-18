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

    # --- Create Bet ---
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
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))

    # --- Bets Overview ---
    st.subheader("Manage Bets")

    # Fetch all bets (open and closed)
    all_bets = supabase_db.client.table("bets").select("*").order("created_at", desc=True).execute().data or []

    for bet in all_bets:
        st.markdown(f"### {bet['title']}  (Status: {'Resolved' if bet['is_resolved'] else ('Closed' if bet['is_closed'] else 'Open')})")
        st.write(f"Description: {bet['description']}")
        st.write(f"Close At: {bet['close_at']}")
        st.write(f"Created At: {bet['created_at']}")

        if not bet['is_closed']:
            # Button to close bet immediately
            if st.button(f"Close Bet {bet['bet_id']}", key=f"close_{bet['bet_id']}"):
                try:
                    betting.close_bet(st.session_state.user, bet['bet_id'])
                    st.success("Bet closed.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.write("This bet is closed.")

        # Show predictions for this bet
        st.write("Predictions:")
        predictions = supabase_db.get_predictions_by_bet(bet['bet_id'])
        if predictions:
            for p in predictions:
                user = supabase_db.get_user_by_username(p.user_id)  # Consider caching for efficiency
                username = user.username if user else p.user_id
                st.write(f"User: {username} - Prediction: {p.prediction}")
        else:
            st.write("No predictions yet.")

        # If bet is closed and not resolved, allow to resolve by entering correct answer
        if bet['is_closed'] and not bet['is_resolved']:
            with st.form(f"resolve_form_{bet['bet_id']}"):
                correct_answer = st.text_input("Enter correct answer to resolve this bet")
                submitted = st.form_submit_button("Resolve Bet")
                if submitted:
                    try:
                        betting.resolve_bet(st.session_state.user, bet['bet_id'], correct_answer)
                        st.success("Bet resolved and points distributed.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(str(e))

        st.markdown("---")



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
