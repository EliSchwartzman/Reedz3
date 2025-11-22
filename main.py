import sys
import os
import getpass
from dotenv import load_dotenv
from models import User
from auth import hash_password, authenticate, is_admin
from betting import create_bet, close_bet, resolve_bet, place_prediction, get_bet_overview
import supabase_db
from datetime import datetime, timedelta

load_dotenv()
ADMIN_CODE = os.getenv("ADMIN_CODE")

def main_menu(user):
    print("\n==== REEDZ MAIN MENU ====")
    if is_admin(user):
        menu_items = [
            ("1", "Create bet"),
            ("2", "Place prediction"),
            ("3", "Close bet"),
            ("4", "Resolve bet"),
            ("5", "View bets"),
            ("6", "View leaderboard"),
            ("7", "User management"),
            ("8", "Logout"),
            ("9", "Exit"),
            ("10", "View predictions for a bet"),
        ]
    else:
        menu_items = [
            ("1", "Place prediction"),
            ("2", "View bets"),
            ("3", "View leaderboard"),
            ("4", "Logout"),
            ("5", "Exit"),
            ("6", "View predictions for a bet"),
        ]
    for k, v in menu_items:
        print(f"{k}. {v}")
    return input("Choice: ")

def auth_menu():
    print("==== REEDZ AUTH MENU ====")
    print("1. Register")
    print("2. Login")
    print("3. Reset password")
    print("4. Exit")
    return input("Choice: ")

def user_management_menu():
    print("\n==== USER MANAGEMENT MENU ====")
    print("1. List all users")
    print("2. Promote/demote user")
    print("3. Change user reedz balance")
    print("4. Delete user")
    print("5. Return to main menu")
    return input("Choice: ")

def print_bets(bets):
    for bet in bets:
        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")

def print_predictions_with_usernames(predictions):
    if not predictions:
        print("No predictions found for this bet.")
        return
    print("\nPredictions:")
    for pred in predictions:
        # Fetch username using user_id (optimize as needed)
        pred_user = supabase_db.get_user_by_username(pred.user_id)
        username = pred_user.username if pred_user else f"UserID {pred.user_id}"
        print(f"User: {username}, Prediction: {pred.prediction}")

def cli():
    user = None
    while not user:
        choice = auth_menu()
        if choice == "1":
            username = input("Username: ")
            password = hash_password(getpass.getpass("Password: "))
            email = input("Email: ")
            while True:
                role = input("Role (Admin/Member): ")
                if role == "Admin":
                    admin_code = getpass.getpass("Enter admin verification code: ")
                    if admin_code != ADMIN_CODE:
                        print("Incorrect admin code. Try again or enter 'Member' as role.")
                        continue
                if role not in ["Admin", "Member"]:
                    print("Role must be 'Admin' or 'Member'.")
                    continue
                break
            u = User(user_id=None, username=username, password=password, email=email, reedz_balance=0, role=role, created_at=datetime.now())
            supabase_db.create_user(u)
            print("User registered. Now, please login.")
        elif choice == "2":
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            user = authenticate(username, password)
            if user:
                print(f"Logged in as {user.username}, role {user.role}")
            else:
                print("Login failed, try again.")
        elif choice == "3":
            email = input("Enter your email address: ")
            found_user = supabase_db.get_user_by_email(email)
            if not found_user:
                print("No user with that email address was found.")
                continue
            new_password = getpass.getpass("Enter new password: ")
            confirm_password = getpass.getpass("Re-enter new password: ")
            if new_password != confirm_password:
                print("Passwords do not match. Try again.")
                continue
            hashed = hash_password(new_password)
            if supabase_db.update_user_password(found_user.user_id, hashed):
                print("Password reset successful. You can now login.")
            else:
                print("Password reset failed. Try again.")
        elif choice == "4":
            print("Goodbye!")
            sys.exit()
    while True:
        choice = main_menu(user)
        if is_admin(user):
            if choice == "1":
                title = input("Bet title: ")
                description = input("Description: ")
                answer_type = input("Type (number/text): ")
                close_at = datetime.now() + timedelta(days=1)
                create_bet(user, title, description, answer_type, close_at)
                print("Bet created.")
            elif choice == "2":
                open_bets = get_bet_overview("open")
                if not open_bets:
                    print("No open bets available for predictions.")
                    continue
                print("\nOpen Bets:")
                print_bets(open_bets)
                try:
                    bet_id = int(input("Enter Bet ID you want to predict on: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                pred = input("Your Prediction: ")
                try:
                    place_prediction(user, bet_id, pred)
                    print("Prediction placed.")
                except Exception as e:
                    print(f"Error: {e}")
            elif choice == "3":
                open_bets = get_bet_overview("open")
                if not open_bets:
                    print("No open bets to close.")
                    continue
                print("\nOpen Bets:")
                print_bets(open_bets)
                try:
                    bet_id = int(input("Enter Bet ID to close: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                close_bet(user, bet_id)
                print("Bet closed.")
            elif choice == "4":
                closed_bets = get_bet_overview("closed")
                if not closed_bets:
                    print("No bets available to resolve.")
                    continue
                print("\nClosed Bets (available to resolve):")
                print_bets(closed_bets)
                try:
                    bet_id = int(input("Enter Bet ID to resolve: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                answer = input("Correct answer: ")
                resolve_bet(user, bet_id, answer)
                print("Bet resolved and Reedz distributed.")
            elif choice == "5":
                open_bets = get_bet_overview("open")
                closed_bets = get_bet_overview("closed")
                resolved_bets = get_bet_overview("resolved")
                print("\n--- Open Bets ---")
                if open_bets:
                    for bet in open_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No open bets.")
                print("\n--- Closed Bets ---")
                if closed_bets:
                    for bet in closed_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No closed bets.")
                print("\n--- Resolved Bets ---")
                if resolved_bets:
                    for bet in resolved_bets:
                        ans_str = f", Answer: {bet['correct_answer']}" if bet.get('correct_answer') else ""
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}{ans_str}")
                else:
                    print("No resolved bets.")
            elif choice == "6":
                leaderboard = supabase_db.get_leaderboard()
                if not leaderboard:
                    print("No users found.")
                else:
                    print("\n==== REEDZ LEADERBOARD ====")
                    print(f"{'Rank':<6}{'Username':<20}{'Reedz':<8}")
                    for idx, entry in enumerate(leaderboard, 1):
                        print(f"{idx:<6}{entry['username']:<20}{entry['reedz_balance']:<8}")
            elif choice == "7":
                while True:
                    sub_choice = user_management_menu()
                    if sub_choice == "1":
                        users = supabase_db.list_all_users()
                        print(f"{'UserID':<8}{'Username':<20}{'Role':<10}{'Reedz':<8}")
                        for u in users:
                            print(f"{u['user_id']:<8}{u['username']:<20}{u['role']:<10}{u['reedz_balance']:<8}")
                    elif sub_choice == "2":
                        try:
                            uid = int(input("Enter User ID to promote/demote: "))
                            new_role = input("New role (Admin/Member): ")
                            if new_role == "Admin":
                                admin_code = getpass.getpass("Enter admin verification code: ")
                                if admin_code != ADMIN_CODE:
                                    print("Incorrect admin code. Promotion cancelled.")
                                    continue
                            if new_role not in ["Admin", "Member"]:
                                print("Role must be 'Admin' or 'Member'.")
                                continue
                            supabase_db.change_role(uid, new_role)
                            print("Role updated.")
                        except Exception as e:
                            print(f"Error: {e}")
                    elif sub_choice == "3":
                        try:
                            uid = int(input("Enter User ID to change Reedz: "))
                            reedz = int(input("New Reedz balance: "))
                            all_users = supabase_db.list_all_users()
                            user_obj = next((u for u in all_users if u['user_id'] == uid), None)
                            if not user_obj:
                                print("User not found.")
                                continue
                            delta = reedz - user_obj['reedz_balance']
                            supabase_db.add_reedz(uid, delta)
                            print("Reedz updated.")
                        except Exception as e:
                            print(f"Error: {e}")
                    elif sub_choice == "4":
                        try:
                            uid = int(input("Enter User ID to delete: "))
                            supabase_db.delete_user(uid)
                            print("User deleted.")
                        except Exception as e:
                            print(f"Error: {e}")
                    elif sub_choice == "5":
                        break
                    else:
                        print("Invalid choice.")
            elif choice == "8":
                print("Logging out...")
                user = None
                while not user:
                    choice = auth_menu()
                    if choice == "1":
                        username = input("Username: ")
                        password = hash_password(getpass.getpass("Password: "))
                        email = input("Email: ")
                        while True:
                            role = input("Role (Admin/Member): ")
                            if role == "Admin":
                                admin_code = getpass.getpass("Enter admin verification code: ")
                                if admin_code != ADMIN_CODE:
                                    print("Incorrect admin code. Try again or enter 'Member' as role.")
                                    continue
                            if role not in ["Admin", "Member"]:
                                print("Role must be 'Admin' or 'Member'.")
                                continue
                            break
                        u = User(user_id=None, username=username, password=password, email=email, reedz_balance=0, role=role, created_at=datetime.now())
                        supabase_db.create_user(u)
                        print("User registered. Now, please login.")
                    elif choice == "2":
                        username = input("Username: ")
                        password = getpass.getpass("Password: ")
                        user = authenticate(username, password)
                        if user:
                            print(f"Logged in as {user.username}, role {user.role}")
                        else:
                            print("Login failed, try again.")
                    elif choice == "3":
                        email = input("Enter your email address: ")
                        found_user = supabase_db.get_user_by_email(email)
                        if not found_user:
                            print("No user with that email address was found.")
                            continue
                        new_password = getpass.getpass("Enter new password: ")
                        confirm_password = getpass.getpass("Re-enter new password: ")
                        if new_password != confirm_password:
                            print("Passwords do not match. Try again.")
                            continue
                        hashed = hash_password(new_password)
                        if supabase_db.update_user_password(found_user.user_id, hashed):
                            print("Password reset successful. You can now login.")
                        else:
                            print("Password reset failed. Try again.")
                    elif choice == "4":
                        print("Goodbye!")
                        sys.exit()
            elif choice == "9":
                print("Goodbye!")
                sys.exit()
            elif choice == "10":
                all_bets = get_bet_overview("")
                if not all_bets:
                    print("No bets found.")
                    continue
                print("\nAll Bets:")
                print_bets(all_bets)
                try:
                    bet_id = int(input("Enter Bet ID to view predictions for: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                predictions = supabase_db.get_predictions_for_bet(bet_id)
                print_predictions_with_usernames(predictions)
            else:
                print("Invalid choice.")
        else:
            if choice == "1":
                open_bets = get_bet_overview("open")
                if not open_bets:
                    print("No open bets available for predictions.")
                    continue
                print("\nOpen Bets:")
                print_bets(open_bets)
                try:
                    bet_id = int(input("Enter Bet ID you want to predict on: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                pred = input("Your Prediction: ")
                try:
                    place_prediction(user, bet_id, pred)
                    print("Prediction placed.")
                except Exception as e:
                    print(f"Error: {e}")
            elif choice == "2":
                open_bets = get_bet_overview("open")
                closed_bets = get_bet_overview("closed")
                resolved_bets = get_bet_overview("resolved")
                print("\n--- Open Bets ---")
                if open_bets:
                    for bet in open_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No open bets.")
                print("\n--- Closed Bets ---")
                if closed_bets:
                    for bet in closed_bets:
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}")
                else:
                    print("No closed bets.")
                print("\n--- Resolved Bets ---")
                if resolved_bets:
                    for bet in resolved_bets:
                        ans_str = f", Answer: {bet['correct_answer']}" if bet.get('correct_answer') else ""
                        print(f"Bet ID: {bet['bet_id']}, Title: {bet['title']}{ans_str}")
                else:
                    print("No resolved bets.")
            elif choice == "3":
                leaderboard = supabase_db.get_leaderboard()
                if not leaderboard:
                    print("No users found.")
                else:
                    print("\n==== REEDZ LEADERBOARD ====")
                    print(f"{'Rank':<6}{'Username':<20}{'Reedz':<8}")
                    for idx, entry in enumerate(leaderboard, 1):
                        print(f"{idx:<6}{entry['username']:<20}{entry['reedz_balance']:<8}")
            elif choice == "4":
                print("Logging out...")
                user = None
                while not user:
                    choice = auth_menu()
                    if choice == "1":
                        username = input("Username: ")
                        password = hash_password(getpass.getpass("Password: "))
                        email = input("Email: ")
                        while True:
                            role = input("Role (Admin/Member): ")
                            if role == "Admin":
                                admin_code = getpass.getpass("Enter admin verification code: ")
                                if admin_code != ADMIN_CODE:
                                    print("Incorrect admin code. Try again or enter 'Member' as role.")
                                    continue
                            if role not in ["Admin", "Member"]:
                                print("Role must be 'Admin' or 'Member'.")
                                continue
                            break
                        u = User(user_id=None, username=username, password=password, email=email, reedz_balance=0, role=role, created_at=datetime.now())
                        supabase_db.create_user(u)
                        print("User registered. Now, please login.")
                    elif choice == "2":
                        username = input("Username: ")
                        password = getpass.getpass("Password: ")
                        user = authenticate(username, password)
                        if user:
                            print(f"Logged in as {user.username}, role {user.role}")
                        else:
                            print("Login failed, try again.")
                    elif choice == "3":
                        email = input("Enter your email address: ")
                        found_user = supabase_db.get_user_by_email(email)
                        if not found_user:
                            print("No user with that email address was found.")
                            continue
                        new_password = getpass.getpass("Enter new password: ")
                        confirm_password = getpass.getpass("Re-enter new password: ")
                        if new_password != confirm_password:
                            print("Passwords do not match. Try again.")
                            continue
                        hashed = hash_password(new_password)
                        if supabase_db.update_user_password(found_user.user_id, hashed):
                            print("Password reset successful. You can now login.")
                        else:
                            print("Password reset failed. Try again.")
                    elif choice == "4":
                        print("Goodbye!")
                        sys.exit()
            elif choice == "5":
                print("Goodbye!")
                sys.exit()
            elif choice == "6":
                all_bets = get_bet_overview("")
                if not all_bets:
                    print("No bets found.")
                    continue
                print("\nAll Bets:")
                print_bets(all_bets)
                try:
                    bet_id = int(input("Enter Bet ID to view predictions for: "))
                except ValueError:
                    print("Invalid Bet ID.")
                    continue
                predictions = supabase_db.get_predictions_for_bet(bet_id)
                print_predictions_with_usernames(predictions)
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    cli()
