"""Streamlit version of NextGen Lead Generator - Flask code ko touch nahi kiya"""

import subprocess
import sys
import os
import html as html_lib

# Playwright browser install on Streamlit Cloud - sabse pehle
# NOTE: We only install the Chromium *browser binary* here (no --with-deps /
# install-deps). The system-level libraries Chromium needs (libnss3, libatk,
# etc.) are installed separately by Streamlit Cloud via packages.txt at
# BUILD time, when the process *does* have root. Calling "install-deps"
# here at runtime tries to run apt-get without root and always fails.
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

import streamlit as st
import pandas as pd
from datetime import datetime
from scraper_pw import scrape_google_maps  # Tumhara existing scraper
from analyzer import analyze_leads         # Tumhara existing analyzer
import config

st.set_page_config(
    page_title="NextGen Lead Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Dark theme CSS — matches the Flask dashboard's look ─────────────────
st.markdown("""
<style>
    .stApp {
        background-color: #0f1117;
        color: #e4e7;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6c63ff, #00d2ff);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    /* Dark-theme the input widgets, which default to white */
    .stTextInput input, .stNumberInput input {
        background-color: #18181b !important;
        color: #e4e7 !important;
        border: 1px solid #3f46 !important;
    }
    .stSelectbox > div > div {
        background-color: #18181b !important;
        color: #e4e4e7 !important;
        border: 1px solid #3f3f46 !important;
    }
    /* Stat cards */
    div[data-testid="stMetric"] {
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 10px;
        padding: 16px 18px;
    }
    div[data-testid="stMetricValue"] { color: #e4e4e7; }
    div[data-testid="stMetricLabel"] { color: #a1a1aa; }
    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #a1a1aa; }
    .stTabs [aria-selected="true"] { color: #e4e4e7 !important; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🎯 NextGen Analytics")
st.markdown("**Lead Generator — Find businesses on Google Maps that need web development services**")
st.divider()

# Search Form
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    business_type = st.text_input("Business Type", "Gym", placeholder="e.g. restaurants, plumbers")

with col2:
    location = st.text_input("Location", "Karachi", placeholder="e.g. Miami, Lahore")

with col3:
    country = st.selectbox("Country", config.COUNTRY_OPTIONS, index=config.COUNTRY_OPTIONS.index("Pakistan"))

with col4:
    max_results = st.number_input("Max Results", min_value=1, max_value=1000000, value=20)

search_button = st.button("🔍 Search Leads", width='stretch')

# Session state for results
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None

if search_button:
    if not business_type or not location or not country:
        st.error("Business Type, Location, and Country are required")
    else:
        query = f"{business_type.strip()} in {location.strip()}, {country.strip()}"

        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_callback(current, total, msg):
            pct = int((current / total) * 100) if total > 0 else 0
            progress_bar.progress(pct)
            status_text.text(f"{current}/{total} — {msg}")

        try:
            with st.spinner("Scraping Google Maps..."):
                leads = scrape_google_maps(
                    query,
                    max_results=max_results,
                    progress_callback=progress_callback
                )

                for lead in leads:
                    lead["country"] = country

                status_text.text("Analyzing websites...")
                progress_bar.progress(0)

                analyze_leads(leads, progress_callback=progress_callback)

                st.session_state.leads_df = pd.DataFrame(leads)
                progress_bar.progress(100)
                status_text.success(f"✅ Done! Found {len(leads)} leads")

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.exception(e)

# ── Custom HTML table renderer (mirrors the Flask dashboard) ────────────
def _score_color(score):
    if score >= 80:
        return "#f97316"   # hot
    if score >= 50:
        return "#fb923c"   # warm
    return "#22c55e"       # low priority

def render_leads_table(df):
    if df.empty:
        st.info("No leads in this category.")
        return

    rows_html = []
    for _, lead in df.iterrows():
        score = int(lead.get("lead_score") or 0)
        color = _score_color(score)

        name = html_lib.escape(str(lead.get("name")) if pd.notna(lead.get("name")) else "N/A")

        # Rating - safe convert
        rating = pd.to_numeric(lead.get("rating"), errors='coerce')
        rating = f"{rating:.1f}" if pd.notna(rating) else "N/A"

        # Reviews - BULLETPROOF FIX
        reviews = pd.to_numeric(lead.get("reviews"), errors='coerce')
        reviews = int(reviews) if pd.notna(reviews) else 0

        category = html_lib.escape(str(lead.get("category")) if pd.notna(lead.get("category")) else "N/A")
        phone = html_lib.escape(str(lead.get("phone")) if pd.notna(lead.get("phone")) else "N/A")
        address = html_lib.escape(str(lead.get("address")) if pd.notna(lead.get("address")) else "")

        email = lead.get("email")
        if pd.notna(email) and str(email).strip() and str(email).lower() != 'nan':
            email_safe = html_lib.escape(str(email))
            email_html = f'<a href="mailto:{email_safe}" style="color:#38bdf8;">{email_safe}</a>'
        else:
            email_html = '<span style="color:#71717a;">N/A</span>'

        website = lead.get("website")
        has_website = pd.notna(website) and str(website).strip()
        report = lead.get("website_report") or {}
        issues = report.get("issues") if isinstance(report, dict) else None
        if issues:
            issues_html = "".join(
                f'<li style="font-size:12px;color:#fbbf24;">⚠ {html_lib.escape(str(i))}</li>' for i in issues
            )
        else:
            issues_html = '<li style="font-size:12px;color:#71717a;">None</li>'

        if has_website:
            site_url = str(website) if str(website).startswith("http") else f"https://{website}"
            website_html = (
                f'<a href="{html_lib.escape(site_url)}" target="_blank" '
                f'rel="noopener noreferrer" style="color:#38bdf8;">{html_lib.escape(str(website))}</a>'
            )
        else:
            website_html = '<span style="color:#ef4444;font-weight:700;">NO WEBSITE</span>'

        maps_url_raw = lead.get("maps_url")
        maps_url = str(maps_url_raw) if pd.notna(maps_url_raw) else "#"
        maps_html = (
            f'<a href="{html_lib.escape(maps_url)}" target="_blank" '
            f'rel="noopener noreferrer" style="color:#a78bfa;text-decoration:none;">📍 Maps</a>'
        )

        rows_html.append(f"""
        <tr style="border-bottom:1px solid #27272a;">
          <td style="padding:10px;white-space:nowrap;">
            <div style="width:34px;height:34px;border-radius:50%;background:{color}22;
                        border:2px solid {color};display:flex;align-items:center;
                        justify-content:center;font-weight:700;color:{color};font-size:12px;">{score}</div>
          </td>
          <td style="padding:10px;min-width:160px;"><strong>{name}</strong><br>
            <small style="color:#a1a1aa;">{rating} ★ · {reviews} reviews</small></td>
          <td style="padding:10px;color:#d4d4d8;white-space:nowrap;">{category}</td>
          <td style="padding:10px;min-width:180px;color:#d4d4d8;">{phone}<br>
            <small style="color:#a1a1aa;">{address}</small></td>
          <td style="padding:10px;white-space:nowrap;">{email_html}</td>
          <td style="padding:10px;min-width:150px;word-break:break-all;">{website_html}</td>
          <td style="padding:10px;min-width:180px;"><ul style="margin:0;padding-left:16px;">{issues_html}</ul></td>
          <td style="padding:10px;white-space:nowrap;">{maps_html}</td>
        </tr>
        """)

    table_html = f"""
    <div style="overflow-x:auto;border:1px solid #27272a;border-radius:10px;">
    <table style="width:100%;border-collapse:collapse;min-width:950px;">
      <thead>
        <tr style="background:#18181b;text-align:left;">
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">SCORE</th>
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">BUSINESS</th>
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">CATEGORY</th>
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">CONTACT</th>
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">EMAIL</th>
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">WEBSITE</th>
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">ISSUES</th>
          <th style="padding:10px;color:#a1a1aa;font-size:12px;">ACTIONS</th>
        </tr>
      </thead>
      <tbody>{''.join(rows_html)}</tbody>
    </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

# ── Display Results ───────────────────────────────────────────────────
if st.session_state.leads_df is not None and not st.session_state.leads_df.empty:
    df = st.session_state.leads_df

    st.divider()

    hot = len(df[df['lead_score'] >= 80])
    warm = len(df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)])
    cold = len(df[df['lead_score'] < 50])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Leads", len(df))
    col2.metric("🔥 Hot", hot)
    col3.metric("🟠 Warm", warm)
    col4.metric("🟢 Low Priority", cold)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["All", "🔥 Hot", "🟠 Warm", "🟢 Low"])

    with tab1:
        render_leads_table(df)

    with tab2:
        render_leads_table(df[df['lead_score'] >= 80])

    with tab3:
        render_leads_table(df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)])

    with tab4:
        render_leads_table(df[df['lead_score'] < 50])

    st.divider()

    # Download CSV
    csv_df = df.drop(columns=["website_report"], errors="ignore")
    csv = csv_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"nextgen_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        width='stretch'
    )

# Footer
st.divider()
st.markdown(
    f"<p style='text-align: center; color: #71717a; font-size: 12px;'>"
    f"&copy; {datetime.now().year} NextGen Analytics. All rights reserved."
    f"</p>",
    unsafe_allow_html=True
)
