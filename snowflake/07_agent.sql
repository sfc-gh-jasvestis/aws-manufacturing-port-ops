-- Port Operations: Cortex Agent
USE SCHEMA MANUFACTURING_PORT_OPS.AI;

CREATE OR REPLACE AGENT PORT_OPS_AGENT
    COMMENT = 'Port Operations & Vessel Tracking Agent for terminal analytics and regulation search'
    PROFILE = '{"display_name": "Port Operations Agent", "color": "teal"}'
    FROM SPECIFICATION
    $$
    models:
      orchestration: auto

    orchestration:
      budget:
        seconds: 30
        tokens: 16000

    instructions:
      response: "You are a port operations analyst. Provide concise, data-driven answers about terminal utilization, vessel queues, wait times, and berth assignments. When discussing congestion, highlight Terminal 3 issues and recommend rerouting to Terminal 1."
      orchestration: "For questions about terminal performance, vessel tracking, queue depths, and wait times, use PortAnalyst. For questions about port regulations, safety rules, berth allocation policies, and environmental requirements, use RegulationsSearch."
      system: "You are an expert port operations agent helping optimize vessel traffic, reduce wait times, and improve terminal utilization at a major container port."
      sample_questions:
        - question: "Which terminal has the longest wait?"
          answer: "I'll query the terminal status data for wait time metrics."
        - question: "How many vessels are waiting?"
          answer: "I'll check the vessel tracking data for waiting vessels."
        - question: "What is the berth allocation policy?"
          answer: "I'll search port regulations for berth allocation procedures."

    tools:
      - tool_spec:
          type: "cortex_analyst_text_to_sql"
          name: "PortAnalyst"
          description: "Analyzes structured port operations data including terminal utilization, vessel tracking, queue depths, wait times, berth schedules, and cargo throughput. Use for any quantitative questions about port performance."
      - tool_spec:
          type: "cortex_search"
          name: "RegulationsSearch"
          description: "Searches port regulations, safety rules, berth allocation policies, environmental requirements, pilotage guidelines, and customs procedures. Use for any questions about port rules and compliance."

    tool_resources:
      PortAnalyst:
        semantic_view: "MANUFACTURING_PORT_OPS.AI.PORT_OPS_SEMANTIC_VIEW"
      RegulationsSearch:
        name: "MANUFACTURING_PORT_OPS.SEARCH.PORT_REGULATIONS_SEARCH"
        max_results: "5"
        title_column: "TITLE"
        id_column: "DOC_ID"
    $$;
