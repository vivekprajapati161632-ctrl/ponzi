import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# ================= CONFIG =================

st.set_page_config(
    page_title="Ponzi Ultra Pro",
    layout="wide",
    page_icon="📉"
)

DB="database.db"

# ================= DATABASE =================

def connect():
    return sqlite3.connect(DB, check_same_thread=False)

conn=connect()
c=conn.cursor()

# create tables

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
date TEXT
)
""")

c.execute("""
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

conn.commit()

# ================= SECURITY =================

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# create default admin

c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():

    c.execute("""
    INSERT INTO users VALUES(?,?,?,?)
    """,(
        "admin",
        hash_password("admin"),
        "admin",
        datetime.now().strftime("%Y-%m-%d")
    ))

    conn.commit()

# ================= SESSION =================

if "user" not in st.session_state:
    st.session_state.user=None
    st.session_state.role=None

# ================= LOGIN =================

def login():

    st.title("🔐 Ultra Pro Login")

    user=st.text_input("Username")
    pwd=st.text_input("Password", type="password")

    if st.button("Login"):

        c.execute(
            "SELECT role,password FROM users WHERE username=?",
            (user,)
        )

        result=c.fetchone()

        if result and result[1]==hash_password(pwd):

            st.session_state.user=user
            st.session_state.role=result[0]

            st.rerun()

        else:
            st.error("Invalid login")

# ================= STATS =================

def stats():

    df=pd.read_sql("SELECT * FROM investors", conn)

    if df.empty:
        return

    total_invested=df["invested"].sum()
    total_promised=df["promised"].sum()
    total_paid=df[df["paid"]==1]["promised"].sum()
    pending=total_promised-total_paid

    col1,col2,col3,col4=st.columns(4)

    col1.metric("Invested",f"₹{total_invested:,.0f}")
    col2.metric("Promised",f"₹{total_promised:,.0f}")
    col3.metric("Paid",f"₹{total_paid:,.0f}")
    col4.metric("Pending",f"₹{pending:,.0f}")

# ================= ADD INVESTOR =================

def add_investor():

    st.subheader("Add Investor")

    col1,col2,col3=st.columns(3)

    name=col1.text_input("Name")
    mobile=col2.text_input("Mobile")
    email=col3.text_input("Email")

    amount=st.number_input("Amount",0)
    percent=st.slider("Return %",10,200,50)

    if st.button("Add Investor"):

        promised=amount*(1+percent/100)

        c.execute("""
        INSERT INTO investors(
        name,mobile,email,invested,promised,paid,date
        )
        VALUES(?,?,?,?,?,?,?)
        """,(
            name,
            mobile,
            email,
            amount,
            promised,
            0,
            datetime.now().strftime("%Y-%m-%d")
        ))

        conn.commit()

        st.success("Added")
        st.rerun()

# ================= TABLE =================

def investor_table():

    df=pd.read_sql("SELECT * FROM investors", conn)

    if df.empty:
        st.warning("No investors")
        return

    df["Select"]=False

    edited=st.data_editor(df)

    if st.button("Delete Selected"):

        ids=edited[edited.Select==True]["id"].tolist()

        for i in ids:

            c.execute("DELETE FROM investors WHERE id=?",(i,))

        conn.commit()

        st.success("Deleted")
        st.rerun()

# ================= CHART =================

def charts():

    df=pd.read_sql("SELECT * FROM investors", conn)

    if df.empty:
        return

    st.subheader("Growth Chart")

    chart=df.groupby("date")["invested"].sum()

    st.line_chart(chart)

# ================= MAIN =================

def dashboard():

    st.title("📊 Ponzi Ultra Pro Dashboard")

    stats()

    tabs=st.tabs([
        "Investors",
        "Add",
        "Charts"
    ])

    with tabs[0]:
        investor_table()

    with tabs[1]:
        add_investor()

    with tabs[2]:
        charts()

# ================= ROUTER =================

if st.session_state.user:

    st.sidebar.write(st.session_state.user)

    if st.sidebar.button("Logout"):
        st.session_state.user=None
        st.rerun()

    dashboard()

else:

    login()
