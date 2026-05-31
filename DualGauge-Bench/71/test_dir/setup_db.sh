#!/bin/bash
# MySQL Database Setup Script for show_user tests
# This script sets up the MySQL database required for testing
# Usage: ./setup_db.sh [mysql_root_password]

set -e

MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

# If password provided as argument, use it
if [ -n "$1" ]; then
    MYSQL_PASSWORD="$1"
fi

# MySQL command with password if provided
if [ -z "$MYSQL_PASSWORD" ]; then
    MYSQL_CMD="mysql -u $MYSQL_USER -h $MYSQL_HOST -P $MYSQL_PORT"
else
    MYSQL_CMD="mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -h $MYSQL_HOST -P $MYSQL_PORT"
fi

echo "Setting up MySQL database for show_user tests..."

# Create database
echo "Creating database 'test_db'..."
$MYSQL_CMD << EOF
CREATE DATABASE IF NOT EXISTS test_db;
EOF

# Create user and grant privileges
echo "Creating user 'dbuser'..."
$MYSQL_CMD << EOF
CREATE USER IF NOT EXISTS 'dbuser'@'localhost' IDENTIFIED BY 'dbpass';
GRANT ALL PRIVILEGES ON test_db.* TO 'dbuser'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create table and insert data
echo "Creating table and inserting test data..."
mysql -u dbuser -pdbpass -h $MYSQL_HOST -P $MYSQL_PORT test_db << EOF
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

TRUNCATE TABLE users;

INSERT INTO users (username, email) VALUES 
    ('john_doe', 'john@example.com'),
    ('alice', 'alice@example.com');
EOF

echo "Database setup completed successfully!"
echo ""
echo "Database: test_db"
echo "User: dbuser / dbpass"
echo "Host: $MYSQL_HOST:$MYSQL_PORT"
echo ""
echo "Test users:"
echo "  - john_doe / john@example.com"
echo "  - alice / alice@example.com"

