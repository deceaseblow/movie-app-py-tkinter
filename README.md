# Movie Explorer — AOOP Final Project

**Movie Explorer** is an advanced object-oriented programming project that demonstrates a full client-server application for movie searching, user authentication, favorites management, and movie reviews.

## Project Overview

This project showcases a robust distributed client-server architecture implemented in Python, featuring:

- **GUI Client:**  
  Built with Tkinter, the client provides a user-friendly graphical interface for login, registration, searching movies, managing favorites, and posting reviews.

- **Backend Server:**  
  A multithreaded Python socket server that handles multiple clients concurrently, processes requests, and interacts with data storage and external APIs.

- **Modular Service Layer:**  
  The server’s business logic is split into modular service classes managing:  
  - User authentication (`AuthService`)  
  - Movie searching via external API (`SearchService`)  
  - User favorites management (`FavoriteService`)  
  - Movie reviews (`CommentService`)

- **External Movie API Integration:**  
  Movie data is fetched from the Watchmode API, including search results, movie details, and poster images.

- **Data Persistence:**  
  User data, favorites, and comments are stored locally in JSON files, enabling stateful interactions across sessions.

## Technologies Used

- Python 3.x for all backend and client code.  
- Tkinter for the GUI application.  
- Python Sockets and Multithreading to implement the server and client communication.  
- Requests library for RESTful API calls to the Watchmode service.  
- `dotenv` for environment variable management (storing API keys securely).  
- JSON for data storage and communication serialization.

## Features

- User registration and login with UUID-based unique IDs.  
- Movie search with autocomplete and thumbnail display.  
- Add or remove movies from personal favorites.  
- View detailed movie information including synopsis, genre, and release year.  
- Post and view user reviews on movies.  
- Real-time interaction with the server using socket communication.  
- Thread-safe server to handle multiple simultaneous clients.

## Setup Instructions

1. Clone the repository.

2. Create a `.env` file at the root with your Watchmode API key:

   ```ini
   WATCHMODE_API_KEY=your_api_key_here

3. Install Dependencies:
    ```ini
    pip install -r requirements.txt
4. Run the Servers for chatroom and server:
    ```ini
    python server.py
    python chatrooms.py
5. Run the client GUI :
    ```ini
    python gui_client.py
