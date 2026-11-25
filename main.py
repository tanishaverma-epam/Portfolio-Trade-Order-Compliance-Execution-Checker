import csv
from decimal import Decimal, InvalidOperation

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

    # Step 1: Validate trade data
    try:
        quantity = Decimal(trade["quantity"])
        price = Decimal(trade["price"])
    except (InvalidOperation, TypeError):
        return "Rejected", "Invalid trade data."

    if (not quantity.is_finite()
            or not price.is_finite()
            or quantity <= 0
            or price <= 0
            or action not in ["Buy", "Sell"]):

        return "Rejected", "Invalid trade data."

    portfolio = portfolios.get(portfolio_id)

    if portfolio is None:
        return "Rejected", "Unknown portfolio."

    cash = portfolio["cash_balance"]
    holdings = portfolio["current_holdings"]

    # Step 2: Restricted security check
    if security_id in portfolio["restricted_securities"]:
        return "Rejected", "Security is restricted for this portfolio."

    # Find existing quantity of the security
    existing_quantity = 0

    for sid, qty, market_price in holdings:
        if sid == security_id:
            existing_quantity += qty

    # Step 3: Sell check
    if action == "Sell":
        if existing_quantity < quantity:
            return "Rejected", "Insufficient holdings to sell."

    # Step 4: Buy affordability check
    if action == "Buy":

        cost = quantity * price

        if cost > cash:
            return "Rejected", "Insufficient cash for this buy order."

        # Step 5: Position concentration check
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

    # Step 6: All checks passed
    return "Approved", "All checks passed."

# Read CSV file and process all trades

with open("trades_test.csv", "r", newline="") as file:

    trades = csv.DictReader(file)

    for trade in trades:

        decision, reason = check_trade(trade)

        print("Portfolio:", trade["portfolio_id"])
        print("Security:", trade["security_id"])
        print("Action:", trade["action"])
        print("Quantity:", trade["quantity"])
        print("Decision:", decision)
        print("Reason:", reason)

        print("-" * 50)