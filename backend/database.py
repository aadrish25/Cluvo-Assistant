import sqlite3
from pathlib import Path
from agno.db.sqlite import SqliteDb

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
DATABASE_PATH = BASE_DIR / "database" / "ksp_crime_platform.db"
MEMORY_DATABASE_PATH = BASE_DIR / "database" / "memory_db.db" 

# create connection to the db
def create_connection():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        print("[DATABASE] Connection to the database established successfully!")
        return conn
    except Exception as e:
        print(f"[DATABASE] Error connecting to the database: {e}")
        return None
    
    
# create memory db -> singleton
memory_db = SqliteDb(db_file=MEMORY_DATABASE_PATH)


# create tables
def init_db():
    try:
        conn = create_connection()
        if conn is not None:
            cursor = conn.cursor()
            with open(DATABASE_SCHEMA_PATH,'r') as f:
                cursor.executescript(f.read())
                conn.commit()
            conn.close()
            print(f"[DATABASE] Database initialized successfully with schema from {DATABASE_SCHEMA_PATH}.")
        else:
            print("[DATABASE] Failed to create tables due to connection error.")
    except Exception as e:
        print(f"[DATABASE] Error initializing the database: {e}")
        
        
# check tables
def test():
    try:
        conn = create_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"[DATABASE] Tables in the database")
            for i,table in enumerate(tables,start=1):
                print(f"{i} - {table['name']}")
            conn.close()
    except Exception as e:
        print(f"[DATABASE] Error testing the database: {e}")
        
        
if __name__=="__main__":
    test()
