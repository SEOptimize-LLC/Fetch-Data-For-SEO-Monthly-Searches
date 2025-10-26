import streamlit as st
import pandas as pd
import requests
import base64
import json
from io import BytesIO
import time
import re

# Page configuration
st.set_page_config(
    page_title="SEO Keyword Research Tool",
    page_icon="🔍",
    layout="wide"
)

# Title and description
st.title("🔍 SEO Keyword Research Tool")
st.markdown("Upload a CSV or Excel file with keywords to fetch monthly search volume and competition data from DataForSEO")

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

def validate_and_clean_keywords(keywords_list, max_words=10):
    """
    Validate and clean keywords before sending to DataForSEO API
    - Remove invalid characters (?, !, *, etc.)
    - Skip keywords with too many words
    - Track skipped keywords and reasons
    """
    valid_keywords = []
    skipped_keywords = []

    for keyword in keywords_list:
        original_keyword = keyword

        # Strip whitespace
        keyword = keyword.strip()

        # Skip empty keywords
        if not keyword:
            skipped_keywords.append({
                'keyword': original_keyword,
                'reason': 'Empty keyword'
            })
            continue

        # Remove invalid characters (keep letters, numbers, spaces, hyphens, and underscores)
        cleaned_keyword = re.sub(r'[^\w\s-]', '', keyword)

        # Remove extra spaces
        cleaned_keyword = ' '.join(cleaned_keyword.split())

        # Check if keyword was heavily modified (lost all content)
        if not cleaned_keyword:
            skipped_keywords.append({
                'keyword': original_keyword,
                'reason': 'Only invalid characters'
            })
            continue

        # Check word count
        word_count = len(cleaned_keyword.split())
        if word_count > max_words:
            skipped_keywords.append({
                'keyword': original_keyword,
                'reason': f'Too many words ({word_count} words, max {max_words})'
            })
            continue

        # Check if significantly different from original (warn user)
        if cleaned_keyword.lower() != original_keyword.lower():
            # Just track this for info, but still use the cleaned version
            valid_keywords.append({
                'original': original_keyword,
                'cleaned': cleaned_keyword,
                'modified': True
            })
        else:
            valid_keywords.append({
                'original': original_keyword,
                'cleaned': cleaned_keyword,
                'modified': False
            })

    return valid_keywords, skipped_keywords

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
    """Process API response and convert to dataframe - returns only Keyword, Search Volume, and Competition"""
    if not response_data or 'tasks' not in response_data:
        return None

    results = []
    for task in response_data.get('tasks', []):
        if task.get('status_code') == 20000:  # Success
            for item in task.get('result', []):
                # Only include the 3 requested fields
                results.append({
                    'Keyword': item.get('keyword'),
                    'Search Volume': item.get('search_volume', 0),
                    'Competition': item.get('competition', 'N/A')
                })
        else:
            # Only show warning if it's not the specific keyword validation errors we're already handling
            status_code = task.get('status_code')
            if status_code not in [40501]:  # Skip validation errors as we handle them
                st.warning(f"Task failed with status code: {status_code}")
                st.warning(f"Message: {task.get('status_message')}")

    if results:
        return pd.DataFrame(results)
    return None

def create_summary_by_page(df):
    """Create summary dataframe grouped by page/URL"""
    # Check if 'page' column exists
    if 'page' not in df.columns:
        return None

    # Group by page and calculate aggregations
    summary = df.groupby('page').agg({
        'Monthly Searches': 'sum',
        'Clicks': 'sum',
        'Impressions': 'sum',
        'Avg. Position': 'mean'
    }).reset_index()

    # Calculate CTR % (Clicks / Impressions * 100)
    summary['CTR %'] = (summary['Clicks'] / summary['Impressions'] * 100).round(2)

    # Rename columns for clarity
    summary.columns = ['Page', 'Total Monthly Searches', 'Total Clicks', 'Total Impressions', 'Avg. Position', 'CTR %']

    # Round average position
    summary['Avg. Position'] = summary['Avg. Position'].round(1)

    # Sort by Total Monthly Searches descending
    summary = summary.sort_values('Total Monthly Searches', ascending=False)

    return summary

def convert_df_to_excel(df, summary_df=None):
    """Convert dataframe to Excel file with multiple sheets"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write main data sheet
        df.to_excel(writer, index=False, sheet_name='All Keywords')

        # Auto-adjust column width for main sheet
        worksheet = writer.sheets['All Keywords']
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(max_len, 50))

        # Write summary sheet if provided
        if summary_df is not None:
            summary_df.to_excel(writer, index=False, sheet_name='Summary by Page')

            # Auto-adjust column width for summary sheet
            summary_worksheet = writer.sheets['Summary by Page']
            for i, col in enumerate(summary_df.columns):
                max_len = max(summary_df[col].astype(str).apply(len).max(), len(col)) + 2
                summary_worksheet.set_column(i, i, min(max_len, 50))

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
                # Validate and clean keywords first
                st.info("🔍 Validating and cleaning keywords...")
                valid_keywords, skipped_keywords = validate_and_clean_keywords(keywords_list)

                # Show validation results
                if skipped_keywords:
                    st.warning(f"⚠️ Skipped {len(skipped_keywords)} invalid keywords")
                    with st.expander("View skipped keywords"):
                        skipped_df = pd.DataFrame(skipped_keywords)
                        st.dataframe(skipped_df, use_container_width=True)

                if not valid_keywords:
                    st.error("❌ No valid keywords to process. Please check your file.")
                    st.stop()

                # Show cleaned keywords info
                modified_keywords = [kw for kw in valid_keywords if kw['modified']]
                if modified_keywords:
                    st.info(f"ℹ️ Cleaned {len(modified_keywords)} keywords (removed special characters)")
                    with st.expander("View modified keywords"):
                        modified_df = pd.DataFrame(modified_keywords)
                        st.dataframe(modified_df[['original', 'cleaned']], use_container_width=True)

                # Extract cleaned keywords for API call
                cleaned_keywords_list = [kw['cleaned'] for kw in valid_keywords]

                # Split keywords into batches (DataForSEO allows up to 1000 keywords per request)
                batch_size = 1000  # DataForSEO limit: 1000 keywords per request
                total_keywords = len(cleaned_keywords_list)
                num_batches = (total_keywords + batch_size - 1) // batch_size

                if num_batches == 1:
                    st.info(f"Processing {total_keywords} keywords in a single API request...")
                else:
                    st.info(f"Processing {total_keywords} keywords in {num_batches} API requests (batches of {batch_size})...")

                all_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(0, total_keywords, batch_size):
                    batch = cleaned_keywords_list[i:i + batch_size]
                    batch_num = i // batch_size + 1

                    if num_batches == 1:
                        status_text.text(f"Making API request for {len(batch)} keywords...")
                    else:
                        status_text.text(f"Making API request {batch_num}/{num_batches} ({len(batch)} keywords)...")

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
                    api_results_df = pd.concat(all_results, ignore_index=True)

                    st.success(f"✅ Successfully fetched data for {len(api_results_df)} keywords!")

                    # Create mapping from original to cleaned keywords
                    keyword_mapping = pd.DataFrame([{
                        'original': kw['original'],
                        'cleaned': kw['cleaned']
                    } for kw in valid_keywords])

                    # Merge API results with mapping
                    api_results_df = api_results_df.merge(
                        keyword_mapping,
                        left_on='Keyword',
                        right_on='cleaned',
                        how='left'
                    )

                    # Create a copy of original dataframe
                    merged_df = df.copy()

                    # Rename the keyword column to 'query' if it's not already named that
                    if keyword_column != 'query':
                        merged_df = merged_df.rename(columns={keyword_column: 'query'})

                    # Merge API results with original data based on query
                    merged_df = merged_df.merge(
                        api_results_df[['original', 'Search Volume', 'Competition']],
                        left_on='query',
                        right_on='original',
                        how='left'
                    )

                    # Drop the extra 'original' column from merge
                    if 'original' in merged_df.columns:
                        merged_df = merged_df.drop(columns=['original'])

                    # Rename API columns to match desired output format
                    merged_df = merged_df.rename(columns={
                        'Search Volume': 'Monthly Searches',
                        'Competition': 'Keyword Difficulty'
                    })

                    # Reorder columns to match desired format
                    # Expected: page, query, Monthly Searches, Keyword Difficulty, Clicks, Impressions, CTR %, Avg. Position
                    desired_order = []
                    if 'page' in merged_df.columns:
                        desired_order.append('page')
                    if 'query' in merged_df.columns:
                        desired_order.append('query')

                    # Add API columns
                    if 'Monthly Searches' in merged_df.columns:
                        desired_order.append('Monthly Searches')
                    if 'Keyword Difficulty' in merged_df.columns:
                        desired_order.append('Keyword Difficulty')

                    # Add remaining columns in order
                    for col in ['Clicks', 'Impressions', 'CTR %', 'Avg. Position']:
                        if col in merged_df.columns:
                            desired_order.append(col)

                    # Add any remaining columns not in the list
                    for col in merged_df.columns:
                        if col not in desired_order:
                            desired_order.append(col)

                    merged_df = merged_df[desired_order]

                    # Create summary by page (if page column exists)
                    summary_df = None
                    if 'page' in merged_df.columns and 'Clicks' in merged_df.columns and 'Impressions' in merged_df.columns:
                        summary_df = create_summary_by_page(merged_df)

                    # Display results
                    st.subheader("📈 Results")
                    st.dataframe(merged_df, use_container_width=True)

                    # Statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Keywords", len(merged_df))
                    with col2:
                        avg_volume = merged_df['Monthly Searches'].mean()
                        st.metric("Avg Monthly Searches", f"{avg_volume:,.0f}")
                    with col3:
                        total_volume = merged_df['Monthly Searches'].sum()
                        st.metric("Total Monthly Searches", f"{total_volume:,.0f}")

                    # Show summary if available
                    if summary_df is not None:
                        st.subheader("📊 Summary by Page")
                        st.dataframe(summary_df, use_container_width=True)

                    # Download buttons
                    st.subheader("💾 Download Results")

                    col1, col2 = st.columns(2)

                    with col1:
                        # CSV download (main data only)
                        csv = merged_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv,
                            file_name="seo_keywords_results.csv",
                            mime="text/csv"
                        )

                    with col2:
                        # Excel download (with both sheets)
                        excel_data = convert_df_to_excel(merged_df, summary_df)
                        st.download_button(
                            label="📥 Download as Excel (with Summary)",
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

    1. **Prepare your file**: Upload a CSV or Excel file from Google Search Console with these columns:
       - `page` - Landing page URL
       - `query` - Search keyword
       - `Clicks` - Number of clicks
       - `Impressions` - Number of impressions
       - `CTR %` - Click-through rate
       - `Avg. Position` - Average position in search results

    2. **Configure API credentials**: Add your DataForSEO credentials in Streamlit Secrets

    3. **Upload the file**: Use the file uploader above

    4. **Select keyword column**: Choose the column containing your keywords (usually "query")

    5. **Fetch data**: Click the button to retrieve SEO metrics

    6. **Download results**: Export your enriched data with two sheets:
       - **All Keywords**: Original data + Monthly Searches + Keyword Difficulty
       - **Summary by Page**: Aggregated metrics per landing page

    ### 📊 Output Data:

    **Sheet 1 - All Keywords:**
    - All original columns from your file
    - **Monthly Searches**: Search volume from DataForSEO API
    - **Keyword Difficulty**: Competition level (LOW, MEDIUM, HIGH)

    **Sheet 2 - Summary by Page:**
    - **Page**: Landing page URL
    - **Total Monthly Searches**: Sum of all keywords for this page
    - **Total Clicks**: Sum of all clicks
    - **Total Impressions**: Sum of all impressions
    - **Avg. Position**: Average ranking position
    - **CTR %**: Calculated from clicks/impressions

    ### ⚠️ Keyword Requirements:
    - Maximum 10 words per keyword
    - Special characters (?, !, *, etc.) will be automatically removed
    - Keywords with invalid format will be skipped with a warning

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
