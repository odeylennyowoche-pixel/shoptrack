from datetime import datetime
from functools import wraps

import click
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shoptrack.db"
app.config["SECRET_KEY"] = "change-this-to-any-random-text"
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)   # "admin" or "cashier"

    def set_password(self, password):
        # Never store the real password, only a one-way hash of it.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)   # selling price
    cost = db.Column(db.Float, nullable=False)    # what the shop paid
    stock = db.Column(db.Integer, default=0)
    low_stock_level = db.Column(db.Integer, default=5)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    sold_at = db.Column(db.DateTime, default=datetime.now)

    product = db.relationship("Product", backref="sales")

    @property
    def total(self):
        return self.quantity * self.unit_price

    @property
    def profit(self):
        return self.quantity * (self.unit_price - self.unit_cost)


with app.app_context():
    db.create_all()


@app.cli.command("create-admin")
@click.argument("username")
@click.password_option()
def create_admin(username, password):
    """Create the first admin account: flask create-admin USERNAME"""
    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists.")
        return
    user = User(username=username, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Admin '{username}' created.")


@app.before_request
def load_logged_in_user():
    # Runs before every request: look up who is logged in (if anyone)
    # and keep them in g.user so views and templates can use it.
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash("Please log in first.")
            return redirect(url_for("login"))
        if g.user.role != "admin":
            flash("Only an admin can do that.")
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapped_view


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"].strip()).first()
        if user and user.check_password(request.form["password"]):
            session.clear()
            session["user_id"] = user.id
            flash(f"Welcome, {user.username}.")
            return redirect(url_for("home"))
        flash("Wrong username or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        role = request.form["role"]
        if role not in ("admin", "cashier"):
            flash("Invalid role.")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
        elif User.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already taken.")
        else:
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f"{role.title()} '{username}' created.")
        return redirect(url_for("users"))
    all_users = User.query.order_by(User.username).all()
    return render_template("users.html", users=all_users)


@app.route("/")
@login_required
def home():
    if g.user.role == "cashier":
        return redirect(url_for("record_sale"))
    return redirect(url_for("products"))


@app.route("/products")
@login_required
def products():
    all_products = Product.query.order_by(Product.name).all()
    return render_template("products.html", products=all_products)


@app.route("/products/add", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        product = Product(
            name=request.form["name"].strip(),
            price=float(request.form["price"]),
            cost=float(request.form["cost"]),
            stock=int(request.form["stock"]),
            low_stock_level=int(request.form["low_stock_level"]),
        )
        db.session.add(product)
        db.session.commit()
        flash(f"{product.name} added.")
        return redirect(url_for("products"))
    return render_template("add_product.html")


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = db.get_or_404(Product, product_id)
    if request.method == "POST":
        product.name = request.form["name"].strip()
        product.price = float(request.form["price"])
        product.cost = float(request.form["cost"])
        product.stock = int(request.form["stock"])
        product.low_stock_level = int(request.form["low_stock_level"])
        db.session.commit()
        flash(f"{product.name} updated.")
        return redirect(url_for("products"))
    return render_template("edit_product.html", product=product)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    if product.sales:
        flash(f"Can't delete {product.name} because it has sales records.")
    else:
        db.session.delete(product)
        db.session.commit()
        flash(f"{product.name} deleted.")
    return redirect(url_for("products"))


@app.route("/sales/new", methods=["GET", "POST"])
@login_required
def record_sale():
    if request.method == "POST":
        product = db.get_or_404(Product, int(request.form["product_id"]))
        quantity = int(request.form["quantity"])
        if quantity < 1:
            flash("Quantity must be at least 1.")
        elif quantity > product.stock:
            flash(f"Only {product.stock} {product.name} left in stock.")
        else:
            # Copy today's price and cost into the sale, so changing the
            # product's price later doesn't rewrite old sales.
            sale = Sale(
                product=product,
                quantity=quantity,
                unit_price=product.price,
                unit_cost=product.cost,
            )
            product.stock -= quantity
            db.session.add(sale)
            db.session.commit()
            flash(f"Sold {quantity} x {product.name} for ₦{sale.total:,.2f}.")
        return redirect(url_for("record_sale"))
    in_stock = Product.query.filter(Product.stock > 0).order_by(Product.name).all()
    return render_template("record_sale.html", products=in_stock)


@app.route("/sales")
@admin_required
def sales():
    recent_sales = Sale.query.order_by(Sale.sold_at.desc()).limit(50).all()
    return render_template("sales.html", sales=recent_sales)


if __name__ == "__main__":
    app.run(debug=True)