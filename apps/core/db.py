import mysql.connector
from mysql.connector import errorcode, pooling

from contextlib import contextmanager

connection_pool = None

try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        user='root',
        password='abc123',     # Change for production environments
        host='sed-backend-core-db',
        database='seddb',
        port=3306,
        autocommit=False,
        get_warnings=True,                      # Change for production environments (True in dev)
        raise_on_warnings=True,                 # Change for production environments (True in dev)
        pool_size=1,                            # Change for production environments (as few as possible in dev)
        connection_timeout=10                   # Might want to increase this for production
    )
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print('Incorrect mysql credentials')
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print('DB could not be found')
    else:
        print(err)
else:
    print('Database connection pool was successfully established')


@contextmanager
def get_connection():
    """
    Returns a MySQL connection that can be used for read/write.
    Should be utilized through "get with resources" methodology.
    """
    connection = connection_pool.get_connection()
    try:
        yield connection
    finally:
        connection.close()
