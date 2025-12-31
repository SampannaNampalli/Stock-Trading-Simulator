import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    id = session["user_id"]

    shares_bought = db.execute(
        "SELECT DISTINCT(symbol) AS symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? AND transaction_type = ? GROUP BY symbol", id, "bought")
    shares_sold = db.execute(
        "SELECT DISTINCT(symbol) AS symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? AND transaction_type = ? GROUP BY symbol", id, "sold")

    net_shares = {}
    quotes = {}
    prices = {}
    total = 0

    for share_a in shares_bought:
        for share_b in shares_sold:
            if share_a["symbol"] == share_b["symbol"]:
                net_shares[share_a["symbol"]] = share_a["shares"] - share_b["shares"]

    for share_a in shares_bought:
        if share_a["symbol"] not in net_shares:
            net_shares[share_a["symbol"]] = share_a["shares"]

    cash = round(db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"], 2)
    for share in net_shares:
        quotes[share] = lookup(share)["price"]
        prices[share] = quotes[share] * net_shares[share]
        prices[share] = round(prices[share], 2)
        total += prices[share]

    total += cash
    total = round(total, 2)

    """
    for stock in net_shares:
        quote = lookup(stock["symbol"])
        stock["price"] = quote["price"]
        stock["net_total"] = stock["price"] * stock["shares"]
    """

    return render_template("index.html", total=total, shares=net_shares, cash=cash, quotes=quotes, prices=prices)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        timestamp = datetime.now()
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        quote = lookup(symbol)

        if not symbol:
            return apology("Please enter a symbol")
        elif not shares:
            return apology("Please enter the no. of shares")
        elif not shares.isdigit() or int(shares) <= 0:
            return apology("Please enter a valid no. of shares")

        if not quote:
            return apology("Symbol not found")

        price = int(shares) * quote["price"]
        id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"]

        if cash < price:
            return apology("Not enough money")

        db.execute("UPDATE users SET cash = ? WHERE id = ?", (cash - price), id)
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   id, symbol, int(shares), quote["price"], "bought", timestamp)

        flash("Bought!")

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    id = session["user_id"]

    history = db.execute(
        "SELECT symbol, shares, price, transaction_type, timestamp FROM transactions WHERE user_id = ?", id)
    quotes = {}

    for dictionary in history:
        quotes[dictionary["symbol"]] = lookup(dictionary["symbol"])["price"]
        if dictionary["transaction_type"] == "sold":
            dictionary["shares"] = (-1) * dictionary["shares"]

    return render_template("history.html", history=history, quotes=quotes)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":

        # Make a symbol variable.
        symbol = request.form.get("symbol")

        # Call lookup
        quote = lookup(symbol)

        # Check whether the entered symbol is valid.
        if not quote:
            return apology("Invalid Symbol")

        quote["price"] = float(round(quote["price"], 2))

        # Render the second template.
        return render_template("quoted.html", symbol=symbol, quote=quote)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conf = request.form.get("confirmation")

        if not username:
            return apology("Username required.")
        elif not password or not conf:
            return apology("Enter a password.")
        elif password != conf:
            return apology("Passwords do not match. Please try again")

        usernames = db.execute("SELECT username FROM users")
        for user in usernames:
            if user["username"] == username:
                return apology("Username already exists")

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   username, generate_password_hash(password))
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    id = session["user_id"]

    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        shares = int(shares)
        stocks = db.execute("SELECT DISTINCT(symbol) AS symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? GROUP BY symbol",
                            id)
        quote = lookup(symbol)["price"]
        price = quote * shares
        cash = int(db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"])
        cash += quote * shares
        timestamp = datetime.now()

        if not symbol:
            return apology("Select a symbol")
        elif not shares:
            return apology("Enter the no. of shares")
        elif shares < 0:
            return apology("Enter a valid no. of shares")

        for stock in stocks:
            if stock["symbol"] == symbol:
                if shares > stock["shares"]:
                    return apology("Not enough shares")
                else:
                    db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type, timestamp) VALUES(?, ?, ?, ?, ?, ?)",
                               id, symbol, shares, price, "sold", timestamp)

        db.execute("UPDATE users SET cash = ?", cash)
        flash("Sold!")
        return redirect("/")

    else:
        symbols = db.execute(
            "SELECT DISTINCT(symbol) AS symbol FROM transactions WHERE user_id = ?", id)
        return render_template("sell.html", symbols=symbols)


@app.route("/money", methods=["GET", "POST"])
@login_required
def money():
    """ Add money to the users account."""

    id = session["user_id"]

    if request.method == "POST":

        amount = int(request.form.get("amount"))

        if not amount:
            return apology("Enter an amount")
        if amount <= 0:
            return apology("Enter a valid amount")

        cash = int(db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"])
        cash += amount
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, id)

        flash("Money added!")
        return redirect("/")

    else:
        return render_template("money.html")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """ Change a user's password. """

    id = session["user_id"]

    if request.method == "POST":

        ex_password = request.form.get("ex_password")
        password = request.form.get("password")
        conf = request.form.get("confirmation")
        hash = db.execute("SELECT hash FROM users WHERE id = ?", id)[0]["hash"]
        new_hash = generate_password_hash(password)

        if not ex_password:
            return apology("Enter the previous password")
        elif not password:
            return apology("Enter a new password")
        elif not conf:
            return apology("Re-enter the new password")
        elif password != conf:
            return apology("The passwords do not match!")
        elif not check_password_hash(hash, ex_password):
            return apology("Enter the correct previous password")

        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, id)

        flash("Password Changed!")
        return redirect("/")

    else:
        return render_template("password.html")
