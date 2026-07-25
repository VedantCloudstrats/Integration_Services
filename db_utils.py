from django.conf import settings


def get_cmms_connection():
    """
    Establish connection to CMMS MS SQL Server.
    """
    import pyodbc

    conn_str = (
        f"DRIVER={{{settings.CMMS_DB_DRIVER}}};"
        f"SERVER={settings.CMMS_DB_HOST},{settings.CMMS_DB_PORT};"
        f"DATABASE={settings.CMMS_DB_NAME};"
        f"UID={settings.CMMS_DB_USER};"
        f"PWD={settings.CMMS_DB_PASSWORD};"
        f"Encrypt=no;TrustServerCertificate=yes"
    )
    return pyodbc.connect(conn_str)


def fetch_cmms_table_data(query, params=None):
    """
    Executes raw SQL query on CMMS database and returns rows as dictionaries.
    """
    conn = get_cmms_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    finally:
        cursor.close()
        conn.close()


def execute_cmms_query(query, params=None):
    """
    Executes modifying SQL query on CMMS database and commits the transaction.
    """
    conn = get_cmms_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
