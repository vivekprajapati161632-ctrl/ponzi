import streamlit as st
import pandas as pd
import os
import re
import json
import hashlib
from datetime import datetime

# ================= CONFIG =================

st.set_page_config(
    page_title="Ponzi Simulator Pro",
    layout="wide",
    page_icon="📉"
)

INVESTOR_FILE = "investors.csv"
USER_FILE = "users.csv"
SESSION_FILE = "session.json"

today = datetime.now().strftime("%Y-%m-%d")

# ================= SECURITY =================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ================= VALIDATION =================

def valid_username(u):
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,20}", u))

def valid_password(p):
    return len(p) >= 4

def valid_mobile(m):
    return bool(re.fullmatch(r"[6-9]\d{9}", m))

def valid_email(e):
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", e))

# ================= SESSION =================

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

            s = json.load(f)

            st.session_state.logged_in = s.get("logged_in", False)
            st.session_state.username = s.get("username", "")
            st.session_state.role = s.get("role", "")

def clear_session():

    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# ================= FILE FUNCTIONS =================

def load_users():

    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)

    return pd.DataFrame(columns=["Username","Password","Role","Date"])

def save_users(df):
    df.to_csv(USER_FILE, index=False)

def load_investors():

    if os.path.exists(INVESTOR_FILE):
        return pd.read_csv(INVESTOR_FILE)

    return pd.DataFrame(columns=[
        "Name","Mobile","Email",
        "Invested","Promised","Paid","Date"
    ])

def save_investors(df):
    df.to_csv(INVESTOR_FILE, index=False)

# ================= INIT =================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

load_session()

# ================= CREATE DEFAULT ADMIN =================

users = load_users()

if "admin" not in users["Username"].values:

    new = pd.DataFrame([{
        "Username":"admin",
        "Password":hash_password("admin"),
        "Role":"admin",
        "Date":today
    }])

    users = pd.concat([users,new])
    save_users(users)

# ================= UI DESIGN =================

def stats_cards(df):

    total_invested = df["Invested"].sum()
    total_promised = df["Promised"].sum()
    pending = total_promised - df[df["Paid"]==True]["Promised"].sum()

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Invested", f"₹{total_invested:,.0f}")
    col2.metric("Total Promised", f"₹{total_promised:,.0f}")
    col3.metric("Pending Liability", f"₹{pending:,.0f}")

# ================= LOGIN PAGE =================

def login_page():

    st.title("🔐 Ponzi Simulator Pro")

    tab1,tab2 = st.tabs(["Login","Register"])

    users = load_users()

    # LOGIN

    with tab1:

        user = st.text_input("Username")
        pwd = st.text_input("Password",type="password")

        if st.button("Login"):

            hashed = hash_password(pwd)

            match = users[
                (users.Username==user) &
                (users.Password==hashed)
            ]

            if not match.empty:

                role = match.iloc[0]["Role"]

                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = role

                save_session(user, role)

                st.success("Login success")
                st.rerun()

            else:
                st.error("Invalid credentials")

    # REGISTER

    with tab2:

        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password",type="password")

        if st.button("Register"):

            if not valid_username(new_user):
                st.error("Invalid username")

            elif not valid_password(new_pass):
                st.error("Weak password")

            elif new_user in users.Username.values:
                st.error("User exists")

            else:

                new = pd.DataFrame([{
                    "Username":new_user,
                    "Password":hash_password(new_pass),
                    "Role":"user",
                    "Date":today
                }])

                users = pd.concat([users,new])
                save_users(users)

                st.success("User created")

# ================= ADMIN PANEL =================

def admin_panel():

    st.title("📊 Admin Dashboard")

    df = load_investors()

    stats_cards(df)

    st.divider()

    # ADD INVESTOR

    st.subheader("Add Investor")

    col1,col2,col3,col4 = st.columns(4)

    name = col1.text_input("Name")
    mobile = col2.text_input("Mobile")
    email = col3.text_input("Email")
    amount = col4.number_input("Amount",0)

    percent = st.slider("Return %",10,200,50)

    if st.button("Add"):

        if not name:
            st.error("Enter name")

        elif not valid_mobile(mobile):
            st.error("Invalid mobile")

        elif not valid_email(email):
            st.error("Invalid email")

        elif mobile in df.Mobile.astype(str).values:
            st.error("Mobile exists")

        else:

            promised = amount*(1+percent/100)

            new = pd.DataFrame([{
                "Name":name,
                "Mobile":mobile,
                "Email":email,
                "Invested":amount,
                "Promised":promised,
                "Paid":False,
                "Date":today
            }])

            df = pd.concat([df,new])
            save_investors(df)

            st.success("Added")
            st.rerun()

    # ================= TABLE =================

    st.subheader("Investors")

    if df.empty:
        st.warning("No investors")
        return

    df["Select"] = False

    edited = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic"
    )

    # REMOVE

    if st.button("Remove Selected"):

        new_df = edited[edited.Select==False]

        save_investors(new_df.drop(columns=["Select"]))

        st.success("Removed")
        st.rerun()

# ================= USER PANEL =================

def user_panel():

    st.title("👤 User Dashboard")

    df = load_investors()

    stats_cards(df)

    search = st.text_input("Search Investor")

    if search:

        df = df[
            df.Name.str.contains(search,case=False) |
            df.Mobile.astype(str).str.contains(search)
        ]

    st.dataframe(df,use_container_width=True)

# ================= MAIN =================

if st.session_state.logged_in:

    st.sidebar.write(f"👤 {st.session_state.username}")
    st.sidebar.write(f"Role: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        clear_session()
        st.rerun()

    if st.session_state.role=="admin":
        admin_panel()
    else:
        user_panel()

else:

    login_page()
