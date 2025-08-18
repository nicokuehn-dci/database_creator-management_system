import sqlite3

# Ask user which database to use
DB_NAME = input("Enter database name (e.g. shop.db): ") or "webstore.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def setup_database():
    conn = get_connection()
    cur = conn.cursor()

    # Customers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        password TEXT
    );
    """)

    # Products
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
    );
    """)

    # Orders
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    conn.commit()
    conn.close()

def add_customer():
    fname = input("First name: ")
    lname = input("Last name: ")
    email = input("Email: ")
    password = input("Password (⚠️ stored insecurely here, should be hashed): ")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO customers (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                (fname, lname, email, password))
    conn.commit()
    conn.close()
    print("✅ Customer added.")

def add_product():
    name = input("Product name: ")
    price = float(input("Price: "))
    stock = int(input("Stock: "))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
    conn.commit()
    conn.close()
    print("✅ Product added.")

def list_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_id, name, price, stock FROM products")
    rows = cur.fetchall()
    conn.close()

    print("\n--- Products ---")
    for r in rows:
        print(f"[{r[0]}] {r[1]} - ${r[2]} (Stock: {r[3]})")
    print("---------------\n")

def place_order():
    customer_id = int(input("Customer ID: "))
    product_id = int(input("Product ID: "))
    quantity = int(input("Quantity: "))

    conn = get_connection()
    cur = conn.cursor()

    # check stock
    cur.execute("SELECT stock FROM products WHERE product_id = ?", (product_id,))
    result = cur.fetchone()
    if not result:
        print("❌ Product not found.")
        conn.close()
        return
    stock = result[0]

    if stock < quantity:
        print("❌ Not enough stock.")
        conn.close()
        return

    # reduce stock
    cur.execute("UPDATE products SET stock = stock - ? WHERE product_id = ?", (quantity, product_id))

    # insert order
    cur.execute("INSERT INTO orders (customer_id, product_id, quantity) VALUES (?, ?, ?)",
                (customer_id, product_id, quantity))

    conn.commit()
    conn.close()
    print("✅ Order placed.")

def list_orders():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT o.order_id, c.first_name || ' ' || c.last_name AS customer,
           p.name AS product, o.quantity, o.order_date
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN products p ON o.product_id = p.product_id;
    """)
    rows = cur.fetchall()
    conn.close()

    print("\n--- Orders ---")
    for r in rows:
        print(f"Order {r[0]}: {r[1]} bought {r[3]} x {r[2]} on {r[4]}")
    print("---------------\n")

def menu():
    while True:
        print(f"\n=== Web Store Menu (DB: {DB_NAME}) ===")
        print("1. Add customer")
        print("2. Add product")
        print("3. List products")
        print("4. Place order")
        print("5. List orders")
        print("0. Exit")

        choice = input("Choose an option: ")
        if choice == "1":
            add_customer()
        elif choice == "2":
            add_product()
        elif choice == "3":
            list_products()
        elif choice == "4":
            place_order()
        elif choice == "5":
            list_orders()
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    setup_database()
    menu()
