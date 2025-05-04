import sqlite3
import os
from tabulate import tabulate
import sys

def display_database(db_path='D:\GitHub\Vehicle-Parking-System\instance\parking_system.db'):
    """
    Display the structure and contents of all tables in the database
    """
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"Database file '{db_path}' not found!")
        return

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
            
        print("\n==== DATABASE STRUCTURE AND CONTENTS ====\n")
        
        # For each table, display structure and contents
        for table in tables:
            table_name = table[0]
            
            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue
                
            print(f"\n\n{'=' * 50}")
            print(f"TABLE: {table_name}")
            print(f"{'=' * 50}")
            
            # Get table structure (column info)
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            
            # Display table structure
            print("\n-- TABLE STRUCTURE --")
            structure_headers = ["ID", "Column Name", "Data Type", "Not Null", "Default Value", "Primary Key"]
            print(tabulate(columns_info, headers=structure_headers, tablefmt="pretty"))
            
            # Get table contents
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100;")
                rows = cursor.fetchall()
                
                # Get column names
                column_names = [column_info[1] for column_info in columns_info]
                
                # Display table contents
                print("\n-- TABLE CONTENTS --")
                if rows:
                    print(tabulate(rows, headers=column_names, tablefmt="pretty"))
                    print(f"Total rows: {len(rows)}")
                    
                    # If we fetched the maximum limit, indicate there may be more rows
                    if len(rows) == 100:
                        print("(Showing first 100 rows)")
                else:
                    print("(No data in this table)")
            except sqlite3.Error as e:
                print(f"Error retrieving data from table {table_name}: {e}")
                
        conn.close()
        print("\n\nDatabase display complete.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check if a database path was provided as argument
    if len(sys.argv) > 1:
        display_database(sys.argv[1])
    else:
        # Use default path
        default_path = 'instance\parking_system.db'
        print(f"Using default database path: {default_path}")
        display_database(default_path)
        print("\nTip: You can specify a different database path as an argument:")
        print("python display.py path/to/your/database.db")
