import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# ================= CONFIG =================

st.set_page_config(
    page_title="Ponzi Enterprise",
    layout="wide",
    page_icon="📊"
)

USER_DB="users.db"
INVESTOR_DB="investors.db"

# ================= DATABASE =================

def connect_user():
    return sqlite3.connect(USER_DB, check_same_thread=False)

def connect_investor():
    return sqlite3.connect(INVESTOR_DB, check_same_thread=False)

user_conn=connect_user()
user_c=user_conn.cursor()

invest_conn=connect_investor()
invest_c=invest_conn.cursor()

# create user table

user_c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
date TEXT
)
""")

# create investor table

invest_c.execute("""
CREATE TABLE IF NOT EXISTS investors(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
mobile TEXT,
email TEXT,
invested REAL,
promised REAL,
paid INTEGER,
date TEXT
)
""")

user_conn.commit()
invest_conn.commit()

# ================= SECURITY =================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ================= CREATE DEFAULT ADMIN =================

user_c.execute("SELECT * FROM users WHERE username='admin'")

if not user_c.fetchone():

    user_c.execute("""
    INSERT INTO users VALUES(?,?,?,?)
    """,(
        "admin",
        hash_password("admin123"),
        "admin",
        datetime.now().strftime("%Y-%m-%d")
    ))

    user_conn.commit()

# ================= SESSION =================

if "user" not in st.session_state:
    st.session_state.user=None
    st.session_state.role=None

# ================= LOGIN =================

def login():

    st.title("🔐 Login System")

    tab1,tab2=st.tabs(["Login","Register"])

    # LOGIN

    with tab1:

        username=st.text_input("Username")
        password=st.text_input("Password",type="password")

        if st.button("Login"):

            user_c.execute(
                "SELECT role,password FROM users WHERE username=?",
                (username,)
            )

            result=user_c.fetchone()

            if result and result[1]==hash_password(password):

                st.session_state.user=username
                st.session_state.role=result[0]

                st.success("Login successful")
                st.rerun()

            else:
                st.error("Invalid login")

    # REGISTER

    with tab2:

        new_user=st.text_input("New Username")
        new_pass=st.text_input("New Password",type="password")

        if st.button("Register"):

            try:

                user_c.execute("""
                INSERT INTO users VALUES(?,?,?,?)
                """,(
                    new_user,
                    hash_password(new_pass),
                    "user",
                    datetime.now().strftime("%Y-%m-%d")
                ))

                user_conn.commit()

                st.success("User created")

            except:
                st.error("User exists")

# ================= ADMIN DASHBOARD =================

def admin_dashboard():

    st.title("📊 Admin Dashboard")

    df=pd.read_sql("SELECT * FROM investors", invest_conn)

    # stats

    if not df.empty:

        col1,col2,col3,col4=st.columns(4)

        col1.metric("Invested",df["invested"].sum())
        col2.metric("Promised",df["promised"].sum())
        col3.metric("Paid",df[df["paid"]==1]["promised"].sum())
        col4.metric("Pending",
            df["promised"].sum()-df[df["paid"]==1]["promised"].sum()
        )

    tabs=st.tabs(["Investors","Add Investor","Delete Investor"])

    # view

    with tabs[0]:

        st.dataframe(df,use_container_width=True)

    # add

    with tabs[1]:

        name=st.text_input("Name")
        mobile=st.text_input("Mobile")
        email=st.text_input("Email")
        amount=st.number_input("Amount",0)
        percent=st.slider("Return %",10,200,50)

        if st.button("Add"):

            promised=amount*(1+percent/100)

            invest_c.execute("""
            INSERT INTO investors(
            name,mobile,email,invested,promised,paid,date
            )
            VALUES(?,?,?,?,?,?,?)
            """,(
                name,mobile,email,
                amount,promised,
                0,
                datetime.now().strftime("%Y-%m-%d")
            ))

            invest_conn.commit()

            st.success("Added")
            st.rerun()

    # delete checkbox

    with tabs[2]:

        if not df.empty:

            df["Select"]=False

            edited=st.data_editor(df)

            if st.button("Delete Selected"):

                ids=edited[edited.Select==True]["id"]

                for i in ids:
                    invest_c.execute(
                        "DELETE FROM investors WHERE id=?",(int(i),)
                    )

                invest_conn.commit()

                st.success("Deleted")
                st.rerun()

# ================= USER DASHBOARD =================

def user_dashboard():

    st.title("👤 User Dashboard")

    df=pd.read_sql("SELECT * FROM investors", invest_conn)

    st.subheader("Investor Data")

    search=st.text_input("Search")

    if search:

        df=df[
            df["name"].str.contains(search,case=False) |
            df["mobile"].astype(str).str.contains(search)
        ]

    st.dataframe(df,use_container_width=True)

    # chart

    st.subheader("Investment Chart")

    if not df.empty:

        chart=df.groupby("date")["invested"].sum()

        st.line_chart(chart)

# ================= ROUTER =================

if st.session_state.user:

    st.sidebar.write("User:",st.session_state.user)
    st.sidebar.write("Role:",st.session_state.role)

    if st.sidebar.button("Logout"):

        st.session_state.user=None
        st.session_state.role=None

        st.rerun()

    if st.session_state.role=="admin":

        admin_dashboard()

    else:

        user_dashboard()

else:

    login()
