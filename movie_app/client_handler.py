import json
from services.auth_service import AuthService
from services.search_service import SearchService
from services.favorite_service import FavoriteService
from services.comment_service import CommentService

auth = AuthService()
search = SearchService()
favorites = FavoriteService()
comments = CommentService()

def handle_client(client_socket):
    with client_socket:
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                request = json.loads(data.decode())
                print("[SERVER] Received:", request)
                response = route_request(request)
                client_socket.sendall(json.dumps(response).encode())
            except ConnectionResetError:
                print("[SERVER] Client disconnected unexpectedly.")
                break
            except Exception as e:
                print("[SERVER ERROR]", str(e))
                try:
                    client_socket.sendall(json.dumps({'status': 'error', 'message': str(e)}).encode())
                except Exception:
                    print("[SERVER] Could not send error response (client may be gone).")
                break


def route_request(request):
    action = request.get("action")
    payload = request.get("data", {})

    if action == "register":
        return auth.create_account(payload)
    elif action == "login":
        return auth.authenticate(payload)
    elif action == "search":
        return search.search_movie(payload)
    elif action == "add_favorite":
        return favorites.add_to_favorites(payload)
    elif action == "remove_favorite":
        return favorites.remove_from_favorites(payload)
    elif action == "add_review":
        return comments.add_review(payload)
    else:
        return {"status": "error", "message": "Invalid action"}
