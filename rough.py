from cs50 import SQL
from helpers import apology, login_required, lookup, usd


db = SQL("sqlite:///finance.db")

num = str("1.6")

if (float(num)).is_integer():
    print("Yes")
else:
    print("No")













"""

history = db.execute("SELECT symbol, shares, price, transaction_type, timestamp FROM transactions WHERE user_id = 2")
quotes = {}


for dictionary in history:
    quotes[dictionary["symbol"]] = 100

for dictionary in history:
    print(f"Symbol: {dictionary["symbol"]} ", end="", sep=" ")

    if dictionary["transaction_type"] == "bought":
        print(f"Shares: {dictionary["shares"]} ", end="", sep=" ")
    else:
        print(f"Shares: -{dictionary["shares"]} ", end="", sep=" ")

    print(f"Price: {quotes[dictionary["symbol"]]} ", end="", sep=" ")
    print(f"Timestamp: {dictionary["timestamp"]}")

"""

"""
shares_bought = db.execute("SELECT DISTINCT(symbol) AS symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? AND transaction_type = ? GROUP BY symbol", 2, "bought")
shares_sold = db.execute("SELECT DISTINCT(symbol) AS symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? AND transaction_type = ? GROUP BY symbol", 2, "sold")
net_shares = {}
quotes = {}
prices = {}

for share_a in shares_bought:
    for share_b in shares_sold:
        if share_a["symbol"] == share_b["symbol"]:
            net_shares[share_a["symbol"]] = share_a["shares"] - share_b["shares"]

for share_a in shares_bought:
    if share_a["symbol"] not in net_shares:
        net_shares[share_a["symbol"]] = share_a["shares"]

for share in net_shares:
    quotes[share] = 100
    prices[share] = quotes[share] * net_shares[share]

for share in net_shares:
    print(f"Symbol: {share} ", end="", sep=" ")
    print(f"Shares: {net_shares[share]} ", end="", sep=" ")
    print(f"Quote: {quotes[share]} ", end="", sep=" ")
    print(f"Total Price: {prices[share]}")
"""
