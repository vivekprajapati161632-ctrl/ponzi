import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

# ================= CONFIG =================

st.set_page_config(
    page_title="Investment Simulation System",
    layout="wide",
    page_icon="📈"
)

DB = "simulation.db"

# ================= DATABASE =================

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

conn = get_conn()
c = conn.cursor()

# Users table

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
balance REAL DEFAULT 0,
referral TEXT,
date TEXT
)
""")

# Transactions table

c.execute("""
CREATE TABLE IF NOT EXISTS transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
type TEXT,
amount REAL,
status TEXT,
date TEXT
)
""")

conn.commit()

# ================= SECURITY =================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ================= DEFAULT ADMIN =================

def create_admin():

    c.execute("SELECT * FROM users WHERE username='admin'")

    if not c.fetchone():

        c.execute("""
        INSERT INTO users VALUES(?,?,?,?,?,?)
        """,(
            "admin",
            hash_password("admin123"),
            "admin",
            0,
            "",
            datetime.now().strftime("%Y-%m-%d")
        ))

        conn.commit()

create_admin()

# ================= SESSION =================

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

# ================= LOGIN =================

def login():

    st.title("🔐 Investment Simulation Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # LOGIN

    with tab1:

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            c.execute(
                "SELECT password, role FROM users WHERE username=?",
                (username,)
            )

            result = c.fetchone()

            if result and result[0] == hash_password(password):

                st.session_state.user = username
                st.session_state.role = result[1]

                st.success("Login successful")
                st.rerun()

            else:
                st.error("Invalid login")

    # REGISTER

    with tab2:

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        referral = st.text_input("Referral (optional)")

        if st.button("Register"):

            try:

                c.execute("""
                INSERT INTO users VALUES(?,?,?,?,?,?)
                """,(
                    new_user,
                    hash_password(new_pass),
                    "user",
                    0,
                    referral,
                    datetime.now().strftime("%Y-%m-%d")
                ))

                conn.commit()

                st.success("Registered successfully")

            except:
                st.error("User already exists")

# ================= ADMIN DASHBOARD =================

def admin_dashboard():

    st.title("📊 Admin Dashboard")

    users = pd.read_sql("SELECT * FROM users", conn)
    tx = pd.read_sql("SELECT * FROM transactions", conn)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Users", len(users))

    if not tx.empty:

        deposits = tx[tx["type"]=="deposit"]["amount"].sum()
        withdrawals = tx[tx["type"]=="withdraw"]["amount"].sum()

    else:
        deposits = 0
        withdrawals = 0

    col2.metric("Total Deposits", deposits)
    col3.metric("Total Withdrawals", withdrawals)

    st.subheader("All Transactions")

    if not tx.empty:

        edited = st.data_editor(tx)

        if st.button("Approve Selected Withdrawals"):

            selected = edited[edited.status=="pending"]

            for i in selected["id"]:

                c.execute("""
                UPDATE transactions
                SET status='approved'
                WHERE id=?
                """,(int(i),))

            conn.commit()
            st.success("Updated")
            st.rerun()

# ================= USER DASHBOARD =================

def user_dashboard():

    st.title("👤 User Dashboard")

    username = st.session_state.user

    c.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = c.fetchone()[0]

    st.metric("Balance", balance)

    tab1, tab2, tab3 = st.tabs(["Deposit","Withdraw","History"])

    # DEPOSIT

    with tab1:

        amount = st.number_input("Deposit Amount", 0.0)

        if st.button("Deposit"):

            new_balance = balance + amount

            c.execute("""
            UPDATE users SET balance=? WHERE username=?
            """,(new_balance, username))

            c.execute("""
            INSERT INTO transactions(username,type,amount,status,date)
            VALUES(?,?,?,?,?)
            """,(
                username,
                "deposit",
                amount,
                "approved",
                datetime.now().strftime("%Y-%m-%d")
            ))

            conn.commit()

            st.success("Deposit successful")
            st.rerun()

    # WITHDRAW

    with tab2:

        amount = st.number_input("Withdraw Amount", 0.0)

        if st.button("Request Withdraw"):

            if amount <= balance:

                c.execute("""
                INSERT INTO transactions(username,type,amount,status,date)
                VALUES(?,?,?,?,?)
                """,(
                    username,
                    "withdraw",
                    amount,
                    "pending",
                    datetime.now().strftime("%Y-%m-%d")
                ))

                conn.commit()

                st.success("Withdraw request submitted")

            else:

                st.error("Insufficient balance")

    # HISTORY

    with tab3:

        df = pd.read_sql(
            f"SELECT * FROM transactions WHERE username='{username}'",
            conn
        )

        st.dataframe(df)

    # PROFIT SIMULATION BUTTON

    st.subheader("Educational Profit Simulation")

    if st.button("Generate 2% Simulation Profit"):

        profit = balance * 0.02
        new_balance = balance + profit

        c.execute("""
        UPDATE users SET balance=? WHERE username=?
        """,(new_balance, username))

        conn.commit()

        st.success(f"Simulation profit added: {profit}")
        st.rerun()

# ================= ROUTER =================

if st.session_state.user:

    st.sidebar.write("User:", st.session_state.user)
    st.sidebar.write("Role:", st.session_state.role)

    if st.sidebar.button("Logout"):

        st.session_state.user = None
        st.session_state.role = None

        st.rerun()

    if st.session_state.role == "admin":

        admin_dashboard()

    else:

        user_dashboard()

else:

    login()                (username,)
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
