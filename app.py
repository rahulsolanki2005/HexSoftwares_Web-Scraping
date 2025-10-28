import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Laptop Web Scraper",
    page_icon="💻",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Functions
@st.cache_data(ttl=3600)
def scrape_laptops(url):
    """Scrape laptop data from the website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        laptops = []
        
        # Find all laptop cards
        products = soup.find_all('div', class_='card-body')
        
        for product in products:
            try:
                # Extract product name
                name_tag = product.find('a', class_='title')
                name = name_tag.get('title', '') if name_tag else 'N/A'
                
                # Extract price
                price_tag = product.find('h4', class_='price')
                price_text = price_tag.text.strip() if price_tag else '$0'
                price = float(price_text.replace('$', '').replace(',', ''))
                
                # Extract description
                desc_tag = product.find('p', class_='description')
                description = desc_tag.text.strip() if desc_tag else 'N/A'
                
                # Extract rating
                rating_tag = product.find('p', {'data-rating': True})
                rating = int(rating_tag['data-rating']) if rating_tag else 0
                
                # Extract number of reviews
                reviews_tag = product.find('p', class_='review-count')
                reviews = reviews_tag.text.strip() if reviews_tag else '0 reviews'
                review_count = int(reviews.split()[0]) if reviews else 0
                
                laptops.append({
                    'Name': name,
                    'Price': price,
                    'Description': description,
                    'Rating': rating,
                    'Reviews': review_count
                })
            except Exception as e:
                continue
        
        return pd.DataFrame(laptops)
    
    except Exception as e:
        st.error(f"Error scraping data: {str(e)}")
        return pd.DataFrame()

def display_metrics(df):
    """Display key metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Products", len(df))
    
    with col2:
        avg_price = df['Price'].mean()
        st.metric("Average Price", f"${avg_price:.2f}")
    
    with col3:
        avg_rating = df['Rating'].mean()
        st.metric("Average Rating", f"{avg_rating:.1f} ⭐")
    
    with col4:
        total_reviews = df['Reviews'].sum()
        st.metric("Total Reviews", f"{total_reviews:,}")

def create_price_distribution(df):
    """Create price distribution chart"""
    fig = px.histogram(
        df, 
        x='Price', 
        nbins=20,
        title='Price Distribution',
        labels={'Price': 'Price ($)', 'count': 'Number of Products'},
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(showlegend=False)
    return fig

def create_rating_distribution(df):
    """Create rating distribution chart"""
    rating_counts = df['Rating'].value_counts().sort_index()
    fig = go.Figure(data=[
        go.Bar(
            x=rating_counts.index,
            y=rating_counts.values,
            marker_color='#ff7f0e',
            text=rating_counts.values,
            textposition='auto'
        )
    ])
    fig.update_layout(
        title='Rating Distribution',
        xaxis_title='Rating (Stars)',
        yaxis_title='Number of Products',
        showlegend=False
    )
    return fig

def create_price_vs_rating(df):
    """Create scatter plot of price vs rating"""
    fig = px.scatter(
        df,
        x='Rating',
        y='Price',
        size='Reviews',
        hover_data=['Name'],
        title='Price vs Rating',
        labels={'Rating': 'Rating (Stars)', 'Price': 'Price ($)'},
        color='Rating',
        color_continuous_scale='Viridis'
    )
    return fig

# Main App
def main():
    st.markdown('<p class="main-header">💻 Laptop Web Scraper Dashboard</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    url = st.sidebar.text_input(
        "Website URL",
        "https://webscraper.io/test-sites/e-commerce/static/computers/laptops"  
    )
    
    # Scrape button
    if st.sidebar.button("🔄 Scrape Data", type="primary"):
        with st.spinner("Scraping data... Please wait..."):
            st.session_state['df'] = scrape_laptops(url)
            st.session_state['scrape_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if data exists
    if 'df' not in st.session_state or st.session_state['df'].empty:
        st.info("👈🏻 Click 'Scrape Data' button in the sidebar to start scraping!")
        return
    
    df = st.session_state['df']
    
    # Display last scrape time
    st.sidebar.success(f"✅ Last scraped: {st.session_state.get('scrape_time', 'N/A')}")
    st.sidebar.metric("Products Found", len(df))
    
    # Filters
    st.sidebar.header("🔍 Filters")
    
    price_range = st.sidebar.slider(
        "Price Range ($)",
        float(df['Price'].min()),
        float(df['Price'].max()),
        (float(df['Price'].min()), float(df['Price'].max()))
    )
    
    rating_filter = st.sidebar.multiselect(
        "Rating",
        options=sorted(df['Rating'].unique()),
        default=sorted(df['Rating'].unique())
    )
    
    # Apply filters
    filtered_df = df[
        (df['Price'] >= price_range[0]) &
        (df['Price'] <= price_range[1]) &
        (df['Rating'].isin(rating_filter))
    ]
    
    # Display metrics
    st.header("📊 Key Metrics")
    display_metrics(filtered_df)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Data Table", 
        "📈 Visualizations", 
        "⭐ Top Rated", 
        "💰 Price Analysis",
        "📥 Export"
    ])
    
    with tab1:
        st.header("Laptop Data")
        
        # Sorting options
        col1, col2 = st.columns([1, 3])
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ["Name", "Price", "Rating", "Reviews"]
            )
        with col2:
            sort_order = st.radio(
                "Order",
                ["Ascending", "Descending"],
                horizontal=True
            )
        
        sorted_df = filtered_df.sort_values(
            by=sort_by,
            ascending=(sort_order == "Ascending")
        )
        
        st.dataframe(
            sorted_df,
            use_container_width=True,
            hide_index=True
        )
    
    with tab2:
        st.header("Data Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_price_distribution(filtered_df),
                use_container_width=True
            )
        
        with col2:
            st.plotly_chart(
                create_rating_distribution(filtered_df),
                use_container_width=True
            )
        
        st.plotly_chart(
            create_price_vs_rating(filtered_df),
            use_container_width=True
        )
    
    with tab3:
        st.header("⭐ Top Rated Laptops")
        
        top_n = st.slider("Select number of top products", 5, 20, 10)
        
        top_rated = filtered_df.nlargest(top_n, 'Rating')
        
        for idx, row in top_rated.iterrows():
            with st.expander(f"⭐ {row['Rating']} - {row['Name']}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {row['Description']}")
                    st.write(f"**Reviews:** {row['Reviews']}")
                with col2:
                    st.metric("Price", f"${row['Price']:.2f}")
                    st.metric("Rating", f"{row['Rating']} ⭐")
    
    with tab4:
        st.header("💰 Price Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Price Statistics")
            stats_df = pd.DataFrame({
                'Metric': ['Minimum', 'Maximum', 'Average', 'Median', 'Std Dev'],
                'Value': [
                    f"${filtered_df['Price'].min():.2f}",
                    f"${filtered_df['Price'].max():.2f}",
                    f"${filtered_df['Price'].mean():.2f}",
                    f"${filtered_df['Price'].median():.2f}",
                    f"${filtered_df['Price'].std():.2f}"
                ]
            })
            st.dataframe(stats_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("Most Expensive Laptops")
            top_expensive = filtered_df.nlargest(5, 'Price')[['Name', 'Price', 'Rating']]
            st.dataframe(top_expensive, hide_index=True, use_container_width=True)
        
        st.subheader("Best Value (High Rating, Low Price)")
        filtered_df['Value_Score'] = filtered_df['Rating'] / (filtered_df['Price'] / 100)
        best_value = filtered_df.nlargest(10, 'Value_Score')[['Name', 'Price', 'Rating', 'Reviews']]
        st.dataframe(best_value, hide_index=True, use_container_width=True)
    
    with tab5:
        st.header("📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Export as CSV")
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"laptops_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col2:
            st.subheader("Export as JSON")
            json_data = filtered_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"laptops_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                type="primary"
            )
        
        st.info(f"Total records to export: {len(filtered_df)}")

if __name__ == "__main__":
    main()