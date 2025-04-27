import sqlite3
from pathlib import Path

class InteriorDesignDB:
    def __init__(self, db_path: str = "interior_design.db"):
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_queries (query_text, room_image_path) VALUES (?, ?)",
                (query_text, room_image_path)
            )
            return cursor.lastrowid

    def save_generated_image(self, query_id: int, room_image_path: str,
                            product_image_path: str, generated_image_path: str,
                            generation_prompt: str):
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT q.query_id, q.query_text, q.timestamp,
                       COUNT(DISTINCT g.image_id) as generated_image_count
                FROM user_queries q
                LEFT JOIN generated_images g ON q.query_id = g.query_id
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
            cursor.execute('SELECT * FROM generated_images WHERE query_id = ?', (query_id,))
            generated_images = cursor.fetchall()
            return {
                'query_info': query_info,
                'generated_images': generated_images
            } 