"""Shared pytest fixtures for the mocked kpub unit tests.

These fixtures make sure no test in this package ever touches a real
MongoDB instance: MongoDBConnector.connect() is replaced with a fake
that hands out MagicMock() 'client'/'collection' objects instead of
opening a real network connection.
"""
from unittest.mock import MagicMock

import pytest

import kpub as kpub_module
from kpub import PublicationDB


@pytest.fixture(autouse=True)
def no_real_mongo(monkeypatch):
    """Replace MongoDBConnector.connect so no test ever opens a real connection."""
    def fake_connect(self, database, collection):
        self.client = MagicMock(name='mongo_client')
        self.collection = MagicMock(name='mongo_collection')

    monkeypatch.setattr(kpub_module.MongoDBConnector, 'connect', fake_connect)


@pytest.fixture
def config():
    """A minimal but representative config dict, mirroring config.live.yaml."""
    return {
        'kpub': {
            'server': 'localhost',
            'port': 27017,
            'user': '',
            'pwd': '',
            'database': 'kpub',
            'collection': 'articles',
        },
        'ADS_API_KEY': 'FAKE-ADS-API-KEY',
        'prepend': 'keck',
        'missions': ['keck'],
        'sciences': [],
        'ads_queries': [
            {'name': 'Ackn/Abstract', 'query': '(ack:keck OR abs:keck)'},
        ],
        'instruments': ['HIRES', 'LRIS'],
        'blacklist': ['THESIS'],
        'archive': ['KOA'],
        'acknowledgement': ['W. M. Keck Foundation'],
        'colors': {'HIRES': 'CYAN', 'KOA': 'YELLOW', 'KECK': 'GREEN'},
        'plots': {'year_begin': 2009, 'instruments': ['HIRES']},
        'aff_defs': [
            {'type': 'keck', 'strings': ['Keck', 'Caltech']},
            {'type': 'usa', 'strings': ['NASA']},
            {'type': 'intl', 'strings': []},
        ],
    }


@pytest.fixture
def db(config):
    """A PublicationDB instance whose .client/.collection are MagicMocks."""
    return PublicationDB(config=config, collection='articles')
