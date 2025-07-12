import pandas as pd
import sqlite3
import sys
import yaml
import os
import datetime
import pdb
import json
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
    #df = pd.read_sql('SELECT bibcode, year, month, date, instruments FROM pubs', sqlite3.connect(input_db))
    df = pd.read_sql('SELECT * FROM pubs', sqlite3.connect(input_db))

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)
    db = PublicationDB(config)

    last_modifier = 'kpub (affiliation set by old db)'
    addingRows = []
    for row in df.to_dict(orient='records'):
        bibcode = row['bibcode']
        metrics = json.loads(row['metrics'])
        row = {**row, **metrics}  # Merge metrics into the row
        date_modified = datetime.datetime.now()
        affiliation = 'keck' 
        row = { **row, 'last_modifier': last_modifier, 'date_modified': date_modified, 'affiliation': affiliation }
        row['instruments'] = row['instruments'].split('|') if row.get('instruments') else []
        archive = row.get('archive')
        if isinstance(archive, str):
            archive = True if '1' in row.get('archive') else False
        elif isinstance(row.get('archive'), int):
            archive = bool(archive) 
        if len(row['instruments']) < 1 and not row['archive']:
            print(f"{bibcode} does not mention any instruments or KOA. setting as unknown affiliation.")
            affiliation = 'unknown'
        row['year'] = int(row['year']) if row.get('year') else None
        row['month'] = int(row['month'].split('-')[-1]) if row.get('month') else None
        row['archive'] = archive 
        row['affiliation'] = affiliation
        row['reason'] = 'Converted from old database' 
        row['snippits'] = []
        # Remove the 'metrics' field as it's already merged into the row
        # Insert the row into the new database
        del row['metrics']
        # Use the bibcode as the unique identifier
        row['_id'] = bibcode
        # Insert the row into the new database

        # resp = db.collection.replace_one({'_id': bibcode}, row, upsert=True)
        # if resp.matched_count == 0:
        #     print(f"Bibcode {bibcode} was not found in the new database, it has been inserted.")
        #     continue
        # if resp.modified_count == 0:
        #     print(f"Bibcode {bibcode} was already set to {affiliation} in the new database, skipping...")
        #     continue
        addingRows.append(row)
    db.collection.insert_many(addingRows)


if __name__ == "__main__":
    input_db = 'kpub.db' 
    print(f"Converting {input_db} to the new database format...")
    convert_to_new_db(input_db)
    print("Conversion completed successfully.")