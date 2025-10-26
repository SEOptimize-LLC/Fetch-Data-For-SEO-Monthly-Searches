# 🔍 SEO Keyword Research Tool

A powerful Streamlit web application for fetching SEO metrics including monthly search volume and keyword difficulty using the DataForSEO API.

## Features

- 📁 **File Upload Support**: Upload CSV or Excel files with your keywords
- 🔍 **SEO Metrics**: Fetch search volume, competition, CPC, and more
- 📊 **Data Visualization**: View results in an interactive table
- 💾 **Export Results**: Download results as CSV or Excel
- 🔐 **Secure Authentication**: Store API credentials securely using Streamlit Secrets
- ⚡ **Batch Processing**: Automatically handles large keyword lists

## Demo

Access the live app: [Your Streamlit Cloud URL]

## What Data You'll Get

- **Search Volume**: Monthly search volume
- **Competition**: Competition level (LOW, MEDIUM, HIGH)
- **Competition Index**: Numerical competition index (0-100)
- **CPC**: Cost per click in USD
- **Top of Page Bid**: Low and high bid ranges
- **Monthly Searches**: Historical search data

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

### 1. Prepare Your Keyword File

Create a CSV or Excel file with your keywords. Example:

**keywords.csv**
```csv
keyword
seo tools
keyword research
backlink checker
content marketing
digital marketing agency
```

**keywords.xlsx**
| keyword |
|---------|
| seo tools |
| keyword research |
| backlink checker |

### 2. Upload File

- Click "Browse files" or drag and drop your file
- Supported formats: CSV, XLSX, XLS

### 3. Select Keyword Column

- Choose which column contains your keywords from the dropdown

### 4. Configure Settings (Optional)

In the sidebar, you can adjust:
- **Location Code**: Default is 2840 (United States)
- **Language Code**: Default is "en" (English)

[Find location codes here](https://docs.dataforseo.com/v3/appendix/locations/)

### 5. Fetch SEO Data

- Click "🚀 Fetch SEO Data" button
- Wait for the API to process your keywords
- View results in the interactive table

### 6. Download Results

- Download as CSV or Excel format
- Results include all fetched metrics

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
