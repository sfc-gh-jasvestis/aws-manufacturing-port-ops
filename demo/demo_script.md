# Demo Script: Port Operations Monitor
## ~70-second walkthrough — AWS + Snowflake

---

## The Story
Terminal 3 at 100% utilization, queue depth 8, 22-hour wait against a 4-hour SLA. MV Pacific Star has been waiting almost a full day.

---

## Personas

| Persona | Tool | What they care about |
|---|---|---|
| Port Operator | Streamlit on Snowflake | Live terminal status, vessel queue, berth schedule |
| Port Authority Director | Amazon QuickSight + Amazon Q | Throughput, SLA breaches, capacity planning |

---

## Script

### [0:00–0:10] HOOK
> "Terminal 3 at 100% utilization, queue depth 8, 22-hour wait against a 4-hour SLA. MV Pacific Star has been waiting almost a full day."

### [0:10–0:35] SNOWFLAKE — STREAMLIT
> Open `MANUFACTURING_PORT_OPS.APP.PORT_OPERATIONS_APP`.
> "Overview banner highlights Terminal 3 and Pacific Star. Terminal Status page: utilization spread from 33% on Terminal 7 up to 100% on Terminal 3 — no longer flat. Vessel Tracking shows Pacific Star anchored. Berth Schedule ranks waiting vessels by wait time. Three Dynamic Tables join 200 vessels, 8 terminals, 5,000 berth assignments live."

### [0:35–0:50] CORTEX AI
> "Ask the Data: 'Which terminal has the longest wait?' Cortex Analyst over `PORT_OPS_SEMANTIC_VIEW` returns Terminal 3 at 21.8h. The semantic view exposes 9 dimensions and 7 metrics — no need to know the schema."

### [0:50–1:05] AWS
> "S3 stage `s3://sg-manufacturing-demos-2026/port-ops/` lands manifests and gate-in/gate-out events. QuickSight `mfg-port-ops-dashboard`: KPIs for terminals, vessels berthed, queue, average utilization, plus utilization-by-terminal and wait-hours-by-terminal with the 4-hour SLA reference line. Amazon Q topic `mfg-port-ops-q` answers 'How many vessels are waiting?' on demand."

### [1:05–1:10] CLOSE
> "Real-time on Snowflake. Executive on AWS QuickSight. One source of truth."

---

## Pre-Recording Checklist
- [ ] Verify Terminal 3 at 100% util / 21.8h wait / queue 8
- [ ] Verify MV Pacific Star WAITING 22h on Terminal 3
- [ ] Open https://app.snowflake.com/SFSEAPAC/sg_demo43/#/streamlit-apps/MANUFACTURING_PORT_OPS.APP.PORT_OPERATIONS_APP
- [ ] Open https://us-west-2.quicksight.aws.amazon.com/sn/dashboards/mfg-port-ops-dashboard
