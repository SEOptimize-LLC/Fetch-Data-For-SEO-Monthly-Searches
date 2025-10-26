import streamlit as st
import pandas as pd
import requests
import base64
import json
from io import BytesIO
import time

# Page configuration
st.set_page_config(
    page_title="SEO Keyword Research Tool",
    page_icon="🔍",
    layout="wide"
)

# Title and description
st.title("🔍 SEO Keyword Research Tool")
st.markdown("Upload a CSV or Excel file with keywords to fetch monthly search volume and keyword difficulty from DataForSEO")

# Sidebar for API configuration
st.sidebar.header("⚙️ Configuration")
st.sidebar.markdown("""
### DataForSEO API Credentials
Configure your credentials in Streamlit Cloud:
1. Go to your app settings
2. Navigate to **Secrets** tab
3. Add your credentials:
```toml
[dataforseo]
login = "your-email@example.com"
password = "your-password"
```
""")

# Check if credentials are configured
def get_credentials():
    """Retrieve DataForSEO credentials from Streamlit secrets"""
    try:
        login = st.secrets["dataforseo"]["login"]
        password = st.secrets["dataforseo"]["password"]
        return login, password
    except Exception as e:
        st.error("⚠️ DataForSEO credentials not configured. Please add them in Streamlit Secrets.")
        st.stop()
        return None, None

# API configuration
st.sidebar.subheader("API Settings")
location_code = st.sidebar.number_input(
    "Location Code",
    value=2840,
    help="Location code for the search (default: 2840 for United States)"
)
language_code = st.sidebar.text_input(
    "Language Code",
    value="en",
    help="Language code (e.g., 'en' for English)"
)

# Main content
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader(
    "📁 Upload your keyword file (CSV or Excel)",
    type=["csv", "xlsx", "xls"],
    help="File should contain a column with keywords"
)

def read_file(file):
    """Read CSV or Excel file and return dataframe"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def call_dataforseo_api(keywords, login, password, location_code, language_code):
    """
    Call DataForSEO API to fetch search volume and keyword difficulty
    Endpoint: POST https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live
    """
    # Prepare authentication
    cred = f"{login}:{password}"
    encoded_cred = base64.b64encode(cred.encode('ascii')).decode('ascii')

    headers = {
        'Authorization': f'Basic {encoded_cred}',
        'Content-Type': 'application/json'
    }

    # Prepare request body
    post_data = [{
        "location_code": location_code,
        "language_code": language_code,
        "keywords": keywords
    }]

    # API endpoint
    url = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"

    try:
        response = requests.post(url, headers=headers, json=post_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        if hasattr(e.response, 'text'):
            st.error(f"Response: {e.response.text}")
        return None

def process_api_response(response_data):
    """Process API response and convert to dataframe"""
    if not response_data or 'tasks' not in response_data:
        return None

    results = []
    for task in response_data.get('tasks', []):
        if task.get('status_code') == 20000:  # Success
            for item in task.get('result', []):
                results.append({
                    'Keyword': item.get('keyword'),
                    'Search Volume': item.get('search_volume'),
                    'Competition': item.get('competition'),
                    'Competition Index': item.get('competition_index'),
                    'Low Top of Page Bid': item.get('low_top_of_page_bid_micros', 0) / 1000000,
                    'High Top of Page Bid': item.get('high_top_of_page_bid_micros', 0) / 1000000,
                    'CPC': item.get('cpc'),
                    'Monthly Searches': json.dumps(item.get('monthly_searches', []))
                })
        else:
            st.warning(f"Task failed with status code: {task.get('status_code')}")
            st.warning(f"Message: {task.get('status_message')}")

    if results:
        return pd.DataFrame(results)
    return None

def convert_df_to_excel(df):
    """Convert dataframe to Excel file for download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Keywords')

        # Auto-adjust column width
        worksheet = writer.sheets['Keywords']
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(max_len, 50))

    return output.getvalue()

# Main processing logic
if uploaded_file is not None:
    # Read the uploaded file
    df = read_file(uploaded_file)

    if df is not None:
        st.success(f"✅ File uploaded successfully! Found {len(df)} rows")

        # Display the uploaded data
        st.subheader("📊 Uploaded Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

        # Column selection
        st.subheader("🎯 Select Keyword Column")
        keyword_column = st.selectbox(
            "Choose the column containing keywords:",
            options=df.columns.tolist()
        )

        # Show preview of selected keywords
        keywords_list = df[keyword_column].dropna().astype(str).tolist()
        st.info(f"Found {len(keywords_list)} keywords")

        with st.expander("Preview keywords (first 10)"):
            st.write(keywords_list[:10])

        # Process button
        if st.button("🚀 Fetch SEO Data", type="primary"):
            # Get credentials
            login, password = get_credentials()

            if login and password:
                # Split keywords into batches (DataForSEO has limits)
                batch_size = 100  # Adjust based on API limits
                total_keywords = len(keywords_list)
                num_batches = (total_keywords + batch_size - 1) // batch_size

                st.info(f"Processing {total_keywords} keywords in {num_batches} batch(es)...")

                all_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(0, total_keywords, batch_size):
                    batch = keywords_list[i:i + batch_size]
                    batch_num = i // batch_size + 1

                    status_text.text(f"Processing batch {batch_num}/{num_batches}...")

                    # Call API
                    response_data = call_dataforseo_api(
                        batch,
                        login,
                        password,
                        location_code,
                        language_code
                    )

                    if response_data:
                        batch_df = process_api_response(response_data)
                        if batch_df is not None:
                            all_results.append(batch_df)

                    # Update progress
                    progress = min((i + batch_size) / total_keywords, 1.0)
                    progress_bar.progress(progress)

                    # Rate limiting - be nice to the API
                    if i + batch_size < total_keywords:
                        time.sleep(1)

                progress_bar.progress(1.0)
                status_text.text("Processing complete!")

                # Combine all results
                if all_results:
                    final_df = pd.concat(all_results, ignore_index=True)

                    st.success(f"✅ Successfully fetched data for {len(final_df)} keywords!")

                    # Display results
                    st.subheader("📈 Results")
                    st.dataframe(final_df, use_container_width=True)

                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Keywords", len(final_df))
                    with col2:
                        avg_volume = final_df['Search Volume'].mean()
                        st.metric("Avg Search Volume", f"{avg_volume:,.0f}")
                    with col3:
                        total_volume = final_df['Search Volume'].sum()
                        st.metric("Total Search Volume", f"{total_volume:,.0f}")
                    with col4:
                        avg_cpc = final_df['CPC'].mean()
                        st.metric("Avg CPC", f"${avg_cpc:.2f}")

                    # Download buttons
                    st.subheader("💾 Download Results")

                    col1, col2 = st.columns(2)

                    with col1:
                        # CSV download
                        csv = final_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv,
                            file_name="seo_keywords_results.csv",
                            mime="text/csv"
                        )

                    with col2:
                        # Excel download
                        excel_data = convert_df_to_excel(final_df)
                        st.download_button(
                            label="📥 Download as Excel",
                            data=excel_data,
                            file_name="seo_keywords_results.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("No results returned from the API. Please check your credentials and try again.")

else:
    # Instructions when no file is uploaded
    st.info("👆 Upload a file to get started")

    st.markdown("""
    ### 📝 Instructions:

    1. **Prepare your file**: Create a CSV or Excel file with a column containing your keywords
    2. **Configure API credentials**: Add your DataForSEO credentials in Streamlit Secrets
    3. **Upload the file**: Use the file uploader above
    4. **Select keyword column**: Choose which column contains your keywords
    5. **Fetch data**: Click the button to retrieve SEO metrics
    6. **Download results**: Export your results as CSV or Excel

    ### 📊 What data you'll get:
    - **Search Volume**: Monthly search volume
    - **Competition**: Competition level (LOW, MEDIUM, HIGH)
    - **Competition Index**: Numerical competition index (0-100)
    - **CPC**: Cost per click
    - **Top of Page Bid**: Low and high bid ranges
    - **Monthly Searches**: Historical search data

    ### 🔗 DataForSEO API Documentation:
    [View API Documentation](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Powered by DataForSEO API | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
