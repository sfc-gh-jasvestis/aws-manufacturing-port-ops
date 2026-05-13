import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import _snowflake
from snowflake.snowpark.context import get_active_session

session = get_active_session()

def coerce_numeric(df, cols=None):
    if df is None or len(df) == 0:
        return df
    target = cols or [c for c in df.columns if df[c].dtype == "object"]
    for c in target:
        try:
            df[c] = pd.Series([float(x) if x is not None else None for x in df[c]], index=df.index, dtype="float64")
        except (TypeError, ValueError):
            pass
    return df
st.set_page_config(page_title="Port Operations Monitor", layout="wide", page_icon="anchor")

STATUS_COLORS = {"BERTHED": "#3498DB", "WAITING": "#F39C12", "DEPARTED": "#95A5A6", "SCHEDULED": "#2ECC71", "COMPLETED": "#27AE60", "AT_SEA": "#3498DB", "ANCHORED": "#F39C12"}

page = st.sidebar.radio("Navigation", ["Overview", "Terminal Status", "Vessel Tracking", "Berth Schedule", "Ask Port Ops"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("### Port Operations")
st.sidebar.caption("Terminal utilization, vessel tracking, and berth scheduling across 8 terminals")


@st.cache_data(ttl=60)
def load_terminals():
    df = coerce_numeric(session.sql("SELECT * FROM MANUFACTURING_PORT_OPS.CURATED.TERMINAL_STATUS ORDER BY UTILIZATION_PCT DESC").to_pandas())
    for c in ["BERTHS", "CRANE_COUNT", "MAX_TEU_PER_DAY", "QUEUE_DEPTH", "VESSELS_BERTHED", "FREE_BERTHS", "UTILIZATION_PCT", "AVG_WAIT_HOURS"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data(ttl=60)
def load_vessels():
    df = coerce_numeric(session.sql("SELECT * FROM MANUFACTURING_PORT_OPS.CURATED.VESSEL_TRACKING").to_pandas())
    for c in ["CURRENT_LAT", "CURRENT_LON", "SPEED_KNOTS", "CAPACITY_TEU", "WAIT_TIME_HOURS"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data(ttl=60)
def load_berths():
    df = coerce_numeric(session.sql("SELECT * FROM MANUFACTURING_PORT_OPS.CURATED.BERTH_SCHEDULE").to_pandas())
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
    anchored = vessels[vessels["STATUS"] == "ANCHORED"].nlargest(1, "WAIT_TIME_HOURS") if "STATUS" in vessels.columns else pd.DataFrame()
    if not anchored.empty:
        hero_vessel = anchored.iloc[0]
        st.error(f"INCIDENT: {bottleneck['TERMINAL_NAME']} at {bottleneck['UTILIZATION_PCT']:.0f}% utilization, queue {int(bottleneck['QUEUE_DEPTH'])}, {bottleneck['AVG_WAIT_HOURS']:.1f}h wait (target 4h) - {hero_vessel['VESSEL_NAME']} waiting {hero_vessel['WAIT_TIME_HOURS']:.0f}h")
    else:
        st.error(f"INCIDENT: {bottleneck['TERMINAL_NAME']} at {bottleneck['UTILIZATION_PCT']:.0f}% utilization, queue {int(bottleneck['QUEUE_DEPTH'])}, {bottleneck['AVG_WAIT_HOURS']:.1f}h wait (target 4h)")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Terminals", len(term))
    c2.metric("Vessels in Queue", int(term["QUEUE_DEPTH"].sum()))
    c3.metric("Vessels Berthed", int(term["VESSELS_BERTHED"].sum()))
    c4.metric("Avg Utilization", f"{term['UTILIZATION_PCT'].mean():.1f}%")
    c5.metric("Max Wait", f"{term['AVG_WAIT_HOURS'].max():.1f}h", delta=f"{term['AVG_WAIT_HOURS'].max()-4:+.1f}h vs target", delta_color="inverse")

    if not anchored.empty:
        hw = anchored.iloc[0]
        d1, d2, d3 = st.columns(3)
        d1.metric("Longest Wait Vessel", hw["VESSEL_NAME"])
        d2.metric("Wait Time", f"{hw['WAIT_TIME_HOURS']:.0f}h")
        d3.metric("Est. Demurrage", f"${hw['WAIT_TIME_HOURS'] * 12000:,.0f}")

    st.divider()
    cc1, cc2 = st.columns(2)
    with cc1:
        tu = term.sort_values("UTILIZATION_PCT")
        x_vals = [float(v) for v in tu["UTILIZATION_PCT"].tolist()]
        y_vals = [str(v) for v in tu["TERMINAL_NAME"].tolist()]
        fig = go.Figure(data=[go.Bar(x=x_vals, y=y_vals, orientation="h", marker=dict(color=x_vals, colorscale="RdYlGn_r", cmin=0, cmax=100), hovertemplate="<b>%{y}</b><br>Utilization: %{x:.1f}%<extra></extra>")])
        fig.add_vline(x=90, line_dash="dash", line_color="red", annotation_text="Critical 90%")
        fig.update_layout(title="Terminal Utilization %", height=380, margin=dict(t=40, b=10), xaxis_title="Utilization %", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        twait = term.dropna(subset=["AVG_WAIT_HOURS"]).sort_values("AVG_WAIT_HOURS")
        x_vals = [float(v) for v in twait["AVG_WAIT_HOURS"].tolist()]
        y_vals = [str(v) for v in twait["TERMINAL_NAME"].tolist()]
        fig = go.Figure(data=[go.Bar(x=x_vals, y=y_vals, orientation="h", marker=dict(color=x_vals, colorscale="OrRd"), hovertemplate="<b>%{y}</b><br>Wait: %{x:.1f}h<extra></extra>")])
        fig.add_vline(x=4, line_dash="dash", line_color="red", annotation_text="Target 4h")
        fig.update_layout(title="Avg Wait Hours", height=380, margin=dict(t=40, b=10), xaxis_title="Hours", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Terminal Status":
    st.title("Terminal Status")
    st.caption("Per-terminal capacity, queues, and dwell")
    term = load_terminals()

    tu2 = term.sort_values("UTILIZATION_PCT")
    x_vals = [str(v) for v in tu2["TERMINAL_NAME"].tolist()]
    y_vals = [float(v) for v in tu2["UTILIZATION_PCT"].tolist()]
    fig = go.Figure(data=[go.Bar(x=x_vals, y=y_vals, marker=dict(color=y_vals, colorscale="RdYlGn_r", cmin=0, cmax=100), text=[f"{v:.0f}" for v in y_vals], textposition="auto", hovertemplate="<b>%{x}</b><br>Utilization: %{y:.1f}%<extra></extra>")])
    fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Critical 90%")
    fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="High 80%")
    fig.update_layout(title="Utilization % per Terminal", height=400, margin=dict(t=40, b=10), yaxis_title="Utilization %", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Terminal Details")
    show = term[["TERMINAL_NAME", "OPERATOR", "BERTHS", "VESSELS_BERTHED", "FREE_BERTHS", "QUEUE_DEPTH", "UTILIZATION_PCT", "AVG_WAIT_HOURS", "CRANE_COUNT", "MAX_TEU_PER_DAY"]]
    st.dataframe(show.reset_index(drop=True), use_container_width=True)

elif page == "Vessel Tracking":
    st.title("Vessel Tracking")
    st.caption("Live vessel positions and statuses")
    v = load_vessels()
    if v.empty:
        st.info("No vessels."); st.stop()

    longest_wait = v[v["STATUS"] == "ANCHORED"].nlargest(1, "WAIT_TIME_HOURS")
    if not longest_wait.empty:
        ps = longest_wait.iloc[0]
        st.warning(f"{ps['VESSEL_NAME']}: {ps['STATUS']} - waiting {ps['WAIT_TIME_HOURS']:.0f}h on {ps.get('ASSIGNED_TERMINAL', 'Terminal 3')}")

    anchored = v[v["STATUS"].isin(["ANCHORED", "WAITING"])]
    total_demurrage = anchored["WAIT_TIME_HOURS"].sum() * 12000

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vessels", len(v))
    c2.metric("At Sea", int((v["STATUS"] == "AT_SEA").sum()))
    c3.metric("Anchored / Waiting", int(len(anchored)))
    c4.metric("Total Demurrage", f"${total_demurrage:,.0f}")

    sc = v["STATUS"].value_counts().reset_index()
    sc.columns = ["STATUS", "COUNT"]
    x_vals = [str(v) for v in sc["STATUS"].tolist()]
    y_vals = [int(v) for v in sc["COUNT"].tolist()]
    bar_colors = [STATUS_COLORS.get(s, "#888") for s in x_vals]
    fig = go.Figure(data=[go.Bar(x=x_vals, y=y_vals, marker_color=bar_colors, text=y_vals, textposition="auto", hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>")])
    fig.update_layout(title="Vessels by Status", height=380, margin=dict(t=40, b=10), showlegend=False, yaxis_title="Count", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 20 Longest Waits")
    long_wait = v.dropna(subset=["WAIT_TIME_HOURS"]).sort_values("WAIT_TIME_HOURS", ascending=False).head(20).copy()
    long_wait["EST_DEMURRAGE"] = long_wait["WAIT_TIME_HOURS"] * 12000
    display_cols = ["VESSEL_NAME", "VESSEL_TYPE", "STATUS", "ASSIGNED_TERMINAL", "WAIT_TIME_HOURS", "EST_DEMURRAGE", "CAPACITY_TEU", "SPEED_KNOTS"]
    st.dataframe(long_wait[display_cols].style.format({"EST_DEMURRAGE": "${:,.0f}", "WAIT_TIME_HOURS": "{:.1f}"}), use_container_width=True)

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
        wsel = waiting.head(15).sort_values("WAIT_TIME_HOURS")
        x_vals = [float(v) for v in wsel["WAIT_TIME_HOURS"].tolist()]
        y_vals = [str(v) for v in wsel["VESSEL_NAME"].tolist()]
        terms = [str(v) for v in wsel["TERMINAL_NAME"].tolist()]
        unique_terms = list(dict.fromkeys(terms))
        palette = ["#3498DB", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C", "#E67E22", "#34495E"]
        cmap = {t: palette[i % len(palette)] for i, t in enumerate(unique_terms)}
        bar_colors = [cmap[t] for t in terms]
        fig = go.Figure(data=[go.Bar(x=x_vals, y=y_vals, orientation="h", marker_color=bar_colors, customdata=terms, hovertemplate="<b>%{y}</b><br>Wait: %{x:.1f}h<br>Terminal: %{customdata}<extra></extra>")])
        fig.add_vline(x=4, line_dash="dash", line_color="red", annotation_text="Target 4h")
        fig.update_layout(title="Top Waiting Vessels", height=400, margin=dict(t=40, b=10, l=180), xaxis_title="Wait Hours", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Berth Schedule Detail")
    st.dataframe(b[["VESSEL_NAME", "VESSEL_TYPE", "TERMINAL_NAME", "BERTH_NUMBER", "STATUS", "WAIT_TIME_HOURS", "CARGO_TYPE", "CONTAINER_COUNT"]].sort_values("STATUS").reset_index(drop=True), use_container_width=True)

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
                                st.dataframe(session.sql(sql).to_pandas().reset_index(drop=True), use_container_width=True)
                            except Exception:
                                pass
                else:
                    st.error(parsed)
            except Exception as e:
                st.error(f"Error: {e}")
