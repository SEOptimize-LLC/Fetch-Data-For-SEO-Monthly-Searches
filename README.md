# DataForSEO Clickstream Search Volume Tool

A Streamlit web application for fetching clickstream-based search volume data and keyword competition metrics from the DataForSEO API.

## Features

- **Clickstream Data**: Uses DataForSEO's Clickstream Global Search Volume API for accurate search metrics
- **US-Focused**: Extracts US-specific search volume from global data
- **Keyword Competition**: Retrieves competition level (LOW, MEDIUM, HIGH) from Google Ads API
- **Duplicate Detection**: Automatically removes duplicate keywords before processing
- **Keyword Validation**: Cleans invalid characters and validates word count
- **Batch Processing**: Automatically handles up to 1,000 keywords per API request
- **Cost Optimized**: Minimizes API costs by batching keywords efficiently
- **Secure**: API credentials stored securely via Streamlit Secrets

## API Endpoints

This tool uses two DataForSEO endpoints:

### 1. Clickstream Global Search Volume
```
POST https://api.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live
```
[Documentation](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live/)

### 2. Google Ads Search Volume (for Competition)
```
POST https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live
```
[Documentation](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)

## Output Data

| Column | Description |
|--------|-------------|
| Keyword | Your original keyword |
| Global Search Volume | Worldwide clickstream search volume |
| US Search Volume | United States clickstream search volume |
| Keyword Difficulty | Competition level (LOW, MEDIUM, HIGH) from Google Ads |

**Note**: The Keyword Difficulty column shows the competition level from Google Ads, which represents the level of advertiser bidding activity for each keyword.

## API Limits

- **1,000 keywords** per API request (automatically batched)
- **2,000 API calls** per minute maximum
- **30 simultaneous requests** maximum

## Prerequisites

1. **DataForSEO Account**: Sign up at [DataForSEO](https://dataforseo.com/)
2. **API Credentials**: Get your API login and password from the DataForSEO dashboard

## Local Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SEOptimize-LLC/Fetch-Data-For-SEO-Monthly-Searches.git
cd Fetch-Data-For-SEO-Monthly-Searches
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Secrets

Create a `.streamlit/secrets.toml` file:

```toml
[dataforseo]
login = "your-email@example.com"
password = "your-password"
```

**Note**: Never commit `secrets.toml` to version control.

### 5. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Deployment to Streamlit Cloud

### 1. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `app.py`
6. Click "Deploy"

### 2. Configure Secrets

1. Go to your app's dashboard on Streamlit Cloud
2. Click "Settings"
3. Navigate to "Secrets" tab
4. Add your credentials:

```toml
[dataforseo]
login = "your-email@example.com"
password = "your-password"
```

5. Click "Save"

## Usage

1. **Prepare your file**: Create a CSV or Excel file with a column containing keywords
2. **Upload the file**: Use the file uploader in the app
3. **Select keyword column**: Choose the column containing your keywords
4. **Fetch data**: Click the button to retrieve search volume and competition data
   - Duplicate keywords are automatically removed
   - Invalid characters are cleaned from keywords
5. **Download results**: Export as CSV or Excel

## Cost Optimization

The app batches keywords to minimize API costs. Each batch makes 2 API calls (Clickstream + Google Ads):

- Up to 1,000 keywords = 2 API requests
- 1,500 keywords = 4 API requests
- 3,000 keywords = 6 API requests

**Note**: Duplicate keywords are automatically removed before processing, further reducing API costs.

## File Structure

```
Fetch-Data-For-SEO-Monthly-Searches/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .streamlit/
│   └── config.toml        # Streamlit configuration
└── .gitignore             # Git ignore file
```

## Troubleshooting

### "DataForSEO credentials not configured" Error

Ensure secrets are properly configured with the exact format:

```toml
[dataforseo]
login = "your-email@example.com"
password = "your-password"
```

### "API Error" Messages

- Verify your DataForSEO credentials are correct
- Check your account has sufficient credits
- Ensure you're not exceeding API rate limits

### File Upload Issues

- Maximum file size: 200MB
- Supported formats: CSV, XLSX, XLS
- File must contain a column with keywords

## Technologies

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation
- **Requests**: HTTP library for API calls
- **XlsxWriter**: Excel file creation

## License

MIT License

## Support

- Open an issue on GitHub for bugs or feature requests
- Contact DataForSEO support for API-related questions

---

Powered by DataForSEO Clickstream & Google Ads APIs
