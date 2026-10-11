# ShopTrack

ShopTrack is a simple inventory and sales system for a small shop, written in
Python with Flask. The owner (admin) manages products and prices, cashiers
record sales, and stock goes down automatically with every sale. A dashboard
shows revenue and profit for today, this week and all time, the best-selling
products, and which products are running low.

## Features

- **Products**: add, edit, delete and list products with selling price, cost price and stock
- **Sales**: record a sale; the price and cost at the time of sale are saved with it
- **Stock tracking**: stock is reduced on each sale, overselling is blocked, and
  products at or below their warning level are marked LOW
- **Admin and cashier roles**: admins can do everything; cashiers can only view
  products and record sales
- **Dashboard** (admin only): items sold, revenue and profit for today, this week
  and all time, the top 5 products, and a low-stock list

## Tech stack

- Python 3.10 or newer
- Flask (web framework)
- Flask-SQLAlchemy (database models)
- SQLite (database file, created automatically)
- HTML templates (Jinja2) and plain CSS

## Setup (Windows)

Open Command Prompt in the `shoptrack` folder and run:

```
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

(`py` is the Python launcher for Windows. If it is missing, use `python -m venv venv`.)

Create the demo admin account (it asks for the password twice):

```
flask create-admin admin
```

Start the app:

```
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

The database is created automatically at `instance\shoptrack.db`. Always run
the commands from inside the `shoptrack` folder: started from another folder,
the app creates and uses a separate, empty database there.

## Demo login details

| Role    | Username  | Password     |
|---------|-----------|--------------|
| Admin   | `admin`   | `admin123`   |
| Cashier | `cashier` | `cashier123` |

These accounts are not built in. Create them after setup:

1. Run `flask create-admin admin` and enter `admin123` as the password.
2. Log in as `admin`, open **Users**, and create the user `cashier` with the
   password `cashier123` and the role Cashier.

**Note:** these passwords are for testing and demonstration only. Use strong,
private passwords for real use, and change `SECRET_KEY` in `app.py` to a long
random value.
