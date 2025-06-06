import pandas as pd
import sqlite3
import sys
import yaml
import os
import datetime
import pdb
sys.path.append('../src')
from kpub import PublicationDB

PACKAGEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
def convert_to_new_db(input_db):
    """
    Convert a CSV file to a new SQLite database format.
    
    Args:
        input_db (str): Path to the input db file.
        output_db (str): Path to the output SQLite database file.
    """
    df = pd.read_sql('SELECT bibcode, year, month, date, instruments FROM pubs', sqlite3.connect(input_db))

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)
    db = PublicationDB(config)

    affiliation = 'keck' 
    last_modifier = 'kpub (affiliation set by old db)'
    for row in df.itertuples():
        bibcode = row.bibcode
        date_modified = datetime.datetime.now()

        resp = db.collection.update_one({'_id': bibcode}, {'$set': {
            'last_modifier': last_modifier,
            'date_modified': date_modified,
            'affiliation': affiliation
        }})

        if resp.matched_count== 0:
            print(f"Bibcode {bibcode} was not found in the new database...")
            continue
        if resp.modified_count == 0:
            print(f"Bibcode {bibcode} was already set to {affiliation} in the new database...")
            continue


if __name__ == "__main__":
    input_db = 'kpub.db' 
    print(f"Converting {input_db} to the new database format...")
    convert_to_new_db(input_db)
    print("Conversion completed successfully.")