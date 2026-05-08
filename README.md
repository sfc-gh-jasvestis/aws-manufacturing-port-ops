# Port Operations & Vessel Tracking

Real-time port operations intelligence powered by Snowflake Cortex AI — optimize berth allocation, reduce vessel wait times, and prevent terminal congestion.

## Architecture

A real-time terminal twin built on **Snowflake** (Snowpipe Streaming, Dynamic Tables, semantic view, Cortex Analyst) and **AWS** (Kinesis Data Firehose, S3, Lambda, Rekognition, QuickSight + Amazon Q). Every gate scan reaches Snowflake in under 5 seconds; gate-camera frames are read by Rekognition `DetectText` and joined to the event stream.

```mermaid
flowchart LR
    Gate[Gate scanner] --> KIN[Kinesis Firehose mfg-portops-gate-events]
    KIN --> SP[Snowpipe Streaming]
    SP --> SF[Snowflake RAW.GATE_EVENTS]
    Cam[Gate camera] --> S3[S3 gate-cam frames]
    S3 --> LAM[Lambda mfg-portops-ocr]
    LAM --> REK[Rekognition DetectText]
    REK --> SF
    SF --> DT[Dynamic Table GATE_EVENTS_5MIN]
    DT --> SemView[Semantic View]
    DT --> ST[Streamlit Port Ops App]
    DT --> QS[QuickSight + Amazon Q]
```


## Personas

| Persona | Role | Key Questions |
|---------|------|---------------|
| **Captain Liu Wei** | Port Authority Director | Which terminals are over capacity? Where do I reroute? |
| **Rachel Torres** | Maritime Operations VP | What's our throughput? Are we meeting SLAs? |

## Data

| Table | Rows | Description |
|-------|------|-------------|
| VESSELS | 200 | Active vessel fleet with status and cargo |
| TERMINALS | 8 | Terminal capacity and current assignments |
| BERTH_ASSIGNMENTS | 5,032 | Historical and active berth allocations |
| PORT_EVENTS | 50,000 | Operational events (arrivals, departures, delays) |
| CARGO_MANIFESTS | 20,001 | Cargo detail per vessel |
| PORT_REGULATIONS | 80 | Maritime rules and procedures |

## Build Instructions

### Prerequisites
- Snowflake account with ACCOUNTADMIN access
- Cortex AI enabled (ML Functions, Search, Agent)
- Warehouse: CORTEX (Medium)

### Deployment

```bash
snowsql -f snowflake/00_setup.sql
snowsql -f snowflake/01_raw_tables.sql
snowsql -f snowflake/02_staging.sql
snowsql -f snowflake/03_dynamic_tables.sql
snowsql -f snowflake/04_search.sql
snowsql -f snowflake/05_ml_models.sql
snowsql -f snowflake/06_semantic_view.sql
snowsql -f snowflake/07_agent.sql
```

### Streamlit App
```
MANUFACTURING_PORT_OPS.APP.PORT_OPERATIONS_APP
```

## Key Demo Numbers

- **8 vessels** queued at Terminal 3 (capacity: 5)
- **18h** average wait time at Terminal 3 (target: 4h)
- **MV Pacific Star** — 22h waiting, $85M cargo
- **Terminal 1** — 2 free berths, ready to absorb rerouted traffic
- **4 vessels** recommended for rerouting

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.
This is a personal project and is not an official Snowflake offering. It comes with no support or warranty. Use it at your own risk. Snowflake has no obligation to maintain, update, or support this code. Do not use this code in production without thorough review and testing.
