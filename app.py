import streamlit as st
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, date


LOGO_PATH = "logo.png"  # optional logo in same folder

st.set_page_config(
    page_title="Resume Shortlisting Dashboard",
    layout="wide",
    page_icon="📊",
)
from PIL import Image

LOGO_PATH = "logo.png"

try:
    logo_img = Image.open(LOGO_PATH)
    st.image(logo_img, width=130)
except Exception:
    st.write("")  # no logo found

# ====== DATA SETUP ======
os.makedirs("data", exist_ok=True)
results_file = os.path.join("data", "results.json")

if not os.path.exists(results_file):
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump([], f)

with open(results_file, "r", encoding="utf-8") as f:
    try:
        results = json.load(f)
    except Exception:
        results = []

df = pd.DataFrame(results)

# Normalize types
if not df.empty:
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "score" in df.columns:
        df["score"] = pd.to_numeric(df["score"], errors="coerce")

# ====== STYLES ======
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(120deg,#fffaf0,#f4fbff); }
    .card { background: white; padding: 18px; border-radius:12px; box-shadow: 0 8px 24px rgba(0,0,0,0.05); }
    .muted {color:#6b7280;}
    .kpi { font-size:24px; font-weight:700; color:#1f2937;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ====== HEADER ======
col_logo, col_title = st.columns([1, 10])
with col_logo:
    try:
        st.image(LOGO_PATH, width=72)
    except Exception:
        pass

with col_title:
    st.title("📈 Resume Shortlisting Dashboard")
    st.markdown(
        "<div class='muted'>Overview of analyses, scores, and skill gaps for the date range you choose.</div>",
        unsafe_allow_html=True,
    )

# ======================================================
# 🔥 SIDEBAR FILTERS (Job, score, FREE date range chosen by user)
# ======================================================
selected_job = "All"
min_score = 0
start_date = None
end_date = None

with st.sidebar:
    st.header("Filters")

    if df.empty:
        st.info("No analysis records yet. Go to Resume Analyzer page and run some analyses.")
    else:
        # Job filter
        if "job_title" in df.columns:
            job_titles = sorted(df["job_title"].dropna().unique().tolist())
        else:
            job_titles = []
        selected_job = st.selectbox("Filter by job title", ["All"] + job_titles)

        # Score filter
        min_score = st.slider("Minimum match score (%)", 0, 100, 0)

        # ===== FREE DATE RANGE: user decides FROM and TO =====
        if "timestamp" in df.columns and df["timestamp"].notna().any():
            data_min_date = df["timestamp"].min().date()
            data_max_date = df["timestamp"].max().date()
            today = date.today()

            # default range: from first record to today (or last record if in future)
            default_start = data_min_date
            default_end = max(data_max_date, today)

            date_range = st.date_input(
                "Date range (From / To)",
                value=(default_start, default_end),
            )

            # --- Normalize date_range into two pure date objects ---
            if isinstance(date_range, tuple):
                if len(date_range) == 2:
                    start_date, end_date = date_range
                elif len(date_range) == 1:
                    start_date = end_date = date_range[0]
                else:
                    # weird edge case, fall back to defaults
                    start_date, end_date = default_start, default_end
            else:
                start_date = end_date = date_range

            # Now start_date and end_date are guaranteed datetime.date objects

            # --- Messages when user goes outside data range / today ---
            if start_date < data_min_date:
                st.warning(
                    f"Analysis data is only available from {data_min_date}. "
                    f"Results will effectively start from that date."
                )

            if end_date > today:
                st.warning(
                    f"You selected an end date in the future ({end_date}). "
                    f"Only existing records up to today ({today}) will be shown."
                )

            st.caption(f"Currently filtering from **{start_date}** to **{end_date}**")
        else:
            st.info("No timestamp data available for date filtering.")

        st.markdown("---")

        # Download all data
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download All Results (CSV)",
            csv_data,
            "resume_results.csv",
            "text/csv",
        )

        # Clear all data (admin)
        if st.button("🗑️ Clear All Data"):
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            st.success("All analysis data cleared. Reload the page.")
            st.stop()

# ======================================================
# 🔥 APPLY FILTERS
# ======================================================
filtered = df.copy()

if not filtered.empty:
    # Job filter
    if selected_job != "All" and "job_title" in filtered.columns:
        filtered = filtered[filtered["job_title"] == selected_job]

    # Score filter
    if "score" in filtered.columns:
        filtered = filtered[filtered["score"] >= min_score]

    # Date range filter (user-chosen FROM / TO)
    if (
        start_date is not None
        and end_date is not None
        and "timestamp" in filtered.columns
    ):
        # Clamp only for filtering logic:
        #   - if start_date < data_min_date, we still compare against it, but effect is same
        #   - if end_date > today, we still compare against it, but no future records anyway
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        filtered = filtered[
            (filtered["timestamp"] >= start_dt) & (filtered["timestamp"] <= end_dt)
        ]

# ======================================================
# 🔥 DASHBOARD KPI CARDS
# ======================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Analyses")
    st.markdown(f"<div class='kpi'>{len(filtered)}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='muted'>Filtered from {len(df)} total</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Avg Score")
    avg_score = (
        round(filtered["score"].mean(), 2)
        if (not filtered.empty and "score" in filtered.columns)
        else 0
    )
    st.markdown(f"<div class='kpi'>{avg_score}%</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Jobs Analyzed")
    job_count = (
        filtered["job_title"].nunique()
        if (not filtered.empty and "job_title" in filtered.columns)
        else 0
    )
    st.markdown(f"<div class='kpi'>{job_count}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Top Missing Skill")
    miss = []
    if not filtered.empty and "missing_skills" in filtered.columns:
        for s in filtered["missing_skills"]:
            if isinstance(s, list):
                miss.extend(s)
    top_missing = pd.Series(miss).value_counts().index[0] if miss else "—"
    st.markdown(f"<div class='kpi'>{top_missing}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ======================================================
# 🔥 MESSAGE IF NO DATA AFTER FILTERS
# ======================================================
if filtered.empty:
    st.warning(
        "No records found for the selected filters (job, score, date range). "
        "If you selected dates before analyses started or only future dates, there will be no data."
    )
    st.stop()

# ======================================================
# 🔥 SCORE DISTRIBUTION
# ======================================================
st.subheader("Score Distribution (Filtered)")
if "score" not in filtered.columns:
    st.info("No score data available.")
else:
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.hist(filtered["score"].dropna(), bins=10, edgecolor="white")
    ax.set_xlabel("Score (%)")
    ax.set_ylabel("Count")
    st.pyplot(fig)

# ======================================================
# 🔥 RECENT ANALYSES
# ======================================================
st.subheader("Recent Analyses (Filtered)")
if "timestamp" in filtered.columns:
    recent = filtered.sort_values("timestamp", ascending=False).head(10)
    recent_display = recent.copy()
    recent_display["timestamp"] = recent_display["timestamp"].dt.strftime(
        "%Y-%m-%d %H:%M"
    )
else:
    recent_display = filtered.copy()

cols_to_show = [
    c for c in ["timestamp", "candidate_name", "job_title", "score"]
    if c in recent_display.columns
]
st.dataframe(recent_display[cols_to_show], use_container_width=True)

# ======================================================
# 🔥 SKILL SUMMARY
# ======================================================
st.subheader("Skill Match Summary (Top 10, Filtered)")

matched_counts = {}
missing_counts = {}

for _, row in filtered.iterrows():
    jd = row.get("jd_skills", []) or []
    rs = row.get("resume_skills", []) or []
    rs_lower = [x.lower() for x in rs if isinstance(x, str)]

    for s in jd:
        if not isinstance(s, str):
            continue
        if s.lower() in rs_lower:
            matched_counts[s] = matched_counts.get(s, 0) + 1
        else:
            missing_counts[s] = missing_counts.get(s, 0) + 1

skills = set(matched_counts) | set(missing_counts)

if skills:
    df_summary = pd.DataFrame({"skill": list(skills)})
    df_summary["matched"] = df_summary["skill"].apply(
        lambda s: matched_counts.get(s, 0)
    )
    df_summary["missing"] = df_summary["skill"].apply(
        lambda s: missing_counts.get(s, 0)
    )
    df_summary = df_summary.sort_values("missing", ascending=False).head(10)
    df_summary = df_summary.set_index("skill")
    st.bar_chart(df_summary)
else:
    st.info("No skill data available for the selected filters.")

st.markdown("---")
st.markdown(
    "➡️ Use the **Resume Analyzer** page to add more records. You can pick any date range you like from the sidebar."
)
footer_html = """
<style>
footer {
    visibility: hidden;
}
#custom-footer {
    position: scroll;
    left: 0;
    bottom: 0;
    width: 100%;
    background: linear-gradient(90deg,#1f77b4,#b8860b);
    color: white;
    text-align: center;
    padding: 8px 0;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.5px;
    z-index: 9999;
}
</style>

<div id="custom-footer">
    Developed by Akhil • ✉️akhillade431@gmail.com
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
