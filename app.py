from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shoptrack.db"
app.config["SECRET_KEY"] = "change-this-to-any-random-text"
db = SQLAlchemy(app)


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


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return redirect(url_for("products"))


@app.route("/products")
def products():
    all_products = Product.query.order_by(Product.name).all()
    return render_template("products.html", products=all_products)


@app.route("/products/add", methods=["GET", "POST"])
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
def delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    if product.sales:
        flash(f"Can't delete {product.name} because it has sales records.")
    else:
        db.session.delete(product)
        db.session.commit()
        flash(f"{product.name} deleted.")
    return redirect(url_for("products"))


if __name__ == "__main__":
    app.run(debug=True)