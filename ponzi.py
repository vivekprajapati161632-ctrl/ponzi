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

# ================= CREATE DEFAULT ADMIN =================

def create_admin():

    c.execute("SELECT * FROM users WHERE username=?", ("admin",))

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

    st.title("🔐 Investment Simulation System")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # LOGIN TAB

    with tab1:

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", key="login_btn"):

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
                st.error("Invalid username or password")

    # REGISTER TAB

    with tab2:

        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        referral = st.text_input("Referral (optional)", key="reg_ref")

        if st.button("Register", key="register_btn"):

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

                st.success("Registration successful")

            except sqlite3.IntegrityError:

                st.error("Username already exists")

# ================= ADMIN DASHBOARD =================

def admin_dashboard():

    st.title("📊 Admin Dashboard")

    users_df = pd.read_sql("SELECT * FROM users", conn)
    tx_df = pd.read_sql("SELECT * FROM transactions", conn)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Users", len(users_df))

    deposits = tx_df[tx_df["type"]=="deposit"]["amount"].sum() if not tx_df.empty else 0
    withdrawals = tx_df[tx_df["type"]=="withdraw"]["amount"].sum() if not tx_df.empty else 0

    col2.metric("Total Deposits", f"₹{deposits:.2f}")
    col3.metric("Total Withdrawals", f"₹{withdrawals:.2f}")

    st.subheader("Pending Withdraw Requests")

    pending = tx_df[(tx_df["type"]=="withdraw") & (tx_df["status"]=="pending")]

    if not pending.empty:

        for index, row in pending.iterrows():

            col1, col2, col3, col4 = st.columns(4)

            col1.write(row["username"])
            col2.write(f"₹{row['amount']}")
            col3.write(row["date"])

            if col4.button("Approve", key=f"approve_{row['id']}"):

                # deduct balance
                c.execute(
                    "UPDATE users SET balance = balance - ? WHERE username=?",
                    (row["amount"], row["username"])
                )

                # update transaction
                c.execute(
                    "UPDATE transactions SET status='approved' WHERE id=?",
                    (row["id"],)
                )

                conn.commit()

                st.success("Withdrawal approved")
                st.rerun()

    st.subheader("All Transactions")

    st.dataframe(tx_df, use_container_width=True)

# ================= USER DASHBOARD =================

def user_dashboard():

    username = st.session_state.user

    st.title(f"👤 Welcome, {username}")

    c.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = c.fetchone()[0]

    st.metric("Current Balance", f"₹{balance:.2f}")

    tab1, tab2, tab3 = st.tabs(["Deposit", "Withdraw", "History"])

    # ================= DEPOSIT =================

    with tab1:

        deposit_amount = st.number_input(
            "Enter Deposit Amount",
            min_value=0.0,
            step=100.0,
            key="deposit_amount"
        )

        if st.button("Deposit", key="deposit_button"):

            c.execute(
                "UPDATE users SET balance = balance + ? WHERE username=?",
                (deposit_amount, username)
            )

            c.execute("""
            INSERT INTO transactions(username,type,amount,status,date)
            VALUES(?,?,?,?,?)
            """,(
                username,
                "deposit",
                deposit_amount,
                "approved",
                datetime.now().strftime("%Y-%m-%d")
            ))

            conn.commit()

            st.success("Deposit successful")
            st.rerun()

    # ================= WITHDRAW =================

    with tab2:

        withdraw_amount = st.number_input(
            "Enter Withdraw Amount",
            min_value=0.0,
            step=100.0,
            key="withdraw_amount"
        )

        if st.button("Request Withdraw", key="withdraw_button"):

            if withdraw_amount <= balance:

                c.execute("""
                INSERT INTO transactions(username,type,amount,status,date)
                VALUES(?,?,?,?,?)
                """,(
                    username,
                    "withdraw",
                    withdraw_amount,
                    "pending",
                    datetime.now().strftime("%Y-%m-%d")
                ))

                conn.commit()

                st.success("Withdraw request submitted")

            else:

                st.error("Insufficient balance")

    # ================= HISTORY =================

    with tab3:

        df = pd.read_sql(
            "SELECT * FROM transactions WHERE username=?",
            conn,
            params=(username,)
        )

        st.dataframe(df, use_container_width=True)

    # ================= PROFIT SIMULATION =================

    st.subheader("Simulation Profit (Educational)")

    if st.button("Add 2% Simulation Profit", key="profit_button"):

        profit = balance * 0.02

        c.execute(
            "UPDATE users SET balance = balance + ? WHERE username=?",
            (profit, username)
        )

        conn.commit()

        st.success(f"Profit added: ₹{profit:.2f}")
        st.rerun()

# ================= ROUTER =================

if st.session_state.user:

    st.sidebar.write("Logged in as:", st.session_state.user)
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

    login()
