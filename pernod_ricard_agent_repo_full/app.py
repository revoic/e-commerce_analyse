"""
E-commerce Intelligence Dashboard

Multi-company e-commerce analysis tool with 7-layer anti-hallucination system.
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
import sys
import os
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analysis_engine import AnalysisEngine


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def make_json_safe(obj):
    """Convert non-serializable objects to JSON-safe format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_safe(item) for item in obj]
    elif hasattr(obj, 'model_dump'):  # Pydantic model
        return make_json_safe(obj.model_dump())
    elif hasattr(obj, '__dict__'):  # Other objects
        return make_json_safe(obj.__dict__)
    else:
        return obj


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="E-commerce Intelligence",
    page_icon="🛒",
    layout="wide"
)


# ==============================================================================
# SIDEBAR CONFIG
# ==============================================================================

with st.sidebar:
    st.title("⚙️ Settings")
    
    st.markdown("""
    ### Analysis Configuration
    
    **Region Focus:** 🇪🇺 EU (especially Germany)
    
    This tool is optimized for European e-commerce intelligence.
    """)
    
    lookback_days = st.slider(
        "Lookback Period (days)",
        min_value=7,
        max_value=90,
        value=30,
        help="How far back to search for news"
    )
    
    max_sources = st.slider(
        "Max Sources",
        min_value=10,
        max_value=100,
        value=30,
        help="Maximum number of sources to analyze"
    )
    
    show_debug = st.checkbox(
        "Show Debug Info",
        value=False,
        help="Display technical details and validation stats"
    )
    
    st.markdown("---")
    st.markdown("""
    ### About
    
    Multi-company e-commerce intelligence with strict fact validation.
    
    **Anti-Hallucination System:**
    - ✅ Source verification
    - ✅ Citation enforcement
    - ✅ Structured extraction
    - ✅ Confidence filtering
    - ✅ Cross-referencing
    - ✅ LLM fact-checking
    """)


# ==============================================================================
# MAIN APP
# ==============================================================================

st.title("🛒 E-commerce Intelligence Tool")
st.markdown("**Discover factual e-commerce signals for any company**")

# Company input
col1, col2 = st.columns([3, 1])

with col1:
    company_name = st.text_input(
        "Company Name",
        value="",
        placeholder="e.g., Zalando, Amazon, Shopify",
        help="Enter any company name to analyze"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🚀 Analyze", type="primary", use_container_width=True)


# ==============================================================================
# RUN ANALYSIS
# ==============================================================================

if analyze_button and company_name:
    # Build config
    config = {
        'lookback_days': lookback_days,
        'max_sources': max_sources
    }
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(message: str, percent: float):
        """Progress callback."""
        progress_bar.progress(percent)
        status_text.info(f"**{message}**")
    
    try:
        # Run analysis
        engine = AnalysisEngine(
            company_name=company_name,
            config=config,
            progress_callback=update_progress
        )
        
        result = engine.run_analysis()
        
        # Clear progress
        progress_bar.empty()
        status_text.empty()
        
        # Check status
        if result['status'] != 'success':
            st.warning(f"⚠️ Analysis completed with issues: {result['status']}")
            if not result['signals']:
                st.info("""
                **No signals found.** This could mean:
                - Company not well-known or limited recent news
                - Try adjusting lookback period
                - Check company name spelling
                """)
        
        # Store result in session
        st.session_state['last_result'] = result
        st.session_state['last_company'] = company_name
        
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        if show_debug:
            st.code(traceback.format_exc(), language="python")
        st.stop()


# ==============================================================================
# DISPLAY RESULTS
# ==============================================================================

if 'last_result' in st.session_state:
    result = st.session_state['last_result']
    company = st.session_state.get('last_company', 'Unknown')
    
    st.markdown("---")
    st.header(f"📊 Analysis Results: {company}")
    
    # Summary metrics
    stats = result.get('stats', {})
    report = result.get('report', {})
    summary = report.get('summary', {}) if report else {}
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sources Analyzed",
            stats.get('source_count', 0)
        )
    
    with col2:
        st.metric(
            "High-Confidence Signals",
            summary.get('high_confidence_signals', 0)
        )
    
    with col3:
        st.metric(
            "Metrics Covered",
            summary.get('metrics_covered', 0)
        )
    
    with col4:
        duration = stats.get('duration_seconds', 0)
        st.metric(
            "Analysis Time",
            f"{duration:.1f}s" if duration else "N/A"
        )
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Signals",
        "📰 Sources",
        "📊 Report",
        "💾 Export"
    ])
    
    # TAB 1: SIGNALS
    with tab1:
        signals = result.get('signals', [])
        
        if not signals:
            st.info("No high-confidence signals found.")
        else:
            st.subheader(f"Found {len(signals)} High-Confidence Signals")
            
            # Filters
            col1, col2 = st.columns(2)
            
            with col1:
                # Get unique metrics
                metrics = list(set(
                    s.get('value', {}).get('metric', 'unknown')
                    for s in signals
                ))
                selected_metric = st.selectbox(
                    "Filter by Metric",
                    options=['All'] + sorted(metrics)
                )
            
            with col2:
                # Get unique regions
                regions = list(set(
                    s.get('value', {}).get('region', 'Unknown')
                    for s in signals
                ))
                selected_region = st.selectbox(
                    "Filter by Region",
                    options=['All'] + sorted(regions)
                )
            
            # Apply filters
            filtered_signals = signals
            if selected_metric != 'All':
                filtered_signals = [
                    s for s in filtered_signals
                    if s.get('value', {}).get('metric') == selected_metric
                ]
            if selected_region != 'All':
                filtered_signals = [
                    s for s in filtered_signals
                    if s.get('value', {}).get('region') == selected_region
                ]
            
            # Display signals
            for i, signal in enumerate(filtered_signals, 1):
                value = signal.get('value', {})
                
                with st.expander(
                    f"**{i}. {value.get('metric', 'Unknown')}** - "
                    f"{value.get('numeric_value', 'N/A')} {value.get('unit', '')} "
                    f"[{signal.get('confidence', 0)*100:.0f}% confidence]"
                ):
                    # Main info
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Metric:** {value.get('metric', 'N/A')}")
                        st.markdown(f"**Value:** {value.get('numeric_value', 'N/A')} {value.get('unit', '')}")
                        st.markdown(f"**Period:** {value.get('period', 'N/A')}")
                        st.markdown(f"**Region:** {value.get('region', 'N/A')}")
                        
                        if value.get('context'):
                            st.markdown(f"**Context:** {value['context']}")
                    
                    with col2:
                        conf = signal.get('confidence', 0)
                        st.metric("Confidence", f"{conf*100:.1f}%")
                        
                        # Validation badges
                        if signal.get('citation_valid'):
                            st.success("✓ Citation verified")
                        
                        corr_count = signal.get('corroboration_count', 0)
                        if corr_count > 0:
                            st.info(f"🔗 {corr_count} corroborating sources")
                        
                        llm_ver = signal.get('llm_verification', {})
                        if llm_ver.get('verified'):
                            st.success("✓ LLM verified")
                    
                    # Quote
                    st.markdown("**Verbatim Quote:**")
                    st.markdown(f"> {signal.get('verbatim_quote', 'N/A')}")
                    
                    # Source
                    st.markdown(f"**Source:** [{signal.get('source_title', 'Unknown')}]({signal.get('source_url', '#')})")
                    
                    # Debug info
                    if show_debug:
                        st.json(signal)
    
    # TAB 2: SOURCES
    with tab2:
        sources = result.get('sources', [])
        
        if not sources:
            st.info("No sources found.")
        else:
            st.subheader(f"Analyzed {len(sources)} Sources")
            
            # Create DataFrame
            source_data = []
            for src in sources:
                source_data.append({
                    'Title': src.get('title', 'N/A')[:60],
                    'Type': src.get('type', 'unknown'),
                    'URL': src.get('url', 'N/A'),
                    'Date': src.get('published_date', 'N/A')
                })
            
            df = pd.DataFrame(source_data)
            
            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Source details
            if show_debug:
                st.markdown("### Source Details")
                for i, src in enumerate(sources[:5], 1):  # Show first 5
                    with st.expander(f"{i}. {src.get('title', 'Unknown')[:80]}"):
                        st.json(src)
    
    # TAB 3: REPORT
    with tab3:
        if not report:
            st.info("Report not available.")
        else:
            st.subheader("Analysis Report")
            
            # Summary
            st.markdown("### Summary")
            summary_df = pd.DataFrame([
                {"Metric": k.replace('_', ' ').title(), "Value": v}
                for k, v in summary.items()
                if not isinstance(v, dict)
            ])
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Signals by metric
            if report.get('signals_by_metric'):
                st.markdown("### Signals by Metric Type")
                
                metric_counts = {
                    metric: len(sigs)
                    for metric, sigs in report['signals_by_metric'].items()
                }
                
                metric_df = pd.DataFrame([
                    {"Metric": m, "Count": c}
                    for m, c in sorted(metric_counts.items(), key=lambda x: -x[1])
                ])
                
                st.dataframe(metric_df, use_container_width=True, hide_index=True)
            
            # Validation stats
            if show_debug and report.get('validation_stats'):
                st.markdown("### Validation Statistics")
                st.json(report['validation_stats'])
    
    # TAB 4: EXPORT
    with tab4:
        st.subheader("Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON export (make sure it's JSON-safe)
            safe_result = make_json_safe(result)
            json_str = json.dumps(safe_result, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Download as JSON",
                data=json_str,
                file_name=f"{company.lower().replace(' ', '_')}_analysis.json",
                mime="application/json"
            )
        
        with col2:
            # CSV export (signals only)
            signals = result.get('signals', [])
            if signals:
                # Flatten signals for CSV
                csv_data = []
                for sig in signals:
                    val = sig.get('value', {})
                    csv_data.append({
                        'Metric': val.get('metric', ''),
                        'Value': val.get('numeric_value', ''),
                        'Unit': val.get('unit', ''),
                        'Period': val.get('period', ''),
                        'Region': val.get('region', ''),
                        'Confidence': sig.get('confidence', 0),
                        'Quote': sig.get('verbatim_quote', ''),
                        'Source': sig.get('source_title', ''),
                        'URL': sig.get('source_url', '')
                    })
                
                df = pd.DataFrame(csv_data)
                csv_str = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download Signals as CSV",
                    data=csv_str,
                    file_name=f"{company.lower().replace(' ', '_')}_signals.csv",
                    mime="text/csv"
                )
            else:
                st.info("No signals to export.")
        
        # Show preview
        if show_debug:
            st.markdown("### Export Preview (JSON)")
            st.code(json_str[:1000] + "\n...", language="json")


# ==============================================================================
# FOOTER
# ==============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>
    E-commerce Intelligence Tool | 
    7-Layer Anti-Hallucination System | 
    Optimized for 🇪🇺 EU Markets
    </small>
</div>
""", unsafe_allow_html=True)
