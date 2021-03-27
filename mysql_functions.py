import mysql.connector
from mysql.connector import Error
import pandas as pd


def create_server_connection(host_name='127.0.0.1', user_name='root', user_password='USAfa1987'):
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
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")


def create_db_connection(db_name='business_wire_alerts', host_name='127.0.0.1', user_name='root', user_password='USAfa1987'):
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
    cursor = connection.cursor()
    try:
        cursor.executemany(sql, val)
        connection.commit()
        # print("Execute list query successful")
    except Error as err:
        print(f"Error: '{err}'")

