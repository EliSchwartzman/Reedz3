import streamlit as st
from models import Role, AnswerType
import auth
import betting
import supabase_db
import datetime
import bcrypt

st.set_page_config(page_title="Reedz Betting Platform", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "submenu" not in st.session_state:
    st.session_state.submenu = None


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


def admin_create_bet():
    st.header("Create Bet")
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


def admin_close_bet():
    st.header("Close Bet")
    open_bets = supabase_db.client.table("bets").select("*").eq("is_closed", False).execute().data or []
    if not open_bets:
        st.info("No open bets to close.")
        return
    for bet in open_bets:
        st.write(f"**{bet['title']}** - Closes at {bet['close_at']}")
        if st.button(f"Close Bet {bet['bet_id']}", key=f"close_{bet['bet_id']}"):
            try:
                betting.close_bet(st.session_state.user, bet['bet_id'])
                st.success("Bet closed.")
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))


def admin_resolve_bet():
    st.header("Resolve Bet")
    closed_unresolved = supabase_db.client.table("bets").select("*").eq("is_closed", True).eq("is_resolved", False).execute().data or []
    if not closed_unresolved:
        st.info("No bets to resolve.")
        return
    for bet in closed_unresolved:
        st.subheader(bet["title"])
        answer = st.text_input("Enter correct answer", key=f"answer_{bet['bet_id']}")
        if st.button(f"Resolve Bet {bet['bet_id']}", key=f"resolve_{bet['bet_id']}"):
            try:
                betting.resolve_bet(st.session_state.user, bet["bet_id"], answer)
                st.success("Bet resolved and points distributed.")
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))


def place_prediction_page():
    st.header("Place Prediction")
    open_bets = supabase_db.client.table("bets").select("*").eq("is_closed", False).execute().data or []
    if not open_bets:
        st.info("No open bets available.")
        return
    for bet in open_bets:
        st.subheader(bet["title"])
        prediction = st.text_input(f"Your prediction for {bet['title']}", key=f"pred_{bet['bet_id']}")
        if st.button(f"Place Prediction {bet['bet_id']}", key=f"place_{bet['bet_id']}"):
            try:
                betting.place_prediction(st.session_state.user, bet['bet_id'], prediction)
                st.success("Prediction placed!")
            except Exception as e:
                st.error(str(e))


# Cache a mapping of user_id to username for efficient lookup
@st.cache_data(show_spinner=False)
def get_user_map():
    users = supabase_db.get_all_users()
    return {user.user_id: user.username for user in users}


def view_predictions_page():
    st.header("View Predictions for a Bet")
    all_bets = supabase_db.client.table("bets").select("*").execute().data or []
    bet_titles = {bet['bet_id']: bet['title'] for bet in all_bets}
    selected_bet = st.selectbox("Select Bet", options=list(bet_titles.keys()), format_func=lambda x: bet_titles[x])
    if selected_bet:
        preds = supabase_db.get_predictions_by_bet(selected_bet)
        if not preds:
            st.info("No predictions placed yet.")
            return
        user_map = get_user_map()
        for p in preds:
            username = user_map.get(p.user_id, p.user_id)  # fallback to UUID if not found
            st.write(f"User: {username} - Prediction: {p.prediction}")


def admin_user_management():
    st.header("User Management")
    users = supabase_db.get_all_users()
    for user in users:
        cols = st.columns([2, 1, 2, 2, 2])
        cols[0].write(user.username)
        cols[1].write(user.role.value)
        cols[2].write(user.reedz)

        if cols[3].button("Promote to Admin", key=f"promote_{user.user_id}"):
            supabase_db.promote_demote_user(user.user_id, Role.ADMIN.value)
            st.experimental_rerun()
        if cols[4].button("Demote to Member", key=f"demote_{user.user_id}"):
            supabase_db.promote_demote_user(user.user_id, Role.MEMBER.value)
            st.experimental_rerun()
        if cols[4].button("Delete User", key=f"delete_{user.user_id}"):
            supabase_db.delete_user_account(user.user_id)
            st.experimental_rerun()


def admin_panel():
    st.sidebar.title("Admin Menu")
    submenu = st.sidebar.radio("Go to:", [
        "Create Bet",
        "Close Bet",
        "Resolve Bet",
        "Place Prediction",
        "See Predictions",
        "User Management"
    ])
    st.session_state.submenu = submenu

    if submenu == "Create Bet":
        admin_create_bet()
    elif submenu == "Close Bet":
        admin_close_bet()
    elif submenu == "Resolve Bet":
        admin_resolve_bet()
    elif submenu == "Place Prediction":
        place_prediction_page()
    elif submenu == "See Predictions":
        view_predictions_page()
    elif submenu == "User Management":
        admin_user_management()


def member_panel():
    st.sidebar.title("Member Menu")
    submenu = st.sidebar.radio("Go to:", [
        "Place Prediction",
        "See Predictions"
    ])
    st.session_state.submenu = submenu

    if submenu == "Place Prediction":
        place_prediction_page()
    elif submenu == "See Predictions":
        view_predictions_page()


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
            member_panel()


if __name__ == "__main__":
    main()
