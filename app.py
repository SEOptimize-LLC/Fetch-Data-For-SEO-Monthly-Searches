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
CLICKSTREAM_API_ENDPOINT = "https://api.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live"
GOOGLE_ADS_API_ENDPOINT = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"

# Page configuration
st.set_page_config(
    page_title="DataForSEO Clickstream Search Volume",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 DataForSEO Clickstream Search Volume Tool")
st.markdown("Upload a file with keywords to fetch clickstream-based search volume data from DataForSEO")

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

st.sidebar.markdown("""
### DataForSEO API Credentials

**For Streamlit Cloud:**
1. Go to your app dashboard at [share.streamlit.io](https://share.streamlit.io)
2. Click on your app's menu (three dots)
3. Select **Settings** > **Secrets**
4. Add your credentials:
```toml
[dataforseo]
login = "your-email@example.com"
password = "your-api-password"
```
5. Click **Save**

**For Local Development:**
Create `.streamlit/secrets.toml` in your project:
```toml
[dataforseo]
login = "your-email@example.com"
password = "your-api-password"
```

[Get API credentials](https://app.dataforseo.com/)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("""
### API Settings (Fixed)
- **Location:** United States (2840)
- **Language:** English (en)
- **Batch Size:** 1,000 keywords per request
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


def call_clickstream_api(keywords, login, password):
    """
    Call DataForSEO Clickstream Global Search Volume API
    Endpoint: POST https://api.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live
    """
    cred = f"{login}:{password}"
    encoded_cred = base64.b64encode(cred.encode('ascii')).decode('ascii')

    headers = {
        'Authorization': f'Basic {encoded_cred}',
        'Content-Type': 'application/json'
    }

    post_data = [{
        "keywords": keywords
    }]

    try:
        response = requests.post(CLICKSTREAM_API_ENDPOINT, headers=headers, json=post_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Clickstream API Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response: {e.response.text}")
        return None


def call_google_ads_api(keywords, login, password):
    """
    Call DataForSEO Google Ads Search Volume API to get competition data
    Endpoint: POST https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live
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
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Google Ads API Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response: {e.response.text}")
        return None


def extract_us_search_volume(countries_data):
    """
    Extract US-specific search volume from the countries breakdown
    Returns the search volume for the United States (location_code 2840)
    """
    if not countries_data:
        return None

    for country in countries_data:
        if country.get('location_code') == LOCATION_CODE:
            return country.get('search_volume', 0)

    return None


def process_clickstream_response(response_data):
    """
    Process Clickstream API response and convert to dataframe
    Returns: Keyword, Global Search Volume, US Search Volume
    """
    if not response_data or 'tasks' not in response_data:
        return None

    results = []
    for task in response_data.get('tasks', []):
        if task.get('status_code') == 20000:  # Success
            for result_item in task.get('result', []):
                items = result_item.get('items', [])
                for item in items:
                    keyword = item.get('keyword', '')
                    global_search_volume = item.get('search_volume', 0) or 0
                    countries_data = item.get('countries', [])

                    # Extract US-specific search volume
                    us_search_volume = extract_us_search_volume(countries_data)
                    if us_search_volume is None:
                        us_search_volume = 0

                    results.append({
                        'Keyword': keyword,
                        'Global Search Volume': global_search_volume,
                        'US Search Volume': us_search_volume
                    })
        else:
            status_code = task.get('status_code')
            if status_code not in [40501]:  # Skip validation errors
                st.warning(f"Clickstream API task failed with status code: {status_code}")
                st.warning(f"Message: {task.get('status_message')}")

    if results:
        return pd.DataFrame(results)
    return None


def process_google_ads_response(response_data):
    """
    Process Google Ads API response to extract competition data
    Returns: Dictionary mapping keyword -> competition level (LOW, MEDIUM, HIGH)
    """
    if not response_data or 'tasks' not in response_data:
        return {}

    competition_map = {}
    for task in response_data.get('tasks', []):
        if task.get('status_code') == 20000:  # Success
            for result_item in task.get('result', []):
                items = result_item.get('items', [])
                for item in items:
                    keyword = item.get('keyword', '')
                    # The API returns competition as "LOW", "MEDIUM", or "HIGH"
                    competition = item.get('competition', None)
                    if competition:
                        competition_map[keyword.lower()] = competition
                    else:
                        competition_map[keyword.lower()] = 'N/A'
        else:
            status_code = task.get('status_code')
            if status_code not in [40501]:  # Skip validation errors
                st.warning(f"Google Ads API task failed with status code: {status_code}")
                st.warning(f"Message: {task.get('status_message')}")

    return competition_map


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
        st.info(f"Found {len(keywords_list)} keywords")

        with st.expander("Preview keywords (first 10)"):
            st.write(keywords_list[:10])

        # Process button
        if st.button("Fetch Search Volume Data", type="primary"):
            login, password = get_credentials()

            if login and password:
                # Validate and clean keywords
                st.info("Validating and cleaning keywords...")
                valid_keywords, skipped_keywords, duplicate_keywords = validate_and_clean_keywords(keywords_list)

                # Show duplicate keywords info
                if duplicate_keywords:
                    st.warning(f"Removed {len(duplicate_keywords)} duplicate keywords")
                    with st.expander("View duplicate keywords"):
                        dup_df = pd.DataFrame(duplicate_keywords)
                        st.dataframe(dup_df, use_container_width=True)

                # Show validation results
                if skipped_keywords:
                    st.warning(f"Skipped {len(skipped_keywords)} invalid keywords")
                    with st.expander("View skipped keywords"):
                        skipped_df = pd.DataFrame(skipped_keywords)
                        st.dataframe(skipped_df, use_container_width=True)

                if not valid_keywords:
                    st.error("No valid keywords to process. Please check your file.")
                    st.stop()

                # Show cleaned keywords info
                modified_keywords = [kw for kw in valid_keywords if kw['modified']]
                if modified_keywords:
                    st.info(f"Cleaned {len(modified_keywords)} keywords (removed special characters)")
                    with st.expander("View modified keywords"):
                        modified_df = pd.DataFrame(modified_keywords)
                        st.dataframe(modified_df[['original', 'cleaned']], use_container_width=True)

                # Extract cleaned keywords for API call
                cleaned_keywords_list = [kw['cleaned'] for kw in valid_keywords]

                # Split keywords into batches (max 1000 per request)
                total_keywords = len(cleaned_keywords_list)
                num_batches = (total_keywords + BATCH_SIZE - 1) // BATCH_SIZE

                st.info(f"Processing {total_keywords} unique keywords...")
                if num_batches > 1:
                    st.info(f"Using {num_batches} batches of up to {BATCH_SIZE} keywords each")

                all_clickstream_results = []
                all_competition_data = {}
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(0, total_keywords, BATCH_SIZE):
                    batch = cleaned_keywords_list[i:i + BATCH_SIZE]
                    batch_num = i // BATCH_SIZE + 1

                    # Step 1: Call Clickstream API for search volume
                    status_text.text(f"Batch {batch_num}/{num_batches}: Fetching search volume data...")
                    clickstream_response = call_clickstream_api(batch, login, password)

                    if clickstream_response:
                        batch_df = process_clickstream_response(clickstream_response)
                        if batch_df is not None:
                            all_clickstream_results.append(batch_df)

                    # Step 2: Call Google Ads API for competition data
                    status_text.text(f"Batch {batch_num}/{num_batches}: Fetching competition data...")
                    google_ads_response = call_google_ads_api(batch, login, password)

                    if google_ads_response:
                        batch_competition = process_google_ads_response(google_ads_response)
                        all_competition_data.update(batch_competition)

                    # Update progress
                    progress = min((i + BATCH_SIZE) / total_keywords, 1.0)
                    progress_bar.progress(progress)

                    # Rate limiting between batches
                    if i + BATCH_SIZE < total_keywords:
                        time.sleep(1)

                progress_bar.progress(1.0)
                status_text.text("Processing complete!")

                # Combine all results
                if all_clickstream_results:
                    api_results_df = pd.concat(all_clickstream_results, ignore_index=True)

                    # Add competition data from Google Ads API
                    api_results_df['Keyword Difficulty'] = api_results_df['Keyword'].apply(
                        lambda kw: all_competition_data.get(kw.lower(), 'N/A')
                    )

                    st.success(f"Successfully fetched data for {len(api_results_df)} keywords!")

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
                    final_df = api_results_df[['original', 'Global Search Volume', 'US Search Volume', 'Keyword Difficulty']].copy()
                    final_df = final_df.rename(columns={'original': 'Keyword'})

                    # Display results
                    st.subheader("Results")
                    st.dataframe(final_df, use_container_width=True)

                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Keywords", len(final_df))
                    with col2:
                        avg_volume = final_df['US Search Volume'].mean()
                        st.metric("Avg US Search Volume", f"{avg_volume:,.0f}")
                    with col3:
                        total_volume = final_df['US Search Volume'].sum()
                        st.metric("Total US Search Volume", f"{total_volume:,.0f}")
                    with col4:
                        high_diff = len(final_df[final_df['Keyword Difficulty'] == 'HIGH'])
                        st.metric("High Difficulty Keywords", high_diff)

                    # Competition breakdown (from Google Ads API)
                    st.subheader("Keyword Competition Breakdown")
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
                else:
                    st.error("No results returned from the API. Please check your credentials and try again.")

else:
    # Instructions when no file is uploaded
    st.info("Upload a file to get started")

    st.markdown("""
    ### Instructions:

    1. **Prepare your file**: Create a CSV or Excel file with a column containing keywords

    2. **Configure API credentials**: Add your DataForSEO credentials in Streamlit Secrets (see sidebar)

    3. **Upload the file**: Use the file uploader above

    4. **Select keyword column**: Choose the column containing your keywords

    5. **Fetch data**: Click the button to retrieve search volume and competition data

    ### Features:

    - **Duplicate removal**: Automatically detects and removes duplicate keywords
    - **Keyword validation**: Cleans invalid characters and validates word count

    ### Output Data:

    | Column | Description |
    |--------|-------------|
    | Keyword | Your original keyword |
    | Global Search Volume | Worldwide clickstream search volume |
    | US Search Volume | United States clickstream search volume |
    | Keyword Difficulty | Competition level (LOW, MEDIUM, HIGH) from Google Ads |

    ### API Limits:

    - **1,000 keywords** per API request (automatically batched)
    - **2,000 API calls** per minute maximum
    - **30 simultaneous requests** maximum

    ### API Documentation:
    - [Clickstream Global Search Volume](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live/)
    - [Google Ads Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Powered by DataForSEO Clickstream & Google Ads APIs</p>
</div>
""", unsafe_allow_html=True)
