-- DROP ROLE IF EXISTS  kpubguy CASCADE;
CREATE ROLE kpubguy WITH 
	SUPERUSER
	CREATEDB
	CREATEROLE
	INHERIT
	LOGIN;

-- DROP DATABASE IF EXISTS vwa;
CREATE DATABASE kpub;
-- ddl-end --

-- DROP SCHEMA IF EXISTS vwa CASCADE;
CREATE SCHEMA kpub;

ALTER SCHEMA kpub OWNER TO kpubguy;

SET search_path TO kpub;

-- DROP TABLE IF EXISTS vwa.walkarounds pubs;
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
);