
import streamlit as st
import pandas as pd
import csv
from decimal import Decimal, InvalidOperation

st.set_page_config(
    page_title="Trade Compliance Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Portfolio Trade Order Compliance")
st.caption("Portfolio Trade Order Compliance & Execution Checker")

portfolios = {
    "POR001": {
        "cash_balance": 20000,
        "restricted_securities": ["XYZCORP"],
        "max_position_pct": Decimal("0.40"),
        "current_holdings": [
            ("AAPL", 100, 150),
            ("TCS", 50, 310)
        ]
    },
    "POR002": {
        "cash_balance": 10000,
        "restricted_securities": [],
        "max_position_pct": Decimal("0.50"),
        "current_holdings": []
    },
    "POR003": {
        "cash_balance": 50000,
        "restricted_securities": ["BADCO"],
        "max_position_pct": Decimal("0.30"),
        "current_holdings": [
            ("RELIANCE", 30, 2400),
            ("INFY", 20, 1500)
        ]
    },
    "POR004": {
        "cash_balance": 45000,
        "restricted_securities": [],
        "max_position_pct": Decimal("0.40"),
        "current_holdings": []
    },
    "POR005": {
        "cash_balance": 10000,
        "restricted_securities": ["PENNY1"],
        "max_position_pct": Decimal("0.10"),
        "current_holdings": [
            ("INFY", 20, 2000)
        ]
    }
}

def check_trade(trade):
    portfolio_id = trade["portfolio_id"]
    security_id = trade["security_id"]
    action = trade["action"]
    # Step 1: Validate input
    try:
        quantity = Decimal(str(trade["quantity"]))
        price = Decimal(str(trade["price"]))
    except (InvalidOperation, TypeError, ValueError):
        return "Rejected", "Invalid trade data."
    if (
        not quantity.is_finite()
        or not price.is_finite()
        or quantity <= 0
        or price <= 0
        or action not in ["Buy", "Sell"]
    ):
        return "Rejected", "Invalid trade data."
    portfolio = portfolios.get(portfolio_id)
    if portfolio is None:
        return "Rejected", "Unknown portfolio."

    cash = portfolio["cash_balance"]
    holdings = portfolio["current_holdings"]

    # Step 2: Restricted security check
    if security_id in portfolio["restricted_securities"]:
        return "Rejected", "Security is restricted for this portfolio."

    # Find existing holdings
    existing_quantity = 0

    for sid, qty, market_price in holdings:
        if sid == security_id:
            existing_quantity += qty

    # Step 3: Sell validation
    if action == "Sell":
        if existing_quantity < quantity:
            return "Rejected", "Insufficient holdings to sell."

    # Step 4: Buy affordability
    if action == "Buy":
        cost = quantity * price
        if cost > cash:
            return "Rejected", "Insufficient cash for this buy order."

        # Step 5: Position concentration
        post_trade_cash = cash - cost
        post_trade_quantity = existing_quantity + quantity
        security_value = post_trade_quantity * price
        other_holdings_value = 0

        for sid, qty, market_price in holdings:
            if sid != security_id:
                other_holdings_value += qty * market_price

        total_portfolio_value = (
            post_trade_cash
            + security_value
            + other_holdings_value
        )
        position_pct = security_value / total_portfolio_value
        if position_pct > portfolio["max_position_pct"]:
            return (
                "Needs Manual Sign-off",
                "Exceeds maximum position concentration — requires approval."
            )

    # Step 6: Approved
    return "Approved", "All checks passed."

st.sidebar.header("Trade Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload trades CSV",
    type=["csv"]
)

if uploaded_file is not None:
    trades_df = pd.read_csv(uploaded_file)
else:
    try:
        trades_df = pd.read_csv("trades_test.csv")
        st.sidebar.success("Using trades_test.csv")
    except FileNotFoundError:
        st.info("Please upload your trades_test.csv file to begin.")
        st.stop()

required_columns = [
    "portfolio_id",
    "security_id",
    "action",
    "quantity",
    "price",
    "security_type"
]

missing_columns = [
    col for col in required_columns
    if col not in trades_df.columns
]

if missing_columns:
    st.error(f"Missing CSV columns: {missing_columns}")
    st.stop()

results = []

for _, trade in trades_df.iterrows():
    trade_data = trade.to_dict()
    decision, reason = check_trade(trade_data)
    results.append({
        "portfolio_id": trade_data["portfolio_id"],
        "security_id": trade_data["security_id"],
        "action": trade_data["action"],
        "quantity": trade_data["quantity"],
        "price": trade_data["price"],
        "security_type": trade_data["security_type"],
        "decision": decision,
        "reason": reason
    })

results_df = pd.DataFrame(results)
st.subheader("Trade Compliance Overview")
total = len(results_df)
approved = (results_df["decision"] == "Approved").sum()
rejected = (results_df["decision"] == "Rejected").sum()
manual = (
    results_df["decision"] == "Needs Manual Sign-off"
).sum()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Trades", total)
col2.metric("Approved", approved)
col3.metric("Rejected", rejected)
col4.metric("Manual Sign-off", manual)
st.divider()

st.subheader("Decision Distribution")

chart_data = pd.DataFrame({
    "Decision": [
        "Approved",
        "Rejected",
        "Needs Manual Sign-off"
    ],
    "Count": [
        approved,
        rejected,
        manual
    ]
})

col1, col2 = st.columns(2)
with col1:
    st.bar_chart(
        chart_data.set_index("Decision")
    )

with col2:
    st.write("### Decision Summary")
    st.write(f"✅ Approved: {approved}")
    st.write(f"❌ Rejected: {rejected}")
    st.write(f"⚠️ Manual Sign-off: {manual}")

st.divider()
st.subheader("Trade Details")
col1, col2 = st.columns(2)

with col1:
    portfolio_filter = st.selectbox(
        "Filter by Portfolio",
        ["All"] + sorted(
            results_df["portfolio_id"].dropna().unique().tolist()
        )
    )

with col2:
    decision_filter = st.selectbox(
        "Filter by Decision",
        [
            "All",
            "Approved",
            "Rejected",
            "Needs Manual Sign-off"
        ]
    )
filtered_df = results_df.copy()
if portfolio_filter != "All":
    filtered_df = filtered_df[
        filtered_df["portfolio_id"] == portfolio_filter
    ]
if decision_filter != "All":
    filtered_df = filtered_df[
        filtered_df["decision"] == decision_filter
    ]
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)
st.write(
    f"Showing {len(filtered_df)} of {total} trades"
)
st.divider()
st.subheader("Download Compliance Report")
csv_data = results_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Compliance Report",
    data=csv_data,
    file_name="trade_compliance_report.csv",
    mime="text/csv"
)
st.success("Trade compliance analysis completed!")