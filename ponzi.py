import streamlit as st
import pandas as pd
import os
import re
import json
from datetime import datetime

st.set_page_config(page_title="Secure Ponzi Simulator", layout="wide")

# ========= DATE =========

today = datetime.now().strftime("%Y-%m-%d")

# ========= FILE SETUP =========

INVESTOR_FILE = "investors.csv"
USER_FILE = "users.csv"
SESSION_FILE = "session.json"

REQUIRED_INVESTOR_COLUMNS = ["Name","Mobile","Email","Invested","Promised","Paid","Date"]
REQUIRED_USER_COLUMNS = ["Username","Password","Role","Date"]

# ========= SESSION FUNCTIONS =========

def save_session(username, role):

    session = {
        "logged_in": True,
        "username": username,
        "role": role
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(session, f)


def load_session():

    if os.path.exists(SESSION_FILE):

        with open(SESSION_FILE, "r") as f:

            session = json.load(f)

            st.session_state.logged_in = session.get("logged_in", False)
            st.session_state.username = session.get("username", "")
            st.session_state.role = session.get("role", "")


def clear_session():

    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# ========= SESSION INIT =========

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# Load saved session
load_session()

# ========= FILE FUNCTIONS =========

def load_users():

    if os.path.exists(USER_FILE):

        df = pd.read_csv(USER_FILE)

        for col in REQUIRED_USER_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        return df.to_dict("records")

    return []


def save_users(data):

    df = pd.DataFrame(data)
    df.to_csv(USER_FILE, index=False)


def load_investors():

    if os.path.exists(INVESTOR_FILE):

        df = pd.read_csv(INVESTOR_FILE)

        for col in REQUIRED_INVESTOR_COLUMNS:

            if col not in df.columns:

                if col == "Paid":
                    df[col] = False
                else:
                    df[col] = ""

        return df.to_dict("records")

    return []


def save_investors(data):

    df = pd.DataFrame(data)
    df.to_csv(INVESTOR_FILE, index=False)

# ========= CREATE DEFAULT ADMIN =========

users = load_users()

if not any(u["Username"] == "admin" for u in users):

    users.append({

        "Username": "admin",
        "Password": "admin",
        "Role": "admin",
        "Date": today

    })

    save_users(users)

# ========= VALIDATION =========

def valid_username(u):
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,20}", u))

def valid_password(p):
    return len(p) >= 4

# ========= LOGIN PAGE =========

def login_page():

    st.title("🔐 Login System")

    tab1, tab2 = st.tabs(["Login", "Create User"])

    users = load_users()

    # LOGIN
    with tab1:

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            for u in users:

                if u["Username"] == username and u["Password"] == password:

                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = u["Role"]

                    save_session(username, u["Role"])

                    st.success("Login successful")

                    st.rerun()

            st.error("Invalid username or password")

    # CREATE USER
    with tab2:

        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Create User"):

            if not valid_username(new_user):

                st.error("Invalid username")

            elif not valid_password(new_pass):

                st.error("Password min 4 char")

            elif any(u["Username"] == new_user for u in users):

                st.error("User exists")

            else:

                users.append({

                    "Username": new_user,
                    "Password": new_pass,
                    "Role": "user",
                    "Date": today

                })

                save_users(users)

                st.success("User created")

# ========= MAIN APP =========

def main_app():

    st.title("📉 Money Gurrented Schem")

    st.sidebar.write(f"Logged in as: {st.session_state.username}")

    if st.sidebar.button("Logout"):

        clear_session()
        st.rerun()

    # Always load latest investors
    st.session_state.investors = load_investors()

    # ADD
    st.sidebar.header("Add Investor")

    name = st.sidebar.text_input("Full Name")
    mobile = st.sidebar.text_input("Mobile")
    email = st.sidebar.text_input("Email")
    amount = st.sidebar.number_input("Amount", min_value=0)
    percent = st.sidebar.slider("Return %", 10, 200, 50)

    if st.sidebar.button("Add Investor"):

        mobiles = [i["Mobile"] for i in st.session_state.investors]
        emails = [i["Email"] for i in st.session_state.investors]

        if mobile in mobiles:

            st.error("Mobile exists")

        elif email in emails:

            st.error("Email exists")

        else:

            promised = amount * (1 + percent / 100)

            st.session_state.investors.append({

                "Name": name,
                "Mobile": mobile,
                "Email": email,
                "Invested": amount,
                "Promised": promised,
                "Paid": False,
                "Date": today

            })

            save_investors(st.session_state.investors)

            st.success("Added")

            st.rerun()

    # REMOVE

    if st.session_state.investors:

        mobiles = [i["Mobile"] for i in st.session_state.investors]

        remove = st.sidebar.selectbox("Remove Investor", mobiles)

        if st.sidebar.button("Remove"):

            st.session_state.investors = [

                i for i in st.session_state.investors
                if i["Mobile"] != remove

            ]

            save_investors(st.session_state.investors)

            st.success("Removed")

            st.rerun()

    # TABLE

    df = pd.DataFrame(st.session_state.investors)

    st.dataframe(df, use_container_width=True)

# ========= ROUTER =========

if st.session_state.logged_in:

    main_app()

else:

    login_page()
