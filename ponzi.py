import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

st.set_page_config(page_title="Secure Ponzi Simulator", layout="wide")

# ========= FILE SETUP =========

today = datetime.now().strftime("%Y-%m-%d")

INVESTOR_FILE = f"investors_{today}.csv"
USER_FILE = f"users_{today}.csv"

REQUIRED_INVESTOR_COLUMNS = ["Name","Mobile","Email","Invested","Promised","Paid","Date"]
REQUIRED_USER_COLUMNS = ["Username","Password","Role","Date"]

# ========= SESSION INIT =========

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

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
    df.to_csv(USER_FILE,index=False)

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
    df.to_csv(INVESTOR_FILE,index=False)

# ========= DEFAULT ADMIN CREATE =========

users = load_users()

if not any(u["Username"]=="admin" for u in users):

    users.append({
        "Username":"admin",
        "Password":"admin",
        "Role":"admin",
        "Date":today
    })

    save_users(users)

# ========= VALIDATION =========

def valid_username(u):
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,20}",u))

def valid_password(p):
    return len(p)>=4

# ========= LOGIN PAGE =========

def login_page():

    st.title("🔐 Login System")

    tab1,tab2 = st.tabs(["Login","Create User"])

    users = load_users()

    # ===== LOGIN =====

    with tab1:

        username = st.text_input("Username")
        password = st.text_input("Password",type="password")

        if st.button("Login"):

            found = False

            for u in users:

                if u["Username"]==username and u["Password"]==password:

                    st.session_state.logged_in=True
                    st.session_state.username=username
                    st.session_state.role=u["Role"]

                    st.success("Login successful")

                    st.rerun()

            if not found:
                st.error("Invalid username or password")

    # ===== CREATE USER =====

    with tab2:

        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password",type="password")

        if st.button("Create User"):

            if not valid_username(new_user):
                st.error("Invalid username")

            elif not valid_password(new_pass):
                st.error("Password min 4 char")

            elif any(u["Username"]==new_user for u in users):
                st.error("User already exists")

            else:

                users.append({
                    "Username":new_user,
                    "Password":new_pass,
                    "Role":"user",
                    "Date":today
                })

                save_users(users)

                st.success("User created")

# ========= MAIN APP =========

def main_app():

    st.title("📉 Money Gurrented Schem")

    st.sidebar.write(f"Logged in as: {st.session_state.username}")

    if st.sidebar.button("Logout"):

        st.session_state.logged_in=False
        st.rerun()

    # ===== LOAD INVESTORS =====

    if "investors" not in st.session_state:
        st.session_state.investors=load_investors()

    # ===== ADD INVESTOR =====

    st.sidebar.header("Add Investor")

    name=st.sidebar.text_input("Full Name")
    mobile=st.sidebar.text_input("Mobile")
    email=st.sidebar.text_input("Email")
    amount=st.sidebar.number_input("Amount",min_value=0)
    percent=st.sidebar.slider("Return %",10,200,50)

    if st.sidebar.button("Add"):

        mobiles=[i["Mobile"] for i in st.session_state.investors]
        emails=[i["Email"] for i in st.session_state.investors]

        if mobile in mobiles:
            st.error("Mobile exists")

        elif email in emails:
            st.error("Email exists")

        else:

            promised=amount*(1+percent/100)

            st.session_state.investors.append({

                "Name":name,
                "Mobile":mobile,
                "Email":email,
                "Invested":amount,
                "Promised":promised,
                "Paid":False,
                "Date":today

            })

            save_investors(st.session_state.investors)

            st.success("Added")

            st.rerun()

    # ===== REMOVE =====

    if st.session_state.investors:

        mobiles=[i["Mobile"] for i in st.session_state.investors]

        remove=st.sidebar.selectbox("Remove",mobiles)

        if st.sidebar.button("Remove"):

            st.session_state.investors=[
                i for i in st.session_state.investors
                if i["Mobile"]!=remove
            ]

            save_investors(st.session_state.investors)

            st.success("Removed")

            st.rerun()

    # ===== TABLE =====

    df=pd.DataFrame(st.session_state.investors)

    st.dataframe(df,use_container_width=True)

# ========= ROUTER =========

if not st.session_state.logged_in:

    login_page()

else:

    main_app()
