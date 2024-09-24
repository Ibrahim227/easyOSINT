import requests


class SearchModel:
    def __init__(self, query):
        self.query = query
        self.base_url = 'https://en.wikipedia.org/w/api.php'  # Wikipedia API endpoint

    def perform_search(self):
        """
        Perform a search query on Wikipedia using the API.
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": self.query,
            "format": "json",
            "utf8": 1  # Ensure proper character encoding
        }

        try:
            # Make the API request to Wikipedia
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()  # Check for request errors

            # Extract data from the JSON response
            data = response.json()
            # print(data)

            # Extract search results
            search_results = data.get("query", {}).get("search", [])

            # Format results as a list of dictionaries
            results = [
                {
                    "title": result["title"],
                    "snippet": result["snippet"],
                    "link": f"https://en.wikipedia.org/wiki/{result['title'].replace(' ', '_')}"
                }
                for result in search_results
            ]

            if results:
                return results
            else:
                return [{"title": "No results found", "snippet": "", "link": ""}]

        except requests.exceptions.RequestException as e:
            # Return an error message in case of request failure
            return [{"title": "Error", "snippet": str(e), "link": ""}]

