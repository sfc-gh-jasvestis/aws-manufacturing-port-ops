-- Port Operations: Semantic View
USE SCHEMA MANUFACTURING_PORT_OPS.AI;

CREATE OR REPLACE SEMANTIC VIEW PORT_OPS_SEMANTIC_VIEW
    COMMENT = 'Port operations analytics: terminals, vessels, berth utilization'
AS
    TABLES (
        CURATED.TERMINAL_STATUS AS terminals
            COLUMNS (
                TERMINAL_NAME AS terminal_name COMMENT 'Terminal identifier',
                BERTH_COUNT AS total_berths COMMENT 'Total berth capacity',
                OCCUPIED_BERTHS AS occupied_berths COMMENT 'Currently occupied berths',
                FREE_BERTHS AS free_berths COMMENT 'Available berths',
                UTILIZATION_PCT AS utilization COMMENT 'Berth utilization percentage',
                VESSELS_QUEUED AS queue_depth COMMENT 'Number of vessels waiting',
                AVG_WAIT_HOURS AS avg_wait_hours COMMENT 'Average wait time in hours'
            ),
        CURATED.VESSEL_TRACKING AS vessels
            COLUMNS (
                VESSEL_NAME AS vessel_name COMMENT 'Name of vessel',
                VESSEL_TYPE AS vessel_type COMMENT 'Type of vessel',
                CURRENT_STATUS AS status COMMENT 'ANCHORED or BERTHED',
                CARGO_VALUE AS cargo_value COMMENT 'Total cargo value in USD',
                HOURS_WAITING AS hours_waiting COMMENT 'Hours since arrival',
                TERMINAL_NAME AS assigned_terminal COMMENT 'Assigned terminal'
            ),
        CURATED.BERTH_SCHEDULE AS berths
            COLUMNS (
                VESSEL_NAME AS vessel_name COMMENT 'Name of vessel at berth',
                TERMINAL_NAME AS terminal_name COMMENT 'Terminal of berth',
                BERTH_NUMBER AS berth_number COMMENT 'Physical berth number',
                DURATION_HOURS AS occupancy_hours COMMENT 'Hours at berth'
            )
    );
