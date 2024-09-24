import requests


class CountryModel:
    """Class to perform country search using RestCountries API"""

    def __init__(self, query):
        self.query = query
        self.results = []

    def perform_search(self):
        """Performs search for country information using the RestCountries API"""
        api_url = f"https://restcountries.com/v3.1/name/{self.query}?fullText=true"

        try:
            # Send the request to the RestCountries API
            response = requests.get(api_url)
            if response.status_code == 200:
                # If successful, parse the JSON response
                self.results = self.parse_results(response.json())
            else:
                self.results = [f"Error: Unable to fetch data. Status code: {response.status_code}"]
        except Exception as e:
            # Catch any exceptions and return an error message
            self.results = [f"Exception occurred: {str(e)}"]

        return self.results

    def parse_results(self, data):
        """Extract relevant country information from the API response"""
        if isinstance(data, list) and len(data) > 0:
            country_info = data[0]  # Get the first matching country
            result = {
                'Name': country_info.get('name', {}).get('common', 'N/A'),
                'Capital': country_info.get('capital', ['N/A'])[0],
                'Region': country_info.get('region', 'N/A'),
                'Population': country_info.get('population', 'N/A'),
                'Area': country_info.get('area', 'N/A'),
                'Currencies': country_info.get('currencies', 'N/A'),
                'SltSpellings': country_info.get('altSpellings', 'N/A'),
                'Subregion': country_info.get('subregion', 'N/A'),
                # 'translations': country_info.get('translations', 'N/A'),
                'LatitudeLongitude': country_info.get('latlng', 'N/A'),
                'Gini': country_info.get('gini', 'N/A'),
                'Timezones': country_info.get('timezones', 'N/A'),
                'Borders': country_info.get('borders', 'N/A'),
                'Flag': country_info.get('flag', 'N/A'),
                'Cioc': country_info.get('cioc', 'N/A'),
                'Languages': ', '.join(country_info.get('languages', {}).values())
            }
            return [result]  # Return a list of dictionaries
        else:
            return ["No results found."]
#
# Example usage
# if __name__ == "__main__":
#     country_model = CountryModel("Niger")
#     search_results = country_model.perform_search()
#     for result in search_results:
#         print(result)
