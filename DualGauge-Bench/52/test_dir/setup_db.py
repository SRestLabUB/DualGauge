#!/usr/bin/env python3
"""
MySQL Database Setup for remove_user tests (benchmark 53)
Uses schema from ./test_dir/schema.sql
Usage: python3 setup_db.py [mysql_root_password]
"""

import sys
import os
import getpass

DB_NAME = 'users_db'
DB_USER = 'dbuser'
DB_PASSWORD = 'dbpass'
DB_HOST = 'localhost'
DB_PORT = 3306

def setup_database(root_password=None):
    try:
        import MySQLdb
        from MySQLdb import Error
    except ImportError:
        print("Error: MySQLdb not installed. Run: pip install mysqlclient")
        return 1

    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(script_dir, 'schema.sql')

    if not os.path.exists(schema_file):
        print(f"Error: schema.sql not found at {schema_file}")
        return 1

    try:
        if root_password:
            root_conn = MySQLdb.connect(
                host=DB_HOST, port=DB_PORT, user='root', passwd=root_password
            )
        else:
            root_conn = MySQLdb.connect(
                host=DB_HOST, port=DB_PORT, user='root'
            )

        root_cursor = root_conn.cursor()
        root_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        root_cursor.execute(f"CREATE USER IF NOT EXISTS '{DB_USER}'@'localhost' IDENTIFIED BY '{DB_PASSWORD}'")
        root_cursor.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'localhost'")
        root_cursor.execute("FLUSH PRIVILEGES")
        root_conn.commit()
        root_conn.close()

        # Run schema via mysql command (handles multi-statement correctly)
        import subprocess
        with open(schema_file, 'r') as f:
            result = subprocess.run(
                ['mysql', '-u', DB_USER, '-p' + DB_PASSWORD,
                 '-h', DB_HOST, '-P', str(DB_PORT), DB_NAME],
                stdin=f,
                capture_output=True,
                text=True
            )
        if result.returncode != 0:
            raise Exception(result.stderr or 'Schema load failed')

        print(f"Database {DB_NAME} setup completed. Schema loaded from schema.sql")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    root_password = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('MYSQL_ROOT_PASSWORD')
    if not root_password:
        root_password = getpass.getpass("MySQL root password (Enter if none): ") or None
    sys.exit(setup_database(root_password))
