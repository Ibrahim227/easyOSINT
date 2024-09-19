"""
    Contains the class SearchModel for scraping Wikipedia
    Import required Module/Lib
"""
# search.py
import requests
from bs4 import BeautifulSoup


class SearchModel:
    def __init__(self, query):
        self.query = query
        self.base_url = 'https://en.wikipedia.org/w/index.php?search='  # Wikipedia search URL

    def perform_search(self):
        """
        Perform a search query on Wikipedia and scrape the results.
        """
        try:
            # Send GET request to Wikipedia search
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(f"{self.base_url}{self.query}", headers=headers)
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
        Parse the HTML soup to extract Wikipedia search results.
        :param soup:
        :return:
        """
        results = []

        # Wikipedia search results are in 'mw-search-result' class divs
        for item in soup.find_all('div', class_='mw-search-result'):
            # Extract the title
            title = item.find('a').get_text()
            # Extract the link to the article (needs to be appended to Wikipedia's base URL)
            link = 'https://en.wikipedia.org' + item.find('a')['href']
            # Extract a brief snippet/description (if available)
            snippet = item.find('div', class_='searchresult').get_text()

            results.append({'title': title, 'link': link, 'snippet': snippet})

        return results
