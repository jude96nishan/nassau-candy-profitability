
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Nassau Candy Profitability Analysis",
    page_icon="🍬",
    layout="wide"
)

# Load and cache data from Excel
@st.cache_data
def load_data():
    df = pd.read_excel('Nassau Candy Distributor.xlsx', sheet_name='Main Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Ship Date'] = pd.to_datetime(df['Ship Date'])
    df['Gross Margin %'] = df['Gross Profit'] / df['Sales']
    df['Profit per Unit'] = df['Gross Profit'] / df['Units']
    return df

df_raw = load_data()

# Sidebar Filters
st.sidebar.title("🍬 Filter Controls")

min_date = df_raw['Order Date'].min().date()
max_date = df_raw['Order Date'].max().date()
date_range = st.sidebar.date_input("Order Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

divisions = list(df_raw['Division'].unique())
selected_divisions = st.sidebar.multiselect("Division Filter", divisions, default=divisions)

regions = list(df_raw['Region'].unique())
selected_regions = st.sidebar.multiselect("Region Filter", regions, default=regions)

margin_threshold = st.sidebar.slider("Minimum Gross Margin % Threshold", 0.0, 1.0, 0.0, step=0.05)
product_search = st.sidebar.text_input("Search Product Name")

# Filtering Data
filtered_df = df_raw[
    (df_raw['Order Date'].dt.date >= date_range[0]) &
    (df_raw['Order Date'].dt.date <= date_range[-1]) &
    (df_raw['Division'].isin(selected_divisions)) &
    (df_raw['Region'].isin(selected_regions)) &
    (df_raw['Gross Margin %'] >= margin_threshold)
]

if product_search:
    filtered_df = filtered_df[filtered_df['Product Name'].str.contains(product_search, case=False, na=False)]

# Dashboard Header & KPIs
st.title("📊 Nassau Candy Distributor — Profitability & Margin Analysis")
st.markdown("Product Line Profitability & Division Performance Dashboard")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Gross Profit'].sum()
total_units = filtered_df['Units'].sum()
overall_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
avg_profit_per_unit = (total_profit / total_units) if total_units > 0 else 0

kpi1.metric("Total Revenue", f"${total_sales:,.2f}")
kpi2.metric("Total Gross Profit", f"${total_profit:,.2f}")
kpi3.metric("Gross Margin %", f"{overall_margin:.1f}%")
kpi4.metric("Units Sold", f"{total_units:,}")
kpi5.metric("Avg Profit / Unit", f"${avg_profit_per_unit:.2f}")

st.markdown("---")

# Dashboard Modules (Tabs)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Product Profitability", 
    "🏬 Division & Region", 
    "📈 Cost Diagnostics", 
    "🎯 Profit Concentration", 
    "📝 Executive Recommendations"
])

# Module 1: Product Profitability
with tab1:
    st.header("Product Margin Leaderboard")
    prod_summary = filtered_df.groupby('Product Name').agg(
        Total_Sales=('Sales', 'sum'),
        Total_Profit=('Gross Profit', 'sum'),
        Total_Units=('Units', 'sum'),
        Cost=('Cost', 'sum')
    ).reset_index()
    
    prod_summary['Margin_Pct'] = (prod_summary['Total_Profit'] / prod_summary['Total_Sales']) * 100
    prod_summary = prod_summary.sort_values(by='Total_Profit', ascending=False)
    
    col1, col2 = st.columns([3, 2])
    with col1:
        fig_bar = px.bar(
            prod_summary.head(10), x='Total_Profit', y='Product Name', orientation='h',
            color='Margin_Pct', color_continuous_scale='Greens',
            title="Top 10 Products by Profit ($)", labels={'Total_Profit': 'Gross Profit ($)'}
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        fig_pie = px.pie(prod_summary.head(7), values='Total_Profit', names='Product Name', title='Top 7 Product Profit Share', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.dataframe(prod_summary.style.format({
        'Total_Sales': '${:,.2f}', 'Total_Profit': '${:,.2f}', 'Cost': '${:,.2f}', 'Total_Units': '{:,}', 'Margin_Pct': '{:.2f}%'
    }), use_container_width=True)

# Module 2: Division & Regional Performance
with tab2:
    st.header("Division & Regional Performance")
    c1, c2 = st.columns(2)
    with c1:
        div_perf = filtered_df.groupby('Division').agg(Sales=('Sales', 'sum'), Gross_Profit=('Gross Profit', 'sum')).reset_index()
        fig_div = px.bar(div_perf, x='Division', y=['Sales', 'Gross_Profit'], barmode='group', title="Revenue vs Profit by Division")
        st.plotly_chart(fig_div, use_container_width=True)
    with c2:
        reg_perf = filtered_df.groupby('Region').agg(Sales=('Sales', 'sum'), Gross_Profit=('Gross Profit', 'sum'), Avg_Margin=('Gross Margin %', 'mean')).reset_index()
        fig_reg = px.bar(reg_perf, x='Region', y='Gross_Profit', color='Avg_Margin', title="Regional Profit & Margin %", color_continuous_scale='Blues')
        st.plotly_chart(fig_reg, use_container_width=True)

# Module 3: Cost Structure Diagnostics
with tab3:
    st.header("Cost Structure Diagnostics & Risk Flags")
    fig_scatter = px.scatter(filtered_df, x='Sales', y='Gross Profit', color='Division', size='Units', hover_data=['Product Name'], title="Sales vs Gross Profit Scatter Plot")
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.subheader("🚨 Low Margin Risk Products (< 55% Margin)")
    low_margin = prod_summary[prod_summary['Margin_Pct'] < 55].sort_values(by='Margin_Pct')
    if not low_margin.empty:
        st.dataframe(low_margin.style.format({'Total_Sales': '${:,.2f}', 'Total_Profit': '${:,.2f}', 'Margin_Pct': '{:.2f}%'}), use_container_width=True)
    else:
        st.success("No products fall below the 55% margin risk threshold.")

# Module 4: Pareto Analysis
with tab4:
    st.header("Profit Concentration (Pareto Analysis)")
    pareto_df = prod_summary.sort_values(by='Total_Profit', ascending=False).copy()
    pareto_df['Cum_Profit'] = pareto_df['Total_Profit'].cumsum()
    pareto_df['Cum_Profit_Pct'] = (pareto_df['Cum_Profit'] / pareto_df['Total_Profit'].sum()) * 100
    
    # 1. Create subplots with secondary Y-axis enabled
fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])

# 2. Add Bar trace for Profit (Primary Y-axis)
fig_pareto.add_trace(
    go.Bar(x=pareto_df['Product Name'], y=pareto_df['Profit'], name='Profit'),
    secondary_y=False
)

# 3. Add Line trace for Cumulative Profit % (Secondary Y-axis)
fig_pareto.add_trace(
    go.Scatter(
        x=pareto_df['Product Name'], 
        y=pareto_df['Cum_Profit_Pct'], 
        name='Cumulative Profit %', 
        line=dict(color='red', width=3)
    ),
    secondary_y=True
)

# 4. Update axis labels
fig_pareto.update_yaxes(title_text="Total Profit ($)", secondary_y=False)
fig_pareto.update_yaxes(title_text="Cumulative Profit (%)", range=[0, 105], secondary_y=True)
fig_pareto.update_layout(title="Pareto Chart: Cumulative Profit Contribution")
    fig_pareto.update_layout(
        title='Pareto Analysis: Cumulative Gross Profit',
        yaxis=dict(title='Gross Profit ($)'),
        yaxis2=dict(title='Cumulative Profit %', overlaying='y', side='right', range=[0, 105]),
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

# Module 5: Executive Recommendations
with tab5:
    st.header("Executive Summary & Action Plan")
    st.markdown('''
    ### Key Findings
    * **Chocolate Core:** The Chocolate division delivers over **90% of total company profit**, serving as the primary financial engine.
    * **Margin Variations:** Key SKUs generate consistent gross margins above **60%**, but individual low-volume items require repricing.
    * **Optimization Goal:** Focus supply chain resources on top profit-generating lines while reviewing pricing structures for secondary product categories.
    ''')
