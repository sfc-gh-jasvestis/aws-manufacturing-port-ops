# Demo Script: Real-time Terminal Twin
## ~70-second walkthrough — Snowflake + Kinesis Firehose + Snowpipe Streaming + Rekognition + QuickSight

---

## The Story
Terminal 3 at 100% utilization. Trucks queueing 22 minutes at Gate 4. Every gate scan lands in Snowflake in under 5 seconds via Kinesis Firehose — and a Lambda using Rekognition reads each container number off the gate camera.

---

## Personas

| Persona | Tool | What they care about |
|---|---|---|
| Yard Operator | Streamlit (real-time gate page) | Per-gate throughput, dwell time, stuck containers |
| Terminal Manager | Amazon QuickSight + Amazon Q | Daily throughput trend, gate utilization |

---

## Script

### [0:00–0:10] HOOK
> "Terminal 3 100% utilization. Gate 4 22-minute dwell. Every truck scan reaches Snowflake in under 5 seconds — Kinesis Firehose into Snowpipe Streaming."

### [0:10–0:30] STREAMLIT — Real-time Gate Events (AWS Kinesis)
> Open `MANUFACTURING_PORT_OPS.APP.PORT_OPERATIONS_APP` -> page **Real-time Gate Events (AWS Kinesis)**.
> "Live counter on the top — events from the last 5 minutes. Below: per-minute throughput chart for the last hour. The 50 most recent events update every page refresh — Firehose `mfg-portops-gate-events` -> Snowpipe Streaming endpoint -> `RAW.GATE_EVENTS`."

### [0:30–0:45] CONTAINER OCR (AWS Rekognition)
> Switch to **Container OCR (AWS Rekognition)**.
> "Gate cameras drop a frame on S3, Lambda `mfg-portops-ocr` triggers on `s3:ObjectCreated`, calls Rekognition `DetectText`, writes the container number into Snowflake. 90%+ confidence on every read — operators don't even type."

### [0:45–1:00] CORTEX AI + QUICKSIGHT
> "Ask Port Ops: 'How many trucks went through Gate 3 in the last hour?' Cortex Analyst answers off the same Dynamic Tables. QuickSight dashboard `mfg-port-ops-dashboard` and Amazon Q topic `mfg-port-ops-q` give the manager the daily view."

### [1:00–1:10] CLOSE
> "Kinesis writes; Rekognition sees; Snowflake aggregates; QuickSight visualises. One stream of truth from the gate to the boardroom."

---

## Pre-Recording Checklist
- [ ] `SELECT COUNT(*) FROM RAW.GATE_EVENTS` returns 200+ rows (task is running)
- [ ] `SELECT COUNT(*) FROM RAW.OCR_RESULTS` returns 40+ rows
- [ ] Real-time Gate Events page renders the per-minute chart
- [ ] Open https://app.snowflake.com/SFSEAPAC/sg_demo43/#/streamlit-apps/MANUFACTURING_PORT_OPS.APP.PORT_OPERATIONS_APP
- [ ] Open https://us-west-2.quicksight.aws.amazon.com/sn/dashboards/mfg-port-ops-dashboard
