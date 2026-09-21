import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Nassau Candy Profitability Analysis",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🍬 Nassau Candy Distributor — Profitability & Sales Dashboard")
st.markdown("""
**Executive Strategic Analytics**  
*Analyzing division margins, regional sales performance, product profitability, and Pareto (80/20) distributions.*
""")

# -----------------------------------------------------------------------------
# 2. DATA LOADING & CLEANING
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Read Main Data sheet from Excel file
    df = pd.read_excel('Nassau Candy Distributor.xlsx', sheet_name='Main Data')
    
    # Ensure dates are datetime format
    if 'Order Date' in df.columns:
        df['Order Date'] = pd.to_datetime(df['Order Date'])
        
    # Calculate Gross Margin % if not present
    if 'Gross Margin %' not in df.columns and 'Sales' in df.columns and 'Gross Profit' in df.columns:
        df['Gross Margin %'] = df['Gross Profit'] / df['Sales']
        
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error loading Excel dataset: {e}")
    st.info("Make sure 'Nassau Candy Distributor.xlsx' is uploaded to the same folder on GitHub.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & FILTERS
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Filter Controls")

# Division Filter
divisions = ['All'] + sorted(df_raw['Division'].dropna().unique().tolist())
selected_division = st.sidebar.selectbox("Select Division", options=divisions)

# Region Filter
regions = ['All'] + sorted(df_raw['Region'].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Select Region", options=regions)

# Ship Mode Filter
ship_modes = ['All'] + sorted(df_raw['Ship Mode'].dropna().unique().tolist())
selected_ship = st.sidebar.selectbox("Select Ship Mode", options=ship_modes)

# Apply Filters
df = df_raw.copy()

if selected_division != 'All':
    df = df[df['Division'] == selected_division]

if selected_region != 'All':
    df = df[df['Region'] == selected_region]

if selected_ship != 'All':
    df = df[df['Ship Mode'] == selected_ship]

# -----------------------------------------------------------------------------
# 4. EXECUTIVE KPIS
# -----------------------------------------------------------------------------
total_sales = df['Sales'].sum()
total_profit = df['Gross Profit'].sum()
total_units = df['Units'].sum()
overall_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Revenue ($)", f"${total_sales:,.2f}")
with col2:
    st.metric("Total Gross Profit ($)", f"${total_profit:,.2f}")
with col3:
    st.metric("Overall Gross Margin", f"{overall_margin:.2f}%")
with col4:
    st.metric("Total Units Sold", f"{total_units:,.0f}")

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. ANALYSIS MODULES (TABS)
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Summary & Division Performance",
    "🗺️ Regional Performance & Margin",
    "📦 Product Profitability & Pareto (80/20)",
    "📑 Raw Data Explorer"
])

# --- TAB 1: DIVISION PERFORMANCE ---
with tab1:
    st.subheader("Division Performance & Margin Overview")
    
    div_summary = df.groupby('Division').agg(
        Total_Sales=('Sales', 'sum'),
        Total_Profit=('Gross Profit', 'sum'),
        Total_Units=('Units', 'sum')
    ).reset_index()
    div_summary['Gross_Margin_%'] = (div_summary['Total_Profit'] / div_summary['Total_Sales']) * 100

    col_a, col_b = st.columns(2)
    
    with col_a:
        fig_div_sales = px.bar(
            div_summary, 
            x='Division', 
            y=['Total_Sales', 'Total_Profit'],
            barmode='group',
            title="Revenue vs. Gross Profit by Division",
            labels={'value': 'Amount ($)', 'variable': 'Metric'}
        )
        st.plotly_chart(fig_div_sales, use_container_width=True)
        
    with col_b:
        fig_div_margin = px.bar(
            div_summary,
            x='Division',
            y='Gross_Margin_%',
            color='Division',
            title="Gross Margin % by Division",
            labels={'Gross_Margin_%': 'Gross Margin (%)'}
        )
        st.plotly_chart(fig_div_margin, use_container_width=True)

# --- TAB 2: REGIONAL PERFORMANCE ---
with tab2:
    st.subheader("Regional Performance & Contribution")
    
    reg_summary = df.groupby(['Region', 'Division']).agg(
        Sales=('Sales', 'sum'),
        Profit=('Gross Profit', 'sum')
    ).reset_index()

    c1, c2 = st.columns(2)
    
    with c1:
        fig_reg_sales = px.bar(
            reg_summary,
            x='Region',
            y='Sales',
            color='Division',
            title="Sales Breakdown by Region and Division"
        )
        st.plotly_chart(fig_reg_sales, use_container_width=True)
        
    with c2:
        fig_reg_profit = px.bar(
            reg_summary,
            x='Region',
            y='Profit',
            color='Division',
            title="Gross Profit Breakdown by Region and Division"
        )
        st.plotly_chart(fig_reg_profit, use_container_width=True)

# --- TAB 3: PARETO ANALYSIS & PRODUCT PROFITABILITY ---
with tab3:
    st.subheader("Product Profitability & Pareto (80/20) Analysis")
    
    prod_summary = df.groupby('Product Name').agg(
        Sales=('Sales', 'sum'),
        Profit=('Gross Profit', 'sum'),
        Units=('Units', 'sum')
    ).reset_index().sort_values(by='Profit', ascending=False)
    
    # Calculate Pareto cumulative profit %
    total_prod_profit = prod_summary['Profit'].sum()
    prod_summary['Cum_Profit'] = prod_summary['Profit'].cumsum()
    prod_summary['Cum_Profit_Pct'] = (prod_summary['Cum_Profit'] / total_prod_profit) * 100

    # Fixed Dual-Axis Pareto Chart using make_subplots
    fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_pareto.add_trace(
        go.Bar(
            x=prod_summary['Product Name'], 
            y=prod_summary['Profit'], 
            name='Gross Profit ($)'
        ),
        secondary_y=False
    )
    
    fig_pareto.add_trace(
        go.Scatter(
            x=prod_summary['Product Name'], 
            y=prod_summary['Cum_Profit_Pct'], 
            name='Cumulative Profit %',
            line=dict(color='red', width=3)
        ),
        secondary_y=True
    )
    
    fig_pareto.update_yaxes(title_text="Gross Profit ($)", secondary_y=False)
    fig_pareto.update_yaxes(title_text="Cumulative Profit (%)", range=[0, 105], secondary_y=True)
    fig_pareto.update_layout(
        title="Pareto Chart: Product Profit Contribution & Cumulative %",
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig_pareto, use_container_width=True)
    
    st.markdown("### Top Products Table")
    st.dataframe(prod_summary, use_container_width=True, hide_index=True)

# --- TAB 4: RAW DATA EXPLORER ---
with tab4:
    st.subheader("Filtered Main Dataset")
    st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Nassau Candy Distributor Profitability Analytics — Executive Dashboard")
