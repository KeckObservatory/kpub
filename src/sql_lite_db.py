import sqlite3 as sql
import json
import logging


log = logging.getLogger('kpub')

class SQLiteDB:
    def __init__(self, filename):
        self.filename = filename 
        self.con = None
        self.cursor = None
        self.connect()
        pubs_table_exists = self.con.execute(
                                """
                                   SELECT COUNT(*) FROM sqlite_master
                                   WHERE type='table' AND name='pubs';
                                """).fetchone()[0]
        if not pubs_table_exists:
            self.create_table()    
    def __del__(self):
        """Destructor to close the database connection."""
        self.close()


    def connect(self):
        """Connect to the SQLite database."""
        self.con = sql.connect(self.filename)
        self.cursor = self.con.cursor()

    def create_table(self):
        self.con.execute("""
                         CREATE TABLE pubs (
                                id INTEGER PRIMARY KEY,
                                bibcode TEXT UNIQUE,
                                year INTEGER,
                                month TEXT,
                                date TEXT,
                                mission TEXT,
                                snippits TEXT,
                                instruments TEXT,
                                archive TEXT,
                                metrics TEXT, 
                                affiliation TEXT,
                                date_modified TEXT DEFAULT (DATETIME('now')),
                                last_modifier TEXT DEFAULT 'kpub');
                                """)

    def close(self):
        """Close the SQLite database connection."""
        if self.con:
            self.con.close()

    def add_row(self, article, month, mission, snippits, instruments, archive, affiliation):
        
        #insert to db
        try:
            cur = self.con.execute("INSERT INTO pubs "
                "(id, bibcode, year, month, date, mission, snippits, instruments, archive, affiliation, metrics) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [article['id'], article['bibcode'], article['year'], month, article['pubdate'],
                mission, json.dumps(snippits), instruments, archive, affiliation, json.dumps(article)])
            log.info(f"Inserted {article['bibcode']}")
            self.con.commit()
        except sql.IntegrityError:
            log.warning('{} was already ingested.'.format(article['bibcode']))

    def delete_by_bibcode(self, bibcode):
        cur = self.con.execute("DELETE FROM pubs WHERE bibcode = ?;", [bibcode])
        log.info('Deleted {} row(s).'.format(cur.rowcount))
        self.con.commit()

    def query(self, mission=None, year=None):
        """Query the database by mission and/or year.

        Parameters
        ----------
        mission : str
            Examples: 'kepler' or 'k2'
        year : int or list of int
            Examples: 2009, 2010, [2009, 2010], ...

        Returns
        -------
        rows : list
            List of SQLite result rows.
        """
        # Build the query
        if mission is None:
            where = "(mission != 'unrelated') "
        else:
            where = "(mission = '{}') ".format(mission)

        if year is not None:
            if isinstance(year, (list, tuple)):  # Multiple years?
                str_year = ["'{}'".format(y) for y in year]
                where += " AND year IN (" + ", ".join(str_year) + ")"
            else:
                where += " AND year = '{}' ".format(year)

        cols = ['year', 'month', 'metrics', 'bibcode']
        query = "SELECT " + ", ".join(cols)
        query += " FROM pubs WHERE {} ".format(where)
        query += " ORDER BY date DESC;"
        # Execute the query
        log.debug(query)
        cur = self.con.execute(query)
        rows = cur.fetchall()
        # Convert to a list of dictionaries
        rows = [ { key:val for key, val in zip(cols, row) } for row in rows]
        return rows

    def get_metadata(self, bibcode):
        """Returns a dictionary of the raw metadata given a bibcode."""
        cur = self.con.execute("SELECT metrics FROM pubs WHERE bibcode = ?;", [bibcode])
        return json.loads(cur.fetchone()[0])

    def get_snippits(self, bibcode):
        """Returns a dictionary of the snippits given a bibcode."""
        cur = self.con.execute("SELECT snippits FROM pubs WHERE bibcode = ?;", [bibcode])
        snippit = json.loads(cur.fetchone()['snippits'])
        return snippit 

    def article_exists(self, article):
        count = self.con.execute("SELECT COUNT(*) FROM pubs WHERE id = ? OR bibcode = ?;",
                                 [article['id'], article['bibcode']]).fetchone()[0]
        return bool(count)

    def select_for_export(self, archive=None):
        cols = ['bibcode', 'mission', 'instruments', 'archive', 'affiliation', 'date_modified', 'last_modifier']
        query = "SELECT " + ", ".join(cols)
        query += " FROM pubs WHERE mission != 'unrelated' "
        if archive: 
            query += " AND archive='1' "
        query += " ORDER BY bibcode asc;"
        rows = self.con.execute(query).fetchall()
        rows = [ { key:val for key, val in zip(cols, row) } for row in rows]
        return rows

    def select_for_spreadsheet(self):
        cols = ['bibcode', 'year', 'month', 'date', 'mission', 'metrics', 'affiliation', 'date_modified', 'last_modifier']
        query = "SELECT " + ", ".join(cols)
        query += " FROM pubs WHERE mission != 'unrelated' "
        query += " ORDER BY bibcode asc;"
        rows = self.con.execute(query).fetchall()
        rows = [ { key:val for key, val in zip(cols, row) } for row in rows]
        return rows


    def get_articles_by_mission_years(self, mission, year_begin, year_end):
        #query
        cols = ['year', 'metrics']
        cur = self.con.execute(f"select {', '.join(cols)} from pubs "
                               f" where mission='{mission}' "
                               f" and year >= '{year_begin}'"
                               f" and year <= '{year_end}'"
                               )
        articles = cur.fetchall()
        articles = [ { key:val for key, val in zip(cols, row) } for row in articles]
        return articles

    def get_articles_by_mission_years_instrument(self, mission, year_begin, year_end, instrument):
        cols = ['year', 'COUNT(*)']
        q = f"SELECT {', '.join(cols)} FROM pubs "
        q += f" WHERE mission = '{mission}' "
        q += f" AND year >= '{year_begin}' "
        q += f" AND year <= '{year_end}' "
        if instrument: 
            q += f" AND instruments like '%{instrument}%' "
        q += " GROUP BY year;"
        cur = self.con.execute(q)
        rows = list(cur.fetchall())
        rows = [ { key:val for key, val in zip(cols, row) } for row in rows]
        return rows

    def get_count_cumulative(self, mission, year):
        cur = self.con.execute("SELECT COUNT(*) FROM pubs "
                                "WHERE mission = ? "
                                "AND year <= ?;",
                                [mission, year])
        return cur.fetchone()[0]