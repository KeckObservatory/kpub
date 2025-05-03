import sqlite3 as sql
import psycopg2
import os
from sql_lite_db import SQLiteDB

class PostgresDB(SQLiteDB):
    def __init__(self, filename):
        self.filename = filename 
        self.con = None
        self.cursor = None
        self.connect()
        pubs_table_exists = self.con.execute(
                                """
                                SELECT FROM information_schema.tables
                                WHERE table_schema='kpub' AND table_name='pubs';
                                """).fetchone()[0]
        if not pubs_table_exists:
            self.create_table()    

    def connect(self):
        """Connect to the SQLite database."""

        # POSTGRES
        POSTGRES_HOST = os.getenv('POSTGRES_HOSTAME')
        POSTGRES_USER = os.getenv('POSTGRES_USER')
        POSTGRES_PORT = os.getenv('POSTGRES_PORT')
        POSTGRES_DB =   os.getenv('POSTGRES_DB')
        self.con = psycopg2.connect(  host=POSTGRES_HOST,
                                      database=POSTGRES_DB,
                                      user=POSTGRES_USER,
                                      port=POSTGRES_PORT)
        self.con = sql.connect(self.filename)
        self.cursor = self.con.cursor()

    def create_table(self):
        # POSTGRES
        self.con.execute("""
        CREATE TABLE pubs (
            id SERIAL PRIMARY KEY,
            bibcode TEXT UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            month TEXT NOT NULL,
            date DATE NOT NULL,
            mission TEXT,
            science TEXT,
            instruments TEXT,
            archive BOOLEAN,
            metrics JSONB
        );""")
