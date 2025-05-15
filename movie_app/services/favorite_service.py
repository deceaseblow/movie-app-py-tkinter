import json
import os

USERS_DB = "db/users.json"

class FavoriteService:
    def __init__(self):
        if not os.path.exists(USERS_DB):
            with open(USERS_DB, "w") as f:
                json.dump({}, f)

    def add_to_favorites(self, data):
        """Add a movie to the user's favorites."""
        username = data.get("username")
        movie_id = data.get("movie_id")

        with open(USERS_DB, "r+") as f:
            users = json.load(f)
            if username not in users:
                return {"status": "fail", "message": "User not found"}

            user = users[username]
            favorites = user.get("favorites", [])

            if movie_id in favorites:
                return {"status": "fail", "message": "Movie already in favorites"}
            favorites.append(movie_id)
            user["favorites"] = favorites  # Update the user's favorites list

            f.seek(0)
            json.dump(users, f)

        return {"status": "success", "message": "Added to favorites"}

    def remove_from_favorites(self, data):
        """Remove a movie from the user's favorites."""
        username = data.get("username")
        movie_id = data.get("movie_id")

        # Load the users' data from the file
        with open(USERS_DB, "r+") as f:
            users = json.load(f)

            if username not in users:
                return {"status": "fail", "message": "User not found"}
            user = users[username]
            favorites = user.get("favorites", [])

            if movie_id not in favorites:
                return {"status": "fail", "message": "Movie not in favorites"}

            favorites.remove(movie_id)
            user["favorites"] = favorites  # Update the user's favorites list

            f.seek(0)
            json.dump(users, f)

        return {"status": "success", "message": "Removed from favorites"}

    def get_user_favorites(self, username):
        """Get the list of favorite movie IDs for a user."""    
        with open(USERS_DB, "r") as f:
            users = json.load(f)

            if username not in users:
                return {"status": "fail", "message": "User not found"}

            return {"status": "success", "favorites": users[username].get("favorites", [])}
