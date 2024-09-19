"""
    Contains the class SearchModel
    Import required Module/Lib
"""
# search.py
import requests
from bs4 import BeautifulSoup


class SearchModel:
    def __init__(self, query):
        self.query = query
        self.base_url = 'https://www.google.com/search?q='  # search engine or website

    def perform_search(self):
        """
        Perform a search query and scrape the results.
        """
        try:
            # Send GET request to the search engine
            response = requests.get(f"{self.base_url}{self.query}")
            response.raise_for_status()  # Ensure successful response

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract relevant data (e.g., search results)
            results = self._parse_results(soup)

            return results

        except requests.exceptions.RequestException as e:
            print(f"Error during the request: {e}")
            return {"error": "Failed to perform search"}

    def _parse_results(self, soup):
        """
        Parse the HTML soup to extract search results.
        """
        results = []
        # Example: Find all links in search results
        for item in soup.find_all('a', class_='result-link'):  # Adjust based on actual structure
            title = item.get_text()
            link = item.get('href')
            results.append({'title': title, 'link': link})
        return results
