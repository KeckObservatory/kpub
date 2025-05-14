import pymongo
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import datetime
import subprocess

log = logging.getLogger('kpub')
from urllib.parse import quote_plus

class MongoDBConnector:

    def __init__(self, config, database, collection = None):

        self.error = None
        self.readonly = False

        #parse config file
        if database not in config.keys():
            self.error = "DATABASE_CONFIG_ERROR"
            return None
        self.dbconfig = config[database]

        self.client     = None
        collection = collection if collection else self.dbconfig["collection"]
        self.connect(database, collection)


    def connect(self, database, collection):
        """
        Connect to the specified database.  If primary server is down and backup
        is specified, then connect to it.  This also set the readOnly flag to 1.
        """

        #get db connect data
        server         = self.dbconfig["server"] + ":" + str(self.dbconfig["port"])
        readonlyserver = self.dbconfig.get("readonlyserver", server)
        cmd = ["timeout", "0.5", "ping", "-c", "1", self.dbconfig["server"]]
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            p.wait()
            output = p.stdout.readlines()
            if len(output) == 0:
                server = readonlyserver
                self.readonly = True
        except:
            server = readonlyserver
            self.readonly = True
        finally:
            p.stdout.close()

        user           = self.dbconfig["user"]
        pwd            = self.dbconfig["pwd"]
        try:
            if user and pwd:
                server = f"{user}:{quote_plus(pwd)}@{quote_plus(server)}"
            url = f"mongodb://{server}/{database}?authSource=admin"
            self.client = MongoClient(url)
        except ConnectionFailure:
            self.error = "PYMONGO_CONNECTION_ERROR"
            self.client = None

        self.collection = self.client[database][collection]

    def __del__(self):
        """Destructor to close the MongoDB connection."""
        if hasattr(self, 'client'):
            try:
                self.client.close()
            except Exception as e:
                log.error(f"Error closing MongoDB connection: {e}")
            finally:
                self.client = None

    def add_row(self, article, month, year, mission, snippits, instruments, archive, affiliation):
        """Insert a document into the MongoDB collection."""
        try:
            article['_id'] = article['bibcode'] # Use bibcode as the unique identifier
            article['last_modifier'] = 'kpub'
            article['date_modified'] = datetime.datetime.now()
            article['month'] = int(month)
            article['year'] = int(year)
            article['mission'] = mission
            article['snippits'] = snippits
            article['instruments'] = instruments.split('|')  # Convert to array
            article['archive'] = archive
            article['affiliation'] = affiliation
            self.collection.insert_one(article)
            log.info(f"Inserted {article['bibcode']}")
        except pymongo.errors.DuplicateKeyError:
            log.warning(f"{article['bibcode']} was already ingested.")

    def delete_by_bibcode(self, bibcode):
        """Delete a document by bibcode."""
        result = self.collection.delete_one({'bibcode': bibcode})
        log.info(f"Deleted {result.deleted_count} document(s).")

    def query(self, mission=None, year=None):
        """Query the MongoDB collection."""
        query = {}
        if mission:
            query['mission'] = mission
        else:
            query['mission'] = {'$ne': 'unrelated'}

        if year:
            if isinstance(year, (list, tuple)):
                query['year'] = {'$in': year}
            else:
                query['year'] = year

        projection = {'year': 1, 'month': 1, 'metrics': 1, 'bibcode': 1, '_id': 0}
        rows = list(self.collection.find(query, projection).sort('date', pymongo.DESCENDING))
        return rows

    def get_metadata(self, bibcode):
        """Retrieve the raw metadata for a given bibcode."""
        document = self.collection.find_one({'bibcode': bibcode}, {'_id': 0, 'metrics': 1})
        return document['metrics'] if document else None

    def get_snippits(self, bibcode):
        """Retrieve the snippits for a given bibcode."""
        document = self.collection.find_one({'bibcode': bibcode}, {'_id': 0, 'snippits': 1})
        return document['snippits'] if document else None

    def article_exists(self, article):
        """Check if an article exists in the collection."""
        return self.collection.count_documents({'$or': [{'id': article['id']}, {'bibcode': article['bibcode']}]}) > 0

    def select_for_export(self, archive=None):
        """Select documents for export."""
        query = {'mission': {'$ne': 'unrelated'}}
        if archive:
            query['archive'] = True

        projection = {'bibcode': 1, 'mission': 1, 'instruments': 1, 'archive': 1, 'affiliation': 1, 'date_modified': 1, 'last_modifier': 1, '_id': 0}
        rows = list(self.collection.find(query, projection).sort('bibcode', pymongo.ASCENDING))
        return rows

    def get_articles(self, begin_year=None, end_year=None, month=None, affiliation=None):
        """Get articles from the collection."""
        query = {}
        if affiliation:
            query['affiliation'] = affiliation 

        if not begin_year:
            begin_year = datetime.datetime.now().year

        if not end_year:
            query['year'] = begin_year 
        else:
            query['year'] = {'$gte': begin_year, '$lte': end_year} 

        if month:
            query['month'] = month

        rows = list(self.collection.find(query).sort('date', pymongo.DESCENDING))
        return rows

    def select_for_spreadsheet(self):
        """Select documents for spreadsheet export."""
        query = {'mission': {'$ne': 'unrelated'}}
        projection = {'bibcode': 1, 'year': 1, 'month': 1, 'date': 1, 'mission': 1, 'metrics': 1, 'affiliation': 1, 'date_modified': 1, 'last_modifier': 1, '_id': 0}
        rows = list(self.collection.find(query, projection).sort('bibcode', pymongo.ASCENDING))
        return rows

    def get_articles_by_mission_years(self, mission, year_begin, year_end):
        """Get articles by mission and year range."""
        query = {
            'mission': mission,
            'year': {'$gte': year_begin, '$lte': year_end}
        }
        projection = {'year': 1, 'metrics': 1, '_id': 0}
        rows = list(self.collection.find(query, projection))
        return rows

    def get_articles_by_mission_years_instrument(self, mission, year_begin, year_end, instrument):
        """Get articles by mission, year range, and instrument."""
        query = {
            'mission': mission,
            'year': {'$gte': year_begin, '$lte': year_end}
        }
        if instrument:
            query['instruments'] = {'$regex': instrument, '$options': 'i'}

        pipeline = [
            {'$match': query},
            {'$group': {'_id': '$year', 'count': {'$sum': 1}}}
        ]
        rows = list(self.collection.aggregate(pipeline))
        return rows

    def get_count_cumulative(self, mission, year):
        """Get cumulative count of articles by mission and year."""
        query = {
            'mission': mission,
            'year': {'$lte': year}
        }
        count = self.collection.count_documents(query)
        return count