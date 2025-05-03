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

        # POSTGRES
        # POSTGRES_HOST = os.getenv('POSTGRES_HOSTAME')
        # POSTGRES_USER = os.getenv('POSTGRES_USER')
        # POSTGRES_PORT = os.getenv('POSTGRES_PORT')
        # POSTGRES_DB = os.getenv('POSTGRES_DB')
        # self.con = psycopg2.connect(  host=POSTGRES_HOST,
        #                               database=POSTGRES_DB,
        #                               user=POSTGRES_USER,
        #                               port=POSTGRES_PORT)
        # """
        #     SELECT  
        #     WHERE table_schema='kpub' AND table_name='pubs';
        # """
        self.con = sql.connect(self.filename)
        self.cursor = self.con.cursor()

    def create_table(self):
        # POSTGRES
        # """
        # CREATE TABLE pubs (
        #     id SERIAL PRIMARY KEY,
        #     bibcode TEXT UNIQUE NOT NULL,
        #     year INTEGER NOT NULL,
        #     month TEXT NOT NULL,
        #     date DATE NOT NULL,
        #     mission TEXT,
        #     science TEXT,
        #     instruments TEXT,
        #     archive BOOLEAN,
        #     metrics JSONB
        # );"""
        self.con.execute("""
                         CREATE TABLE pubs(
                                id UNIQUE,
                                bibcode UNIQUE,
                                year,
                                month,
                                date,
                                mission,
                                science,
                                instruments,
                                archive,
                                metrics)""")

    def close(self):
        """Close the SQLite database connection."""
        if self.con:
            self.con.close()

    def add_row(self, article, month, mission, science, instruments, archive):
        
        #insert to db
        try:
            cur = self.con.execute("INSERT INTO pubs "
                "(id, bibcode, year, month, date, mission, science, instruments, archive, metrics) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [article['id'], article['bibcode'], article['year'], month, article['pubdate'],
                mission, science, instruments, archive, json.dumps(article)])
            log.info(f"Inserted {article['bibcode']}")
            self.con.commit()
        except sql.IntegrityError:
            log.warning('{} was already ingested.'.format(article['bibcode']))

    def delete_by_bibcode(self, bibcode):
        cur = self.con.execute("DELETE FROM pubs WHERE bibcode = ?;", [bibcode])
        log.info('Deleted {} row(s).'.format(cur.rowcount))
        self.con.commit()

    def query(self, mission=None, science=None, year=None):
        """Query the database by mission and/or science and/or year.

        Parameters
        ----------
        mission : str
            Examples: 'kepler' or 'k2'
        science : str
            Examples: 'exoplanets' or 'astrophysics'
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

        if science is not None:
            where += " AND science = '{}' ".format(science)

        if year is not None:
            if isinstance(year, (list, tuple)):  # Multiple years?
                str_year = ["'{}'".format(y) for y in year]
                where += " AND year IN (" + ", ".join(str_year) + ")"
            else:
                where += " AND year = '{}' ".format(year)

        cur = self.con.execute("SELECT year, month, metrics, bibcode "
                               "FROM pubs "
                               "WHERE {} "
                               "ORDER BY date DESC; ".format(where))
        return cur.fetchall()

    def get_metadata(self, bibcode):
        """Returns a dictionary of the raw metadata given a bibcode."""
        cur = self.con.execute("SELECT metrics FROM pubs WHERE bibcode = ?;", [bibcode])
        return json.loads(cur.fetchone()[0])

    def article_exists(self, article):
        count = self.con.execute("SELECT COUNT(*) FROM pubs WHERE id = ? OR bibcode = ?;",
                                 [article['id'], article['bibcode']]).fetchone()[0]
        return bool(count)

    def select_for_export(self, archive=None):
        query = "SELECT bibcode, mission, science, instruments, archive "
        query += " FROM pubs WHERE mission != 'unrelated' "
        if archive: 
            query += " AND archive='1' "
        query += " ORDER BY bibcode asc;"

        rows = self.con.execute(query).fetchall()
        return rows

    def select_for_spreadsheet(self):
        rows = self.con.execute("SELECT bibcode, year, month, date, mission, science, metrics "
                            "FROM pubs WHERE mission != 'unrelated' ORDER BY bibcode;")
        return rows.fetchall()


    def get_articles_by_mission_years(self, mission, year_begin, year_end):
        #query
        cur = self.con.execute("select year, metrics from pubs "
                               f" where mission='{mission}' "
                               f" and year >= '{year_begin}'"
                               f" and year <= '{year_end}'"
                               )
        articles = cur.fetchall()

        return articles

    def get_articles_by_mission_years_instrument(self, mission, year_begin, year_end, instrument):
        q = "SELECT year, COUNT(*) FROM pubs "
        q += f" WHERE mission = '{mission}' "
        q += f" AND year >= '{year_begin}' "
        if instrument: 
            q += f" AND instruments like '%{instrument}%' "
        q += " GROUP BY year;"
        cur = self.con.execute(q)
        rows = list(cur.fetchall())
        return rows

    def get_count_cumulative(self, mission, year):
        cur = self.con.execute("SELECT COUNT(*) FROM pubs "
                                "WHERE mission = ? "
                                "AND year <= ?;",
                                [mission, year])
        return cur.fetchone()[0]