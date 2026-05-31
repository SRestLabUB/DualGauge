-- Database setup for CWE-522_author_1
-- This script creates the database, user, and populates test data
-- Usage: mysql -u root -p < schema.sql

-- Create database
CREATE DATABASE IF NOT EXISTS users_db;
USE users_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    userid VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255) NOT NULL
);

-- Clear existing data
TRUNCATE TABLE users;

-- Insert test data
-- Note: In production, passwords should be hashed (e.g., using bcrypt)
-- For testing purposes, using plain text passwords matching fc_tests expectations
INSERT INTO users (userid, password) VALUES 
    ('john_doe', 'securepass'),
    ('admin', 'admin123');

-- Display created data
SELECT * FROM users;

