"""
NextGen Analytics - PREMIUM Frontend | Old Flask Style + Stop Button
Triple System: Web + Marketing + Power BI / Fabric + AI
"""

import streamlit as st
import pandas as pd
import config
from scraper_pw import scrape_google_maps
from analyzer import analyze_leads
from datetime import datetime
import io
import html as html_lib

st.set_page_config(
    page_title="NextGen Analytics — Triple Lead Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── PREMIUM DARK THEME — Exactly like old Flask dashboard ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: #0f1117;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit default menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 20px;
    }
    
    /* Header */
    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 32px;
        flex-wrap: wrap;
        gap: 16px;
        padding: 24px 0 0 0;
    }
    .header h1 {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(135deg, #6c63ff, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header p {
        color: #71717a;
        font-size: 14px;
        margin-top: 6px;
        line-height: 1.5;
    }
    .badge-premium {
        display: inline-block;
        background: linear-gradient(135deg, #6c63ff, #00d2ff);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        margin-left: 10px;
        vertical-align: middle;
        letter-spacing: 0.5px;
    }
    
    /* Search Panel - Like old Flask */
    .search-panel {
        background: #1a1d27;
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    /* Info box */
    .info-box {
        background: rgba(108,99,255,0.08);
        border: 1px solid #27272a;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 13px;
        color: #a1a1aa;
    }
    .info-box strong {
        color: #e4e4e7;
    }
    
    /* Stats cards */
    .stats-row {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
        flex-wrap: wrap;
    }
    .stat-card {
        background: #1a1d27;
        border: 1px solid #27272a;
        border-radius: 10px;
        padding: 16px 24px;
        flex: 1;
        min-width: 150px;
    }
    .stat-card .num {
        font-size: 28px;
        font-weight: 700;
        color: #e4e4e7;
    }
    .stat-card.hot .num { color: #ef4444; }
    .stat-card.warm .num { color: #f97316; }
    .stat-card.cold .num { color: #22c55e; }
    .stat-card .label {
        font-size: 12px;
        color: #71717a;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 11px 24px !important;
        transition: all 0.2s !important;
        border: none !important;
    }
    .btn-primary button {
        background: linear-gradient(135deg, #6c63ff, #00d2ff) !important;
        color: white !important;
    }
    .btn-primary button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    .btn-stop button {
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        color: white !important;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
        70% { box-shadow: 0 0 0 10px rgba(239,68,68,0); }
        100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
    }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox > div > div {
        background-color: #0f1117 !important;
        color: #e4e4e7 !important;
        border: 1px solid #27272a !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
    .stTextInput input:focus, .stSelectbox > div > div:focus-within {
        border-color: #6c63ff !important;
    }
    .stSelectbox label, .stTextInput label, .stSlider label, .stNumberInput label {
        color: #71717a !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Progress bar - Flask style */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6c63ff, #00d2ff) !important;
        border-radius: 8px !important;
    }
    .stProgress > div {
        background: #27272a !important;
        border-radius: 8px !important;
        height: 8px !important;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background: #1a1d27 !important;
        border: 1px solid #27272a !important;
        border-radius: 10px !important;
        padding: 16px 24px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #71717a !important;
        font-size: 12px !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #e4e4e7 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    /* Table */
    .ngtable {
        background: #1a1d27;
        border: 1px solid #27272a;
        border-radius: 12px;
        overflow: hidden;
    }
    .ngtable th {
        background: #1a1d27;
        color: #71717a;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 16px;
        border-bottom: 1px solid #27272a;
    }
    .ngtable td {
        padding: 12px 16px;
        font-size: 13px;
        border-bottom: 1px solid #27272a;
        vertical-align: top;
    }
    .ngtable tr:hover {
        background: rgba(108,99,255,0.05);
    }
    .ngtable a { color: #00d2ff; text-decoration: none; }
    .ngtable a:hover { text-decoration: underline; }
    
    /* Filter tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #1a1d27;
        border: 1px solid #27272a;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #71717a;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        padding: 6px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #6c63ff !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Session states
if 'is_searching' not in st.session_state:
    st.session_state.is_searching = False
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None
if 'leads_raw' not in st.session_state:
    st.session_state.leads_raw = None

# ── HEADER — Like old Flask ──
st.markdown("""
<div class="header">
    <div>
        <h1>🎯 NextGen Analytics <span class="badge-premium">TRIPLE SYSTEM</span></h1>
        <p>AI-Powered Google Maps Scraping — Find businesses that need <strong>Web Development</strong> + <strong>Marketing</strong> + <strong>Power BI / Fabric Dashboards</strong><br>
        Auto-detects: Missing websites, 100+ reviews with no data system, high-volume businesses needing automation</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    💡 <strong>How this works for Agency:</strong> This tool finds 3 types of hot leads — (1) No/bad website = Web Dev client, (2) Low rating = Marketing client, (3) 100+ reviews / High traffic but no dashboard = Power BI client. Business Type tum apne hisaab se change kar sakte ho!
</div>
""", unsafe_allow_html=True)

# ── SEARCH PANEL — Like old Flask dashboard ──
st.markdown('<div class="search-panel">', unsafe_allow_html=True)

# Lead Type Dropdown + Business Type in same row like Flask
col_lead, col_biz, col_loc, col_country, col_max = st.columns([1.2, 1.5, 1, 1, 0.5])

with col_lead:
    lead_type_options = getattr(config, 'LEAD_TYPE_OPTIONS', [
        {"value": "all", "label": "🌟 All — Web + Mkt + Power BI", "desc": "Finds all opportunities"},
        {"value": "web", "label": "💻 Web Development", "desc": "No/bad websites"},
        {"value": "marketing", "label": "📢 Marketing", "desc": "Low rating, few reviews"},
        {"value": "powerbi", "label": "📊 Power BI / Fabric", "desc": "High reviews, data-heavy - HIGH TICKET"},
        {"value": "ai", "label": "🤖 AI & Automation", "desc": "High volume, needs AI bot"},
    ])
    lead_type_labels = [opt["label"] for opt in lead_type_options]
    lead_type_values = [opt["value"] for opt in lead_type_options]
    
    selected_label = st.selectbox(
        "🎯 LEAD TYPE (DROPDOWN)",
        lead_type_labels,
        index=0,
        help="Web = No website, Marketing = Low rating, Power BI = High reviews"
    )
    selected_lead_type = lead_type_values[lead_type_labels.index(selected_label)]
    selected_desc = [opt for opt in lead_type_options if opt["value"] == selected_lead_type][0].get("desc", "")

with col_biz:
    business_type = st.text_input(
        "BUSINESS TYPE (TUM CHANGE KARTE RAHO)",
        placeholder="e.g. Real Estate, Dentists, Restaurants",
        help="You can type anything"
    )

with col_loc:
    location = st.text_input(
        "LOCATION",
        placeholder="e.g. Karachi, Dubai",
        value="Karachi"
    )

with col_country:
    countries = getattr(config, 'COUNTRY_OPTIONS', getattr(config, 'COUNTRIES', ["Pakistan", "United States", "United Kingdom"]))
    default_idx = countries.index("Pakistan") if "Pakistan" in countries else 0
    country = st.selectbox("COUNTRY", countries, index=default_idx)

with col_max:
    max_results = st.number_input("MAX", min_value=1, max_value=1000, value=20)

# Second row for description + buttons
col_desc, col_btn1, col_btn2 = st.columns([3, 1, 1])

with col_desc:
    st.markdown(f"<small style='color:#71717a'>ℹ️ {selected_desc} | Current: <strong style='color:#e4e4e7'>{selected_label}</strong> | {business_type or 'Enter business type'} in {location}, {country}</small>", unsafe_allow_html=True)

with col_btn1:
    # Find / Stop button logic
    if not st.session_state.is_searching:
        search_btn = st.button("🔍 Find Leads", type="primary", use_container_width=True)
        stop_btn = False
        st.markdown('<div class="btn-primary"></div>', unsafe_allow_html=True)
    else:
        search_btn = False
        stop_btn = st.button("⏹️ Stop", type="secondary", use_container_width=True)
        st.markdown('<div class="btn-stop"></div>', unsafe_allow_html=True)
        if stop_btn:
            st.session_state.stop_requested = True
            st.session_state.is_searching = False
            st.warning("🛑 Stopping... Please wait")
            st.rerun()

with col_btn2:
    if st.session_state.leads_df is not None and not st.session_state.leads_df.empty:
        csv_df = st.session_state.leads_df.drop(columns=["website_report"], errors="ignore")
        csv = csv_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export CSV",
            data=csv,
            file_name=f"nextgen_{selected_lead_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# ── Custom HTML table renderer — Old Flask style ──
def _score_color(score):
    if score >= 80:
        return "#ef4444"
    if score >= 50:
        return "#f97316"
    return "#22c55e"

def render_leads_table(df):
    if df.empty:
        st.info("No leads in this category.")
        return

    rows_html = []
    for _, lead in df.iterrows():
        raw_score = lead.get("lead_score")
        score = int(raw_score) if pd.notna(raw_score) else 0
        color = _score_color(score)

        name = html_lib.escape(str(lead.get("name")) if pd.notna(lead.get("name")) else "N/A")
        rating = html_lib.escape(str(lead.get("rating")) if pd.notna(lead.get("rating")) else "N/A")
        reviews = html_lib.escape(str(lead.get("reviews")) if pd.notna(lead.get("reviews")) else "0")
        category = html_lib.escape(str(lead.get("category")) if pd.notna(lead.get("category")) else "N/A")
        phone = html_lib.escape(str(lead.get("phone")) if pd.notna(lead.get("phone")) else "N/A")
        address = html_lib.escape(str(lead.get("address")) if pd.notna(lead.get("address")) else "")
        opportunity_label = html_lib.escape(str(lead.get("opportunity_label")) if pd.notna(lead.get("opportunity_label")) else "")

        email = lead.get("email")
        if pd.notna(email) and str(email).strip():
            email_safe = html_lib.escape(str(email))
            email_html = f'<a href="mailto:{email_safe}">{email_safe}</a>'
        else:
            email_html = '<span style="color:#71717a;">N/A</span>'

        website = lead.get("website")
        has_website = pd.notna(website) and str(website).strip()
        report = lead.get("website_report")
        issues = report.get("issues") if isinstance(report, dict) else None
        extra_issues = lead.get("extra_issues") if isinstance(lead.get("extra_issues"), list) else []
        
        all_issues = []
        if issues:
            all_issues.extend(issues)
        if extra_issues:
            all_issues.extend(extra_issues)
        
        if all_issues:
            issues_html = "".join(f'<li style="font-size:11px;color:#eab308;">⚠ {html_lib.escape(str(i)[:80])}</li>' for i in all_issues[:4])
        else:
            issues_html = '<li style="font-size:11px;color:#71717a;">None</li>'

        if has_website:
            site_url = str(website) if str(website).startswith("http") else f"https://{website}"
            site_url_safe = html_lib.escape(site_url)
            site_text_safe = html_lib.escape(str(website)[:25])
            website_html = f'<a href="{site_url_safe}" target="_blank">{site_text_safe}</a>'
        else:
            website_html = '<span style="color:#ef4444;font-weight:700;font-size:11px;">NO WEBSITE</span>'

        maps_url_raw = lead.get("maps_url")
        maps_url = html_lib.escape(str(maps_url_raw)) if pd.notna(maps_url_raw) else "#")
        maps_html = f'<a href="{maps_url}" target="_blank">📍 Maps</a>'

        score_badge = f'<span style="display:inline-block;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:700;background:{color}22;color:{color};border:1px solid {color}44;">{score} {"🔥" if score>=80 else ""}</span>'
        type_badge_color = "#00d2ff" if "POWER BI" in opportunity_label else "#a5a3ff" if "WEB" in opportunity_label else "#f97316" if "MARKETING" in opportunity_label else "#22c55e"
        type_badge = f'<div style="font-size:9px;color:{type_badge_color};font-weight:700;margin-top:4px;background:{type_badge_color}15;padding:2px 6px;border-radius:10px;display:inline-block;">{opportunity_label}</div>' if opportunity_label else ''

        cellstyle = 'padding:12px 16px;word-wrap:break-word;overflow-wrap:break-word;vertical-align:top;font-size:13px;border-bottom:1px solid #27272a;'

        row = f"<tr>"
        row += f'<td style="{cellstyle}">{score_badge}<br>{type_badge}</td>'
        row += f'<td style="{cellstyle}"><strong style="color:#f4f4f5;">{name}</strong><br><small style="color:#71717a;">{rating} ★ · {reviews} reviews</small></td>'
        row += f'<td style="{cellstyle}color:#d4d4d8;">{category}</td>'
        row += f'<td style="{cellstyle}color:#d4d4d8;">{phone}<br><small style="color:#71717a;">{address[:40]}</small></td>'
        row += f'<td style="{cellstyle}">{email_html}</td>'
        row += f'<td style="{cellstyle}">{website_html}</td>'
        row += f'<td style="{cellstyle}"><ul style="margin:0;padding-left:14px;list-style:none;">{issues_html}</ul></td>'
        row += f'<td style="{cellstyle}">{maps_html}</td>'
        row += "</tr>"
        rows_html.append(row)

    header = '<tr><th style="padding:12px 16px;color:#71717a;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #27272a;">SCORE+TYPE</th><th style="padding:12px 16px;color:#71717a;font-size:11px;">BUSINESS</th><th style="padding:12px 16px;color:#71717a;font-size:11px;">CATEGORY</th><th style="padding:12px 16px;color:#71717a;font-size:11px;">CONTACT</th><th style="padding:12px 16px;color:#71717a;font-size:11px;">EMAIL</th><th style="padding:12px 16px;color:#71717a;font-size:11px;">WEBSITE</th><th style="padding:12px 16px;color:#71717a;font-size:11px;">OPPORTUNITY</th><th style="padding:12px 16px;color:#71717a;font-size:11px;">ACTIONS</th></tr>'

    table_html = '<div style="background:#1a1d27;border:1px solid #27272a;border-radius:12px;overflow:hidden;"><div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;min-width:1000px;">'
    table_html += f'<thead>{header}</thead><tbody>{"".join(rows_html)}</tbody></table></div></div>'

    st.markdown(table_html, unsafe_allow_html=True)

# ── Search Logic with Stop Button ──
if search_btn:
    if not business_type or not location:
        st.error("Business Type and Location are required")
        st.stop()
    
    st.session_state.is_searching = True
    st.session_state.stop_requested = False
    
    query = f"{business_type.strip()} in {location.strip()}, {country.strip()}"
    
    st.markdown(f"""
    <div style="background:#1a1d27;border:1px solid #27272a;border-radius:8px;padding:12px 16px;margin:16px 0;">
        <span style="color:#71717a;font-size:13px;">🔍 Searching:</span> <strong style="color:#e4e4e7;">{query}</strong> | 
        <span style="color:#71717a;">Mode:</span> <strong style="color:#00d2ff;">{selected_label}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    class StopException(Exception):
        pass
    
    def on_scrape_progress(current, total, msg):
        if st.session_state.stop_requested:
            raise StopException("Stopped by user")
        pct = int((current / total * 50) if total > 0 else 0)
        progress_bar.progress(pct)
        status_text.text(f"[Scraping] {current}/{total} — {msg}")
    
    def on_analyze_progress(current, total, msg):
        if st.session_state.stop_requested:
            raise StopException("Stopped by user")
        pct = 50 + int((current / total * 50) if total > 0 else 0)
        progress_bar.progress(min(pct, 100))
        status_text.text(f"[Analyzing {selected_lead_type}] {current}/{total} — {msg}")
    
    try:
        status_text.text("Starting Google Maps scraping...")
        leads = scrape_google_maps(
            query,
            max_results=max_results,
            progress_callback=on_scrape_progress
        )

        if st.session_state.stop_requested:
            raise StopException("Stopped")

        if not leads:
            st.warning("No leads found. Try different business type or location.")
            st.session_state.is_searching = False
            st.stop()

        for lead in leads:
            lead["country"] = country
            lead["lead_type"] = selected_lead_type

        status_text.text(f"Analyzing {len(leads)} leads for {selected_lead_type}...")
        progress_bar.progress(0)

        analyze_leads(leads, lead_type=selected_lead_type, progress_callback=on_analyze_progress)

        if st.session_state.stop_requested:
            raise StopException("Stopped")

        st.session_state.leads_df = pd.DataFrame(leads)
        st.session_state.leads_raw = leads
        
        progress_bar.progress(100)
        status_text.success(f"✅ Done! Found {len(leads)} leads ({sum(1 for l in leads if l.get('is_hot_opportunity'))} hot)")
        st.session_state.is_searching = False

    except StopException:
        st.warning("🛑 Search stopped by user")
        st.session_state.is_searching = False
        status_text.text("Stopped")
        progress_bar.progress(0)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)
        st.session_state.is_searching = False

# ── Display Results — Old Flask style ──
if st.session_state.leads_df is not None and not st.session_state.leads_df.empty:
    df = st.session_state.leads_df
    leads_raw = st.session_state.leads_raw or []

    st.markdown("<br>", unsafe_allow_html=True)

    # Stats Row — Like old Flask
    hot = len(df[df['lead_score'] >= 80]) if 'lead_score' in df.columns else 0
    warm = len(df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)]) if 'lead_score' in df.columns else 0
    cold = len(df[df['lead_score'] < 50]) if 'lead_score' in df.columns else 0
    powerbi_hot = sum(1 for l in leads_raw if 'POWER BI' in (l.get('opportunity_label') or '') or l.get('powerbi_opportunity'))
    is_hot_count = sum(1 for l in leads_raw if l.get('is_hot_opportunity'))

    # Custom stats cards like Flask
    st.markdown(f"""
    <div class="stats-row" style="display:flex;gap:16px;margin-bottom:24px;">
        <div class="stat-card" style="background:#1a1d27;border:1px solid #27272a;border-radius:10px;padding:16px 24px;flex:1;">
            <div class="num" style="font-size:28px;font-weight:700;color:#e4e4e7;">{len(df)} {f'<span style="font-size:14px;color:#00d2ff;">({powerbi_hot} 📊)</span>' if powerbi_hot>0 else ''}</div>
            <div class="label" style="font-size:12px;color:#71717a;margin-top:4px;">TOTAL LEADS</div>
        </div>
        <div class="stat-card hot" style="background:#1a1d27;border:1px solid #27272a;border-radius:10px;padding:16px 24px;flex:1;">
            <div class="num" style="font-size:28px;font-weight:700;color:#ef4444;">{hot}</div>
            <div class="label" style="font-size:12px;color:#71717a;margin-top:4px;">🔥 HOT (NO/BAD SITE + POWER BI)</div>
        </div>
        <div class="stat-card warm" style="background:#1a1d27;border:1px solid #27272a;border-radius:10px;padding:16px 24px;flex:1;">
            <div class="num" style="font-size:28px;font-weight:700;color:#f97316;">{warm}</div>
            <div class="label" style="font-size:12px;color:#71717a;margin-top:4px;">🟠 WARM (OUTDATED / DATA MESS)</div>
        </div>
        <div class="stat-card cold" style="background:#1a1d27;border:1px solid #27272a;border-radius:10px;padding:16px 24px;flex:1;">
            <div class="num" style="font-size:28px;font-weight:700;color:#22c55e;">{cold}</div>
            <div class="label" style="font-size:12px;color:#71717a;margin-top:4px;">🟢 LOW PRIORITY</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs — Old + New merged
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🌟 All", "🔥 Hot", "🟠 Warm", "💻 Web", "📢 Marketing", "📊 Power BI", "🤖 AI"])

    with tab1:
        st.markdown(f"#### Lead Results — {selected_label} ({len(df)})")
        render_leads_table(df)

    with tab2:
        hot_df = df[df['lead_score'] >= 80] if 'lead_score' in df.columns else pd.DataFrame()
        st.markdown(f"#### 🔥 Hot Leads ({len(hot_df)})")
        render_leads_table(hot_df)

    with tab3:
        warm_df = df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)] if 'lead_score' in df.columns else pd.DataFrame()
        st.markdown(f"#### 🟠 Warm Leads ({len(warm_df)})")
        render_leads_table(warm_df)

    with tab4:
        web_df = df[df['opportunity_label'].astype(str).str.contains('WEB', na=False)] if 'opportunity_label' in df.columns else pd.DataFrame()
        st.markdown(f"#### 💻 Web Development Clients ({len(web_df)})")
        render_leads_table(web_df)

    with tab5:
        mkt_df = df[df['opportunity_label'].astype(str).str.contains('MARKETING', na=False)] if 'opportunity_label' in df.columns else pd.DataFrame()
        st.markdown(f"#### 📢 Marketing Clients ({len(mkt_df)})")
        render_leads_table(mkt_df)

    with tab6:
        pb_df = df[df['opportunity_label'].astype(str).str.contains('POWER BI', na=False)] if 'opportunity_label' in df.columns else pd.DataFrame()
        st.markdown(f"#### 📊 Power BI / Fabric Clients — HIGH TICKET ({len(pb_df)})")
        render_leads_table(pb_df)

    with tab7:
        ai_df = df[df['opportunity_label'].astype(str).str.contains('AI', na=False)] if 'opportunity_label' in df.columns else pd.DataFrame()
        st.markdown(f"#### 🤖 AI & Automation Clients ({len(ai_df)})")
        render_leads_table(ai_df)

else:
    if st.session_state.leads_df is None and not st.session_state.is_searching:
        st.markdown("""
        <div style="background:#1a1d27;border:1px solid #27272a;border-radius:12px;padding:24px;text-align:center;margin-top:20px;">
            <h3 style="color:#e4e4e7;margin-bottom:12px;">👋 Welcome to Triple Lead System</h3>
            <p style="color:#a1a1aa;font-size:14px;line-height:1.6;">
            <strong style="color:#e4e4e7;">1. Lead Type select karo</strong> (Dropdown) — Web, Marketing, Power BI, AI, All<br>
            <strong style="color:#e4e4e7;">2. Business Type likho</strong> — Real Estate, Dentists, Restaurants, Gyms — Tum roz change kar sakte ho<br>
            <strong style="color:#e4e4e7;">3. Location + Country</strong> — 195 countries available<br>
            <strong style="color:#e4e4e7;">4. Find Leads dabao</strong> — 1-2 minute me leads ayenge | Stop button se kabhi bhi rok sakte ho
            </p>
            <div style="margin-top:16px;display:flex;gap:16px;justify-content:center;">
                <span style="background:#1a1d27;border:1px solid #27272a;padding:8px 16px;border-radius:8px;color:#a1a1aa;font-size:12px;">5 Lead Types</span>
                <span style="background:#1a1d27;border:1px solid #27272a;padding:8px 16px;border-radius:8px;color:#a1a1aa;font-size:12px;">195 Countries</span>
                <span style="background:#1a1d27;border:1px solid #27272a;padding:8px 16px;border-radius:8px;color:#a1a1aa;font-size:12px;">Unlimited Business Types</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown(
    f"<p style='text-align:center;padding:24px 0 8px;color:#71717a;font-size:12px;'>&copy; {datetime.now().year} NextGen Analytics — Triple Lead System | Old Premium Frontend Restored | Stop Button Added</p>",
    unsafe_allow_html=True
)
