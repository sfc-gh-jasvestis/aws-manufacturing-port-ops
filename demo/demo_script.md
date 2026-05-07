# Demo Script: Port Operations — Real-time Terminal Twin
## ~3-Minute Recorded Walkthrough
**Format**: Screen recording with voiceover
**Target**: Customer meeting / booth loop / social share
**Pre-requisites**: Data loaded, Streamlit deployed, QuickSight dashboard published, gate-events seed task running, Rekognition Lambda `mfg-portops-ocr` deployed

---

## Two Personas

| Persona | Role | Tool | What they care about |
|---|---|---|---|
| **Yard Operator** | Real-time gate control | Streamlit (Real-time Gate Events page) | Per-gate throughput, dwell time, container ID accuracy, stuck containers |
| **Terminal Manager** | Daily / weekly oversight | Amazon QuickSight + Amazon Q | Throughput trends, gate utilization heatmap, vessel turnaround |

---

## What's Built

| Layer | Component | Detail |
|---|---|---|
| **Ingest (AWS)** | Kinesis Data Firehose + S3 | `mfg-portops-gate-events` stream + `s3://sg-manufacturing-demos-2026/port-ops/gate-cam/` for camera frames |
| **Streaming** | Snowpipe Streaming | Sub-5-second latency from gate scan to row in `RAW.GATE_EVENTS` |
| **Vision** | AWS Lambda + Rekognition | `mfg-portops-ocr` Lambda triggers on `s3:ObjectCreated`, calls Rekognition `DetectText`, writes container number to `RAW.OCR_RESULTS` |
| **RAW** | 4 tables | TERMINALS (8), VESSELS, BERTHS, GATE_EVENTS (live) + OCR_RESULTS |
| **CURATED** | 4 Dynamic Tables | TERMINAL_STATUS, VESSEL_TRACKING, BERTH_SCHEDULE, GATE_EVENTS_5MIN |
| **AI** | Semantic View + Agent | PORT_OPS_SEMANTIC_VIEW |
| **AWS Hero** | Kinesis Firehose + Snowpipe Streaming + Rekognition | Stream `mfg-portops-gate-events`, Lambda `mfg-portops-ocr`, foundation model `text-detection` |
| **Consumption** | Streamlit | 8-page Port Operations Monitor |
| | QuickSight | `mfg-port-ops-dashboard` + Amazon Q topic `mfg-port-ops-q` |

---

## Pre-Recording Checklist

- [ ] Seed task `RAW.SEED_GATE_EVENTS` is RESUMED — `SHOW TASKS IN MANUFACTURING_PORT_OPS.RAW`
- [ ] `SELECT COUNT(*) FROM MANUFACTURING_PORT_OPS.RAW.GATE_EVENTS` returns 200+ (and growing)
- [ ] `SELECT COUNT(*) FROM MANUFACTURING_PORT_OPS.RAW.OCR_RESULTS` returns 40+
- [ ] Terminal 3 utilization = 100% in `TERMINAL_STATUS`
- [ ] MV Pacific Star wait > 22h in `VESSEL_TRACKING`
- [ ] Open Streamlit: https://app.snowflake.com/SFSEAPAC/sg_demo43/#/streamlit-apps/MANUFACTURING_PORT_OPS.APP.PORT_OPERATIONS_APP
- [ ] Open QuickSight: https://us-west-2.quicksight.aws.amazon.com/sn/dashboards/mfg-port-ops-dashboard
- [ ] Pre-open AWS tabs:
  - Kinesis: `https://us-west-2.console.aws.amazon.com/firehose/home?region=us-west-2#/details/mfg-portops-gate-events`
  - Lambda: `https://us-west-2.console.aws.amazon.com/lambda/home?region=us-west-2#/functions/mfg-portops-ocr`
  - S3 (gate cam): `https://s3.console.aws.amazon.com/s3/buckets/sg-manufacturing-demos-2026?prefix=port-ops/gate-cam/`
- [ ] Audio: quiet room, external mic
- [ ] Resolution: 1920x1080

---

## Script

### [0:00–0:20] THE PROBLEM & ARCHITECTURE

**Show**: Streamlit Overview page — Terminal 3 at 100%, MV Pacific Star at 22h wait

> "Terminal 3 at one hundred percent utilization. MV Pacific Star anchored twenty-two hours waiting for berth. Gate 4 dwell time twenty-two minutes per truck. Most port-ops tools update every fifteen minutes. By then the queue is already around the block. We're going to fix that — every gate scan reaches Snowflake in under five seconds, every container number is read off the camera by **Amazon Rekognition**, and every minute is aggregated for the manager. Snowflake plus AWS, real-time."

### [0:20–0:45] PAGE 1: TERMINAL STATUS + VESSEL TRACKING

**Show**: Terminal utilization heatmap, vessel queue chart

**Tech**: Dynamic Tables (5-min refresh)

> "Eight terminals, two hundred vessels, one thousand berth slots. Terminal 3 saturated; Terminal 5 only sixty-three percent — load balancing opportunity in plain sight. The MV Pacific Star, twenty-two hours queued, is exactly the kind of vessel we should re-route to Terminal 5 right now."

### [0:45–1:25] PAGE 2: REAL-TIME GATE EVENTS — Kinesis + Snowpipe Streaming

**Show**: Click `Real-time Gate Events (AWS Kinesis)` page

**Tech**: Kinesis Firehose + Snowpipe Streaming + 1-min Dynamic Table

> "Here's the AWS hero. Every gate scanner publishes a JSON event to **Kinesis Firehose** delivery stream `mfg-portops-gate-events`. Firehose forwards every record to a **Snowpipe Streaming** endpoint — and the row appears in `RAW.GATE_EVENTS` in under five seconds. Look at the *Last 5 min* counter — it ticks up while we watch. The per-minute throughput chart aggregates a one-minute Dynamic Table. No batch ingest, no S3 staging, no copy job."

**Action**: Refresh the page once to show the counter updating.

> "Watch the counter — five new events in the last sixty seconds. That's the seed task simulating live throughput. In production this is real Firehose."

**Action**: Switch to **AWS Kinesis console** → show delivery stream `mfg-portops-gate-events` with bytes-in metric.

> "There's the Firehose metric on the AWS side — bytes flowing in continuously. Same data, two consoles, identical truth."

### [1:25–1:55] PAGE 3: CONTAINER OCR — Rekognition

**Show**: Click `Container OCR (AWS Rekognition)` page

**Tech**: Lambda + Rekognition `DetectText`

> "Now the vision side. Every gate camera drops a frame into `s3://sg-manufacturing-demos-2026/port-ops/gate-cam/`. **AWS Lambda** `mfg-portops-ocr` triggers on `s3:ObjectCreated`, calls **Rekognition `DetectText`**, and writes the detected container number plus confidence into `RAW.OCR_RESULTS`. Confidence over ninety percent on every read — operators don't have to type a thing. Rekognition handles the OCR; Snowflake handles the join."

**Action**: Switch to **AWS Lambda console** → show recent invocations of `mfg-portops-ocr` (success rate ~100%).

### [1:55–2:25] PAGE 4: ASK PORT OPS

**Show**: Type "How many trucks went through Gate 3 in the last hour?" — confirm answer

**Tech**: Cortex Analyst + Semantic View

> "Natural language. **Cortex Analyst** over `PORT_OPS_SEMANTIC_VIEW` reads the live Dynamic Table and answers in plain English. 'How many trucks went through Gate 3 in the last hour?' — answered. 'Which berth has the longest current wait?' — answered. Same conversational interface for the yard operator and the night-shift supervisor."

### [2:25–2:55] QUICKSIGHT + AMAZON Q — the manager view

**Show**: Switch to QuickSight dashboard `mfg-port-ops-dashboard`

**Tech**: QuickSight Snowflake direct query + Amazon Q topic

> "Operator works in real time on Streamlit. Manager works in QuickSight — `mfg-port-ops-dashboard` rolls up daily throughput, gate utilization heatmap, vessel turnaround. **Amazon Q topic** `mfg-port-ops-q` answers 'What was peak gate throughput today?' or 'Which terminal had the longest dwell?' — from a phone in the operations centre."

### [2:55–3:10] CLOSE

> "Recap. Gate scanners publish to **Kinesis Firehose** — Snowflake gets every record in under five seconds via **Snowpipe Streaming**. Cameras drop frames in **S3**; **Lambda** calls **Rekognition `DetectText`** to extract the container number. Snowflake **Dynamic Tables** aggregate to one-minute buckets. **Cortex Analyst** answers operator questions; **QuickSight** plus **Amazon Q** answer the manager's. Three AWS services on the data path, four Snowflake capabilities on the analytics path, one real-time terminal twin. From the gate to the boardroom — in five seconds. That's **Port Operations** on Snowflake and AWS."

---

## Key Demo Differentiators (vs other AWS demos)

1. **Snowpipe Streaming, not Snowpipe** — sub-5-second latency, per-record (not per-file) ingest.
2. **Rekognition + Snowflake join** — vision and structured data joined in one query, no separate ML pipeline.
3. **Live data on stage** — the seed task means the demo is *literally* growing while you record.
4. **Two AWS consoles in the demo** — Kinesis Firehose metrics + Lambda invocations make the AWS side tangible.
5. **Q topic answers** to try: "What was peak throughput today?" / "Which terminal has the longest dwell?" / "How many trucks at gate 4 in the last hour?"
