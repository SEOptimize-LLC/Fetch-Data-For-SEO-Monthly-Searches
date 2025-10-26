# 🔍 SEO Keyword Research Tool

A powerful Streamlit web application for enriching Google Search Console data with SEO metrics from DataForSEO API.

## Features

- 📁 **Google Search Console Integration**: Upload CSV/Excel exports from GSC
- 🔍 **SEO Metrics**: Fetch monthly search volume and keyword difficulty
- 📊 **Data Merging**: Combines your GSC data with API results
- 📈 **Summary Reports**: Automatic page-level aggregations
- 💾 **Multi-Sheet Export**: Download Excel files with detailed and summary data
- 🔐 **Secure Authentication**: Store API credentials securely using Streamlit Secrets
- ⚡ **Batch Processing**: Automatically handles large keyword lists
- ✨ **Keyword Validation**: Auto-cleans special characters and validates keywords

## Demo

Access the live app: [Your Streamlit Cloud URL]

## Input Data Format

Upload a CSV or Excel file from Google Search Console with these columns:

| Column | Description |
|--------|-------------|
| `page` | Landing page URL |
| `query` | Search keyword/query |
| `Clicks` | Number of clicks |
| `Impressions` | Number of impressions |
| `CTR %` | Click-through rate |
| `Avg. Position` | Average position in search results |

## Output Data Format

**Sheet 1 - All Keywords:**
- All original columns from your input file
- `Monthly Searches` - Search volume from DataForSEO API
- `Keyword Difficulty` - Competition level (LOW, MEDIUM, HIGH)

**Sheet 2 - Summary by Page:**
- `Page` - Landing page URL
- `Total Monthly Searches` - Sum of all keyword search volumes for this page
- `Total Clicks` - Sum of all clicks
- `Total Impressions` - Sum of all impressions
- `Avg. Position` - Average ranking position
- `CTR %` - Calculated as (Total Clicks / Total Impressions) × 100

## Prerequisites

1. **DataForSEO Account**: Sign up at [DataForSEO](https://dataforseo.com/)
2. **API Credentials**: Get your API login and password from DataForSEO dashboard

## Local Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Fetch-Data-For-SEO-Monthly-Searches.git
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

### 4. Configure Secrets (Local Development)

Create a `.streamlit/secrets.toml` file in the project root:

```toml
[dataforseo]
login = "your-email@example.com"
password = "your-password"
```

**Note**: Never commit `secrets.toml` to version control!

### 5. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Deployment to Streamlit Cloud

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `app.py`
6. Click "Deploy"

### 3. Configure Secrets in Streamlit Cloud

1. Go to your app's dashboard on Streamlit Cloud
2. Click on "Settings" (⚙️)
3. Navigate to the "Secrets" tab
4. Add your DataForSEO credentials:

```toml
[dataforseo]
login = "your-email@example.com"
password = "your-password"
```

5. Click "Save"
6. Your app will automatically restart with the new credentials

## Usage

### 1. Export Data from Google Search Console

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Navigate to **Performance** → **Search Results**
3. Click **Export** and download as CSV or Excel
4. Ensure the export includes: page, query, clicks, impressions, CTR, and position

### 2. Upload File to App

- Click "Browse files" or drag and drop your GSC export
- Supported formats: CSV, XLSX, XLS

### 3. Select Keyword Column

- Choose the column containing your keywords (usually "query")

### 4. Configure Settings (Optional)

In the sidebar, you can adjust:
- **Location Code**: Default is 2840 (United States)
- **Language Code**: Default is "en" (English)

[Find location codes here](https://docs.dataforseo.com/v3/appendix/locations/)

### 5. Fetch SEO Data

- Click "🚀 Fetch SEO Data" button
- App validates and cleans keywords automatically
- API fetches search volume and competition data
- View results in the interactive table

### 6. Download Enriched Results

**CSV Download:**
- Contains all data merged in a single file

**Excel Download (Recommended):**
- **Sheet 1 - All Keywords**: Complete data with all original columns + API data
- **Sheet 2 - Summary by Page**: Aggregated metrics per landing page

## API Rate Limits

The app automatically handles batch processing with rate limiting to comply with DataForSEO API limits:
- Maximum 100 keywords per request
- 1-second delay between batches
- Adjust `batch_size` in `app.py` if needed

## File Structure

```
Fetch-Data-For-SEO-Monthly-Searches/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .streamlit/
│   └── config.toml            # Streamlit configuration
└── .gitignore                 # Git ignore file
```

## Configuration

### Location Codes

Common location codes:
- **2840**: United States
- **2826**: United Kingdom
- **2124**: Canada
- **2036**: Australia
- **2276**: Germany

[Full list of location codes](https://docs.dataforseo.com/v3/appendix/locations/)

### Language Codes

Common language codes:
- **en**: English
- **es**: Spanish
- **fr**: French
- **de**: German
- **it**: Italian

## Troubleshooting

### "DataForSEO credentials not configured" Error

- Ensure secrets are properly configured in Streamlit Cloud
- Check that the format matches exactly:
  ```toml
  [dataforseo]
  login = "your-email@example.com"
  password = "your-password"
  ```

### "API Error" Messages

- Verify your DataForSEO credentials are correct
- Check your DataForSEO account has sufficient credits
- Ensure you're not exceeding API rate limits

### File Upload Issues

- Maximum file size: 200MB
- Ensure file contains a column with keywords
- Check file format is CSV or Excel

## API Documentation

- [DataForSEO API Documentation](https://docs.dataforseo.com/)
- [Search Volume Endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)

## Technologies Used

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP library for API calls
- **OpenPyXL**: Excel file handling
- **XlsxWriter**: Excel file creation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Contact DataForSEO support for API-related questions
- Check Streamlit documentation for deployment issues

## Acknowledgments

- [DataForSEO](https://dataforseo.com/) for providing the SEO API
- [Streamlit](https://streamlit.io/) for the amazing web framework

## Future Enhancements

- [ ] Add support for multiple search engines
- [ ] Include keyword suggestions
- [ ] Add data visualization charts
- [ ] Export to Google Sheets
- [ ] Historical data tracking
- [ ] Competitor analysis features
- [ ] Bulk keyword difficulty scoring

---

Made with ❤️ using Streamlit and DataForSEO API
