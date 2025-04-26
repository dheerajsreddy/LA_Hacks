# Home Depot and Contractor Search Project

This project contains two main scripts:
1. `test_homedepot_search.py` - Searches Home Depot products using Gemini AI and SerpAPI
2. `test_contractor_search_dynamic_location.py` - Finds contractors using Google Places API and Gemini AI

## Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with the following API keys:
```
GEMINI_API_KEY=your_gemini_api_key
SERPAPI_API_KEY=your_serpapi_key
PLACES_API_KEY=your_google_places_api_key
```

3. Get your API keys:
   - Gemini API: https://ai.google.dev/
   - SerpAPI: https://serpapi.com/
   - Google Places API: https://developers.google.com/maps

## Important Security Notes
- Never commit your `.env` file to version control
- Regenerate your API keys if they have been exposed
- Monitor your API usage and billing