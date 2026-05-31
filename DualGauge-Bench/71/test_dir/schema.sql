-- MySQL schema for users table
-- Database setup for CWE-089_codeql_1
-- This script creates the database, user, and populates test data
-- Usage: mysql -u root -p < schema.sql

-- Create database
CREATE DATABASE IF NOT EXISTS test_db;
USE test_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clear existing data
TRUNCATE TABLE users;

-- Insert test users matching fc_tests
INSERT INTO users (username, email) VALUES 
    ('john_doe', 'john@example.com'),
    ('alice', 'alice@example.com');
