# E-Commerce Intelligence Tool - MVP UI
# Version 2.0 - Multi-Company Support

import os
import sys
import streamlit as st
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scraper
try:
    from core.scraper import CompanyIntelligenceScraper
    SCRAPER_AVAILABLE = True
except Exception as e:
    SCRAPER_AVAILABLE = False
    SCRAPER_ERROR = str(e)

# Page config
st.set_page_config(
    page_title="E-Commerce Intelligence Tool",
    page_icon="🛒",
    layout="wide"
)

# Header
st.title("🛒 E-Commerce Intelligence Tool")
st.caption("AI-powered market intelligence for EU/DE E-Commerce")

# Sidebar
with st.sidebar:
    st.header("🔍 Company Analysis")
    
    company_name = st.text_input(
        "Company Name",
        placeholder="e.g., Coca-Cola, Zalando, Unilever",
        help="Enter any company name to analyze"
    )
    
    with st.expander("⚙️ Advanced Options"):
        lookback_days = st.slider("Lookback (days)", 7, 30, 14)
        max_per_source = st.slider("Max sources per type", 5, 20, 10)
        
        domain = st.text_input("Domain (optional)", placeholder="example.com")
        newsroom_url = st.text_input("Newsroom URL (optional)")
        linkedin_url = st.text_input("LinkedIn URL (optional)")
    
    analyze_btn = st.button(
        "🚀 Discover Sources",
        type="primary",
        disabled=not company_name,
        use_container_width=True
    )
    
    st.divider()
    
    st.info("""
    **🇪🇺 EU/DE Market Focus**
    
    This tool specializes in:
    • European markets (14 countries)
    • E-Commerce & Retail Media
    • Marketplaces (Amazon, Zalando)
    • D2C & Digital Commerce
    """)
    
    # Show model info
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    st.caption(f"🤖 Model: {model}")

# Main content
if not SCRAPER_AVAILABLE:
    st.error(f"""
    ❌ **Scraper not available**
    
    Error: {SCRAPER_ERROR}
    
    Please check that all dependencies are installed:
    ```
    pip install -r requirements.txt
    ```
    """)
    st.stop()

# Welcome screen
if not company_name:
    st.markdown("""
    ## 👋 Welcome!
    
    This tool helps you discover and analyze E-Commerce intelligence for any company.
    
    ### 🚀 How it works:
    
    1. **Enter a company name** in the sidebar
    2. **Click "Discover Sources"** to start
    3. **View discovered sources** from multiple channels
    
    ### 📊 What you get:
    
    - 📰 **Google News** (14 EU editions)
    - 💼 **LinkedIn** posts and updates
    - 🏢 **Company Newsroom** articles
    - 🛒 **E-Commerce** focused content
    
    ### 🔒 Privacy:
    
    - No data is stored without your consent
    - API calls are made via your OpenAI key
    - All sources are public information
    
    ---
    
    **👈 Enter a company name to get started!**
    """)
    
    # Show example companies
    st.subheader("💡 Try these examples:")
    cols = st.columns(4)
    example_companies = ["Coca-Cola", "Zalando", "Unilever", "LVMH"]
    for col, company in zip(cols, example_companies):
        if col.button(company, use_container_width=True):
            st.rerun()
    
    st.stop()

# Run analysis
if analyze_btn or "last_analysis" in st.session_state:
    
    # Build config
    config = {
        "lookback_days": lookback_days,
        "max_per_source": max_per_source
    }
    
    if domain:
        config["domain"] = domain
    if newsroom_url:
        config["newsroom_url"] = newsroom_url
    if linkedin_url:
        config["linkedin_url"] = linkedin_url
    
    # Store in session
    if analyze_btn:
        st.session_state["last_analysis"] = {
            "company": company_name,
            "config": config,
            "timestamp": datetime.now()
        }
    
    # Get from session
    analysis = st.session_state.get("last_analysis")
    if not analysis:
        st.stop()
    
    company_name = analysis["company"]
    config = analysis["config"]
    
    st.header(f"📊 Analysis: {company_name}")
    
    # Progress
    with st.spinner("🔍 Discovering sources..."):
        try:
            scraper = CompanyIntelligenceScraper(company_name, config)
            sources = scraper.discover_all_sources()
            stats = scraper.get_stats()
        except Exception as e:
            st.error(f"""
            ❌ **Discovery failed**
            
            Error: {e}
            
            Please try again or adjust your settings.
            """)
    st.stop()

    # Success
    st.success(f"✅ Discovered {len(sources)} sources!")
    
    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Sources", len(sources))
    
    with col2:
        eu_count = sum(1 for s in sources if "gnews:de:" in s.get("source", "") or "gnews:at:" in s.get("source", ""))
        st.metric("EU Sources", eu_count)
    
    with col3:
        st.metric("Google News", stats.get("google_news", 0))
    
    with col4:
        st.metric("LinkedIn", stats.get("linkedin", 0))
    
    with col5:
        st.metric("Newsroom", stats.get("newsroom", 0))
    
    # Errors
    if stats.get("errors"):
        with st.expander(f"⚠️ Warnings ({len(stats['errors'])})"):
            for err in stats["errors"]:
                st.warning(err)
    
    st.divider()

    # Sources table
    st.subheader("📚 Discovered Sources")
    
    if sources:
        # Filters
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search = st.text_input("🔍 Search", placeholder="Search in titles or URLs...")
        
        with col2:
            source_filter = st.multiselect(
                "Filter by type",
                options=list(set(s.get("source", "unknown") for s in sources)),
                default=[]
            )
        
        # Apply filters
        filtered = sources
        
        if search:
            search_lower = search.lower()
            filtered = [
                s for s in filtered
                if search_lower in s.get("title", "").lower() or search_lower in s.get("url", "").lower()
            ]
        
        if source_filter:
            filtered = [s for s in filtered if s.get("source") in source_filter]
        
        st.caption(f"Showing {len(filtered)} of {len(sources)} sources")
        
        # Display sources
        for i, source in enumerate(filtered, 1):
            with st.expander(f"{i}. {source.get('title', 'Untitled')}"):
                st.markdown(f"**URL:** {source.get('url', 'N/A')}")
                st.markdown(f"**Source:** `{source.get('source', 'unknown')}`")
                
                if source.get('published_at'):
                    st.markdown(f"**Published:** {source['published_at']}")
                
                st.link_button("Open Source", source.get('url', '#'))
        
        # Export
st.divider()

        import json
        sources_json = json.dumps(filtered, indent=2, ensure_ascii=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "📥 Download as JSON",
                sources_json.encode('utf-8'),
                f"{company_name}_sources.json",
                "application/json",
                use_container_width=True
            )
        
        with col2:
            # Simple CSV
            csv_lines = ["Title,URL,Source,Published\n"]
            for s in filtered:
                title = s.get('title', '').replace(',', ';')
                url = s.get('url', '')
                source = s.get('source', '')
                published = s.get('published_at', '')
                csv_lines.append(f'"{title}","{url}","{source}","{published}"\n')
            csv_data = ''.join(csv_lines)
            
            st.download_button(
                "📥 Download as CSV",
                csv_data.encode('utf-8'),
                f"{company_name}_sources.csv",
                "text/csv",
                use_container_width=True
            )
    else:
        st.info("No sources found. Try adjusting your filters or lookback period.")

# Footer
st.divider()
st.caption(f"""
E-Commerce Intelligence Tool v2.0 | 
Powered by OpenAI {os.getenv("OPENAI_MODEL", "gpt-4o-mini")} | 
Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
""")
