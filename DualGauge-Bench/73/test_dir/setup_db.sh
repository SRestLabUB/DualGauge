#!/bin/bash
# MySQL Database Setup Script for checkPassword tests
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

echo "Setting up MySQL database for checkPassword tests..."

# Create database
echo "Creating database 'users_db'..."
$MYSQL_CMD << EOF
CREATE DATABASE IF NOT EXISTS users_db;
EOF

# Create user and grant privileges
echo "Creating user 'dbuser'..."
$MYSQL_CMD << EOF
CREATE USER IF NOT EXISTS 'dbuser'@'localhost' IDENTIFIED BY 'dbpass';
GRANT ALL PRIVILEGES ON users_db.* TO 'dbuser'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create table and insert data
echo "Creating table and inserting test data..."
mysql -u dbuser -pdbpass -h $MYSQL_HOST -P $MYSQL_PORT users_db << EOF
CREATE TABLE IF NOT EXISTS users (
    userid VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255) NOT NULL
);

TRUNCATE TABLE users;

INSERT INTO users (userid, password) VALUES 
    ('john_doe', 'securepass'),
    ('admin', 'admin123');
EOF

echo "Database setup completed successfully!"
echo ""
echo "Database: users_db"
echo "User: dbuser / dbpass"
echo "Host: $MYSQL_HOST:$MYSQL_PORT"
echo ""
echo "Test users:"
echo "  - john_doe / securepass"
echo "  - admin / admin123"

