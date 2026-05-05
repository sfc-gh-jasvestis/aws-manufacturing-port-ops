# Port Operations & Vessel Tracking — Demo Script

## Story

You're Captain Liu Wei, Port Authority Director. Your control room screen flashes red — Terminal 3 is over capacity. Within 3.5 minutes, you'll identify the bottleneck, find MV Pacific Star with $85M cargo waiting 22 hours, discover Terminal 1 has spare berths, and execute a rerouting plan that clears the queue.

## Personas

| Persona | Title | Goal |
|---------|-------|------|
| **Captain Liu Wei** | Port Authority Director | Maintain flow, prevent gridlock, protect cargo value |
| **Rachel Torres** | Maritime Operations VP | Throughput optimization, SLA compliance |

## What's Built

| Layer | Object | Purpose |
|-------|--------|---------|
| Data | 200 vessels, 8 terminals, 50K events, 20K manifests | Complete port model |
| Dynamic Tables | TERMINAL_STATUS, VESSEL_TRACKING, BERTH_SCHEDULE | Real-time operations view |
| ML | Vessel Arrivals Forecast, Queue Depth Anomaly | Predictive scheduling |
| Search | PORT_REGULATIONS_SEARCH (80 docs) | Maritime rules retrieval |
| Semantic View | PORT_OPS_SEMANTIC_VIEW | Natural language analytics |
| Agent | PORT_OPS_AGENT | Conversational port assistant |
| Streamlit | PORT_OPERATIONS_APP | Operations dashboard |

## Narrative Arc

```
ALERT → IDENTIFY → ASSESS → FIND_CAPACITY → REROUTE → CONFIRM
  │         │          │          │             │          │
  ▼         ▼          ▼          ▼             ▼          ▼
Terminal  8 queued   MV Pacific  Terminal 1    Move 4     Queue
3 red    (cap 5)   Star 22h    2 free        ships     cleared
                   $85M cargo   berths
```

## Timed Script (3.5 minutes)

### Opening — Port Control Dashboard (0:00–0:20)
- Open Streamlit app — PORT_OPERATIONS_APP
- "I'm Captain Liu Wei, managing operations for one of Asia's busiest ports"
- KPI cards: 8 terminals | 200 vessels | Terminal 3 CRITICAL | 18h avg wait
- **Key visual:** Terminal status heatmap, Terminal 3 glowing red

### Beat 1 — Identify the Bottleneck (0:20–0:50)
- Click Terminal 3 detail
- "8 vessels queued — our capacity is 5. We're 60% over limit"
- "Average wait time has ballooned to 18 hours — target is 4"
- Show queue depth chart
- **Number:** 8 vessels queued, capacity 5, 18h avg wait (target 4h)

### Beat 2 — High-Value Vessel at Risk (0:50–1:20)
- Navigate to Vessel Tracking
- Filter: TERMINAL_3, STATUS = 'ANCHORED'
- "MV Pacific Star — 22 hours waiting with $85M in cargo"
- "4,200 TEU of electronics components destined for 3 countries"
- "Every hour of delay costs the shipping line approximately $15K"
- **Number:** MV Pacific Star, 22h waiting, $85M cargo, 4,200 TEU

### Beat 3 — Find Available Capacity (1:20–1:50)
- Switch to Terminal Overview
- Scan all 8 terminals
- "Terminal 1 — 2 free berths, average wait just 2 hours"
- "It can handle Panamax vessels, which covers Pacific Star"
- **Number:** Terminal 1: 2 free berths, 2h avg wait

### Beat 4 — Ask AI for Rerouting Plan (1:50–2:30)
- Open AI Assistant
- Type: "Recommend a rerouting plan for Terminal 3 overflow"
- Agent responds: "Reroute 4 vessels to Terminal 1 (2 free berths + 2 departing within 3h). Priority: MV Pacific Star first ($85M cargo), then by wait time"
- "The agent checked berth compatibility, crane availability, and departure schedules"
- **Key moment:** AI generates prioritized rerouting sequence

### Beat 5 — Validate Against Regulations (2:30–3:10)
- Type: "Are there any draft restrictions for Terminal 1?"
- Cortex Search retrieves berth specifications
- "Maximum draft 14.5m — Pacific Star draws 13.2m. We're clear"
- Show regulation document snippet
- **Number:** 14.5m max draft vs 13.2m vessel draft

### Closing — Execute the Plan (3:10–3:30)
- Return to terminal overview
- "Reroute initiated: 4 vessels moving to Terminal 1"
- "MV Pacific Star berthing within 90 minutes instead of 8+ more hours"
- "We just prevented $85M of cargo from sitting in our harbor overnight"
- **Tagline:** "See the bottleneck, find the capacity, clear the queue — in minutes"

## Pre-Recording Checklist

- [ ] Streamlit app loaded with terminal heatmap
- [ ] Terminal 3 showing 8 queued vessels (cap 5)
- [ ] 18h average wait visible for Terminal 3
- [ ] MV Pacific Star: 22h waiting, $85M cargo visible
- [ ] Terminal 1 showing 2 free berths
- [ ] Agent responding with rerouting recommendation
- [ ] Search returning draft restriction regulations
- [ ] Warehouse CORTEX is STARTED

## Key Questions to Anticipate

1. **"How do you handle tide windows?"** — Port events track tidal constraints; berth assignments validate draft clearance
2. **"What about vessel priority?"** — Priority field supports CRITICAL, HIGH, STANDARD; agent factors cargo value and wait time
3. **"Can this integrate with AIS?"** — Yes, S3 stage can ingest AIS feeds via Snowpipe for real-time vessel positions
4. **"What if Terminal 1 can't handle the vessel type?"** — Semantic view includes berth specifications; agent validates compatibility before recommending
5. **"How does this scale to multiple ports?"** — Architecture supports multi-port; add PORT_ID dimension to all tables
