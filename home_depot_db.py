import sqlite3
from pathlib import Path

class HomeDepotDB:
    def __init__(self, db_path: str = "home_depot.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS user_queries (
                    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    room_image_path TEXT
                );
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    title TEXT,
                    price TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    product_url TEXT,
                    image_url TEXT,
                    local_image_path TEXT,
                    seller TEXT,
                    FOREIGN KEY (query_id) REFERENCES user_queries(query_id)
                );
            ''')
            conn.commit()

    def save_user_query(self, query_text: str, room_image_path: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_queries (query_text, room_image_path) VALUES (?, ?)",
                (query_text, room_image_path)
            )
            return cursor.lastrowid

    def save_products(self, query_id: int, products: list):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for product in products:
                cursor.execute('''
                    INSERT INTO products (
                        query_id, title, price, rating, reviews_count,
                        product_url, image_url, local_image_path, seller
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    query_id,
                    product.get('title'),
                    product.get('price'),
                    product.get('rating'),
                    product.get('reviews'),
                    product.get('link'),
                    product.get('image'),
                    product.get('downloaded_image_path'),
                    product.get('seller', {}).get('name')
                ))

    def get_query_history(self, limit: int = 10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT q.query_id, q.query_text, q.timestamp,
                       COUNT(DISTINCT p.product_id) as product_count
                FROM user_queries q
                LEFT JOIN products p ON q.query_id = p.query_id
                GROUP BY q.query_id
                ORDER BY q.timestamp DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_query_details(self, query_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_queries WHERE query_id = ?', (query_id,))
            query_info = cursor.fetchone()
            cursor.execute('SELECT * FROM products WHERE query_id = ?', (query_id,))
            products = cursor.fetchall()
            return {
                'query_info': query_info,
                'products': products
            } 