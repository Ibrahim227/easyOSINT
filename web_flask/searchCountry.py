"""Import module/lib"""
import requests
from bs4 import BeautifulSoup


class CountryModel:
    """Define a class Model to perform search on Google"""
    def __init__(self, query):
        self.query = query
        self.results = []

    def perform_search(self):
        # Simulate a Google search (replace with actual Google API or scraping logic)
        google_url = f"https://www.google.com/search?q={self.query}+country+info"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Send the request to Google (In real-world, you'd handle this more robustly)
        try:
            response = requests.get(google_url, headers=headers)
            if response.status_code == 200:
                self.results = self.parse_results(response.text)
            else:
                self.results = ["Error performing search"]
        except Exception as e:
            self.results = [f"Exception occurred: {str(e)}"]

        return self.results

    def parse_results(self, html):
        # Parse the search results from the response (simplified for demonstration)
        soup = BeautifulSoup(html, 'html.parser')
        search_results = []

        for g in soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd'):  # Sample class from a Google search result
            title = g.get_text()
            search_results.append(title)

        # Limit to top 5 results for simplicity
        return search_results[:5]
