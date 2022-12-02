import sqlite3
import os
import sys

WORKING_PATH = "./APP/"
DBNAME = "main.db"
dbpath = os.path.join(WORKING_PATH, DBNAME)
OVERWRITE_TABLES = False

connection = None

try:
    connection = sqlite3.connect(dbpath)
    print('Created successfully')
except Exception as e:
    print('Creation failed :', e)
    sys.exit(1)

cursor = connection.cursor()
overwrite_string = ""
if OVERWRITE_TABLES:
    overwrite_string = "IF NOT EXISTS"


# create USERS table
try:
    cursor.execute(
        """CREATE TABLE {0} USERS(
            user_id TEXT PRIMARY KEY,
            email TEXT,
            password TEXT,
            tokens_key TEXT
            request_key TEXT
            )""".format(overwrite_string)
        )
except Exception as e:
    print('Creation of USERS failed :', e)

# create REQUESTS table
try:
    cursor.execute(
        """CREATE TABLE {0} REQUESTS(
            request_id TEXT PRIMARY KEY,
            user_id TEXT,
            state INT,
            token TEXT
            )""".format(overwrite_string)
        )
except Exception as e:
    print('Creation of USERS failed :', e)


 # create TOKENS table
try:
    cursor.execute(
        """CREATE TABLE {0} TOKENS(
            token_id TEXT PRIMARY KEY,
            value TEXT
            rights INT
            )""".format(overwrite_string)
        )
except Exception as e:
    print('Creation of USERS failed :', e)