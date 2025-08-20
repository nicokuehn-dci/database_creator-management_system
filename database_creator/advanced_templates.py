"""
Advanced templates for more complex database structures.
"""

def get_advanced_ecommerce_template():
    """Return the advanced e-commerce template definition."""
    return {
        "customers": {
            "columns": {
                "customer_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "first_name": "TEXT NOT NULL",
                "last_name": "TEXT NOT NULL",
                "email": "TEXT UNIQUE NOT NULL",
                "password_hash": "TEXT NOT NULL",
                "phone": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "last_login": "TIMESTAMP",
                "status": "TEXT DEFAULT 'active'"
            }
        },
        "customer_addresses": {
            "columns": {
                "address_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "customer_id": "INTEGER NOT NULL",
                "address_type": "TEXT DEFAULT 'shipping'",
                "street": "TEXT NOT NULL",
                "city": "TEXT NOT NULL",
                "state": "TEXT NOT NULL",
                "zip_code": "TEXT NOT NULL",
                "country": "TEXT NOT NULL",
                "is_default": "BOOLEAN DEFAULT 0"
            },
            "constraints": [
                "FOREIGN KEY (customer_id) REFERENCES customers(customer_id)"
            ]
        },
        "categories": {
            "columns": {
                "category_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "description": "TEXT",
                "parent_id": "INTEGER",
                "image_url": "TEXT",
                "active": "BOOLEAN DEFAULT 1"
            },
            "constraints": [
                "FOREIGN KEY (parent_id) REFERENCES categories(category_id)"
            ]
        },
        "suppliers": {
            "columns": {
                "supplier_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "contact_name": "TEXT",
                "email": "TEXT",
                "phone": "TEXT",
                "address": "TEXT",
                "website": "TEXT",
                "notes": "TEXT"
            }
        },
        "products": {
            "columns": {
                "product_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "sku": "TEXT UNIQUE",
                "name": "TEXT NOT NULL",
                "description": "TEXT",
                "price": "REAL NOT NULL",
                "cost": "REAL",
                "category_id": "INTEGER",
                "supplier_id": "INTEGER",
                "stock": "INTEGER DEFAULT 0",
                "weight": "REAL",
                "dimensions": "TEXT",
                "image_url": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "active": "BOOLEAN DEFAULT 1"
            },
            "constraints": [
                "FOREIGN KEY (category_id) REFERENCES categories(category_id)",
                "FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)"
            ]
        },
        "product_attributes": {
            "columns": {
                "attribute_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "product_id": "INTEGER NOT NULL",
                "name": "TEXT NOT NULL",
                "value": "TEXT NOT NULL"
            },
            "constraints": [
                "FOREIGN KEY (product_id) REFERENCES products(product_id)"
            ]
        },
        "inventory_locations": {
            "columns": {
                "location_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "address": "TEXT",
                "type": "TEXT DEFAULT 'warehouse'"
            }
        },
        "inventory": {
            "columns": {
                "inventory_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "product_id": "INTEGER NOT NULL",
                "location_id": "INTEGER NOT NULL",
                "quantity": "INTEGER NOT NULL DEFAULT 0",
                "last_updated": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            "constraints": [
                "FOREIGN KEY (product_id) REFERENCES products(product_id)",
                "FOREIGN KEY (location_id) REFERENCES inventory_locations(location_id)"
            ]
        },
        "purchase_orders": {
            "columns": {
                "po_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "supplier_id": "INTEGER NOT NULL",
                "order_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "delivery_date": "TIMESTAMP",
                "status": "TEXT DEFAULT 'pending'",
                "total_amount": "REAL",
                "notes": "TEXT"
            },
            "constraints": [
                "FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)"
            ]
        },
        "purchase_order_items": {
            "columns": {
                "item_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "po_id": "INTEGER NOT NULL",
                "product_id": "INTEGER NOT NULL",
                "quantity": "INTEGER NOT NULL",
                "unit_price": "REAL NOT NULL",
                "received_quantity": "INTEGER DEFAULT 0"
            },
            "constraints": [
                "FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)",
                "FOREIGN KEY (product_id) REFERENCES products(product_id)"
            ]
        },
        "orders": {
            "columns": {
                "order_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "customer_id": "INTEGER NOT NULL",
                "order_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "shipping_address_id": "INTEGER",
                "billing_address_id": "INTEGER",
                "shipping_method": "TEXT",
                "payment_method": "TEXT",
                "subtotal": "REAL NOT NULL",
                "tax": "REAL DEFAULT 0",
                "shipping_cost": "REAL DEFAULT 0",
                "total_amount": "REAL NOT NULL",
                "status": "TEXT DEFAULT 'pending'",
                "notes": "TEXT"
            },
            "constraints": [
                "FOREIGN KEY (customer_id) REFERENCES customers(customer_id)",
                "FOREIGN KEY (shipping_address_id) REFERENCES customer_addresses(address_id)",
                "FOREIGN KEY (billing_address_id) REFERENCES customer_addresses(address_id)"
            ]
        },
        "order_items": {
            "columns": {
                "item_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "order_id": "INTEGER NOT NULL",
                "product_id": "INTEGER NOT NULL",
                "quantity": "INTEGER NOT NULL",
                "unit_price": "REAL NOT NULL",
                "subtotal": "REAL NOT NULL",
                "discount": "REAL DEFAULT 0"
            },
            "constraints": [
                "FOREIGN KEY (order_id) REFERENCES orders(order_id)",
                "FOREIGN KEY (product_id) REFERENCES products(product_id)"
            ]
        },
        "payments": {
            "columns": {
                "payment_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "order_id": "INTEGER NOT NULL",
                "amount": "REAL NOT NULL",
                "payment_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "payment_method": "TEXT NOT NULL",
                "transaction_id": "TEXT",
                "status": "TEXT DEFAULT 'completed'"
            },
            "constraints": [
                "FOREIGN KEY (order_id) REFERENCES orders(order_id)"
            ]
        },
        "shipments": {
            "columns": {
                "shipment_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "order_id": "INTEGER NOT NULL",
                "tracking_number": "TEXT",
                "carrier": "TEXT",
                "ship_date": "TIMESTAMP",
                "delivery_date": "TIMESTAMP",
                "status": "TEXT DEFAULT 'processing'"
            },
            "constraints": [
                "FOREIGN KEY (order_id) REFERENCES orders(order_id)"
            ]
        },
        "reviews": {
            "columns": {
                "review_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "product_id": "INTEGER NOT NULL",
                "customer_id": "INTEGER NOT NULL",
                "rating": "INTEGER NOT NULL",
                "review_text": "TEXT",
                "review_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "approved": "BOOLEAN DEFAULT 0"
            },
            "constraints": [
                "FOREIGN KEY (product_id) REFERENCES products(product_id)",
                "FOREIGN KEY (customer_id) REFERENCES customers(customer_id)"
            ]
        },
        "discounts": {
            "columns": {
                "discount_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "code": "TEXT UNIQUE",
                "description": "TEXT",
                "amount": "REAL NOT NULL",
                "is_percentage": "BOOLEAN DEFAULT 1",
                "start_date": "TIMESTAMP",
                "end_date": "TIMESTAMP",
                "min_order_amount": "REAL DEFAULT 0",
                "max_uses": "INTEGER",
                "current_uses": "INTEGER DEFAULT 0",
                "active": "BOOLEAN DEFAULT 1"
            }
        }
    }
