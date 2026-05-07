import streamlit as st
import pandas as pd
import json
import plotly.express as px
import _snowflake
from snowflake.snowpark.context import get_active_session

session = get_active_session()
st.set_page_config(page_title="Port Operations Monitor", layout="wide", page_icon="anchor")

STATUS_COLORS = {"BERTHED": "#3498DB", "WAITING": "#F39C12", "DEPARTED": "#95A5A6", "SCHEDULED": "#2ECC71", "COMPLETED": "#27AE60", "AT_SEA": "#3498DB", "ANCHORED": "#F39C12"}

page = st.sidebar.radio("Navigation", ["Overview", "Terminal Status", "Vessel Tracking", "Berth Schedule", "Real-time Gate Events (AWS Kinesis)", "Container OCR (AWS Rekognition)", "Ask Port Ops", "AWS Architecture"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("### Port Operations")
st.sidebar.caption("Terminal utilization, vessel tracking, and berth scheduling across 8 terminals")


@st.cache_data(ttl=60)
def load_terminals():
    df = session.sql("SELECT * FROM MANUFACTURING_PORT_OPS.CURATED.TERMINAL_STATUS ORDER BY UTILIZATION_PCT DESC").to_pandas()
    for c in ["BERTHS", "CRANE_COUNT", "MAX_TEU_PER_DAY", "QUEUE_DEPTH", "VESSELS_BERTHED", "FREE_BERTHS", "UTILIZATION_PCT", "AVG_WAIT_HOURS"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data(ttl=60)
def load_vessels():
    df = session.sql("SELECT * FROM MANUFACTURING_PORT_OPS.CURATED.VESSEL_TRACKING").to_pandas()
    for c in ["CURRENT_LAT", "CURRENT_LON", "SPEED_KNOTS", "CAPACITY_TEU", "WAIT_TIME_HOURS"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data(ttl=60)
def load_berths():
    df = session.sql("SELECT * FROM MANUFACTURING_PORT_OPS.CURATED.BERTH_SCHEDULE").to_pandas()
    for c in ["WAIT_TIME_HOURS", "CAPACITY_TEU", "CONTAINER_COUNT"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


if page == "Overview":
    st.title("Port Operations Monitor")
    st.caption("Live terminal status, vessel queue, and berth scheduling")
    term = load_terminals()
    berth = load_berths()
    vessels = load_vessels()

    bottleneck = term.iloc[0]
    waiting_pacific = berth[(berth["VESSEL_NAME"].str.contains("Pacific Star", na=False))]
    star_wait = waiting_pacific["WAIT_TIME_HOURS"].max() if not waiting_pacific.empty else 0
    st.error(f"INCIDENT: {bottleneck['TERMINAL_NAME']} at {bottleneck['UTILIZATION_PCT']:.0f}% utilization, queue {int(bottleneck['QUEUE_DEPTH'])}, {bottleneck['AVG_WAIT_HOURS']:.1f}h wait (target 4h) - MV Pacific Star waiting {star_wait:.0f}h")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Terminals", len(term))
    c2.metric("Vessels in Queue", int(term["QUEUE_DEPTH"].sum()))
    c3.metric("Vessels Berthed", int(term["VESSELS_BERTHED"].sum()))
    c4.metric("Avg Utilization", f"{term['UTILIZATION_PCT'].mean():.1f}%")
    c5.metric("Max Wait", f"{term['AVG_WAIT_HOURS'].max():.1f}h", delta=f"{term['AVG_WAIT_HOURS'].max()-4:+.1f}h vs target", delta_color="inverse")

    st.divider()
    cc1, cc2 = st.columns(2)
    with cc1:
        fig = px.bar(term.sort_values("UTILIZATION_PCT"), x="UTILIZATION_PCT", y="TERMINAL_NAME", orientation="h", color="UTILIZATION_PCT", color_continuous_scale="RdYlGn_r", range_color=[0, 100], title="Terminal Utilization %")
        fig.add_vline(x=90, line_dash="dash", line_color="red", annotation_text="Critical 90%")
        fig.update_layout(height=380, margin=dict(t=40, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        twait = term.dropna(subset=["AVG_WAIT_HOURS"]).sort_values("AVG_WAIT_HOURS")
        fig = px.bar(twait, x="AVG_WAIT_HOURS", y="TERMINAL_NAME", orientation="h", color="AVG_WAIT_HOURS", color_continuous_scale="OrRd", title="Avg Wait Hours")
        fig.add_vline(x=4, line_dash="dash", line_color="red", annotation_text="Target 4h")
        fig.update_layout(height=380, margin=dict(t=40, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

elif page == "Terminal Status":
    st.title("Terminal Status")
    st.caption("Per-terminal capacity, queues, and dwell")
    term = load_terminals()

    fig = px.bar(term.sort_values("UTILIZATION_PCT"), x="TERMINAL_NAME", y="UTILIZATION_PCT", color="UTILIZATION_PCT", color_continuous_scale="RdYlGn_r", range_color=[0, 100], title="Utilization % per Terminal", text_auto=".0f")
    fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Critical 90%")
    fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="High 80%")
    fig.update_layout(height=400, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Terminal Details")
    show = term[["TERMINAL_NAME", "OPERATOR", "BERTHS", "VESSELS_BERTHED", "FREE_BERTHS", "QUEUE_DEPTH", "UTILIZATION_PCT", "AVG_WAIT_HOURS", "CRANE_COUNT", "MAX_TEU_PER_DAY"]]
    st.dataframe(show, use_container_width=True, hide_index=True)

elif page == "Vessel Tracking":
    st.title("Vessel Tracking")
    st.caption("Live vessel positions and statuses")
    v = load_vessels()
    if v.empty:
        st.info("No vessels."); st.stop()

    pacific = v[v["VESSEL_NAME"].str.contains("Pacific Star", na=False)]
    if not pacific.empty:
        ps = pacific.iloc[0]
        st.warning(f"MV Pacific Star: {ps['STATUS']} - waiting {ps['WAIT_TIME_HOURS']:.0f}h on {ps.get('ASSIGNED_TERMINAL', 'Terminal 3')}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Vessels", len(v))
    c2.metric("At Sea", int((v["STATUS"] == "AT_SEA").sum()))
    c3.metric("Anchored / Waiting", int(v["STATUS"].isin(["ANCHORED", "WAITING"]).sum()))

    sc = v["STATUS"].value_counts().reset_index()
    sc.columns = ["STATUS", "COUNT"]
    fig = px.bar(sc, x="STATUS", y="COUNT", color="STATUS", color_discrete_map=STATUS_COLORS, title="Vessels by Status", text_auto=True)
    fig.update_layout(height=380, margin=dict(t=40, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 20 Longest Waits")
    long_wait = v.dropna(subset=["WAIT_TIME_HOURS"]).sort_values("WAIT_TIME_HOURS", ascending=False).head(20)
    st.dataframe(long_wait[["VESSEL_NAME", "VESSEL_TYPE", "STATUS", "ASSIGNED_TERMINAL", "WAIT_TIME_HOURS", "CAPACITY_TEU", "SPEED_KNOTS"]], use_container_width=True, hide_index=True)

elif page == "Berth Schedule":
    st.title("Berth Schedule")
    st.caption("Active berth assignments and queue")
    b = load_berths()

    waiting = b[b["STATUS"] == "WAITING"].sort_values("WAIT_TIME_HOURS", ascending=False)
    berthed = b[b["STATUS"] == "BERTHED"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Currently Berthed", len(berthed))
    c2.metric("Waiting", len(waiting))
    c3.metric("Avg Wait (Waiting)", f"{waiting['WAIT_TIME_HOURS'].mean():.1f}h" if not waiting.empty else "0h")

    if not waiting.empty:
        fig = px.bar(waiting.head(15).sort_values("WAIT_TIME_HOURS"), x="WAIT_TIME_HOURS", y="VESSEL_NAME", orientation="h", color="TERMINAL_NAME", title="Top Waiting Vessels")
        fig.add_vline(x=4, line_dash="dash", line_color="red", annotation_text="Target 4h")
        fig.update_layout(height=400, margin=dict(t=40, b=10, l=180))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Berth Schedule Detail")
    st.dataframe(b[["VESSEL_NAME", "VESSEL_TYPE", "TERMINAL_NAME", "BERTH_NUMBER", "STATUS", "WAIT_TIME_HOURS", "CARGO_TYPE", "CONTAINER_COUNT"]].sort_values("STATUS"), use_container_width=True, hide_index=True)

elif page == "Real-time Gate Events (AWS Kinesis)":
    st.title("Real-time Gate Events")
    st.caption("Kinesis Firehose -> Snowpipe Streaming -> Snowflake (5-min Dynamic Table)")
    try:
        recent = session.sql("SELECT EVENT_TS, GATE_ID, DIRECTION, CONTAINER_NUM, CARRIER_NAME, DWELL_SECONDS FROM MANUFACTURING_PORT_OPS.RAW.GATE_EVENTS ORDER BY EVENT_TS DESC LIMIT 50").to_pandas()
        c1, c2, c3, c4 = st.columns(4)
        total = session.sql("SELECT COUNT(*) FROM MANUFACTURING_PORT_OPS.RAW.GATE_EVENTS").to_pandas().iloc[0, 0]
        last_min = session.sql("SELECT COUNT(*) FROM MANUFACTURING_PORT_OPS.RAW.GATE_EVENTS WHERE EVENT_TS > DATEADD('minute', -5, CURRENT_TIMESTAMP())").to_pandas().iloc[0, 0]
        c1.metric("Total Events", f"{int(total):,}")
        c2.metric("Last 5 min", int(last_min))
        c3.metric("Source", "Kinesis Firehose")
        c4.metric("Latency", "< 5 sec")
        st.success("Firehose delivery stream `mfg-portops-gate-events` writes to Snowpipe Streaming endpoint; Dynamic Table `CURATED.GATE_EVENTS_5MIN` aggregates every minute.")
        bucket = session.sql("SELECT TO_VARCHAR(BUCKET_TS, 'HH24:MI') AS T, SUM(EVENT_COUNT) AS EVENTS FROM MANUFACTURING_PORT_OPS.CURATED.GATE_EVENTS_5MIN WHERE BUCKET_TS > DATEADD('hour', -1, CURRENT_TIMESTAMP()) GROUP BY 1 ORDER BY 1").to_pandas()
        if not bucket.empty:
            fig = px.bar(bucket, x="T", y="EVENTS", title="Gate events per minute (last hour)")
            fig.update_layout(height=320, margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
        st.subheader("50 most recent events")
        st.dataframe(recent, use_container_width=True)
    except Exception as e:
        st.error(f"Stream error: {e}")

elif page == "Container OCR (AWS Rekognition)":
    st.title("Container OCR via AWS Rekognition")
    st.caption("Gate cameras -> S3 -> Lambda -> Rekognition DetectText -> Snowflake")
    try:
        ocr = session.sql("SELECT OCR_TS, GATE_ID, S3_KEY, DETECTED_TEXT, CONFIDENCE_PCT FROM MANUFACTURING_PORT_OPS.RAW.OCR_RESULTS ORDER BY OCR_TS DESC LIMIT 30").to_pandas()
        c1, c2, c3 = st.columns(3)
        c1.metric("OCR Records", len(ocr))
        c2.metric("Avg Confidence", f"{ocr['CONFIDENCE_PCT'].astype(float).mean():.1f}%")
        c3.metric("Lambda", "mfg-portops-ocr")
        st.info("Lambda `mfg-portops-ocr` reads each gate-cam frame from `s3://sg-manufacturing-demos-2026/port-ops/gate-cam/`, calls Rekognition `DetectText`, and writes the result to `RAW.OCR_RESULTS`.")
        st.dataframe(ocr, use_container_width=True)
    except Exception as e:
        st.error(f"OCR error: {e}")

elif page == "Ask Port Ops":
    st.title("Ask the Data")
    st.caption("Natural language questions powered by Cortex Analyst")
    samples = ["Which terminal has the longest wait?", "How many vessels are waiting?", "What is the average utilization across terminals?"]
    sample = st.selectbox("Sample questions:", [""] + samples)
    q = st.text_input("Or type your question:", value=sample)
    if q:
        with st.spinner("Cortex Analyst..."):
            try:
                body = {"messages": [{"role": "user", "content": [{"type": "text", "text": q}]}], "semantic_view": "MANUFACTURING_PORT_OPS.AI.PORT_OPS_SEMANTIC_VIEW"}
                resp = _snowflake.send_snow_api_request("POST", "/api/v2/cortex/analyst/message", {}, {}, body, None, 30000)
                parsed = json.loads(resp["content"])
                if resp["status"] < 400:
                    for block in parsed.get("message", {}).get("content", []):
                        if block.get("type") == "text":
                            st.markdown(block.get("text", ""))
                        elif block.get("type") == "sql":
                            sql = block.get("statement", "")
                            with st.expander("SQL"):
                                st.code(sql, language="sql")
                            try:
                                st.dataframe(session.sql(sql).to_pandas(), use_container_width=True, hide_index=True)
                            except Exception:
                                pass
                else:
                    st.error(parsed)
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "AWS Architecture":
    st.title("AWS Architecture - Real-time Terminal Twin")
    st.caption("Snowflake + Kinesis Firehose + Snowpipe Streaming + Rekognition + QuickSight")
    a, b, c, d = st.columns(4)
    a.metric("AWS Hero", "Kinesis Firehose")
    b.metric("Stream", "mfg-portops-gate-events")
    c.metric("Vision", "Rekognition")
    d.metric("Latency", "< 5 sec")
    st.markdown(
        """
**Data flow**

1. **Gate scanners** publish JSON event records to **Kinesis Data Firehose** delivery stream `mfg-portops-gate-events`.
2. Firehose forwards every record to a **Snowpipe Streaming** endpoint -> rows land in `RAW.GATE_EVENTS` with sub-5-second latency.
3. **Gate cameras** drop frames into `s3://sg-manufacturing-demos-2026/port-ops/gate-cam/`. **AWS Lambda** `mfg-portops-ocr` triggers on `s3:ObjectCreated`, calls **Rekognition `DetectText`**, and writes the container number to `RAW.OCR_RESULTS`.
4. A **Dynamic Table** `CURATED.GATE_EVENTS_5MIN` aggregates throughput per gate every minute.
5. **QuickSight** dashboard `mfg-port-ops-dashboard` and **Amazon Q topic** `mfg-port-ops-q` answer "How many trucks have come through gate 3 in the last 10 minutes?" off the same Snowflake data.

**ARNs**

- `arn:aws:kinesis:us-west-2:018437500440:deliverystream/mfg-portops-gate-events`
- `arn:aws:s3:::sg-manufacturing-demos-2026/port-ops/gate-cam/`
- `arn:aws:lambda:us-west-2:018437500440:function:mfg-portops-ocr`
- `arn:aws:rekognition:us-west-2::foundation-model/text-detection`
        """
    )
