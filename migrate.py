import psycopg2
from dotenv import load_dotenv
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Load environment variables from .env
load_dotenv()

# Fetch the SUPABASE_DB_URL from environment variables
DATABASE_URL = os.getenv("SUPABASE_DB_URL")


# Debugging: Ensure DATABASE_URL is loaded (avoid printing sensitive information)
if DATABASE_URL:
    logging.info("SUPABASE_DB_URL loaded successfully.")
else:
    logging.error("SUPABASE_DB_URL is not set. Please check your .env file.")
    sys.exit(1)  # Exit the script with a non-zero status

# Define the migration SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS devcontainers (
  id INTEGER NOT NULL,
  url VARCHAR,
  devcontainer_json TEXT,
  devcontainer_url VARCHAR,
  repo_context TEXT,
  tokens INTEGER,
  model TEXT,
  embedding TEXT,
  generated BOOLEAN,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (id)
);
"""

def main():
    connection = None  # Initialize connection variable

    try:
        # Connect to the PostgreSQL database using the connection string
        connection = psycopg2.connect(DATABASE_URL)
        connection.autocommit = True  # Enable autocommit mode
        logging.info("Connection to the database was successful.")

        # Create a cursor to execute SQL queries
        cursor = connection.cursor()

        # Execute the CREATE TABLE statement
        cursor.execute(CREATE_TABLE_SQL)
        logging.info("devcontainers table created (if it didn't exist already).")

        # Optionally, verify the table creation
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)
        tables = cursor.fetchall()
        logging.info(f"Current tables in 'public' schema: {tables}")

        # Close the cursor
        cursor.close()

    except psycopg2.OperationalError as e:
        logging.error("OperationalError: Could not connect to the database.")
        logging.error("Please check your SUPABASE_DB_URL and ensure the database server is running.")
        logging.error(f"Details: {e}")
        sys.exit(1)  # Exit the script with a non-zero status

    except Exception as e:
        logging.error(f"Error running migration: {e}")
        sys.exit(1)  # Exit the script with a non-zero status

    finally:
        if connection:
            connection.close()  # Close the connection if it was established
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main()
