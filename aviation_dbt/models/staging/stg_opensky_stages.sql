WITH source_data AS (

    SELECT
        RAW_DATA
    FROM AVIATION_DB.RAW.OPENSKY_STATES_RAW

),

flattened AS (

    SELECT
        value AS aircraft_data
    FROM source_data,
        LATERAL FLATTEN(
            input => RAW_DATA:states
        )

)

SELECT
    aircraft_data[0]::STRING AS ICAO24,
    TRIM(aircraft_data[1]::STRING) AS CALLSIGN,
    aircraft_data[2]::STRING AS COUNTRY,

    aircraft_data[5]::FLOAT AS LONGITUDE,
    aircraft_data[6]::FLOAT AS LATITUDE,

    aircraft_data[7]::FLOAT AS BARO_ALTITUDE,
    aircraft_data[9]::FLOAT AS VELOCITY,
    aircraft_data[10]::FLOAT AS TRUE_TRACK,

    TO_TIMESTAMP_NTZ(
        aircraft_data[3]::NUMBER
    ) AS POSITION_TIMESTAMP

FROM flattened