-- prepare_similarity_search_service_db.sql

-- Create the database for the similarity search service
CREATE DATABASE similarity_search_service_db;

-- Connect to the database
\connect similarity_search_service_db

-- Enable vector extension (for pgvector)
-- timescaledb-ha image already has the extension installed, just enable it in this DB
CREATE EXTENSION IF NOT EXISTS vector;