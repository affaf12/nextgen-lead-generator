"""
NextGen Analytics - FINAL MERGED Streamlit App
Triple System (Web + Marketing + Power BI + AI) + VIP 195 Countries + Dark Theme
Kuch bhi deleted nahi - sab kuch merged
"""

import subprocess
import sys
import os
import html as html_lib

# Playwright browser install on Streamlit Cloud - sabse pehle (Purane wale se)
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

import streamlit as st
import pandas as pd
import config
from scraper_pw import scrape_google_maps
from analyzer import analyze_leads
from datetime import datetime
import io

st.set_page_config(
    page_title="NextGen Analytics - Triple Lead Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dark theme CSS — Purane wale se + Naye wale ka badge ─────────────────
st.markdown("""
<style>
    .stApp {
        background-color: #0f1117;
        color: #e4e4e7;
    }
    .main-header {
        background: linear-gradient(135deg, #6c63ff, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 32px;
        font-weight: 800;
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        background: linear-gradient(135deg, #6c63ff, #00d2ff);
        color: white;
        margin-left: 10px;
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
    .stTextInput input, .stNumberInput input {
        background-color: #18181b !important;
        color: #e4e4e7 !important;
        border: 1px solid #3f3f46 !important;
    }
    .stSelectbox > div > div {
        background-color: #18181b !important;
        color: #e4e4e7 !important;
        border: 1px solid #3f3f46 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        border-radius: 10px !important;
        padding: 16px 18px !important;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricLabel"] * {
        color: #d4d4d8 !important;
        opacity: 1 !important;
    }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] div {
        color: #f4f4f5 !important;
        opacity: 1 !important;
    }
    .stTabs [data-baseweb="tab"] { color: #a1a1aa; }
    .stTabs [aria-selected="true"] { color: #e4e4e7 !important; }
    .ngtable td, .ngtable th { color: #d4d4d8; }
    .ngtable a { color: #38bdf8; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🎯 NextGen Analytics <span class="badge">TRIPLE SYSTEM</span></h1>', unsafe_allow_html=True)
st.markdown("**Find Web Dev + Marketing + Power BI / Fabric clients on Google Maps** - Business Type tum apne hisaab se change karte raho")

# ── Sidebar — Lead Type Dropdown (Naye wale se) ──
st.sidebar.header("🎯 Lead Type (Dropdown)")

lead_type_options = getattr(config, 'LEAD_TYPE_OPTIONS', [
    {"value": "all", "label": "🌟 All - Web + Marketing + Power BI + AI", "desc": "Finds all opportunities"},
    {"value": "web", "label": "💻 Web Development Clients", "desc": "No/bad websites"},
    {"value": "marketing", "label": "📢 Marketing Clients", "desc": "Low rating, few reviews"},
    {"value": "powerbi", "label": "📊 Power BI / Fabric Clients", "desc": "High reviews, data-heavy - HIGH TICKET"},
    {"value": "ai", "label": "🤖 AI & Automation Clients", "desc": "High volume, needs AI bot"},
])

lead_type_labels = [opt["label"] for opt in lead_type_options]
lead_type_values = [opt["value"] for opt in lead_type_options]

selected_label = st.sidebar.selectbox(
    "Select Client Type",
    lead_type_labels,
    index=0,
    help="Web = No website, Marketing = Low rating, Power BI = High reviews, AI = Booking businesses"
)

selected_lead_type = lead_type_values[lead_type_labels.index(selected_label)]
selected_desc = [opt for opt in lead_type_options if opt["value"] == selected_lead_type][0].get("desc", "")
st.sidebar.info(f"ℹ️ {selected_desc}")

st.sidebar.divider()
st.sidebar.header("🔍 Search Settings")

business_type = st.sidebar.text_input(
    "Business Type (Tum change karte raho)",
    placeholder="e.g. Real Estate, Dentists, Restaurants, Car Dealers",
    help="You can type anything - Real Estate, Clinics, Gyms, etc.",
    value="Gym"
)

location = st.sidebar.text_input(
    "Location",
    placeholder="e.g. Karachi, Dubai, Miami",
    value="Karachi"
)

countries = getattr(config, 'COUNTRY_OPTIONS', getattr(config, 'COUNTRIES', ["Pakistan", "United States", "United Kingdom", "India"]))
default_idx = countries.index("Pakistan") if "Pakistan" in countries else 0
country = st.sidebar.selectbox("Country", countries, index=default_idx)

max_results = st.sidebar.slider("Max Results", 1, 100, 20)

st.sidebar.divider()
search_button = st.sidebar.button("🔍 Find Leads", type="primary", use_container_width=True)

# Info box (Naye wale se)
st.info(f"💡 **Current Mode:** {selected_label} | **Business:** {business_type or 'Not set'} | **Location:** {location}, {country} | Business Type tum apne hisaab se change kar sakte ho")

# Session state for results (Purane wale se)
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None
if 'leads_raw' not in st.session_state:
    st.session_state.leads_raw = None

# ── Search Logic ──
if search_button:
    if not business_type or not location or not country:
        st.error("Business Type, Location, and Country are required")
        st.stop()
    
    query = f"{business_type.strip()} in {location.strip()}, {country.strip()}"
    st.write(f"### 🔍 Searching: {query} | Mode: {selected_label}")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def on_scrape_progress(current, total, msg):
        pct = int((current / total * 50) if total > 0 else 0)
        progress_bar.progress(pct)
        status_text.text(f"[Scraping] {current}/{total} - {msg}")
    
    def on_analyze_progress(current, total, msg):
        pct = 50 + int((current / total * 50) if total > 0 else 0)
        progress_bar.progress(min(pct, 100))
        status_text.text(f"[Analyzing {selected_lead_type}] {current}/{total} - {msg}")
    
    try:
        status_text.text("Starting Google Maps scraping...")
        leads = scrape_google_maps(
            query,
            max_results=max_results,
            progress_callback=on_scrape_progress
        )

        if not leads:
            st.warning("No leads found. Try different business type or location.")
            st.stop()

        for lead in leads:
            lead["country"] = country
            lead["lead_type"] = selected_lead_type

        status_text.text(f"Analyzing {len(leads)} leads for {selected_lead_type} opportunities...")
        progress_bar.progress(0)

        analyze_leads(leads, lead_type=selected_lead_type, progress_callback=on_analyze_progress)

        # Save to session
        st.session_state.leads_df = pd.DataFrame(leads)
        st.session_state.leads_raw = leads
        
        progress_bar.progress(100)
        status_text.success(f"✅ Done! Found {len(leads)} leads ({sum(1 for l in leads if l.get('is_hot_opportunity'))} hot)")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)


# ── Custom HTML table renderer (Purane wale se - preserved) ────────────
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
            email_html = f'<a href="mailto:{email_safe}" style="color:#38bdf8;">{email_safe}</a>'
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
            issues_html = "".join(f'<li style="font-size:11px;color:#fbbf24;">⚠ {html_lib.escape(str(i))}</li>' for i in all_issues[:5])
        else:
            issues_html = '<li style="font-size:11px;color:#71717a;">None</li>'

        if has_website:
            site_url = str(website) if str(website).startswith("http") else f"https://{website}"
            site_url_safe = html_lib.escape(site_url)
            site_text_safe = html_lib.escape(str(website))
            website_html = f'<a href="{site_url_safe}" target="_blank" rel="noopener noreferrer" style="color:#38bdf8;">{site_text_safe}</a>'
        else:
            website_html = '<span style="color:#ef4444;font-weight:700;">NO WEBSITE</span>'

        maps_url_raw = lead.get("maps_url")
        maps_url = html_lib.escape(str(maps_url_raw)) if pd.notna(maps_url_raw) else "#"
        maps_html = f'<a href="{maps_url}" target="_blank" rel="noopener noreferrer" style="color:#a78bfa;text-decoration:none;">📍 Maps</a>'

        score_badge = f'<div style="width:30px;height:30px;border-radius:50%;background:{color}22;border:2px solid {color};display:flex;align-items:center;justify-content:center;font-weight:700;color:{color};font-size:11px;">{score}</div>'
        type_badge_color = "#00d2ff" if "POWER BI" in opportunity_label else "#a78bfa" if "WEB" in opportunity_label else "#fb923c" if "MARKETING" in opportunity_label else "#22c55e"
        type_badge = f'<div style="font-size:9px;color:{type_badge_color};font-weight:700;margin-top:4px;">{opportunity_label}</div>' if opportunity_label else ''

        cellstyle = 'padding:8px;word-wrap:break-word;overflow-wrap:break-word;vertical-align:top;font-size:13px;'

        row = "<tr style=\"border-bottom:1px solid #27272a;\">"
        row += f'<td style="{cellstyle}">{score_badge}{type_badge}</td>'
        row += f'<td style="{cellstyle}color:#e4e4e7;"><strong style="color:#f4f4f5;">{name}</strong><br><small style="color:#a1a1aa;">{rating} ★ · {reviews} reviews</small></td>'
        row += f'<td style="{cellstyle}color:#d4d4d8;">{category}</td>'
        row += f'<td style="{cellstyle}color:#d4d4d8;">{phone}</td>'
        row += f'<td style="{cellstyle}color:#a1a1aa;">{address}</td>'
        row += f'<td style="{cellstyle}">{email_html}</td>'
        row += f'<td style="{cellstyle}">{website_html}</td>'
        row += f'<td style="{cellstyle}"><ul style="margin:0;padding-left:14px;">{issues_html}</ul></td>'
        row += f'<td style="{cellstyle}">{maps_html}</td>'
        row += "</tr>"
        rows_html.append(row)

    header = '<tr style="background:#18181b;text-align:left;"><th style="padding:8px;color:#a1a1aa;font-size:11px;">SCORE+TYPE</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">BUSINESS</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">CATEGORY</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">PHONE</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">ADDRESS</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">EMAIL</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">WEBSITE</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">OPPORTUNITY</th><th style="padding:8px;color:#a1a1aa;font-size:11px;">ACTIONS</th></tr>'

    table_html = '<div class="ngtable" style="overflow-x:auto;border:1px solid #27272a;border-radius:10px;">'
    table_html += '<table style="width:100%;table-layout:fixed;border-collapse:collapse;color:#d4d4d8;">'
    table_html += '<colgroup><col style="width:7%"><col style="width:14%"><col style="width:10%"><col style="width:10%"><col style="width:16%"><col style="width:11%"><col style="width:11%"><col style="width:15%"><col style="width:6%"></colgroup>'
    table_html += f'<thead>{header}</thead><tbody>{"".join(rows_html)}</tbody></table></div>'

    st.markdown(table_html, unsafe_allow_html=True)


# ── Display Results ───────────────────────────────────────────────────
if st.session_state.leads_df is not None and not st.session_state.leads_df.empty:
    df = st.session_state.leads_df
    leads_raw = st.session_state.leads_raw or []

    st.divider()

    # Metrics - Merged from both versions
    hot = len(df[df['lead_score'] >= 80]) if 'lead_score' in df.columns else 0
    warm = len(df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)]) if 'lead_score' in df.columns else 0
    cold = len(df[df['lead_score'] < 50]) if 'lead_score' in df.columns else 0
    powerbi_hot = sum(1 for l in leads_raw if 'POWER BI' in (l.get('opportunity_label') or '') or l.get('powerbi_opportunity'))
    is_hot_count = sum(1 for l in leads_raw if l.get('is_hot_opportunity'))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Leads", len(df))
    col2.metric("🔥 Hot", hot)
    col3.metric("🟠 Warm", warm)
    col4.metric("📊 Power BI Hot", powerbi_hot)
    col5.metric("💎 All Hot", is_hot_count)

    st.divider()

    # Tabs - Merged: Purane wale + Naye wale
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🌟 All", "🔥 Hot", "🟠 Warm", "🟢 Low", "💻 Web", "📢 Marketing", "📊 Power BI"])

    with tab1:
        st.subheader(f"All Leads ({len(df)}) - {selected_label}")
        render_leads_table(df)

    with tab2:
        hot_df = df[df['lead_score'] >= 80] if 'lead_score' in df.columns else pd.DataFrame()
        st.subheader(f"Hot Leads ({len(hot_df)})")
        render_leads_table(hot_df)

    with tab3:
        warm_df = df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)] if 'lead_score' in df.columns else pd.DataFrame()
        st.subheader(f"Warm Leads ({len(warm_df)})")
        render_leads_table(warm_df)

    with tab4:
        low_df = df[df['lead_score'] < 50] if 'lead_score' in df.columns else pd.DataFrame()
        st.subheader(f"Low Priority ({len(low_df)})")
        render_leads_table(low_df)

    with tab5:
        web_df = df[df['opportunity_label'].astype(str).str.contains('WEB', na=False)] if 'opportunity_label' in df.columns else pd.DataFrame()
        st.subheader(f"💻 Web Development Clients ({len(web_df)})")
        render_leads_table(web_df)

    with tab6:
        mkt_df = df[df['opportunity_label'].astype(str).str.contains('MARKETING', na=False)] if 'opportunity_label' in df.columns else pd.DataFrame()
        st.subheader(f"📢 Marketing Clients ({len(mkt_df)})")
        render_leads_table(mkt_df)

    with tab7:
        pb_df = df[df['opportunity_label'].astype(str).str.contains('POWER BI', na=False)] if 'opportunity_label' in df.columns else pd.DataFrame()
        if pb_df.empty:
            # Fallback check powerbi_opportunity
            pb_df = df[df.apply(lambda x: x.get('powerbi_opportunity', False) if isinstance(x, dict) else False, axis=1)] if not df.empty else pd.DataFrame()
        st.subheader(f"📊 Power BI / Fabric Clients - HIGH TICKET ({len(pb_df)})")
        render_leads_table(pb_df)

    st.divider()

    # Detailed cards (Naye wale se - preserved)
    st.subheader("📋 Detailed Lead Cards (Top 10)")
    for lead in leads_raw[:10]:
        report = lead.get('website_report', {}) if isinstance(lead, dict) else {}
        with st.expander(f"{lead.get('name','N/A')} — Score: {lead.get('lead_score',0)} — {lead.get('opportunity_label','')} — {lead.get('rating','')}★"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Category:** {lead.get('category','N/A')}")
                st.write(f"**Rating:** {lead.get('rating','')} ★ ({lead.get('reviews',0)} reviews)")
                st.write(f"**Phone:** {lead.get('phone','N/A')}")
                st.write(f"**Email:** {lead.get('email','N/A')}")
                st.write(f"**Address:** {lead.get('address','')}")
            with c2:
                st.write(f"**Website:** {lead.get('website','NO WEBSITE')}")
                st.write(f"**Tech:** {', '.join(report.get('tech_signals',[])) if isinstance(report, dict) else ''}")
                st.write(f"**Country:** {lead.get('country','')}")
                st.write(f"**Lead Type:** {lead.get('lead_type','')}")
            st.write("**Opportunities:**")
            all_issues = []
            if isinstance(report, dict):
                all_issues.extend(report.get('issues', []))
            if lead.get('extra_issues'):
                all_issues.extend(lead.get('extra_issues', []))
            for issue in all_issues:
                st.write(f"- {issue}")

    st.divider()

    # Download CSV (Purane wale se - preserved + Naye wale ka)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_df = df.drop(columns=["website_report"], errors="ignore")
        csv = csv_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download All Leads CSV",
            data=csv,
            file_name=f"nextgen_{selected_lead_type}_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_dl2:
        # Also provide filtered download info
        st.info(f"💡 Tip: Use tabs to filter - All, Hot, Web, Marketing, Power BI - then download")

else:
    # Welcome screen (Naye wale se)
    if st.session_state.leads_df is None:
        st.markdown("""
        ### 👋 How to use this Triple System:
        
        1. **Sidebar me Lead Type select karo** (Dropdown):
           - 🌟 All = Sab kuch milega (Web + Marketing + Power BI + AI)
           - 💻 Web Development = Jinka website nahi hai ya kharab hai
           - 📢 Marketing = Low rating / Kam reviews wale
           - 📊 Power BI / Fabric = High reviews, Real Estate, Car Dealers - HIGH TICKET $950+
           - 🤖 AI & Automation = Booking wale (Restaurant, Clinic, Hotel)
        
        2. **Business Type likho** - Tum roz change kar sakte ho:
           - Real Estate, Dentists, Restaurants, Gyms, Clinics, Car Dealers, Hotels
        
        3. **Location + Country** select karo (195 countries available)
        
        4. **Find Leads** dabao - 1-2 minute me leads ayenge
        
        ---
        **Example for Power BI:** Lead Type: 📊 Power BI, Business Type: Real Estate Agencies, Location: Dubai
        """)
        
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Lead Types", "5 Types", "Web, Mkt, Power BI, AI, All")
        with col2:
            st.metric("Countries", "195", "All UN countries")
        with col3:
            st.metric("Business Types", "Unlimited", "You type anything")

# Footer (Purane wale se)
st.divider()
st.markdown(
    f"<p style='text-align: center; color: #71717a; font-size: 12px;'>"
    f"&copy; {datetime.now().year} NextGen Analytics — Triple System | Web + Marketing + Power BI + AI | All rights reserved."
    f"</p>",
    unsafe_allow_html=True
)
