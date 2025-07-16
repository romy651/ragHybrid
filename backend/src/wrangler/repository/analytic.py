import os
from pathlib import Path
import sqlite3
import csv

from wrangler.model.product import Product


default_analytic_directory = Path("src/store/analytic.sqlite")

class Analytic: 
    """
    Analytic class to manage the database connection and create the database tables
    """
    def __init__(self, db_path: Path = default_analytic_directory):
        self.db_path = db_path
        self._connection = self.create_db()

    def create_db(self) -> sqlite3.Connection:
        """
        Create the database tables
        """
        db = sqlite3.connect(self.db_path)

        # if not exists we create the table documents
        db.execute("""CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY, 
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                turnover TEXT NOT NULL,
                launch_date DATE NOT NULL,
                country TEXT NOT NULL,
                segment TEXT CHECK(segment IN ('Low', 'Medium', 'High')) NOT NULL
            )
        """)
        db.commit()
        return db
    
    def create_product(self, file_path: Path) -> None:
        """
        add data from csv file to the product table
        """
        with file_path.open('r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            cursor = self._connection.cursor()
            for row in csv_reader:
                product = Product(
                    name=row['name'],
                    description=row['description'],
                    turnover=row['turnover'],
                    launch_date=row['launch_date'],
                    country=row['country'],
                    segment=row['segment']
                )
                cursor.execute(
                    "INSERT INTO products (name, description, turnover, launch_date, country, segment) VALUES (?, ?, ?, ?, ?, ?)",
                    (product.name, product.description, product.turnover, product.launch_date, product.country, product.segment)
                )
            self._connection.commit()
    
    def get_table_schema(self) -> dict:
        """
        Get the table schema
        """
        cursor = self._connection.cursor()
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        return {
            "table_name": "products",
            "columns": [
                {
                    "column_name": column[1],
                    "data_type": column[2],
                    "is_nullable": column[3],
                    "default_value": column[4],
                    "primary_key": column[5]
                } for column in columns
            ]
        }
    
    def execute_query(self, query: str) -> list:
        """
        Execute a query over the sqlite database
        """
        cursor = self._connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()
        
    
    def close(self) -> None:
        """
        Close the database connection
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None





