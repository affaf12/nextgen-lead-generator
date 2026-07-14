"""Streamlit version of NextGen Lead Generator - Flask code ko touch nahi kiya"""

import subprocess
import sys
import os

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

# Dark theme CSS - Flask app jaisa
st.markdown("""
<style>
    .stApp {
        background-color: #0f1117;
        color: #e4e4e7;
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
    max_results = st.number_input("Max Results", min_value=1, max_value=1000, value=20)

search_button = st.button("🔍 Search Leads", use_container_width=True)

# Session state for results
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None

if search_button:
    if not business_type or not location or not country:
        st.error("Business Type, Location, and Country are required")
    else:
        query = f"{business_type.strip()} in {location.strip()}, {country.strip()}"
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(current, total, msg):
            pct = int((current / total) * 100) if total > 0 else 0
            progress_bar.progress(pct)
            status_text.text(f"{current}/{total} — {msg}")
        
        try:
            with st.spinner("Scraping Google Maps..."):
                # Use tumhara existing scraper
                leads = scrape_google_maps(
                    query, 
                    max_results=max_results, 
                    progress_callback=progress_callback
                )
                
                for lead in leads:
                    lead["country"] = country
                
                status_text.text("Analyzing websites...")
                progress_bar.progress(0)
                
                # Use tumhara existing analyzer
                analyze_leads(leads, progress_callback=progress_callback)
                
                # Convert to DataFrame
                st.session_state.leads_df = pd.DataFrame(leads)
                progress_bar.progress(100)
                status_text.success(f"✅ Done! Found {len(leads)} leads")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.exception(e)

# Display Results
if st.session_state.leads_df is not None and not st.session_state.leads_df.empty:
    df = st.session_state.leads_df
    
    st.divider()
    
    # Stats Cards
    hot = len(df[df['lead_score'] >= 80])
    warm = len(df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)])
    cold = len(df[df['lead_score'] < 50])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Leads", len(df))
    col2.metric("🔥 Hot", hot)
    col3.metric("🟠 Warm", warm)
    col4.metric("🟢 Low Priority", cold)
    
    st.divider()
    
    # Filter tabs
    tab1, tab2, tab3, tab4 = st.tabs(["All", "🔥 Hot", "🟠 Warm", "🟢 Low"])
    
    with tab1:
        st.dataframe(
            df[['lead_score', 'name', 'category', 'phone', 'email', 'website', 'rating', 'reviews']],
            use_container_width=True,
            hide_index=True
        )
    
    with tab2:
        hot_df = df[df['lead_score'] >= 80]
        st.dataframe(hot_df[['lead_score', 'name', 'phone', 'email', 'website']], use_container_width=True, hide_index=True)
    
    with tab3:
        warm_df = df[(df['lead_score'] >= 50) & (df['lead_score'] < 80)]
        st.dataframe(warm_df[['lead_score', 'name', 'phone', 'email', 'website']], use_container_width=True, hide_index=True)
    
    with tab4:
        cold_df = df[df['lead_score'] < 50]
        st.dataframe(cold_df[['lead_score', 'name', 'phone', 'email', 'website']], use_container_width=True, hide_index=True)
    
    # Download CSV - Fixed
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"nextgen_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

# Footer
st.divider()
st.markdown(
    f"<p style='text-align: center; color: #71717a; font-size: 12px;'>"
    f"&copy; {datetime.now().year} NextGen Analytics. All rights reserved."
    f"</p>", 
    unsafe_allow_html=True
)
