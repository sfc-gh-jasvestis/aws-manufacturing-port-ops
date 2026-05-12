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
| **RAW** | 4 tables | TERMINALS (8), VESSELS, BERTHS, GATE_EVENTS (live — 6,500+ and growing) + OCR_RESULTS |
| **CURATED** | 4 Dynamic Tables | TERMINAL_STATUS, VESSEL_TRACKING, BERTH_SCHEDULE, GATE_EVENTS_5MIN |
| **AI** | Semantic View + Agent | PORT_OPS_SEMANTIC_VIEW |
| **AWS Hero** | Kinesis Firehose + Snowpipe Streaming + Rekognition | Stream `mfg-portops-gate-events`, Lambda `mfg-portops-ocr`, foundation model `text-detection` |
| **Consumption** | Streamlit | 8-page Port Operations Monitor |
| | QuickSight | `mfg-port-ops-dashboard` + Amazon Q topic `mfg-port-ops-q` |

---

## Pre-Recording Checklist

- [ ] Seed task `RAW.SEED_GATE_EVENTS` is RESUMED — `SHOW TASKS IN MANUFACTURING_PORT_OPS.RAW`
- [ ] `SELECT COUNT(*) FROM MANUFACTURING_PORT_OPS.RAW.GATE_EVENTS` returns 43,900+ (and growing every minute)
- [ ] `SELECT COUNT(*) FROM MANUFACTURING_PORT_OPS.RAW.OCR_RESULTS` returns 40+
- [ ] Terminal 3 utilization = 100% in `TERMINAL_STATUS` (CONGESTED) — shows as ~90%+ bar in chart
- [ ] Storm Runner wait ~49h in `VESSEL_TRACKING`; incident banner shows "Storm Runner waiting 49h"
- [ ] Overview metrics: Terminals=8, Vessels in Queue=12, Vessels Berthed=23, Avg Utilization=65.8%, Max Wait=15.1h (+11.1h vs target)
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

### [0:00–0:20] OVERVIEW — THE PROBLEM (Streamlit Overview page)

**On screen**:
- 🔴 INCIDENT banner: "Terminal 3 at 100% utilization, queue 8, 15.1h wait — **Storm Runner** waiting 49h"
- 5 KPI cards (row 1): Terminals=8 | Vessels in Queue=12 | Vessels Berthed=23 | Avg Utilization=65.8% | Max Wait=15.1h (+11.1h vs target)
- 3 KPI cards (row 2): **Longest Wait Vessel=Storm Runner** | Wait Time=49h | Est. Demurrage=$584,400
- Terminal Utilization % chart (Terminal 3 bar past red "Critical 90%" line; Terminal 7 lowest ~33% green)
- Wait Hours chart (Terminal 3 at ~15h longest; Terminal 2 at ~13h; "Target 4h" red dashed line)

**Metric validating narrative**: "Longest Wait Vessel" KPI card = Storm Runner; "Wait Time" KPI = 49h; "Est. Demurrage" KPI = $584K; Max Wait = 15.1h; Utilization chart shows Terminal 3 at critical.

> "Five hundred eighty-four thousand dollars. That number — right there — is what one ship has cost us while it sits at anchor. Storm Runner, forty-nine hours waiting. Twelve vessels in queue. Max wait fifteen hours against a four-hour target. And look at the utilization chart — Terminal 3's bar has blown past the critical line. But this isn't a report from yesterday. Every number on this screen updated five seconds ago. That's the difference."

---

### [0:20–0:40] TERMINAL STATUS — the capacity view (Streamlit Terminal Status page)

**On screen**:
- Per-terminal table: TERMINAL_NAME, UTILIZATION_PCT, QUEUE_DEPTH, VESSELS_BERTHED, AVG_WAIT_HOURS, FREE_BERTHS
- Terminal 3 row: 100% util, queue 8, 15.1h wait, 0 free berths
- Terminal 8 row: 50% util, queue 0, 4.6h wait, 2 free berths (lowest wait, best reroute target)

**Metric validating narrative**: Terminal 3 row shows 100% / queue 8 / 15.1h; Terminal 8 shows 50% / 4.6h wait / 2 free berths.

**Tech**: Dynamic Tables (5-min refresh)

> "Terminal 3 — full. One hundred percent. Eight ships queued, zero berths free. But look at Terminal 8 — fifty percent utilized, two berths sitting empty, four-hour wait. The solution is staring at us. Reroute three ships, crisis over. These are Snowflake Dynamic Tables — refreshing every five minutes, zero manual pipelines."

---

### [0:40–1:00] VESSEL TRACKING — the cost of inaction (Streamlit Vessel Tracking page)

**On screen**:
- ⚠️ Warning banner: "Storm Runner: ANCHORED - waiting 49h on Terminal 1"
- 4 KPI cards: Vessels=200 | At Sea=43 | Anchored/Waiting=82 | **Total Demurrage=~$X,XXX,XXX**
- Vessels by Status bar chart (ANCHORED bar highlighted)
- "Top 20 Longest Waits" table with **EST_DEMURRAGE column** — Storm Runner row #1 at 48.7h / ~$584K; Pacific Glory row #2 at 48.4h / ~$581K

**Metric validating narrative**: "Total Demurrage" KPI card shows fleet-wide cost; EST_DEMURRAGE column in table shows per-vessel cost; Storm Runner + Pacific Glory dollar amounts visible in table rows.

> "There's Storm Runner — top of the table, forty-nine hours anchored. Look at the demurrage column: five hundred eighty-four thousand dollars, one ship. Pacific Glory right behind — five eighty-one. Scroll up to the KPI: total demurrage across the fleet, right there in black and white. This isn't a forecast — it's money we are burning *right now*, visible to anyone with a browser."

---

### [1:00–1:30] REAL-TIME GATE EVENTS — Kinesis + Snowpipe Streaming (Streamlit Gate Events page)

**On screen**:
- 4 KPI cards: Total Events=43,900+ | Last 5 min=count | Source=Kinesis Firehose | Latency=< 5 sec
- Per-minute bar chart (gate events per minute, last hour)
- 50 most recent events table

**Metric validating narrative**: Total Events counter (growing live); Latency KPI = < 5 sec; per-minute chart bars visible.

**Tech**: Kinesis Firehose + Snowpipe Streaming + 5-min Dynamic Table

> "This is how we get five-second latency. Every gate scan fires into **Kinesis Firehose**, **Snowpipe Streaming** writes the row — look at the counter: forty-three thousand events and climbing. Watch..."

**Action**: Refresh the page.

> "It just went up. That's real. Happening *now*. Not a nightly batch, not an hourly sync — every single truck, every gate, five seconds from scan to screen."

**Action**: Switch to **AWS Kinesis console** → show delivery stream `mfg-portops-gate-events`.

> "Same data on the AWS side — bytes flowing continuously. One truth, two consoles."

---

### [1:30–2:00] CONTAINER OCR — Rekognition (Streamlit OCR page)

**On screen**:
- 3 KPI cards: OCR Records=40 | Avg Confidence=93.8% | Lambda=mfg-portops-ocr
- Info box: explains Lambda → Rekognition → Snowflake flow
- **Gate camera photo** showing container door with clearly readable `TCNU 9156324` code, size `45G1`, weight markings (30,480 KGS), and CIMC badge
- Detail panel: Detected Text=`TCNU 9156324` | Size/Type=45G1 — 40FT HIGH CUBE | Max Gross=30,480 KGS | Tare=3,840 KGS | Manufacturer=CIMC | Confidence=98.7%
- OCR results table: OCR_TS, GATE_ID, S3_KEY, DETECTED_TEXT, CONFIDENCE_PCT

**Metric validating narrative**: Container code `TCNU 9156324` visible in both the photo AND the detail panel; weight markings (30,480 KGS) visible in photo AND detail panel; Confidence 98.7% in detail panel; Avg Confidence KPI = 93.8%.

**Tech**: Lambda + Rekognition `DetectText`

> "Container numbers — typed by hand in most ports. Here, a camera takes a frame, **Lambda** sends it to **Rekognition**, and the container ID lands in Snowflake. Look at the photo — `TCNU 9156324` right there on the door — and now look at the detail panel: same code, extracted in under two seconds. Ninety-eight-point-seven percent confidence. Max gross, tare weight, manufacturer — all pulled off the door with zero keystrokes."

**Action**: Switch to **AWS Lambda console** → show `mfg-portops-ocr` invocations.

---

### [2:00–2:30] ASK PORT OPS — natural language (Streamlit Ask Port Ops page)

**On screen**:
- Text input box with question
- Cortex Analyst response: SQL + results table showing Terminal 3 at 100%

**Metric validating narrative**: Cortex Analyst returns "Terminal 3, 100% utilization" — matches Overview page KPIs.

**Tech**: Cortex Analyst + Semantic View

> "Plain English. 'Which terminal is most congested?' — and **Cortex Analyst** comes back with Terminal 3, one hundred percent, zero free berths. Same live data, no SQL required. The yard operator at 2 AM and the terminal manager at 9 AM get the same answer from the same source of truth."

---

### [2:30–2:55] QUICKSIGHT + AMAZON Q — the manager view (QuickSight dashboard)

**On screen**:
- QuickSight dashboard `mfg-port-ops-dashboard`: KPIs, throughput chart, utilization heatmap
- Amazon Q topic `mfg-port-ops-q` ready for questions

**Metric validating narrative**: QuickSight KPIs match Streamlit (same underlying Dynamic Table); Amazon Q answers same queries.

**Tech**: QuickSight Snowflake direct query + Amazon Q topic

> "Same data, different audience. The operator lives in Streamlit — real-time, five-second refresh. The manager opens QuickSight on their phone — utilization heatmaps, terminal rankings. Same Dynamic Table underneath both. And with **Amazon Q**: 'Which terminal is most congested?' — answered in plain English, from a phone."

---

### [2:55–3:15] CLOSE

> "Five seconds from gate to Snowflake. Container codes read by Rekognition — zero keystrokes. Dynamic Tables keeping every metric current. Cortex Analyst answering 'which terminal is most congested?' in plain English. QuickSight putting it on the manager's phone. Storm Runner sat at anchor for forty-nine hours — five hundred eighty-four thousand dollars in demurrage — because nobody could see the queue. With this stack, you see it in five seconds. One reroute decision, half a million saved. **That's Port Operations on Snowflake and AWS.**"

---

## Key Demo Differentiators (vs other AWS demos)

1. **Snowpipe Streaming, not Snowpipe** — sub-5-second latency, per-record (not per-file) ingest.
2. **Live data on stage** — the seed task means the data is *literally growing during the recording*. Counter goes up live.
3. **Rekognition + Snowflake join** — vision and structured data joined in one query, no separate ML pipeline.
4. **49-hour demurrage** — Storm Runner's wait time makes the cost of inaction tangible ($584K in demurrage at $12K/hr — shown as a KPI card).
5. **Two AWS consoles in the demo** — Kinesis metrics + Lambda invocations make the AWS side concrete.
6. **Q topic answers** to try: "What was peak throughput today?" / "Which terminal has the longest wait?" / "How many trucks at Gate 4 in the last hour?"
