# streamlit_app.py
"""
eBay Smart Bid Controller - Web Application
Upload your eBay Keyword and Query reports for bid optimization and negative keyword suggestions!
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
if 'keyword_data' not in st.session_state:
    st.session_state.keyword_data = None
if 'query_data' not in st.session_state:
    st.session_state.query_data = None
if 'bid_recommendations' not in st.session_state:
    st.session_state.bid_recommendations = None
if 'negative_keywords' not in st.session_state:
    st.session_state.negative_keywords = None

# Title and description
st.title("🎯 eBay Smart Bid Controller")
st.markdown("**Optimize your eBay Promoted Listings with intelligent bid adjustments and negative keyword suggestions**")

# Sidebar for rules configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("📐 Performance Thresholds")
    acos_good = st.number_input("Good ACOS - Increase bids if below (%)", min_value=5, max_value=100, value=30, step=5)
    acos_poor = st.number_input("Poor ACOS - Decrease bids if above (%)", min_value=10, max_value=200, value=50, step=5)
    
    st.subheader("📊 Activity Thresholds")
    min_impressions_for_ctr = st.number_input("Min impressions to evaluate CTR", min_value=10, max_value=1000, value=100, step=10)
    min_clicks_no_sales = st.number_input("Min clicks with 0 sales to decrease", min_value=1, max_value=50, value=5, step=1)
    
    st.subheader("💰 Spend Thresholds")
    pause_spend = st.number_input("Pause if ad spend above ($) with 0 sales", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
    
    st.subheader("🔧 Bid Adjustments")
    increase_percent = st.number_input("Bid increase %", min_value=5, max_value=50, value=15, step=5)
    decrease_percent = st.number_input("Bid decrease %", min_value=5, max_value=50, value=15, step=5)
    
    st.subheader("🚫 Negative Keywords")
    min_queries_for_negative = st.number_input("Min queries to consider for negative", min_value=1, max_value=20, value=3, step=1)
    max_acos_for_negative = st.number_input("Max ACOS to add as negative (%)", min_value=50, max_value=500, value=100, step=10)
    
    st.divider()
    st.info("💡 Adjust thresholds based on your profit margins")

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload Reports", "📊 Bid Adjustments", "🚫 Negative Keywords"])

def clean_currency(value):
    """Clean currency strings to float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        return float(value.replace('$', '').replace(',', '').strip())
    return float(value)

def clean_percentage(value):
    """Clean percentage strings to float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        return float(value.replace('%', '').strip())
    return float(value)

def process_keyword_report(df):
    """Process and clean keyword report"""
    # Skip warning header if present
    if len(df) > 0 and 'Some details' in str(df.iloc[0, 0]):
        df = df.iloc[2:]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        df.reset_index(drop=True, inplace=True)
    
    # Create a standardized dataframe with consistent column names
    processed_df = pd.DataFrame()
    
    # Map all columns, stripping whitespace
    for col in df.columns:
        col_clean = str(col).strip()
        processed_df[col_clean] = df[col].values
    
    # Ensure numeric columns are numeric
    numeric_cols = ['Impressions', 'Clicks', 'Sold quantity']
    for col in numeric_cols:
        if col in processed_df.columns:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
    
    # Clean currency columns
    currency_cols = ['Bid', 'Ad fees', 'Sales', 'Average cost per click', 'Average cost per sale']
    for col in currency_cols:
        if col in processed_df.columns:
            processed_df[col] = processed_df[col].apply(clean_currency)
    
    # Add calculated columns
    processed_df['ACOS'] = 0
    processed_df['CTR_calc'] = 0
    
    if 'Sales' in processed_df.columns and 'Ad fees' in processed_df.columns:
        processed_df['ACOS'] = processed_df.apply(
            lambda row: (row['Ad fees'] / row['Sales'] * 100) if row['Sales'] > 0 
            else (999 if row['Ad fees'] > 0 else 0), axis=1
        )
    
    if 'Clicks' in processed_df.columns and 'Impressions' in processed_df.columns:
        processed_df['CTR_calc'] = processed_df.apply(
            lambda row: (row['Clicks'] / row['Impressions'] * 100) if row['Impressions'] > 0 
            else 0, axis=1
        )
    
    # Ensure Status column exists
    if 'Status' not in processed_df.columns:
        processed_df['Status'] = 'Active'
    
    return processed_df

def process_query_report(df):
    """Process and clean query report"""
    # Skip warning header if present
    if len(df) > 0 and 'Some details' in str(df.iloc[0, 0]):
        df = df.iloc[2:]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        df.reset_index(drop=True, inplace=True)
    
    # Create a standardized dataframe with consistent column names
    processed_df = pd.DataFrame()
    
    # Map all columns, stripping whitespace
    for col in df.columns:
        col_clean = str(col).strip()
        processed_df[col_clean] = df[col].values
    
    # Ensure numeric columns are numeric
    numeric_cols = ['Impressions', 'Clicks', 'Sold quantity']
    for col in numeric_cols:
        if col in processed_df.columns:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
    
    # Clean currency columns
    currency_cols = ['Keyword Bid', 'Ad fees', 'Sales']
    for col in currency_cols:
        if col in processed_df.columns:
            processed_df[col] = processed_df[col].apply(clean_currency)
    
    # Add ACOS calculation
    processed_df['ACOS'] = 0
    if 'Sales' in processed_df.columns and 'Ad fees' in processed_df.columns:
        processed_df['ACOS'] = processed_df.apply(
            lambda row: (row['Ad fees'] / row['Sales'] * 100) if row['Sales'] > 0 
            else (999 if row['Ad fees'] > 0 else 0), axis=1
        )
    
    return processed_df

def generate_bid_recommendations(keyword_df, config):
    """Generate bid adjustment recommendations"""
    recommendations = []
    
    for _, row in keyword_df.iterrows():
        # Skip inactive keywords
        if 'Status' in row and row['Status'] != 'Active':
            continue
        
        # Get values with defaults if columns don't exist
        current_bid = row.get('Bid', 0)
        impressions = row.get('Impressions', 0)
        clicks = row.get('Clicks', 0)
        sales = row.get('Sold quantity', 0)
        ad_fees = row.get('Ad fees', 0)
        revenue = row.get('Sales', 0)
        acos = row.get('ACOS', 0)
        ctr = row.get('CTR_calc', 0)
        keyword = row.get('Seller Keyword', 'Unknown')
        match_type = row.get('Keyword Match Type', 'Unknown')
        
        action = None
        reason = ""
        new_bid = current_bid
        
        # Rule 1: Pause if high spend with no sales
        if ad_fees >= config['pause_spend'] and sales == 0:
            action = "PAUSE"
            new_bid = 0
            reason = f"Spent ${ad_fees:.2f} with 0 sales"
        
        # Rule 2: Low CTR (lots of impressions, no clicks)
        elif impressions >= config['min_impressions_for_ctr'] and clicks == 0:
            action = "INCREASE"
            new_bid = current_bid * (1 + config['increase_percent'] / 100)
            reason = f"{int(impressions)} impressions with 0 clicks - bid may be too low"
        
        # Rule 3: High clicks but no sales
        elif clicks >= config['min_clicks_no_sales'] and sales == 0:
            action = "DECREASE"
            new_bid = current_bid * (1 - config['decrease_percent'] / 100)
            reason = f"{int(clicks)} clicks with 0 sales - reduce spend"
        
        # Rule 4: Good ACOS - increase to get more volume
        elif acos < config['acos_good'] and sales > 0:
            action = "INCREASE"
            new_bid = current_bid * (1 + config['increase_percent'] / 100)
            reason = f"ACOS {acos:.1f}% is excellent - scale up"
        
        # Rule 5: Poor ACOS - decrease to improve profitability
        elif acos > config['acos_poor'] and sales > 0:
            action = "DECREASE"
            new_bid = current_bid * (1 - config['decrease_percent'] / 100)
            reason = f"ACOS {acos:.1f}% is too high - reduce bid"
        
        if action:
            recommendations.append({
                'Keyword': keyword,
                'Match Type': match_type,
                'Current Bid': current_bid,
                'New Bid': round(new_bid, 2),
                'Action': action,
                'Change ($)': round(new_bid - current_bid, 2),
                'Reason': reason,
                'Impressions': int(impressions),
                'Clicks': int(clicks),
                'Sales': int(sales),
                'Ad Spend': round(ad_fees, 2),
                'Revenue': round(revenue, 2),
                'ACOS (%)': round(acos, 1) if acos < 999 else 'N/A',
                'CTR (%)': round(ctr, 2)
            })
    
    return pd.DataFrame(recommendations)

def find_negative_keywords(query_df, config):
    """Identify potential negative keywords from query report"""
    
    # Check if we have the Search Query column
    if 'Search Query' not in query_df.columns:
        return pd.DataFrame()
    
    # Create aggregation dict for available columns
    agg_dict = {}
    if 'Impressions' in query_df.columns:
        agg_dict['Impressions'] = 'sum'
    if 'Clicks' in query_df.columns:
        agg_dict['Clicks'] = 'sum'
    if 'Ad fees' in query_df.columns:
        agg_dict['Ad fees'] = 'sum'
    if 'Sales' in query_df.columns:
        agg_dict['Sales'] = 'sum'
    if 'Sold quantity' in query_df.columns:
        agg_dict['Sold quantity'] = 'sum'
    
    if not agg_dict:
        return pd.DataFrame()
    
    # Group by search query
    query_summary = query_df.groupby('Search Query').agg(agg_dict).reset_index()
    
    # Calculate ACOS for each query
    if 'Sales' in query_summary.columns and 'Ad fees' in query_summary.columns:
        query_summary['ACOS'] = query_summary.apply(
            lambda row: (row['Ad fees'] / row['Sales'] * 100) if row['Sales'] > 0 
            else (999 if row['Ad fees'] > 0 else 0), axis=1
        )
    else:
        query_summary['ACOS'] = 0
    
    # Filter for negative keyword candidates
    negative_candidates = query_summary[
        (query_summary.get('Clicks', 0) >= config['min_queries_for_negative']) &
        ((query_summary['ACOS'] > config['max_acos_for_negative']) | 
         ((query_summary.get('Sales', 0) == 0) & (query_summary.get('Ad fees', 0) > 0)))
    ].copy()
    
    if len(negative_candidates) == 0:
        return pd.DataFrame()
    
    negative_candidates['Recommendation'] = negative_candidates.apply(
        lambda row: 'No sales despite clicks' if row.get('Sales', 0) == 0 
        else f'ACOS too high ({row["ACOS"]:.1f}%)', axis=1
    )
    
    # Sort by wasted spend
    negative_candidates['Wasted Spend'] = negative_candidates.apply(
        lambda row: row.get('Ad fees', 0) if row.get('Sales', 0) == 0 
        else row.get('Ad fees', 0) - (row.get('Sales', 0) * config['acos_good'] / 100), axis=1
    )
    
    negative_candidates = negative_candidates.sort_values('Wasted Spend', ascending=False)
    
    # Select columns for output
    output_cols = ['Search Query', 'Recommendation', 'Wasted Spend']
    if 'Clicks' in negative_candidates.columns:
        output_cols.insert(1, 'Clicks')
    if 'Ad fees' in negative_candidates.columns:
        output_cols.insert(-1, 'Ad fees')
    if 'Sales' in negative_candidates.columns:
        output_cols.insert(-1, 'Sales')
    if 'ACOS' in negative_candidates.columns:
        output_cols.insert(-1, 'ACOS')
    
    return negative_candidates[output_cols].round(2)

with tab1:
    st.header("📤 Upload Your eBay Reports")
    
    st.info("📌 You need to upload BOTH reports from the same campaign: Keyword Report and Query Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Keyword Report")
        keyword_file = st.file_uploader(
            "Upload Keyword Report CSV",
            type=['csv'],
            key='keyword_upload',
            help="This report shows performance by keyword with bid information"
        )
        
        if keyword_file:
            try:
                keyword_df = pd.read_csv(keyword_file)
                keyword_df = process_keyword_report(keyword_df)
                st.session_state.keyword_data = keyword_df
                
                # Show summary
                active_keywords = keyword_df[keyword_df.get('Status', 'Active') == 'Active'] if 'Status' in keyword_df.columns else keyword_df
                st.success(f"✅ Loaded {len(active_keywords)} active keywords")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if 'Clicks' in keyword_df.columns:
                        st.metric("Keywords with clicks", 
                                 len(active_keywords[active_keywords['Clicks'] > 0]))
                with col_b:
                    if 'Sold quantity' in keyword_df.columns:
                        st.metric("Keywords with sales", 
                                 len(active_keywords[active_keywords['Sold quantity'] > 0]))
            except Exception as e:
                st.error(f"Error processing keyword file: {str(e)}")
    
    with col2:
        st.subheader("2️⃣ Query Report")
        query_file = st.file_uploader(
            "Upload Query Report CSV",
            type=['csv'],
            key='query_upload',
            help="This report shows actual search queries and their performance"
        )
        
        if query_file:
            try:
                query_df = pd.read_csv(query_file)
                query_df = process_query_report(query_df)
                st.session_state.query_data = query_df
                
                # Show summary
                st.success(f"✅ Loaded {len(query_df)} search queries")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if 'Clicks' in query_df.columns:
                        st.metric("Queries with clicks", 
                                 len(query_df[query_df['Clicks'] > 0]))
                with col_b:
                    if 'Sold quantity' in query_df.columns:
                        st.metric("Queries with sales", 
                                 len(query_df[query_df['Sold quantity'] > 0]))
            except Exception as e:
                st.error(f"Error processing query file: {str(e)}")
    
    # Analyze button
    if st.session_state.keyword_data is not None and st.session_state.query_data is not None:
        if st.button("🔍 Analyze Campaign", type="primary", use_container_width=True):
            with st.spinner("Analyzing your campaign..."):
                
                # Generate bid recommendations
                config = {
                    'acos_good': acos_good,
                    'acos_poor': acos_poor,
                    'min_impressions_for_ctr': min_impressions_for_ctr,
                    'min_clicks_no_sales': min_clicks_no_sales,
                    'pause_spend': pause_spend,
                    'increase_percent': increase_percent,
                    'decrease_percent': decrease_percent,
                    'min_queries_for_negative': min_queries_for_negative,
                    'max_acos_for_negative': max_acos_for_negative
                }
                
                bid_recs = generate_bid_recommendations(st.session_state.keyword_data, config)
                st.session_state.bid_recommendations = bid_recs
                
                # Find negative keywords
                neg_keywords = find_negative_keywords(st.session_state.query_data, config)
                st.session_state.negative_keywords = neg_keywords
                
                st.success(f"✅ Analysis complete! Found {len(bid_recs)} bid adjustments and {len(neg_keywords)} negative keyword candidates")
                st.balloons()

with tab2:
    st.header("📊 Bid Adjustment Recommendations")
    
    if st.session_state.bid_recommendations is not None and not st.session_state.bid_recommendations.empty:
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        recs = st.session_state.bid_recommendations
        
        with col1:
            total_recs = len(recs)
            st.metric("Total Adjustments", total_recs)
        
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
        
        # Column ordering
        all_columns = list(recs.columns)
        st.multiselect(
            "Select and reorder columns (drag to rearrange):",
            options=all_columns,
            default=all_columns,
            key="column_order"
        )
        
        # Filter by action
        action_filter = st.selectbox(
            "Filter by action:",
            ["All"] + list(recs['Action'].unique())
        )
        
        if action_filter != "All":
            filtered_recs = recs[recs['Action'] == action_filter]
        else:
            filtered_recs = recs
        
        # Apply column ordering
        selected_cols = st.session_state.get('column_order', all_columns)
        if selected_cols:
            filtered_recs = filtered_recs[selected_cols]
        
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
                "Revenue": st.column_config.NumberColumn(format="$%.2f")
            }
        )
        
        # Download button
        csv = filtered_recs.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="bid_recommendations.csv">📥 Download Bid Recommendations</a>'
        st.markdown(href, unsafe_allow_html=True)
        
    else:
        st.info("👈 Upload both reports and click Analyze to see bid recommendations")

with tab3:
    st.header("🚫 Negative Keyword Suggestions")
    
    if st.session_state.negative_keywords is not None and not st.session_state.negative_keywords.empty:
        
        st.write(f"Found {len(st.session_state.negative_keywords)} search queries that are wasting budget:")
        
        # Summary of wasted spend
        if 'Wasted Spend' in st.session_state.negative_keywords.columns:
            total_wasted = st.session_state.negative_keywords['Wasted Spend'].sum()
            st.metric("💸 Total Wasted Spend", f"${total_wasted:.2f}")
        
        st.divider()
        
        # Display negative keyword candidates
        st.dataframe(
            st.session_state.negative_keywords,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ad fees": st.column_config.NumberColumn(format="$%.2f"),
                "Sales": st.column_config.NumberColumn(format="$%.2f"),
                "ACOS": st.column_config.NumberColumn(format="%.1f"),
                "Wasted Spend": st.column_config.NumberColumn(format="$%.2f")
            }
        )
        
        # Download button
        csv = st.session_state.negative_keywords.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="negative_keywords.csv">📥 Download Negative Keyword List</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        st.divider()
        st.info("💡 Add these as negative keywords in your eBay campaign to stop wasting budget on non-converting searches")
        
    else:
        st.info("👈 Upload both reports and click Analyze to see negative keyword suggestions")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center'>
    <p>Made with ❤️ for eBay sellers | 
    <a href='https://github.com/Betty-Cod3s/ebay-smart-bid-controller'>GitHub</a>
    </p>
</div>
""", unsafe_allow_html=True)
