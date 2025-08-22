import sqlite3
import random
import datetime
import os
from pathlib import Path


def populate_music_library(db_path):
    """Populate the music library database."""
    print(f"Populating music library database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM artists")
    cursor.execute("DELETE FROM albums")
    cursor.execute("DELETE FROM songs")
    cursor.execute("DELETE FROM playlists")
    cursor.execute("DELETE FROM playlist_songs")
    
    # Sample artists
    artists = [
        (1, "The Algorithms", "France", 2010, "Electronic music producer collective"),
        (2, "Code and Keys", "USA", 2008, "Indie rock band with programming themes"),
        (3, "Binary Beats", "Germany", 2015, "Electronic music duo"),
        (4, "Recursive Funk", "UK", 2012, "Jazz-funk fusion group"),
        (5, "Loop Quantum", "Japan", 2018, "Experimental electronic ensemble"),
        (6, "Syntax Error", "Canada", 2011, "Punk rock band"),
        (7, "Data Structures", "Sweden", 2014, "Progressive metal band"),
        (8, "Function Junction", "Australia", 2016, "Folk rock group"),
        (9, "Variable Jazz", "Italy", 2009, "Jazz trio"),
        (10, "Null Reference", "Brazil", 2019, "Alternative rock band")
    ]
    
    # Insert artists
    cursor.executemany(
        "INSERT INTO artists (artist_id, name, country, formed_year, bio) VALUES (?, ?, ?, ?, ?)",
        artists
    )
    
    # Sample albums
    albums = [
        (1, "Algorithmic Dreams", 1, 2018, "Electronic", "algo_dreams.jpg"),
        (2, "Code Complete", 2, 2015, "Indie Rock", "code_complete.jpg"),
        (3, "Binary Sunset", 3, 2019, "Electronic", "binary_sunset.jpg"),
        (4, "Recursive Grooves", 4, 2016, "Jazz-Funk", "recursive_grooves.jpg"),
        (5, "Quantum States", 5, 2020, "Experimental", "quantum_states.jpg"),
        (6, "Exception Handled", 6, 2017, "Punk Rock", "exception_handled.jpg"),
        (7, "Tree Traversal", 7, 2018, "Progressive Metal", "tree_traversal.jpg"),
        (8, "Return Values", 8, 2019, "Folk Rock", "return_values.jpg"),
        (9, "Dynamic Types", 9, 2014, "Jazz", "dynamic_types.jpg"),
        (10, "Memory Leak", 10, 2020, "Alternative", "memory_leak.jpg"),
        (11, "Compiled Thoughts", 1, 2020, "Electronic", "compiled_thoughts.jpg"),
        (12, "Debugging Sessions", 2, 2018, "Indie Rock", "debugging_sessions.jpg"),
        (13, "Loop Invariant", 4, 2018, "Jazz-Funk", "loop_invariant.jpg"),
        (14, "Stack Overflow", 6, 2019, "Punk Rock", "stack_overflow.jpg"),
        (15, "Big-O Notation", 7, 2020, "Progressive Metal", "big_o.jpg")
    ]
    
    # Insert albums
    cursor.executemany(
        "INSERT INTO albums (album_id, title, artist_id, release_year, genre, cover_art) VALUES (?, ?, ?, ?, ?, ?)",
        albums
    )
    
    # Sample songs - 5 songs per album
    songs = []
    song_id = 1
    
    for album_id in range(1, 16):
        for track in range(1, 6):
            duration = random.randint(180, 360)  # 3-6 minutes in seconds
            title = f"Track {track} - Album {album_id}"
            
            if album_id == 1:
                titles = ["Algorithm One", "Recursive Beat", "Stack Overflow", "Memory Allocation", "Garbage Collection"]
                title = titles[track-1]
            elif album_id == 2:
                titles = ["Compile Time", "Runtime Error", "Debug Mode", "Clean Code", "Final Build"]
                title = titles[track-1]
            
            songs.append((song_id, title, album_id, track, duration, "Lyrics not available"))
            song_id += 1
    
    # Insert songs
    cursor.executemany(
        "INSERT INTO songs (song_id, title, album_id, track_number, duration, lyrics) VALUES (?, ?, ?, ?, ?, ?)",
        songs
    )
    
    # Sample playlists
    playlists = [
        (1, "Coding Session", datetime.datetime.now().isoformat(), "Music to code to"),
        (2, "Workout Mix", datetime.datetime.now().isoformat(), "Energetic songs"),
        (3, "Relaxation", datetime.datetime.now().isoformat(), "Calm and soothing tracks"),
        (4, "Party Time", datetime.datetime.now().isoformat(), "Upbeat songs for gatherings"),
        (5, "Focus Mode", datetime.datetime.now().isoformat(), "Concentration enhancers")
    ]
    
    # Insert playlists
    cursor.executemany(
        "INSERT INTO playlists (playlist_id, name, created_at, description) VALUES (?, ?, ?, ?)",
        playlists
    )
    
    # Sample playlist songs - random songs in each playlist
    playlist_songs = []
    entry_id = 1
    
    for playlist_id in range(1, 6):
        # Get random songs (at most 10, but no more than available)
        max_songs = min(10, song_id - 1)
        playlist_tracks = random.sample(range(1, song_id), max_songs)
        for position, track_id in enumerate(playlist_tracks, 1):
            playlist_songs.append((entry_id, playlist_id, track_id, position))
            entry_id += 1
    
    # Insert playlist songs
    cursor.executemany(
        "INSERT INTO playlist_songs (id, playlist_id, song_id, position) VALUES (?, ?, ?, ?)",
        playlist_songs
    )
    
    conn.commit()
    conn.close()
    print(f"Music library database populated successfully!")


def populate_shop(db_path, is_webstore=False):
    """Populate the shop or webstore database."""
    shop_type = "webstore" if is_webstore else "shop"
    print(f"Populating {shop_type} database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM orders")
    
    # Sample customers
    customers = [
        (1, "John", "Doe", "john.doe@example.com", "password123"),
        (2, "Jane", "Smith", "jane.smith@example.com", "secure456"),
        (3, "Alice", "Johnson", "alice.j@example.com", "alice2023"),
        (4, "Bob", "Brown", "bob.brown@example.com", "bobpass"),
        (5, "Charlie", "Davis", "charlie.d@example.com", "char123"),
        (6, "Diana", "Evans", "diana.e@example.com", "diana2023"),
        (7, "Edward", "Foster", "edward.f@example.com", "edpass"),
        (8, "Fiona", "Garcia", "fiona.g@example.com", "fionaG"),
        (9, "George", "Harris", "george.h@example.com", "geo456"),
        (10, "Hannah", "Ingram", "hannah.i@example.com", "hannah!")
    ]
    
    # Insert customers
    cursor.executemany(
        "INSERT INTO customers (customer_id, first_name, last_name, email, password) VALUES (?, ?, ?, ?, ?)",
        customers
    )
    
    # Sample products for shop
    if not is_webstore:
        products = [
            (1, "Coffee Mug", 12.99, 50),
            (2, "T-Shirt", 19.99, 30),
            (3, "Notebook", 5.99, 100),
            (4, "Pen Set", 8.99, 75),
            (5, "Water Bottle", 15.99, 40),
            (6, "Laptop Sleeve", 24.99, 25),
            (7, "Phone Case", 18.99, 60),
            (8, "Desk Lamp", 29.99, 20),
            (9, "Mouse Pad", 7.99, 90),
            (10, "Wireless Charger", 22.99, 35),
            (11, "Headphones", 49.99, 15),
            (12, "Bluetooth Speaker", 39.99, 25),
            (13, "Backpack", 34.99, 30),
            (14, "Sunglasses", 15.99, 40),
            (15, "Umbrella", 11.99, 50)
        ]
    # Sample products for webstore (electronics focused)
    else:
        products = [
            (1, "Laptop", 899.99, 20),
            (2, "Smartphone", 699.99, 30),
            (3, "Tablet", 349.99, 25),
            (4, "Wireless Earbuds", 129.99, 40),
            (5, "Smart Watch", 199.99, 35),
            (6, "External SSD 1TB", 149.99, 50),
            (7, "Mechanical Keyboard", 89.99, 30),
            (8, "Gaming Mouse", 59.99, 45),
            (9, "Webcam", 79.99, 25),
            (10, "Bluetooth Speaker", 69.99, 40),
            (11, "4K Monitor", 299.99, 15),
            (12, "Graphics Card", 499.99, 10),
            (13, "Wireless Router", 119.99, 30),
            (14, "USB-C Hub", 49.99, 50),
            (15, "Power Bank", 39.99, 60)
        ]
    
    # Insert products
    cursor.executemany(
        "INSERT INTO products (product_id, name, price, stock) VALUES (?, ?, ?, ?)",
        products
    )
    
    # Sample orders - Generate random orders from the past 30 days
    orders = []
    order_id = 1
    
    for _ in range(50):  # Generate 50 orders
        customer_id = random.randint(1, 10)
        product_id = random.randint(1, 15)
        quantity = random.randint(1, 5)
        
        # Random date in the past 30 days
        days_ago = random.randint(0, 30)
        order_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).isoformat()
        
        orders.append((order_id, customer_id, product_id, quantity, order_date))
        order_id += 1
    
    # Insert orders
    cursor.executemany(
        "INSERT INTO orders (order_id, customer_id, product_id, quantity, order_date) VALUES (?, ?, ?, ?, ?)",
        orders
    )
    
    conn.commit()
    conn.close()
    print(f"{shop_type.capitalize()} database populated successfully!")


def populate_test_db(db_path):
    """Populate the test database with more sample data."""
    print(f"Populating test database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add more test records
    test_records = [
        (3, "Test Record 3", 123.45),
        (4, "Test Record 4", 67.89),
        (5, "Test Record 5", 234.56),
        (6, "Test Record 6", 78.90),
        (7, "Test Record 7", 345.67),
        (8, "Test Record 8", 89.01),
        (9, "Test Record 9", 456.78),
        (10, "Test Record 10", 90.12)
    ]
    
    # Insert test records
    cursor.executemany(
        "INSERT INTO test (id, name, value) VALUES (?, ?, ?)",
        test_records
    )
    
    conn.commit()
    conn.close()
    print(f"Test database populated successfully!")


if __name__ == "__main__":
    # Create databases directory if it doesn't exist
    Path("databases").mkdir(exist_ok=True)
    
    # Populate music library database
    populate_music_library("database.db")
    
    # Populate shop database
    populate_shop("sample_databases/shop.db")
    
    # Populate webstore database
    populate_shop("sample_databases/webstore.db", is_webstore=True)
    
    # Populate music library database in sample_databases folder
    # First check what schema it has - if it has a music schema, populate accordingly
    conn = sqlite3.connect("sample_databases/musiclibrary.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']
    conn.close()
    
    # If it has shop tables, populate with shop data
    if set(tables) == set(['customers', 'products', 'orders']):
        populate_shop("sample_databases/musiclibrary.db", is_webstore=False)
    else:
        print("Warning: musiclibrary.db doesn't have expected schema. Skipping.")
    
    # Populate test database
    populate_test_db("databases/test.db")
    
    print("\nAll databases have been successfully populated with test data!")
