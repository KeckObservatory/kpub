import pymongo
import logging

log = logging.getLogger('kpub')

class MongoDB:
    def __init__(self, uri, db_name, collection_name):
        """Initialize the MongoDB connection."""
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        # Ensure the collection exists
        if collection_name not in self.db.list_collection_names():
            log.info(f"Creating collection: {collection_name}")

    def __del__(self):
        """Destructor to close the MongoDB connection."""
        self.client.close()

    def add_row(self, article, month, mission, science, instruments, archive):
        """Insert a document into the MongoDB collection."""
        try:
            article['month'] = month
            article['mission'] = mission
            article['science'] = science
            article['instruments'] = instruments.split('|')  # Convert to array
            article['archive'] = archive
            self.collection.insert_one(article)
            log.info(f"Inserted {article['bibcode']}")
        except pymongo.errors.DuplicateKeyError:
            log.warning(f"{article['bibcode']} was already ingested.")

    def delete_by_bibcode(self, bibcode):
        """Delete a document by bibcode."""
        result = self.collection.delete_one({'bibcode': bibcode})
        log.info(f"Deleted {result.deleted_count} document(s).")

    def query(self, mission=None, science=None, year=None):
        """Query the MongoDB collection."""
        query = {}
        if mission:
            query['mission'] = mission
        if science:
            query['science'] = science
        if year:
            if isinstance(year, (list, tuple)):
                query['year'] = {'$in': year}
            else:
                query['year'] = year

        return list(self.collection.find(query).sort('date', pymongo.DESCENDING))

    def get_metadata(self, bibcode):
        """Retrieve the raw metadata for a given bibcode."""
        document = self.collection.find_one({'bibcode': bibcode}, {'_id': 0, 'metrics': 1})
        return document['metrics'] if document else None

    def article_exists(self, article):
        """Check if an article exists in the collection."""
        return self.collection.count_documents({'$or': [{'id': article['id']}, {'bibcode': article['bibcode']}]}) > 0

    def select_for_export(self, archive=None):
        """Select documents for export."""
        query = {'mission': {'$ne': 'unrelated'}}
        if archive:
            query['archive'] = True

        return list(self.collection.find(query, {'_id': 0, 'bibcode': 1, 'mission': 1, 'science': 1, 'instruments': 1, 'archive': 1}).sort('bibcode', pymongo.ASCENDING))

    def select_for_spreadsheet(self):
        """Select documents for spreadsheet export."""
        query = {'mission': {'$ne': 'unrelated'}}
        return list(self.collection.find(query, {'_id': 0, 'bibcode': 1, 'year': 1, 'month': 1, 'date': 1, 'mission': 1, 'science': 1, 'metrics': 1}).sort('bibcode', pymongo.ASCENDING))

    def get_articles_by_mission_years(self, mission, year_begin, year_end):
        """Get articles by mission and year range."""
        query = {
            'mission': mission,
            'year': {'$gte': year_begin, '$lte': year_end}
        }
        return list(self.collection.find(query, {'_id': 0, 'year': 1, 'metrics': 1}))

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
        return list(self.collection.aggregate(pipeline))

    def get_count_cumulative(self, mission, year):
        """Get cumulative count of articles by mission and year."""
        query = {
            'mission': mission,
            'year': {'$lte': year}
        }
        return self.collection.count_documents(query)