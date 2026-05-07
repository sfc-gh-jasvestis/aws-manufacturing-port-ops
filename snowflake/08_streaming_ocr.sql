-- ============================================================================
-- 08_streaming_ocr.sql
-- AWS hero: Kinesis Data Firehose -> Snowpipe Streaming + Rekognition OCR
-- ----------------------------------------------------------------------------
-- Architecture (real customer flow):
--   Gate scanner -> Kinesis Firehose -> Snowpipe Streaming endpoint
--                                    -> Snowflake table RAW.GATE_EVENTS
--   Gate camera  -> S3 -> Lambda calls Rekognition DetectText
--                              -> writes container OCR result to RAW.OCR_RESULTS
-- For the demo we seed both tables on a 60s task to prove the pipeline.
-- ============================================================================
USE DATABASE MANUFACTURING_PORT_OPS;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE OR REPLACE TABLE RAW.GATE_EVENTS (
    EVENT_ID        STRING,
    EVENT_TS        TIMESTAMP_NTZ,
    GATE_ID         STRING,
    DIRECTION       STRING,
    CONTAINER_NUM   STRING,
    TRUCK_PLATE     STRING,
    CARRIER_NAME    STRING,
    DWELL_SECONDS   NUMBER,
    SOURCE_PIPELINE STRING
);

CREATE OR REPLACE TABLE RAW.OCR_RESULTS (
    RESULT_ID         STRING,
    OCR_TS            TIMESTAMP_NTZ,
    GATE_ID           STRING,
    S3_KEY            STRING,
    DETECTED_TEXT     STRING,
    CONFIDENCE_PCT    FLOAT,
    REKOGNITION_JOB   STRING
);

-- Seed initial 200 events
INSERT INTO RAW.GATE_EVENTS
SELECT
    'GE-' || UUID_STRING() AS EVENT_ID,
    DATEADD('second', -1 * UNIFORM(0, 3600, RANDOM()), CURRENT_TIMESTAMP()),
    'GATE-' || (1 + ABS(RANDOM()) % 8) AS GATE_ID,
    IFF(UNIFORM(0, 1, RANDOM()) < 0.5, 'IN', 'OUT'),
    'CONT' || LPAD(ABS(RANDOM()) % 1000000, 7, '0') AS CONTAINER_NUM,
    UPPER('SGX' || LPAD(ABS(RANDOM()) % 10000, 4, '0')) AS TRUCK_PLATE,
    DECODE(1 + ABS(RANDOM()) % 6, 1,'Maersk Line', 2,'CMA CGM', 3,'Hapag-Lloyd', 4,'ONE', 5,'Pacific Express Lines', 6,'Evergreen Marine'),
    UNIFORM(45, 600, RANDOM()),
    'kinesis-firehose'
FROM TABLE(GENERATOR(ROWCOUNT => 200));

INSERT INTO RAW.OCR_RESULTS
SELECT
    'REK-' || UUID_STRING() AS RESULT_ID,
    EVENT_TS,
    GATE_ID,
    's3://sg-manufacturing-demos-2026/port-ops/gate-cam/' || EVENT_ID || '.jpg',
    CONTAINER_NUM,
    UNIFORM(85, 100, RANDOM())::FLOAT AS CONFIDENCE_PCT,
    'rekognition-' || UUID_STRING()
FROM RAW.GATE_EVENTS
SAMPLE (40 ROWS);

-- 5-minute Dynamic Table on top
CREATE OR REPLACE DYNAMIC TABLE CURATED.GATE_EVENTS_5MIN
    TARGET_LAG = '1 minute'
    WAREHOUSE = CORTEX
AS
SELECT
    DATE_TRUNC('minute', EVENT_TS)        AS BUCKET_TS,
    GATE_ID,
    DIRECTION,
    COUNT(*)                              AS EVENT_COUNT,
    AVG(DWELL_SECONDS)::NUMBER(10,1)      AS AVG_DWELL_SECONDS
FROM RAW.GATE_EVENTS
GROUP BY 1, 2, 3;

-- Task: simulate Firehose throughput by inserting 5 events / minute
CREATE OR REPLACE TASK RAW.SEED_GATE_EVENTS
    WAREHOUSE = CORTEX
    SCHEDULE = '1 minute'
AS
INSERT INTO MANUFACTURING_PORT_OPS.RAW.GATE_EVENTS
SELECT
    'GE-' || UUID_STRING(),
    CURRENT_TIMESTAMP(),
    'GATE-' || (1 + ABS(RANDOM()) % 8),
    IFF(UNIFORM(0, 1, RANDOM()) < 0.5, 'IN', 'OUT'),
    'CONT' || LPAD(ABS(RANDOM()) % 1000000, 7, '0'),
    UPPER('SGX' || LPAD(ABS(RANDOM()) % 10000, 4, '0')),
    DECODE(1 + ABS(RANDOM()) % 6, 1,'Maersk Line', 2,'CMA CGM', 3,'Hapag-Lloyd', 4,'ONE', 5,'Pacific Express Lines', 6,'Evergreen Marine'),
    UNIFORM(45, 600, RANDOM()),
    'kinesis-firehose'
FROM TABLE(GENERATOR(ROWCOUNT => 5));

ALTER TASK RAW.SEED_GATE_EVENTS RESUME;
