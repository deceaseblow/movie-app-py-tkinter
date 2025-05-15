import json
import os

COMMENTS_DB = "db/comments.json"

class CommentService:
    def __init__(self):
        if not os.path.exists(COMMENTS_DB):
            with open(COMMENTS_DB, "w") as f:
                json.dump({}, f)

    def add_review(self, data):
        username = data.get("username")
        movie_id = str(data.get("movie_id"))
        comment = data.get("comment")
        with open(COMMENTS_DB, "r+") as f:
            comments = json.load(f)
            comments.setdefault(movie_id, [])
            comments[movie_id].append({"user": username, "comment": comment})
            f.seek(0)
            json.dump(comments, f)
        return {"status": "success", "message": "Review added"}
