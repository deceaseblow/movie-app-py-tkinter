import requests
import os
from requests.exceptions import Timeout
from dotenv import load_dotenv

load_dotenv()

class SearchService:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = "https://api.watchmode.com/v1/search/"

    def search_movie(self, payload):
        query = payload.get("query")    
        if not query:
            return {"status": "error", "message": "No query provided"}

        try:
            response = requests.get(self.base_url, params={
                "apiKey": self.api_key,
                "search_field": "name",
                "search_value": query
            }, timeout=10)  # Increased timeout to 10 seconds

            if response.status_code == 200:
                data = response.json()
                results = data.get("title_results", [])[:5]  # Limit to 5 results
                filtered_results = []

                print(f"[SearchService] Received {len(results)} results for query: {query}")

                for result in results:
                    movie_id = result.get("id")
                    if movie_id:
                        print(f"Fetching image for movie ID: {movie_id}")
                        image_url = self.get_movie_image(movie_id)
                        if image_url:
                            result['image_url'] = image_url
                        filtered_results.append(result)  # Add the result even without image

                return {"status": "success", "results": filtered_results}

            else:
                return {"status": "error", "message": f"API Error: {response.status_code}"}

        except Timeout:
            print(f"[SearchService] Request timed out while searching for '{query}'")
            return {"status": "error", "message": "Search request timed out"}
        except Exception as e:
            print(f"[SearchService] Error during search: {str(e)}")
            return {"status": "error", "message": f"Search error: {str(e)}"}

    def get_movie_by_id(self, movie_id):
        """Get complete movie details by ID."""
        try:
            movie_details_url = f"https://api.watchmode.com/v1/title/{movie_id}/details/"
            response = requests.get(movie_details_url, params={
                "apiKey": self.api_key
            }, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching movie ID {movie_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error retrieving movie ID {movie_id}: {str(e)}")
            return None

    def get_movie_image(self, movie_id):
        """Fetch movie details including the image URL."""
        try:
            movie_details_url = f"https://api.watchmode.com/v1/title/{movie_id}/details/"
            response = requests.get(movie_details_url, params={
                "apiKey": self.api_key
            }, timeout=10)  # Increased timeout to 10 seconds

            if response.status_code == 200:
                movie_data = response.json()
                poster_url = movie_data.get("poster")

                if poster_url:
                    print(f"Poster URL for movie ID {movie_id}: {poster_url}")
                    return poster_url
                else:
                    print(f"No poster URL found for movie ID {movie_id}")
                    return None
            else:
                print(f"Error fetching movie details for movie ID {movie_id}: {response.status_code}")
                return None
        except Timeout:
            print(f"[SearchService] Timeout while fetching image for movie ID {movie_id}")
            return None
        except Exception as e:
            print(f"Error fetching image for movie ID {movie_id}: {e}")
            return None