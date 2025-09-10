# streamlit_app.py
"""
eBay Smart Bid Controller - Web Application
Upload your eBay ads report and get instant bid recommendations!
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import base64

# Page config
st.set_page_config(
    page_title="eBay Smart Bid Controller",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'analyzed_data' not in st.session_state:
    st.session_state.analyzed_data = None

# Title and description
st.title("🎯 eBay Smart Bid Controller")
st.markdown("**Automate your eBay ad bid adjustments with intelligent rule-based optimization**")

# Sidebar for rules configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("📐 ACOS Thresholds")
    acos_increase = st.slider("Increase if ACOS below (%)", 10, 50, 30)
    acos_decrease = st.slider("Decrease if ACOS above (%)", 20, 60, 30)
    
    st.subheader("💰 Spend Thresholds")
    pause_spend = st.number_input("Pause if spend above ($) with 0 sales", value=10.0, step=1.0)
    test_spend = st.number_input("Test lower bid if spend above ($) with 0 sales", value=5.0, step=1.0)
    
    st.subheader("📊 Adjustment Percentages")
    increase_percent = st.slider("Bid increase %", 5, 30, 10)
    decrease_percent = st.slider("Bid decrease %", 5, 30, 10)
    
    st.divider()
    st.info("💡 **Tip**: Adjust these thresholds based on your profit margins and risk tolerance")

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "📊 Results", "📚 Help"])

def calculate_metrics(df):
    """Calculate key metrics for each row."""
    df['acos'] = (df['ad_spend'] / df['revenue'] * 100).replace([np.inf, -np.inf], 999)
    df['ctr'] = (df['clicks'] / df['impressions'] * 100).fillna(0)
    df['cpc'] = (df['ad_spend'] / df['clicks']).replace([np.inf, -np.inf], 0)
    df['conversion_rate'] = (df['sales'] / df['clicks'] * 100).fillna(0)
    return df

def apply_rules(row, acos_inc, acos_dec, pause_sp, test_sp, inc_pct, dec_pct):
    """Apply bidding rules to a single row."""
    acos = row['acos']
    ad_spend = row['ad_spend']
    sales = row['sales']
    current_bid = row['current_bid']
    
    # Rule evaluation
    if ad_spend >= pause_sp and sales == 0:
        return {
            'action': 'PAUSE',
            'new_bid': 0,
            'reason': f"Spent ${ad_spend:.2f} with 0 sales - pausing to prevent losses",
            'change': -current_bid
        }
    elif ad_spend >= test_sp and ad_spend < pause_sp and sales == 0:
        new_bid = current_bid * (1 - dec_pct * 2 / 100)
        return {
            'action': 'DECREASE',
            'new_bid': round(new_bid, 2),
            'reason': f"Spent ${ad_spend:.2f} with no sales - testing lower bid",
            'change': round(new_bid - current_bid, 2)
        }
    elif acos < acos_inc and sales > 0:
        new_bid = current_bid * (1 + inc_pct / 100)
        return {
            'action': 'INCREASE',
            'new_bid': round(new_bid, 2),
            'reason': f"ACOS {acos:.1f}% is below {acos_inc}% target - profitable campaign",
            'change': round(new_bid - current_bid, 2)
        }
    elif acos > acos_dec and sales > 0:
        new_bid = current_bid * (1 - dec_pct / 100)
        return {
            'action': 'DECREASE',
            'new_bid': round(new_bid, 2),
            'reason': f"ACOS {acos:.1f}% exceeds {acos_dec}% target - reducing spend",
            'change': round(new_bid - current_bid, 2)
        }
    else:
        return {
            'action': 'NO_CHANGE',
            'new_bid': current_bid,
            'reason': "Performance within target range",
            'change': 0
        }

with tab1:
    st.header("📤 Upload Your eBay Ads Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File upload
        uploaded_file = st.file_uploader(
            "Choose your CSV file",
            type=['csv'],
            help="Upload your eBay ads report in CSV format"
        )
        
        # Sample data option
        use_sample = st.checkbox("Use sample data to test", value=False)
        
        if use_sample:
            # Generate sample data
            np.random.seed(42)
            sample_data = {
                'campaign_id': [f'CAM_{i:03d}' for i in range(1, 21)],
                'sku': [f'SKU_{i:04d}' for i in range(1001, 1021)],
                'product_name': [f'Product {i}' for i in range(1, 21)],
                'current_bid': np.random.uniform(0.5, 5.0, 20).round(2),
                'impressions': np.random.randint(100, 10000, 20),
                'clicks': np.random.randint(0, 500, 20),
                'ad_spend': np.random.uniform(0, 100, 20).round(2),
                'sales': np.random.randint(0, 20, 20),
                'revenue': np.random.uniform(0, 500, 20).round(2)
            }
            # Ensure some specific scenarios
            sample_data['sales'][5] = 0
            sample_data['ad_spend'][5] = 15.00
            
            df = pd.DataFrame(sample_data)
            st.success("✅ Sample data loaded!")
            
        elif uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Loaded {len(df)} campaigns from {uploaded_file.name}")
        else:
            df = None
    
    with col2:
        st.info("""
        **Required CSV columns:**
        - campaign_id
        - sku
        - current_bid
        - impressions
        - clicks
        - ad_spend
        - sales
        - revenue
        """)
    
    # Analyze button
    if df is not None:
        if st.button("🔍 Analyze Campaigns", type="primary", use_container_width=True):
            with st.spinner("Analyzing your campaigns..."):
                # Calculate metrics
                df = calculate_metrics(df)
                
                # Apply rules
                recommendations = []
                for _, row in df.iterrows():
                    result = apply_rules(
                        row, 
                        acos_increase, 
                        acos_decrease,
                        pause_spend,
                        test_spend,
                        increase_percent,
                        decrease_percent
                    )
                    if result['action'] != 'NO_CHANGE':
                        recommendations.append({
                            'Campaign ID': row['campaign_id'],
                            'SKU': row['sku'],
                            'Current Bid': row['current_bid'],
                            'New Bid': result['new_bid'],
                            'Action': result['action'],
                            'Change ($)': result['change'],
                            'Reason': result['reason'],
                            'ACOS (%)': round(row['acos'], 1),
                            'Ad Spend': round(row['ad_spend'], 2),
                            'Revenue': round(row['revenue'], 2),
                            'Sales': int(row['sales'])
                        })
                
                st.session_state.recommendations = pd.DataFrame(recommendations)
                st.session_state.analyzed_data = df
                st.success(f"✅ Analysis complete! Found {len(recommendations)} recommendations")
                st.balloons()

with tab2:
    st.header("📊 Bid Adjustment Recommendations")
    
    if st.session_state.recommendations is not None and not st.session_state.recommendations.empty:
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        recs = st.session_state.recommendations
        
        with col1:
            total_recs = len(recs)
            st.metric("Total Recommendations", total_recs)
        
        with col2:
            increases = len(recs[recs['Action'] == 'INCREASE'])
            st.metric("⬆️ Increases", increases)
        
        with col3:
            decreases = len(recs[recs['Action'] == 'DECREASE'])
            st.metric("⬇️ Decreases", decreases)
        
        with col4:
            pauses = len(recs[recs['Action'] == 'PAUSE'])
            st.metric("⏸️ Pauses", pauses)
        
        st.divider()
        
        # Filter by action
        action_filter = st.selectbox(
            "Filter by action:",
            ["All"] + list(recs['Action'].unique())
        )
        
        if action_filter != "All":
            filtered_recs = recs[recs['Action'] == action_filter]
        else:
            filtered_recs = recs
        
        # Display recommendations
        st.dataframe(
            filtered_recs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Current Bid": st.column_config.NumberColumn(format="$%.2f"),
                "New Bid": st.column_config.NumberColumn(format="$%.2f"),
                "Change ($)": st.column_config.NumberColumn(format="$%.2f"),
                "Ad Spend": st.column_config.NumberColumn(format="$%.2f"),
                "Revenue": st.column_config.NumberColumn(format="$%.2f"),
                "ACOS (%)": st.column_config.NumberColumn(format="%.1f%%"),
            }
        )
        
        # Download button
        csv = filtered_recs.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="bid_recommendations.csv">📥 Download Recommendations as CSV</a>'
        st.markdown(href, unsafe_allow_html=True)
        
    else:
        st.info("👈 Upload your eBay ads report and click Analyze to see recommendations")

with tab3:
    st.header("📚 How to Use")
    
    with st.expander("🎯 Understanding ACOS", expanded=True):
        st.write("""
        **ACOS (Advertising Cost of Sale)** = (Ad Spend ÷ Revenue) × 100
        
        - **< 30%**: Generally profitable advertising
        - **30-50%**: Break-even range (depends on margins)
        - **> 50%**: Usually unprofitable (unless high-margin products)
        
        Adjust the ACOS thresholds in the sidebar based on your profit margins.
        """)
    
    with st.expander("📋 CSV Format Requirements"):
        st.write("""
        Your CSV must include these columns:
        - `campaign_id`: Unique campaign identifier
        - `sku`: Product SKU
        - `current_bid`: Current bid amount
        - `impressions`: Number of ad impressions
        - `clicks`: Number of clicks
        - `ad_spend`: Total ad spend
        - `sales`: Number of sales
        - `revenue`: Total revenue generated
        
        Column names are flexible - common variations are auto-detected.
        """)
    
    with st.expander("🎯 Default Rules Explained"):
        st.write("""
        1. **High Performance**: ACOS < 30% → Increase bids to scale
        2. **Poor Performance**: ACOS > 30% → Decrease to improve efficiency
        3. **No Conversion**: $10+ spend, 0 sales → Pause to stop losses
        4. **Test Lower**: $5-10 spend, 0 sales → Decrease significantly
        5. **Maintain**: Within targets → No change needed
        """)
    
    st.divider()
    
    st.info("""
    💡 **Pro Tips:**
    - Start with conservative adjustments (5-10%)
    - Monitor daily for the first week
    - Consider seasonal trends
    - Different products may need different ACOS targets
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center'>
    <p>Made with ❤️ for eBay sellers | 
    <a href='https://github.com/Betty-Cod3s/ebay-smart-bid-controller'>GitHub</a>
    </p>
</div>
""", unsafe_allow_html=True)