import sqlite3
from pathlib import Path

class ContractorsDB:
    def __init__(self, db_path: str = "contractors.db"):
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
                    location TEXT
                );
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
            ''')
            conn.commit()

    def save_user_query(self, query_text: str, location: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_queries (query_text, location) VALUES (?, ?)",
                (query_text, location)
            )
            return cursor.lastrowid

    def save_contractors(self, query_id: int, contractors: list):
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

    def get_query_history(self, limit: int = 10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT q.query_id, q.query_text, q.timestamp,
                       COUNT(DISTINCT c.contractor_id) as contractor_count
                FROM user_queries q
                LEFT JOIN contractors c ON q.query_id = c.query_id
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
            cursor.execute('SELECT * FROM contractors WHERE query_id = ?', (query_id,))
            contractors = cursor.fetchall()
            return {
                'query_info': query_info,
                'contractors': contractors
            } 