import sqlite3
from pathlib import Path
import json
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "home_design.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.executescript('''
                -- User queries table
                CREATE TABLE IF NOT EXISTS user_queries (
                    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    room_image_path TEXT
                );

                -- Products table
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

                -- Contractors table
                CREATE TABLE IF NOT EXISTS contractors (
                    contractor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    name TEXT,
                    address TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    place_id TEXT,
                    FOREIGN KEY (query_id) REFERENCES user_queries(query_id)
                );

                -- Generated images table
                CREATE TABLE IF NOT EXISTS generated_images (
                    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    room_image_path TEXT,
                    product_image_path TEXT,
                    generated_image_path TEXT,
                    generation_prompt TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES user_queries(query_id)
                );
            ''')
            conn.commit()

    def save_user_query(self, query_text: str, room_image_path: str) -> int:
        """Save a user query and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_queries (query_text, room_image_path) VALUES (?, ?)",
                (query_text, room_image_path)
            )
            return cursor.lastrowid

    def save_products(self, query_id: int, products: list):
        """Save product information."""
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

    def save_contractors(self, query_id: int, contractors: list):
        """Save contractor information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for contractor in contractors:
                cursor.execute('''
                    INSERT INTO contractors (
                        query_id, name, address, rating,
                        reviews_count, place_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    query_id,
                    contractor.get('name'),
                    contractor.get('vicinity'),
                    contractor.get('rating'),
                    contractor.get('user_ratings_total'),
                    contractor.get('place_id')
                ))

    def save_generated_image(self, query_id: int, room_image_path: str,
                           product_image_path: str, generated_image_path: str,
                           generation_prompt: str):
        """Save generated image information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO generated_images (
                    query_id, room_image_path, product_image_path,
                    generated_image_path, generation_prompt
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                query_id,
                room_image_path,
                product_image_path,
                generated_image_path,
                generation_prompt
            ))

    def get_query_history(self, limit: int = 10):
        """Get recent query history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT q.query_id, q.query_text, q.timestamp,
                       COUNT(DISTINCT p.product_id) as product_count,
                       COUNT(DISTINCT c.contractor_id) as contractor_count,
                       COUNT(DISTINCT g.image_id) as generated_image_count
                FROM user_queries q
                LEFT JOIN products p ON q.query_id = p.query_id
                LEFT JOIN contractors c ON q.query_id = c.query_id
                LEFT JOIN generated_images g ON q.query_id = g.query_id
                GROUP BY q.query_id
                ORDER BY q.timestamp DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_query_details(self, query_id: int):
        """Get detailed information for a specific query."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get query info
            cursor.execute('SELECT * FROM user_queries WHERE query_id = ?', (query_id,))
            query_info = cursor.fetchone()
            
            # Get products
            cursor.execute('SELECT * FROM products WHERE query_id = ?', (query_id,))
            products = cursor.fetchall()
            
            # Get contractors
            cursor.execute('SELECT * FROM contractors WHERE query_id = ?', (query_id,))
            contractors = cursor.fetchall()
            
            # Get generated images
            cursor.execute('SELECT * FROM generated_images WHERE query_id = ?', (query_id,))
            generated_images = cursor.fetchall()
            
            return {
                'query_info': query_info,
                'products': products,
                'contractors': contractors,
                'generated_images': generated_images
            } 