from urllib.parse import quote_plus
import pymongo
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import datetime
import subprocess
import os
import yaml

log = logging.getLogger('kpub')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "config.live.yaml")


def from_config(database="kpub", collection=None, config_path=CONFIG_PATH):
    """Create a MongoDBConnector using connection details from config.live.yaml."""
    with open(config_path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return MongoDBConnector(config, database, collection)


class MongoDBConnector:

    def __init__(self, config, database, collection=None):

        self.error = None
        self.readonly = False

        # parse config file
        if database not in config.keys():
            self.error = "DATABASE_CONFIG_ERROR"
            return None
        self.dbconfig = config[database]

        self.client = None
        collection = collection if collection else self.dbconfig["collection"]
        self.connect(database, collection)

    def connect(self, database, collection):
        """
        Connect to the specified database.  If primary server is down and backup
        is specified, then connect to it.  This also set the readOnly flag to 1.
        """

        # get db connect data
        server = self.dbconfig["server"] + ":" + str(self.dbconfig["port"])
        readonlyserver = self.dbconfig.get("readonlyserver", server)
        cmd = ["ping", "-c", "1", "-W", "1", self.dbconfig["server"]]
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait(timeout=2)
            if p.returncode != 0:
                server = readonlyserver
                self.readonly = True
        except Exception:
            server = readonlyserver
            self.readonly = True

        user = self.dbconfig["user"]
        pwd = self.dbconfig["pwd"]
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

    def add_row(self, article, month, year, mission, 
                snippits, instruments, archive, affiliation, 
                reason, hasAcknowledgement=False):
        """Insert a document into the MongoDB collection."""
        try:
            # Use bibcode as the unique identifier
            article['_id'] = article['bibcode']

            article['last_modifier'] = 'kpub'
            article['date_modified'] = datetime.datetime.now()
            article['date_created'] = article['date_modified']
            article['month'] = int(month)
            article['year'] = int(year)
            article['mission'] = mission
            article['snippits'] = snippits
            article['instruments'] = instruments.split('|')  # Convert to array
            article['archive'] = archive
            article['affiliation'] = affiliation
            article['reason'] = reason
            article['has_acknowledgement'] = hasAcknowledgement
            self.collection.insert_one(article)
            #self.collection.replace_one({'_id': article['_id']}, article, upsert=True)
            log.info(f"Inserted {article['bibcode']}")
        except pymongo.errors.DuplicateKeyError:
            log.warning(f"{article['bibcode']} was already ingested.")
    
    
    def update_citation_fields(self, bibcode, citation_fields):
        """Update a document's citation fields in the MongoDB collection."""
        try:
            updated_fields = {
                'last_modifier': 'kpub',
                'date_modified': datetime.datetime.now(),
                **citation_fields
            }
            self.collection.update_one({'_id': bibcode}, {'$set': updated_fields})
            log.info(f"Updated citation fields for {bibcode}")
        except Exception as e:
            log.error(f"Error updating citation count for {bibcode}: {e}")

    def update_row_affiliation(self, article):
        """Update a document's affiliation and archive in the MongoDB collection."""
        try:
            updated_fields = {
                'last_modifier': article['last_modifier'],
                'date_modified': article['date_modified'],
                'affiliation': article['affiliation'],
            }
            if article.get('archive'):
                updated_fields['archive'] = article['archive']
            if article.get('note'):
                updated_fields['note'] = article['note']
            if article.get('instruments', None) is not None: # sometimes can be an empty array.
                updated_fields['instruments'] = article['instruments']
            self.collection.update_one({'_id': article['_id']}, {'$set': updated_fields})
            log.info(f"Updated {article['bibcode']}")
            return article
        except Exception as e:
            log.error(f"Error updating {article['bibcode']}: {e}")

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

        rows = list(self.collection.find(
            query).sort('date', pymongo.DESCENDING))
        return rows

    def get_metrics_data(self, year_begin, year_end, filter_archive=None):

        query = { 'year': {'$gte': year_begin, '$lte': year_end}, 
                    'affiliation': 'keck' }
        if filter_archive is not None:
            query['archive'] = filter_archive
        match = {'$match': query }
        unwind = {'$unwind': '$author_norm'}
        group = {'$group': 
                  {'_id': '$year', 
                   'author_count': {'$sum': 1}, 
                   'author_set': {'$addToSet': '$author_norm'}, 
                   'first_author_set': {'$addToSet': '$first_author_norm'}, 
                   'bibcodes': {'$addToSet': '$bibcode'}}}
        project = {'$project': 
                    {'paper_count': {'$size': '$bibcodes'}, 
                     'author_count': {'$size': '$author_set'}, 
                     'first_author_count': {'$size': '$first_author_set' }, 
                     '_id': 1, 
                     'count': 1}}
        sort = {'$sort': {'_id': 1}}
        pipeline = [ match, unwind, group, project, sort ]

        result = list(self.collection.aggregate(pipeline))
        return result

    def article_exists(self, article):
        """Check if an article exists in the collection."""
        return self.collection.count_documents({'$or': [{'id': article['id']}, {'bibcode': article['bibcode']}]}) > 0

    def get_articles(self, begin_year=None, end_year=None, month=None, affiliation=None):
        """Get articles from the collection."""
        query = {}
        if affiliation:
            query['affiliation'] = affiliation

        if not begin_year:
            begin_year = end_year

        if not end_year:
            query['year'] = begin_year
        else:
            query['year'] = {'$gte': begin_year, '$lte': end_year}

        if month:
            query['month'] = month

        rows = list(self.collection.find(
            query).sort('date', pymongo.DESCENDING))
        return rows

    def select_for_spreadsheet(self):
        """Select documents for spreadsheet export."""
        query = {'mission': {'$ne': 'unrelated'}}
        projection = {'bibcode': 1, 'year': 1, 'month': 1, 'date': 1, 'mission': 1,
                      'metrics': 1, 'affiliation': 1, 'date_modified': 1, 'last_modifier': 1, '_id': 0}
        rows = list(self.collection.find(query, projection).sort(
            'bibcode', pymongo.ASCENDING))
        return rows

    def get_articles_by_mission_years(self, mission, year_begin, year_end):
        """Get articles by mission and year range."""
        query = {
            'mission': mission,
            'affiliation': 'keck',
            'year': {'$gte': year_begin, '$lte': year_end}
        }
        projection = {'year': 1, 'metrics': 1, '_id': 0}
        rows = list(self.collection.find(query, projection))
        return rows

    def get_articles_by_years_instrument(self, year_begin, year_end, instrument=None, filter_archive=None):
        """Get articles by year range, and instrument."""
        pipeline = []
        query = { 'year': {'$gte': year_begin, '$lte': year_end }, 'affiliation': 'keck' }
        group = {'_id': {'year': '$year'}, 'count': {'$sum': 1}}
        if instrument:
            pipeline.append({'$unwind': '$instruments'})
            query['instruments'] = instrument
            group['_id']['instrument'] = '$instruments'
        if filter_archive is not None:
            if isinstance(filter_archive, str):
                filter_archive = filter_archive.lower() == 'true'
            query['archive'] = bool(filter_archive)
        pipeline.append({'$match': query})

        sort = {'$sort': {'year': 1}}
        pipeline.append({'$group': group})
        pipeline.append(sort)
        rows = list(self.collection.aggregate(pipeline))
        # build a dict with all years in the range. 
        yeardict = {year: 0 for year in range(year_begin, year_end + 1)}
        for row in rows:
            yeardict[row['_id']['year']] = row['count']
        return yeardict

    def get_count_cumulative(self, year):
        """Get cumulative count of articles by mission and year."""
        query = {
            'year': {'$lte': year, 'affiliation': 'keck'},
        }
        count = self.collection.count_documents(query)
        return count

    def get_fulltext(self, bibcodes):
        """Get full text documents for the given bibcodes."""
        query = {'bibcode': {'$in': bibcodes}}
        rows = list(self.collection.find(query))
        return rows

    def upsert_fulltext(self, bibcode, fulltext):
        """Insert or update the extracted plaintext for a publication in the 'fulltext' collection."""
        fulltext_collection = self.client['kpub']['fulltext']
        fulltext_collection.update_one(
            {'_id': bibcode},
            {'$set': {
                'bibcode': bibcode,
                'fulltext': fulltext,
                'last_updated': datetime.datetime.now(),
            }},
            upsert=True
        )
        log.info(f"Saved fulltext for {bibcode}")