-- Port Operations: Cortex Agent
USE SCHEMA MANUFACTURING_PORT_OPS.AI;

CREATE OR REPLACE CORTEX AGENT PORT_OPS_AGENT
    COMMENT = 'AI assistant for port operations and vessel management'
    MODEL = 'claude-3-5-sonnet'
    TOOLS = (
        'MANUFACTURING_PORT_OPS.AI.PORT_OPS_SEMANTIC_VIEW' AS PortAnalyst,
        'MANUFACTURING_PORT_OPS.SEARCH.PORT_REGULATIONS_SEARCH' AS RegulationsSearch,
        'snowflake.cortex.data_to_chart' AS ChartGenerator
    )
    SYSTEM_PROMPT = 'You are a port operations intelligence assistant. Help harbor masters and port authorities optimize berth allocation, reduce vessel wait times, and manage terminal congestion. Always reference specific terminals, vessel names, and wait times in your recommendations.';
