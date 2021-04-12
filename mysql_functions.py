import mysql.connector
from mysql.connector import Error
import pandas as pd


def create_server_connection(host_name='127.0.0.1', user_name='root', user_password='USAfa1987'):
    """
    Creates a connection to the local server
    :param host_name: host name of server
    :param user_name: user name
    :param user_password: password related to username
    :return: Connection to server
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password
        )
        # print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def create_database(connection, query):
    """
    Creates a database on the server
    :param connection: Connection to server
    :param query: Query to create the database
    :return:
    """
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")


def create_db_connection(db_name='business_wire_alerts', host_name='127.0.0.1', user_name='root', user_password='USAfa1987'):
    """
    Creates a database connection
    :param db_name: Database name
    :param host_name: Host name of server
    :param user_name: User name that can access server
    :param user_password: Password associated with the username
    :return: Connection parameter
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        # print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def execute_query(connection, query):
    """
    Exectures a query on a table
    :param connection: Connection parameter
    :param query: Query to run
    :return: 1 (success) or 0 (failure)
    """
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        # print("Query successful")
        return 1
    except Error as err:
        print(f"Error: '{err}'")
        return 0


def execute_placeholder_query(connection, sql, val):
    """
    Nut sure what this does
    :param connection:
    :param sql:
    :param val:
    :return:
    """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, val)
        connection.commit()
        # print("Query successful")
        return 1
    except Error as err:
        print(f"Error: '{err}'")
        return 0


def read_query(connection, query):
    """
    Read data from a MySQL table
    :param connection: Connection parameter
    :param query: Query to run
    :return: Result (if successful), 0 if query fails
    """
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        # print("Read Query Successful")
        return result
    except Error as err:
        print(f"Error: '{err}'")
        return 0


def execute_list_query(connection, sql, val):
    """
    Unsure what this is supposed to do.
    :param connection: Connection parameter
    :param sql:
    :param val:
    :return: NA
    """
    cursor = connection.cursor()
    try:
        cursor.executemany(sql, val)
        connection.commit()
        # print("Execute list query successful")
    except Error as err:
        print(f"Error: '{err}'")

