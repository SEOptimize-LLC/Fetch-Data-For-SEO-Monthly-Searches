import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO
import time
import re

# Constants - Fixed for US English only
LOCATION_CODE = 2840  # United States
LANGUAGE_CODE = "en"  # English
BATCH_SIZE = 1000  # DataForSEO limit: 1000 keywords per request
GOOGLE_ADS_API_ENDPOINT = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"

# Page configuration
st.set_page_config(
    page_title="DataForSEO Keyword Search Volume",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for results persistence
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Title and description
st.title("📊 DataForSEO Keyword Search Volume Tool")
st.markdown("Upload a file with keywords to fetch US search volume and keyword difficulty from Google Ads data")

# Sidebar for API configuration
st.sidebar.header("Configuration")

# Check if credentials are configured
credentials_configured = False
try:
    if st.secrets.get("dataforseo", {}).get("login") and st.secrets.get("dataforseo", {}).get("password"):
        credentials_configured = True
except Exception:
    pass

if credentials_configured:
    st.sidebar.success("API Credentials Configured")
else:
    st.sidebar.warning("API Credentials Not Configured")


st.sidebar.markdown("---")
st.sidebar.markdown("""
### API Settings (Fixed)
- **Location:** United States (2840)
- **Language:** English (en)
- **Batch Size:** 1,000 keywords per request
- **Data Source:** Google Ads API
""")


def get_credentials():
    """Retrieve DataForSEO credentials from Streamlit secrets"""
    try:
        login = st.secrets["dataforseo"]["login"]
        password = st.secrets["dataforseo"]["password"]
        return login, password
    except Exception:
        st.error("DataForSEO credentials not configured. Please add them in Streamlit Secrets.")
        st.stop()
        return None, None


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
    - Remove duplicate keywords (case-insensitive)
    - Remove invalid characters
    - Skip keywords with too many words
    - Track skipped keywords and reasons
    """
    valid_keywords = []
    skipped_keywords = []
    duplicate_keywords = []
    seen_keywords = set()  # Track unique keywords (lowercase for case-insensitive comparison)

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

        # Remove invalid characters (keep letters, numbers, spaces, hyphens, underscores)
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

        # Check for duplicates (case-insensitive)
        cleaned_lower = cleaned_keyword.lower()
        if cleaned_lower in seen_keywords:
            duplicate_keywords.append({
                'keyword': original_keyword,
                'reason': 'Duplicate keyword'
            })
            continue

        # Mark as seen and add to valid list
        seen_keywords.add(cleaned_lower)
        valid_keywords.append({
            'original': original_keyword,
            'cleaned': cleaned_keyword,
            'modified': cleaned_keyword.lower() != original_keyword.lower()
        })

    return valid_keywords, skipped_keywords, duplicate_keywords


def call_google_ads_api(keywords, login, password):
    """
    Call DataForSEO Google Ads Search Volume API
    Returns search volume for US location and competition data
    """
    cred = f"{login}:{password}"
    encoded_cred = base64.b64encode(cred.encode('ascii')).decode('ascii')

    headers = {
        'Authorization': f'Basic {encoded_cred}',
        'Content-Type': 'application/json'
    }

    post_data = [{
        "keywords": keywords,
        "location_code": LOCATION_CODE,
        "language_code": LANGUAGE_CODE
    }]

    try:
        response = requests.post(GOOGLE_ADS_API_ENDPOINT, headers=headers, json=post_data)
        response.raise_for_status()
        result = response.json()

        # Debug: Show API response status
        if result.get('status_code') != 20000:
            st.error(f"API Status: {result.get('status_code')} - {result.get('status_message')}")

        return result
    except requests.exceptions.RequestException as e:
        st.error(f"Google Ads API Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response: {e.response.text}")
        return None


def get_latest_monthly_search_volume(monthly_searches):
    """
    Extract the most recent month's search volume from monthly_searches array.
    Returns the search volume for the last available month (most recent 30 days of data).
    """
    if not monthly_searches:
        return 0

    # Sort by year and month descending to get the most recent
    sorted_months = sorted(
        monthly_searches,
        key=lambda x: (x.get('year', 0), x.get('month', 0)),
        reverse=True
    )

    if sorted_months:
        return sorted_months[0].get('search_volume', 0) or 0
    return 0


def process_google_ads_response(response_data):
    """
    Process Google Ads API response to extract:
    - Keyword
    - Last month's search volume (US)
    - Competition level (keyword difficulty)
    """
    if not response_data:
        st.error("No response data received from API")
        return None

    if 'tasks' not in response_data:
        st.error(f"No 'tasks' in response. Response keys: {list(response_data.keys())}")
        st.error(f"Full response: {response_data}")
        return None

    results = []
    for task in response_data.get('tasks', []):
        task_status = task.get('status_code')
        if task_status == 20000:  # Success
            task_result = task.get('result')
            if not task_result:
                st.warning("Task succeeded but result is empty")
                continue

            for result_item in task_result:
                items = result_item.get('items', [])
                if not items:
                    st.warning("Result item has no items")
                    continue

                for item in items:
                    keyword = item.get('keyword', '')

                    # Get the most recent month's search volume
                    monthly_searches = item.get('monthly_searches', [])
                    last_month_volume = get_latest_monthly_search_volume(monthly_searches)

                    # Get competition level (keyword difficulty)
                    competition = item.get('competition', None)
                    if not competition:
                        competition = 'N/A'

                    results.append({
                        'Keyword': keyword,
                        'US Search Volume (Last Month)': last_month_volume,
                        'Keyword Difficulty': competition
                    })
        else:
            st.error(f"Task failed with status code: {task_status}")
            st.error(f"Message: {task.get('status_message')}")

    if results:
        return pd.DataFrame(results)

    st.warning("No results extracted from API response")
    return None


def convert_df_to_excel(df):
    """Convert dataframe to Excel file"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Keywords')

        # Auto-adjust column width
        worksheet = writer.sheets['Keywords']
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(max_len, 50))

    return output.getvalue()


# Main content
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your keyword file (CSV or Excel)",
    type=["csv", "xlsx", "xls"],
    help="File should contain a column with keywords"
)

# Main processing logic
if uploaded_file is not None:
    df = read_file(uploaded_file)

    if df is not None:
        st.success(f"File uploaded successfully! Found {len(df)} rows")

        # Display the uploaded data
        st.subheader("Uploaded Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

        # Column selection
        st.subheader("Select Keyword Column")
        keyword_column = st.selectbox(
            "Choose the column containing keywords:",
            options=df.columns.tolist()
        )

        # Show preview of selected keywords
        keywords_list = df[keyword_column].dropna().astype(str).tolist()

        # Validate and analyze keywords immediately
        valid_keywords, skipped_keywords, duplicate_keywords = validate_and_clean_keywords(keywords_list)
        cleaned_keywords_list = [kw['cleaned'] for kw in valid_keywords]
        total_keywords = len(cleaned_keywords_list)
        num_batches = (total_keywords + BATCH_SIZE - 1) // BATCH_SIZE

        # Show keyword analysis summary
        st.subheader("Keyword Analysis")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total in File", f"{len(keywords_list):,}")
        with col2:
            st.metric("Duplicates Removed", f"{len(duplicate_keywords):,}")
        with col3:
            st.metric("Invalid/Skipped", f"{len(skipped_keywords):,}")
        with col4:
            st.metric("Unique Keywords", f"{total_keywords:,}")

        # Show details in expanders
        if duplicate_keywords:
            with st.expander(f"View {len(duplicate_keywords):,} duplicate keywords"):
                dup_df = pd.DataFrame(duplicate_keywords)
                st.dataframe(dup_df, use_container_width=True)

        if skipped_keywords:
            with st.expander(f"View {len(skipped_keywords):,} skipped keywords"):
                skipped_df = pd.DataFrame(skipped_keywords)
                st.dataframe(skipped_df, use_container_width=True)

        modified_keywords = [kw for kw in valid_keywords if kw['modified']]
        if modified_keywords:
            with st.expander(f"View {len(modified_keywords):,} cleaned keywords"):
                modified_df = pd.DataFrame(modified_keywords)
                st.dataframe(modified_df[['original', 'cleaned']], use_container_width=True)

        with st.expander("Preview unique keywords (first 10)"):
            st.write(cleaned_keywords_list[:10])

        if not valid_keywords:
            st.error("No valid keywords to process. Please check your file.")
            st.stop()

        # Show batch info
        if num_batches > 1:
            st.info(f"Will process {total_keywords:,} unique keywords in {num_batches} API batches")
        else:
            st.info(f"Will process {total_keywords:,} unique keywords in 1 API batch")

        # Process button
        if st.button("Fetch Search Volume Data", type="primary"):
            login, password = get_credentials()

            if login and password:
                all_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(0, total_keywords, BATCH_SIZE):
                    batch = cleaned_keywords_list[i:i + BATCH_SIZE]
                    batch_num = i // BATCH_SIZE + 1

                    status_text.text(f"Batch {batch_num}/{num_batches}: Fetching search volume and difficulty data...")
                    google_ads_response = call_google_ads_api(batch, login, password)

                    if google_ads_response:
                        batch_df = process_google_ads_response(google_ads_response)
                        if batch_df is not None:
                            all_results.append(batch_df)

                    # Update progress
                    progress = min((i + BATCH_SIZE) / total_keywords, 1.0)
                    progress_bar.progress(progress)

                    # Rate limiting between batches
                    if i + BATCH_SIZE < total_keywords:
                        time.sleep(1)

                progress_bar.progress(1.0)
                status_text.text("Processing complete!")

                # Combine all results
                if all_results:
                    api_results_df = pd.concat(all_results, ignore_index=True)

                    # Create mapping from original to cleaned keywords
                    keyword_mapping = pd.DataFrame([{
                        'original': kw['original'],
                        'cleaned': kw['cleaned']
                    } for kw in valid_keywords])

                    # Merge API results with mapping to get original keywords
                    api_results_df = api_results_df.merge(
                        keyword_mapping,
                        left_on='Keyword',
                        right_on='cleaned',
                        how='left'
                    )

                    # Create final output with original keywords
                    final_df = api_results_df[['original', 'US Search Volume (Last Month)', 'Keyword Difficulty']].copy()
                    final_df = final_df.rename(columns={'original': 'Keyword'})

                    # Store in session state to persist after download
                    st.session_state.results_df = final_df
                    st.session_state.processing_complete = True
                else:
                    st.error("No results returned from the API. Please check your credentials and try again.")

        # Display results if available (from session state)
        if st.session_state.processing_complete and st.session_state.results_df is not None:
            final_df = st.session_state.results_df

            st.success(f"Successfully fetched data for {len(final_df)} keywords!")

            # Display results
            st.subheader("Results")
            st.dataframe(final_df, use_container_width=True)

            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Keywords", len(final_df))
            with col2:
                avg_volume = final_df['US Search Volume (Last Month)'].mean()
                st.metric("Avg Search Volume", f"{avg_volume:,.0f}")
            with col3:
                total_volume = final_df['US Search Volume (Last Month)'].sum()
                st.metric("Total Search Volume", f"{total_volume:,.0f}")
            with col4:
                high_diff = len(final_df[final_df['Keyword Difficulty'] == 'HIGH'])
                st.metric("High Difficulty Keywords", high_diff)

            # Competition breakdown
            st.subheader("Keyword Difficulty Breakdown")
            st.caption("Competition level based on advertiser bidding activity from Google Ads")
            difficulty_counts = final_df['Keyword Difficulty'].value_counts()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                low_count = difficulty_counts.get('LOW', 0)
                st.metric("LOW", low_count)
            with col2:
                med_count = difficulty_counts.get('MEDIUM', 0)
                st.metric("MEDIUM", med_count)
            with col3:
                high_count = difficulty_counts.get('HIGH', 0)
                st.metric("HIGH", high_count)
            with col4:
                na_count = difficulty_counts.get('N/A', 0)
                st.metric("N/A", na_count)

            # Download buttons
            st.subheader("Download Results")

            col1, col2 = st.columns(2)

            with col1:
                csv = final_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name="keyword_search_volume.csv",
                    mime="text/csv"
                )

            with col2:
                excel_data = convert_df_to_excel(final_df)
                st.download_button(
                    label="Download as Excel",
                    data=excel_data,
                    file_name="keyword_search_volume.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # Clear results button
            if st.button("Clear Results & Start Over"):
                st.session_state.results_df = None
                st.session_state.processing_complete = False
                st.rerun()

else:
    # Reset session state when no file is uploaded
    st.session_state.results_df = None
    st.session_state.processing_complete = False

    # Instructions when no file is uploaded
    st.info("Upload a file to get started")

    st.markdown("""
    ### Instructions:

    1. **Prepare your file**: Create a CSV or Excel file with a column containing keywords

    2. **Configure API credentials**: Add your DataForSEO credentials in Streamlit Secrets

    3. **Upload the file**: Use the file uploader above

    4. **Select keyword column**: Choose the column containing your keywords

    5. **Fetch data**: Click the button to retrieve search volume and keyword difficulty

    ### Features:

    - **Duplicate removal**: Automatically detects and removes duplicate keywords
    - **Keyword validation**: Cleans invalid characters and validates word count
    - **Persistent results**: Results stay visible after downloading

    ### Output Data:

    | Column | Description |
    |--------|-------------|
    | Keyword | Your original keyword |
    | US Search Volume (Last Month) | Most recent month's search volume for US |
    | Keyword Difficulty | Competition level (LOW, MEDIUM, HIGH) from Google Ads |

    ### API Limits:

    - **1,000 keywords** per API request (automatically batched)
    - **2,000 API calls** per minute maximum
    - **30 simultaneous requests** maximum

    ### API Documentation:
    - [Google Ads Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Powered by DataForSEO Google Ads API</p>
</div>
""", unsafe_allow_html=True)
