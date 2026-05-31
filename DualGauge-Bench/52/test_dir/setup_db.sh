#!/bin/bash
# MySQL Database Setup for remove_user tests (benchmark 53)
# Uses schema from ./test_dir/schema.sql
# Usage: ./setup_db.sh [mysql_root_password]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="${SCRIPT_DIR}/schema.sql"

MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
DB_NAME="users_db"
DB_USER="dbuser"
DB_PASSWORD="dbpass"

if [ -n "$1" ]; then
    MYSQL_PASSWORD="$1"
fi

if [ -z "$MYSQL_PASSWORD" ]; then
    MYSQL_CMD="mysql -u $MYSQL_USER -h $MYSQL_HOST -P $MYSQL_PORT"
else
    MYSQL_CMD="mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -h $MYSQL_HOST -P $MYSQL_PORT"
fi

echo "Setting up MySQL database for remove_user tests..."

# Create database
echo "Creating database '$DB_NAME'..."
$MYSQL_CMD -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"

# Create user and grant privileges
echo "Creating user '$DB_USER'..."
$MYSQL_CMD << EOF
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# Run schema.sql
echo "Running schema from $SCHEMA_FILE..."
mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$MYSQL_HOST" -P "$MYSQL_PORT" "$DB_NAME" < "$SCHEMA_FILE"

echo "Database setup completed!"
echo "Database: $DB_NAME | User: $DB_USER | Host: $MYSQL_HOST:$MYSQL_PORT"
