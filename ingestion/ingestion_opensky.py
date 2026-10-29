import json
import requests
import snowflake.connector

from config.config import (
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_USER,
    SNOWFLAKE_PASSWORD,
    SNOWFLAKE_DATABASE,
    SNOWFLAKE_SCHEMA,
    SNOWFLAKE_WAREHOUSE,
    SNOWFLAKE_ROLE,
)

OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

conn = None
cursor = None

try:
    # 1. Fetch aircraft data from OpenSky
    response = requests.get(OPENSKY_API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()

    states = data.get("states") or []

    print("OpenSky API connected successfully!")
    print("API response time:", data.get("time"))
    print("Aircraft records received:", len(states))

    # 2. Connect to Snowflake
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        database="AVIATION_DB",
        schema="RAW",
        warehouse=SNOWFLAKE_WAREHOUSE,
        role=SNOWFLAKE_ROLE,
    )

    cursor = conn.cursor()

    # 3. Verify the active Snowflake context
    cursor.execute("""
        SELECT
            CURRENT_DATABASE(),
            CURRENT_SCHEMA(),
            CURRENT_ROLE(),
            CURRENT_WAREHOUSE()
    """)

    print("Snowflake context:", cursor.fetchone())

    # 4. Insert data into the fully qualified table
    cursor.execute("""
        INSERT INTO AVIATION_DB.RAW.OPENSKY_STATES_RAW (RAW_DATA)
        SELECT PARSE_JSON(%s)
    """, (json.dumps(data),))

    inserted_rows = cursor.rowcount

    conn.commit()

    print("Rows inserted:", inserted_rows)
    print("Data committed successfully!")

    # 5. Verify the inserted record count
    cursor.execute("""
        SELECT COUNT(*)
        FROM AVIATION_DB.RAW.OPENSKY_STATES_RAW
    """)

    print("Total raw records in Snowflake:", cursor.fetchone()[0])

except Exception as error:
    if conn is not None:
        conn.rollback()

    print("INGESTION FAILED:", repr(error))
    raise

finally:
    if cursor is not None:
        cursor.close()

    if conn is not None:
        conn.close()
