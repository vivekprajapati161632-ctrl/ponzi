import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ponzi Scheme Simulator", layout="wide")

st.title("📉 Money Gurrented Schem")
st.write("Trust your future")

# Session state initialize
if "investors" not in st.session_state:
    st.session_state.investors = []

if "total_balance" not in st.session_state:
    st.session_state.total_balance = 0

if "paid_out" not in st.session_state:
    st.session_state.paid_out = 0

# Sidebar controls
st.sidebar.header("Controls")

name = st.sidebar.text_input("Investor Name")
amount = st.sidebar.number_input("Investment Amount", min_value=0)
return_percent = st.sidebar.slider("Promised Return %", 10, 200, 50)

if st.sidebar.button("Add Investor"):
    if name and amount > 0:
        promised = amount * (1 + return_percent/100)
        st.session_state.investors.append({
            "Name": name,
            "Invested": amount,
            "Promised": promised,
            "Paid": False
        })
        st.session_state.total_balance += amount

# payout simulation
if st.sidebar.button("Pay Old Investors"):
    for investor in st.session_state.investors:
        if not investor["Paid"]:
            if st.session_state.total_balance >= investor["Promised"]:
                st.session_state.total_balance -= investor["Promised"]
                st.session_state.paid_out += investor["Promised"]
                investor["Paid"] = True
            else:
                st.error("💥 Good Return scheme.")
                break

# Reset button
if st.sidebar.button("Reset Scheme"):
    st.session_state.investors = []
    st.session_state.total_balance = 0
    st.session_state.paid_out = 0

# Display stats
col1, col2, col3 = st.columns(3)

col1.metric("Total Balance", f"₹{st.session_state.total_balance}")
col2.metric("Total Paid Out", f"₹{st.session_state.paid_out}")
col3.metric("Total Investors", len(st.session_state.investors))

# Display investors table
if st.session_state.investors:
    df = pd.DataFrame(st.session_state.investors)
    st.subheader("Investor List")
    st.dataframe(df, use_container_width=True)

# Explanation
st.markdown("---")
st.subheader("Explanation")

