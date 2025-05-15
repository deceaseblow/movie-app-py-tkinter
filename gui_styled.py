import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import socket
import json
from urllib.request import urlopen
from PIL import Image, ImageTk
import io
import requests
from movie_app.services.search_service import SearchService
from PIL import Image, ImageDraw

HOST = '127.0.0.1'
PORT = 5000

# ----- Network Communication -----
def send_request(action, data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(15)  # Increased timeout to 15 seconds
            s.connect((HOST, PORT))
            request = json.dumps({"action": action, "data": data})
            s.sendall(request.encode())

            chunks = []
            while True:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    
                    try:
                        full_response = b''.join(chunks).decode()
                        json.loads(full_response)  # Test if it's valid JSON
                        break  # If we can parse it as JSON, we're done
                    except json.JSONDecodeError:
                        # Not complete yet, continue receiving
                        continue
                except socket.timeout:
                    if chunks:  # If we have some data but timed out
                        break
                    else:
                        return {"status": "error", "message": "Request timed out"}
            
            if not chunks:
                return {"status": "error", "message": "No data received from server"}
                
            full_response = b''.join(chunks).decode()
            try:
                return json.loads(full_response)
            except json.JSONDecodeError:
                return {"status": "error", "message": f"Invalid JSON response: {full_response[:100]}..."}
                
    except socket.timeout:
        return {"status": "error", "message": "Connection timed out"}
    except ConnectionRefusedError:
        return {"status": "error", "message": "Could not connect to server. Is it running?"}
    except Exception as e:
        return {"status": "error", "message": f"Network error: {str(e)}"}

# ----- Fonts & Colors -----
COLORS = {
    "primary": "#1E3A8A",  # Deep blue
    "secondary": "#6D28D9",  # Purple
    "accent": "#F59E0B",  # Amber
    "background": "#F8FAFC",  # Light gray
    "dark_bg": "#1E293B",  # Dark slate
    "light_text": "#F1F5F9",  # Very light gray
    "dark_text": "#334155",  # Slate
    "card_bg": "#FFFFFF",  # White
    "card_border": "#E2E8F0",  # Light gray
    "error": "#EF4444",  # Red
    "success": "#10B981",  # Green
}

FONTS = {
    "title": ("Helvetica", 22, "bold"),
    "subtitle": ("Helvetica", 18, "bold"),
    "heading": ("Helvetica", 16, "bold"),
    "subheading": ("Helvetica", 14, "bold"),
    "normal": ("Helvetica", 12),
    "small": ("Helvetica", 10),
    "button": ("Helvetica", 12, "bold"),
    "small_button": ("Helvetica", 10, "bold"),
}

# ----- Custom Widgets -----
class StyledButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        bg_color = kwargs.pop('bg_color', COLORS["primary"])
        fg_color = kwargs.pop('fg_color', COLORS["light_text"])
        hover_color = kwargs.pop('hover_color', COLORS["secondary"])
        button_font = kwargs.pop('font', FONTS["button"])
        
        super().__init__(
            master, 
            bg=bg_color, 
            fg=fg_color, 
            font=button_font,
            activebackground=hover_color,
            activeforeground=COLORS["light_text"],
            relief=tk.FLAT,
            borderwidth=0,
            padx=15,
            pady=8,
            cursor="hand2",
            **kwargs
        )

class AccentButton(StyledButton):
    def __init__(self, master=None, **kwargs):
        super().__init__(
            master, 
            bg_color=COLORS["accent"],
            hover_color="#E3A008",  # Darker amber
            **kwargs
        )

class MovieCard(tk.Frame):
    def __init__(self, master, movie, show_detail_callback, toggle_favorite_callback, is_favorite=False):
        super().__init__(
            master, 
            bg=COLORS["card_bg"], 
            padx=10, 
            pady=10, 
            highlightbackground=COLORS["card_border"],
            highlightthickness=1,
        )
        
        # Store movie data and callbacks
        self.movie = movie
        self.show_detail_callback = show_detail_callback
        self.toggle_favorite_callback = toggle_favorite_callback
        
        # Add drop shadow effect
        self.configure(relief=tk.RAISED, borderwidth=1)
        
        # Movie title and properties
        title = movie.get("name", "") or movie.get("title", "Untitled")
        image_url = movie.get("image_url") or movie.get("poster")
        
        # Image display
        if image_url:
            try:
                response = requests.get(image_url, stream=True, timeout=5)
                response.raise_for_status()
                
                img_data = Image.open(io.BytesIO(response.content))
                img_data = img_data.resize((180, 270), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img_data)
                
                self.img_label = tk.Label(self, image=photo, bg=COLORS["card_bg"], cursor="hand2")
                self.img_label.image = photo
                self.img_label.pack(pady=(0, 10))
                self.img_label.bind("<Button-1>", lambda e: show_detail_callback(movie))
            except Exception as e:
                print(f"Error loading image for {title}: {str(e)}")
                self._show_placeholder_image()
        else:
            self._show_placeholder_image()
        
        # Movie title with truncation
        if len(title) > 25:
            display_title = title[:25] + "..."
        else:
            display_title = title
            
        self.title_label = tk.Label(
            self, 
            text=display_title, 
            font=FONTS["subheading"], 
            fg=COLORS["dark_text"],
            bg=COLORS["card_bg"],
            wraplength=180,
            cursor="hand2"
        )
        self.title_label.pack(pady=(0, 10))
        self.title_label.bind("<Button-1>", lambda e: show_detail_callback(movie))
        
        # Button frame
        button_frame = tk.Frame(self, bg=COLORS["card_bg"])
        button_frame.pack(fill=tk.X, expand=True)
        
        # Favorite icon
        favorite_text = "★ Remove" if is_favorite else "☆ Favorite"
        self.fav_button = StyledButton(
            button_frame,
            text=favorite_text,
            bg_color=COLORS["accent"] if is_favorite else COLORS["primary"],
            font=FONTS["small_button"],
            command=lambda: toggle_favorite_callback(movie)
        )
        self.fav_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Details button
        self.details_button = StyledButton(
            button_frame,
            text="Details",
            bg_color=COLORS["secondary"],
            font=FONTS["small_button"],
            command=lambda: show_detail_callback(movie)
        )
        self.details_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        
        # Make the whole card clickable
        self.bind("<Button-1>", lambda e: show_detail_callback(movie))
        
    def _show_placeholder_image(self):
        """Display a placeholder image when no movie poster is available"""
        placeholder = Image.new("RGB", (180, 270), color="#D1D5DB")
        # Create a gradient effect for the placeholder
        for y in range(270):
            for x in range(180):
                # Create a gradient from top to bottom
                r = int(209 + (y / 270) * 20)
                g = int(213 + (y / 270) * 20)
                b = int(219 + (y / 270) * 20)
                placeholder.putpixel((x, y), (r, g, b))
                
        # Add text "No Image" to the placeholder
        draw = ImageDraw.Draw(placeholder)
        draw.text((90, 135), "No Image", fill="#6B7280", anchor="mm")
        
        photo = ImageTk.PhotoImage(placeholder)
        self.img_label = tk.Label(self, image=photo, bg=COLORS["card_bg"], cursor="hand2")
        self.img_label.image = photo
        self.img_label.pack(pady=(0, 10))
        self.img_label.bind("<Button-1>", lambda e: self.show_detail_callback(self.movie))

# ----- GUI -----
class MovieApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Watch2Watch - Your Movie Companion")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.configure(bg=COLORS["background"])
        
        # Set app icon
        try:
            self.iconbitmap("movie_app/assets/icon.ico")
        except:
            pass  # Ignore if icon file not found
            
        # Add window drop shadow and border
        self.attributes("-alpha", 0.97)  # Slight transparency
            
        # Center window on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 900) // 2
        y = (screen_height - 700) // 2
        self.geometry(f"900x700+{x}+{y}")
        
        self.username = None
        self.user_id = None
        self.search_service = SearchService()
        
        # Create custom style for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure(
            "TEntry",
            fieldbackground=COLORS["card_bg"],
            background=COLORS["card_bg"],
            foreground=COLORS["dark_text"],
            borderwidth=1,
            font=FONTS["normal"]
        )
        
        self.build_home_ui()
    
    def clear_window(self):
        """Clear all widgets from the window."""
        for widget in self.winfo_children():
            widget.destroy()

    def build_home_ui(self):
        """Home page with welcome and nav buttons."""
        self.clear_window()
        self.configure(bg=COLORS["background"])
        
        # Logo and welcome text
        logo_frame = tk.Frame(self, bg=COLORS["background"], pady=40)
        logo_frame.pack(fill=tk.X)
        
        logo_text = tk.Label(
            logo_frame, 
            text="Watch2Watch", 
            font=("Helvetica", 36, "bold"), 
            fg=COLORS["primary"],
            bg=COLORS["background"]
        )
        logo_text.pack()
        
        tagline = tk.Label(
            logo_frame, 
            text="Your Personal Movie Companion", 
            font=FONTS["subtitle"], 
            fg=COLORS["secondary"],
            bg=COLORS["background"]
        )
        tagline.pack(pady=10)
        
        # Main content frame
        content_frame = tk.Frame(self, bg=COLORS["background"], pady=20)
        content_frame.pack(expand=True)
        
        # Auth buttons
        login_btn = StyledButton(
            content_frame,
            text="LOGIN",
            width=20,
            height=2,
            command=lambda: self.build_auth_ui("login")
        )
        login_btn.pack(pady=10)
        
        register_btn = AccentButton(
            content_frame,
            text="REGISTER",
            width=20,
            height=2,
            command=lambda: self.build_auth_ui("register")
        )
        register_btn.pack(pady=10)
        
        # Footer
        footer = tk.Label(
            self, 
            text="© 2025 Watch2Watch - All Rights Reserved", 
            font=FONTS["small"], 
            fg=COLORS["dark_text"],
            bg=COLORS["background"]
        )
        footer.pack(side=tk.BOTTOM, pady=10)

    def build_auth_ui(self, mode):
        """Shows login or register input page based on mode."""
        self.clear_window()
        self.configure(bg=COLORS["background"])
        
        action_label = "Login" if mode == "login" else "Register"

        # Header
        back_btn = StyledButton(
            self,
            text="← Back",
            bg_color=COLORS["dark_bg"],
            font=FONTS["small_button"],
            command=self.build_home_ui
        )
        back_btn.pack(anchor=tk.NW, padx=20, pady=20)
        
        # Auth form container
        form_container = tk.Frame(
            self, 
            bg=COLORS["card_bg"],
            padx=40,
            pady=40,
            highlightbackground=COLORS["card_border"],
            highlightthickness=1
        )
        form_container.pack(expand=True, padx=40, pady=20)
        
        # Form title
        tk.Label(
            form_container, 
            text=f"{action_label} to Watch2Watch", 
            font=FONTS["title"], 
            fg=COLORS["primary"],
            bg=COLORS["card_bg"]
        ).pack(pady=(0, 30))

        # Username field
        tk.Label(
            form_container, 
            text="Username", 
            font=FONTS["normal"], 
            fg=COLORS["dark_text"],
            bg=COLORS["card_bg"],
            anchor=tk.W
        ).pack(fill=tk.X, pady=(0, 5))
        
        username_entry = tk.Entry(
            form_container,
            font=FONTS["normal"],
            bg=COLORS["background"],
            fg=COLORS["dark_text"],
            insertbackground=COLORS["dark_text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS["card_border"]
        )
        username_entry.pack(fill=tk.X, ipady=8, pady=(0, 15))

        # Password field
        tk.Label(
            form_container, 
            text="Password", 
            font=FONTS["normal"], 
            fg=COLORS["dark_text"],
            bg=COLORS["card_bg"],
            anchor=tk.W
        ).pack(fill=tk.X, pady=(0, 5))
        
        password_entry = tk.Entry(
            form_container,
            font=FONTS["normal"],
            bg=COLORS["background"],
            fg=COLORS["dark_text"],
            insertbackground=COLORS["dark_text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS["card_border"],
            show="•"
        )
        password_entry.pack(fill=tk.X, ipady=8, pady=(0, 30))

        def submit():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if not username or not password:
                messagebox.showwarning("Missing Info", "Please enter both username and password.")
                return

            try:
                response = send_request(mode, {"username": username, "password": password})
                if response["status"] == "success":
                    self.username = username
                    self.user_id = response.get("user_id")
                    self.build_main_ui()
                else:
                    messagebox.showerror(f"{action_label} Failed", response["message"])
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # Submit button
        submit_btn = StyledButton(
            form_container,
            text=action_label.upper(),
            width=20,
            height=2,
            command=submit
        )
        submit_btn.pack(pady=10)
        
        # Switch to other auth mode
        other_mode = "register" if mode == "login" else "login"
        other_label = "Need an account? Register" if mode == "login" else "Already have an account? Login"
        
        switch_btn = tk.Label(
            form_container,
            text=other_label,
            font=FONTS["normal"],
            fg=COLORS["secondary"],
            bg=COLORS["card_bg"],
            cursor="hand2"
        )
        switch_btn.pack(pady=15)
        switch_btn.bind("<Button-1>", lambda e: self.build_auth_ui(other_mode))

    def build_main_ui(self):
        self.clear_window()
        self.configure(bg=COLORS["background"])

        # Create main container
        main_container = tk.Frame(self, bg=COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left sidebar
        sidebar = tk.Frame(main_container, bg=COLORS["dark_bg"], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)  # Prevent sidebar from shrinking
        
        # App logo in sidebar
        logo_frame = tk.Frame(sidebar, bg=COLORS["dark_bg"], pady=20)
        logo_frame.pack(fill=tk.X)
        
        logo_text = tk.Label(
            logo_frame, 
            text="W2W", 
            font=("Helvetica", 24, "bold"), 
            fg=COLORS["light_text"],
            bg=COLORS["dark_bg"]
        )
        logo_text.pack()
        
        # User info in sidebar
        user_frame = tk.Frame(sidebar, bg=COLORS["dark_bg"], pady=10)
        user_frame.pack(fill=tk.X)
        
        user_icon = tk.Label(
            user_frame,
            text="👤",
            font=("Helvetica", 24),
            fg=COLORS["light_text"],
            bg=COLORS["dark_bg"]
        )
        user_icon.pack()
        
        user_label = tk.Label(
            user_frame,
            text=self.username,
            font=FONTS["normal"],
            fg=COLORS["light_text"],
            bg=COLORS["dark_bg"]
        )
        user_label.pack(pady=5)
        
        # Navigation buttons
        nav_frame = tk.Frame(sidebar, bg=COLORS["dark_bg"], pady=20)
        nav_frame.pack(fill=tk.X)
        
        search_btn = tk.Button(
            nav_frame,
            text="🔍  Search",
            font=FONTS["button"],
            fg=COLORS["light_text"],
            bg=COLORS["dark_bg"],
            activebackground=COLORS["primary"],
            activeforeground=COLORS["light_text"],
            bd=0,
            cursor="hand2",
            relief=tk.FLAT,
            anchor=tk.W,
            padx=20,
            pady=10,
            command=self.show_search_view
        )
        search_btn.pack(fill=tk.X, pady=5)
        
        favorites_btn = tk.Button(
            nav_frame,
            text="★  Favorites",
            font=FONTS["button"],
            fg=COLORS["light_text"],
            bg=COLORS["dark_bg"],
            activebackground=COLORS["primary"],
            activeforeground=COLORS["light_text"],
            bd=0,
            cursor="hand2",
            relief=tk.FLAT,
            anchor=tk.W,
            padx=20,
            pady=10,
            command=self.show_favorites_view
        )
        favorites_btn.pack(fill=tk.X, pady=5)
        
        # Logout button at bottom of sidebar
        logout_frame = tk.Frame(sidebar, bg=COLORS["dark_bg"])
        logout_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        
        logout_btn = tk.Button(
            logout_frame,
            text="⟲  Logout",
            font=FONTS["button"],
            fg=COLORS["light_text"],
            bg=COLORS["dark_bg"],
            activebackground=COLORS["error"],
            activeforeground=COLORS["light_text"],
            bd=0,
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.logout
        )
        logout_btn.pack(fill=tk.X)

        # Main content area
        self.content_panel = tk.Frame(main_container, bg=COLORS["background"])
        self.content_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Default to search view
        self.show_search_view()
        
    def show_search_view(self):
        """Display the search interface."""
        for widget in self.content_panel.winfo_children():
            widget.destroy()

        # Top header area
        header = tk.Frame(self.content_panel, bg=COLORS["background"], pady=20)
        header.pack(fill=tk.X, padx=20)
        
        # Page title
        title_label = tk.Label(
            header,
            text="Search Movies",
            font=FONTS["title"],
            fg=COLORS["primary"],
            bg=COLORS["background"]
        )
        title_label.pack(anchor=tk.W)
        
        # Search bar container
        search_container = tk.Frame(self.content_panel, bg=COLORS["background"], pady=10)
        search_container.pack(fill=tk.X, padx=20)
        
        # Search entry
        self.search_box = tk.Entry(
            search_container,
            font=FONTS["normal"],
            bg=COLORS["card_bg"],
            fg=COLORS["dark_text"],
            insertbackground=COLORS["dark_text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS["card_border"]
        )
        self.search_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        
        # Search button
        search_btn = StyledButton(
            search_container,
            text="Search",
            command=self.search_movie
        )
        search_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Bind Enter key to search
        self.search_box.bind('<Return>', lambda event: self.search_movie())

        # Search results area
        self.results_frame = tk.Frame(self.content_panel, bg=COLORS["background"])
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Initial message
        welcome_msg = tk.Label(
            self.results_frame,
            text="Enter a movie title to search",
            font=FONTS["heading"],
            fg=COLORS["dark_text"],
            bg=COLORS["background"]
        )
        welcome_msg.pack(pady=50)

    def remove_favorite(self, movie):
        """Handle removing a movie from favorites."""
        try:
            with open("movie_app/db/users.json", "r") as f:
                users_data = json.load(f)

            user_data = next((user for user in users_data if user["id"] == self.user_id), None)

            if user_data and "favorites" in user_data:
                if movie in user_data["favorites"]:
                    user_data["favorites"].remove(movie)

                    with open("movie_app/db/users.json", "w") as f:
                        json.dump(users_data, f, indent=4)

                    messagebox.showinfo("Removed", f"{movie['title']} has been removed from favorites.")
                    self.show_favorites_view()  # Refresh favorites view
                else:
                    messagebox.showwarning("Not Found", "Movie not found in favorites.")
            else:
                messagebox.showwarning("Error", "User or favorites not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error removing favorite: {str(e)}")

    def register(self):
        """Handle user registration."""
        username = simpledialog.askstring("Register", "Enter username:")
        password = simpledialog.askstring("Register", "Enter password:", show='*')
        if username and password:
            try:
                response = send_request("register", {"username": username, "password": password})
                messagebox.showinfo("Register", response["message"])
            except Exception as e:
                messagebox.showerror("Error", f"Error during registration: {str(e)}")

    def login(self):
        """Handle user login."""
        username = simpledialog.askstring("Login", "Enter username:")
        password = simpledialog.askstring("Login", "Enter password:", show='*')
        if username and password:
            try:
                response = send_request("login", {"username": username, "password": password})
                if response["status"] == "success":
                    self.username = username
                    self.user_id = response.get("user_id") # Assuming the server returns a user_id
                    self.build_main_ui()
                else:
                    messagebox.showerror("Login Failed", response["message"])
            except Exception as e:
                messagebox.showerror("Error", f"Error during login: {str(e)}")

    def logout(self):
        """Logout the user."""
        self.username = None
        self.user_id = None
        self.build_home_ui()
    
    def search_movie(self):
        """Search for a movie."""
        query = self.search_box.get().strip()
        query = query.replace("\n", "").replace("\r", "")  # Clean newlines

        if not query:
            messagebox.showinfo("Info", "Please enter a search term")
            return

        # Show a loading indicator
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        loading_label = tk.Label(self.results_frame, text="Searching, please wait...", font=("Arial", 12))
        loading_label.pack(pady=20)
        self.results_frame.update()  # Force update to show loading message

        try:
            response = send_request("search", {"query": query})
            #print(f"Server response: {response}")  # Debugging line to inspect the API response

            # Clear loading indicator
            for widget in self.results_frame.winfo_children():
                widget.destroy()

            if response and "status" in response:
                if response["status"] == "success":
                    results = response.get("results", [])
                    if results:
                        self.display_search_results(results)
                        #print("Search Results:")
                        for result in results:
                            print(f"- {result.get('name', 'Unknown')}")
                    else:
                        no_results = tk.Label(self.results_frame, text=f"No results found for '{query}'", font=("Arial", 12))
                        no_results.pack(pady=20)
                else:
                    error_msg = response.get("message", "Unknown error occurred")
                    error_label = tk.Label(self.results_frame, text=f"Error: {error_msg}", font=("Arial", 12), fg="red")
                    error_label.pack(pady=20)
            else:
                error_label = tk.Label(self.results_frame, text="Received invalid response format from server", font=("Arial", 12), fg="red")
                error_label.pack(pady=20)
        except Exception as e:
            for widget in self.results_frame.winfo_children():
                widget.destroy()
            error_label = tk.Label(self.results_frame, text=f"Error: {str(e)}", font=("Arial", 12), fg="red")
            error_label.pack(pady=20)
            print(f"Exception during search: {str(e)}")
    
    def show_movie_detail(self, movie):
        """Display a single movie page with more info."""
        for widget in self.content_panel.winfo_children():
            widget.destroy()    

        # Get movie information
        title = movie.get("name", "") or movie.get("title", "Untitled")
        movie_id = movie.get("id")
        image_url = movie.get("image_url") or movie.get("poster")

        # Create header container
        header_frame = tk.Frame(self.content_panel, pady=20)
        header_frame.pack(fill=tk.X)

        # Back button at top
        back_btn = tk.Button(header_frame, text="⬅ Back", command=self.show_search_view)
        back_btn.pack(anchor="w", padx=20, pady=(0, 20))

        # Content area
        content_frame = tk.Frame(self.content_panel)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # Left side - Poster image
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, padx=(0, 20))

        if image_url:
            try:
                # Fetch and display the poster image
                response = requests.get(image_url, stream=True, timeout=5)
                response.raise_for_status()
                
                img_data = Image.open(io.BytesIO(response.content))
                img_data = img_data.resize((200, 300), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img_data)
                
                img_label = tk.Label(left_frame, image=photo)
                img_label.image = photo  # Keep reference
                img_label.pack()
            except Exception as e:
                print(f"Error loading detail image: {str(e)}")
                placeholder = Image.new("RGB", (200, 300), color=(200, 200, 200))
                photo = ImageTk.PhotoImage(placeholder)
                img_label = tk.Label(left_frame, image=photo)
                img_label.image = photo
                img_label.pack()
        else:
            # No image available
            placeholder = Image.new("RGB", (200, 300), color=(200, 200, 200))
            photo = ImageTk.PhotoImage(placeholder)
            img_label = tk.Label(left_frame, image=photo)
            img_label.image = photo
            img_label.pack()

        # Right side - Movie information
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Movie title
        tk.Label(right_frame, text=title, font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 10))

        # Check if movie is in favorites
        is_favorite = False
        try:
            with open("movie_app/db/users.json", "r") as f:
                users_data = json.load(f)
                
            # Handle both dictionary and list format
            if isinstance(users_data, dict):
                for username, user_data in users_data.items():
                    if user_data.get("id") == self.user_id:
                        favorites = user_data.get("favorites", [])
                        # Convert to strings for comparison
                        favorite_ids = [str(fav_id) for fav_id in favorites]
                        is_favorite = str(movie_id) in favorite_ids
                        break
            else:
                for user_data in users_data:
                    if user_data.get("id") == self.user_id:
                        favorites = user_data.get("favorites", [])
                        # Convert to strings for comparison
                        favorite_ids = [str(fav_id) for fav_id in favorites]
                        is_favorite = str(movie_id) in favorite_ids
                        break
        except Exception as e:
            print(f"Error checking favorites: {str(e)}")

        # Favorite button
        favorite_text = "⭐ Remove from Favorites" if is_favorite else "⭐ Add to Favorites"
        favorite_btn = tk.Button(
            right_frame, 
            text=favorite_text,
            command=lambda: self.toggle_favorite(movie)
        )
        favorite_btn.pack(anchor="w", pady=10)

        # Additional movie details
        # Try to get more details if possible
        try:
            # First try using the search service directly
            movie_details = self.search_service.get_movie_by_id(movie_id)
            
            if not movie_details:
                # Fall back to the server request
                movie_detail_response = send_request("get_movie_details", {"movie_id": movie_id})
                if movie_detail_response and movie_detail_response.get("status") == "success":
                    movie_details = movie_detail_response.get("data", {})
            
            if movie_details:
                # Add any available details
                if movie_details.get("year"):
                    tk.Label(right_frame, text=f"Year: {movie_details['year']}", font=("Arial", 12)).pack(anchor="w", pady=3)
                
                if movie_details.get("genre"):
                    tk.Label(right_frame, text=f"Genre: {movie_details['genre']}", font=("Arial", 12)).pack(anchor="w", pady=3)
                
                if movie_details.get("plot"):
                    tk.Label(right_frame, text="Plot:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 3))
                    plot_text = tk.Text(right_frame, wrap=tk.WORD, height=8, width=40)
                    plot_text.insert(tk.END, movie_details['plot'])
                    plot_text.config(state=tk.DISABLED)  # Make read-only
                    plot_text.pack(anchor="w", pady=3)
        except Exception as e:
            print(f"Error fetching movie details: {str(e)}")

        # Create a container for reviews section at the bottom of the page
        reviews_container = tk.Frame(self.content_panel)
        reviews_container.pack(fill=tk.X, expand=True, padx=20, pady=20)
        
        # Reviews header
        tk.Label(reviews_container, text="Reviews", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Load existing comments
        comments = self.load_comments(movie_id)
        
        # Comments display area with scrollbar
        comments_frame = tk.Frame(reviews_container)
        comments_frame.pack(fill=tk.X, expand=True)
        
        if comments:
            # Create a scrollable area for comments if there are many
            comments_canvas = tk.Canvas(comments_frame, height=150)
            comments_scrollbar = tk.Scrollbar(comments_frame, orient="vertical", command=comments_canvas.yview)
            scrollable_comments = tk.Frame(comments_canvas)
            
            scrollable_comments.bind(
                "<Configure>",
                lambda e: comments_canvas.configure(scrollregion=comments_canvas.bbox("all"))
            )
            
            comments_canvas.create_window((0, 0), window=scrollable_comments, anchor="nw")
            comments_canvas.configure(yscrollcommand=comments_scrollbar.set)
            
            comments_canvas.pack(side="left", fill="both", expand=True)
            comments_scrollbar.pack(side="right", fill="y")
            
            # Display each comment
            for i, comment in enumerate(comments):
                comment_frame = tk.Frame(scrollable_comments, bd=1, relief=tk.SOLID, padx=10, pady=10)
                comment_frame.pack(fill=tk.X, pady=5)
                
                # Format: Comment #1: [comment text]
                comment_text = f"Comment #{i+1}: {comment}"
                tk.Label(comment_frame, text=comment_text, wraplength=400, justify=tk.LEFT).pack(anchor="w")
        else:
            tk.Label(comments_frame, text="No reviews yet for this movie.", font=("Arial", 10)).pack(anchor="w")
        
        # Add comment section
        comment_input_frame = tk.Frame(reviews_container)
        comment_input_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(comment_input_frame, text="Write a review:", font=("Arial", 12)).pack(anchor="w", pady=5)
        
        # Text area for comment input
        comment_text = tk.Text(comment_input_frame, height=2, width=30)
        comment_text.pack(pady=5)
        
        # Submit button
        def submit_comment():
            new_comment = comment_text.get("1.0", tk.END).strip()
            if new_comment:
                success = self.add_comment(movie_id, new_comment)
                if success:
                    # Clear the comment input field
                    comment_text.delete("1.0", tk.END)
                    # Refresh the movie detail view to show the new comment
                    self.show_movie_detail(movie)
            else:
                messagebox.showinfo("Empty Comment", "Please write something before submitting.")
        # Add the submit button - THIS WAS THE MISSING PART
        submit_btn = tk.Button(comment_input_frame, text="Submit Review", command=submit_comment)
        submit_btn.pack(pady=5)
    
    
    def load_comments(self, movie_id):
        """Load comments for a specific movie from comments.json."""
        try:
            # Ensure movie_id is a string for consistent lookup
            movie_id_str = str(movie_id)
            
            try:
                with open("movie_app/db/comments.json", "r") as f:
                    comments_data = json.load(f)
            except FileNotFoundError:
                # Create the file if it doesn't exist
                comments_data = {}
                with open("movie_app/db/comments.json", "w") as f:
                    json.dump(comments_data, f, indent=4)
            
            # Return comments for this movie, or an empty list if none exist
            return comments_data.get(movie_id_str, {}).get("comments", [])
        
        except Exception as e:
            print(f"Error loading comments: {str(e)}")
            return []

    def add_comment(self, movie_id, comment_text):
        """Add a comment to a movie in comments.json."""
        try:
            # Ensure movie_id is a string for consistent storage
            movie_id_str = str(movie_id)
            
            # Load existing comments
            try:
                with open("movie_app/db/comments.json", "r") as f:
                    comments_data = json.load(f)
            except FileNotFoundError:
                comments_data = {}
            except json.JSONDecodeError:
                comments_data = {}
            
            # Initialize movie entry if it doesn't exist
            if movie_id_str not in comments_data:
                comments_data[movie_id_str] = {"comments": []}
            
            # Add the new comment
            comments_data[movie_id_str]["comments"].append(comment_text)
            
            # Save back to file
            with open("movie_app/db/comments.json", "w") as f:
                json.dump(comments_data, f, indent=4)
            
            messagebox.showinfo("Success", "Your review has been added!")
            return True
        
        except Exception as e:
            print(f"Error adding comment: {str(e)}")
            messagebox.showerror("Error", f"Could not add your review: {str(e)}")
            return False
    
    
    
    # Also need to update the toggle_favorite function to ensure consistent ID format
    def toggle_favorite(self, movie):
        """Add or remove a movie ID to/from favorites."""
        try:
            with open("movie_app/db/users.json", "r") as f:
                users_data = json.load(f)

            # Handle both dictionary and list format for users data
            if isinstance(users_data, dict):
                # Dictionary format (username: user_data)
                for username, user_data in users_data.items():
                    if user_data["id"] == self.user_id:
                        favorites = user_data.get("favorites", [])
                        movie_id = movie.get("id")
                        
                        # Convert all IDs to strings for consistent comparison
                        favorite_ids = [str(fav_id) for fav_id in favorites]
                        movie_id_str = str(movie_id)
                        
                        # Debug print
                        print(f"Current favorites before toggle: {favorites}")
                        print(f"Toggling movie: {movie.get('name', 'Unnamed')} with ID: {movie_id_str}")

                        # Check if movie is in favorites
                        is_favorite = movie_id_str in favorite_ids
                        if is_favorite:
                            # Find and remove the ID (keeping its original format)
                            for i, fav_id in enumerate(favorites):
                                if str(fav_id) == movie_id_str:
                                    del favorites[i]
                                    break
                            messagebox.showinfo("Removed", f"{movie.get('name', 'Movie')} removed from favorites.")
                        else:
                            # Add it in its original format
                            favorites.append(movie_id)
                            messagebox.showinfo("Added", f"{movie.get('name', 'Movie')} added to favorites.")

                        user_data["favorites"] = favorites

                        with open("movie_app/db/users.json", "w") as f:
                            json.dump(users_data, f, indent=4)

                        print(f"Current favorites after toggle: {favorites}")  # Debug print
                        
                        # Refresh the view based on current view
                        if hasattr(self, 'search_box') and self.search_box.winfo_exists():
                            # We're in search view - just refresh current view
                            self.show_search_view()
                        else:
                            # We're likely in favorites view - refresh that
                            self.show_favorites_view()
                        return
            else:
                # List format (list of user objects)
                for user_data in users_data:
                    if user_data["id"] == self.user_id:
                        favorites = user_data.get("favorites", [])
                        movie_id = movie.get("id")
                        
                        # Convert all IDs to strings for consistent comparison
                        favorite_ids = [str(fav_id) for fav_id in favorites]
                        movie_id_str = str(movie_id)
                        
                        # Debug print
                        print(f"Current favorites before toggle: {favorites}")
                        print(f"Toggling movie: {movie.get('name', 'Unnamed')} with ID: {movie_id_str}")

                        # Check if movie is in favorites
                        is_favorite = movie_id_str in favorite_ids
                        if is_favorite:
                            # Find and remove the ID (keeping its original format)
                            for i, fav_id in enumerate(favorites):
                                if str(fav_id) == movie_id_str:
                                    del favorites[i]
                                    break
                            messagebox.showinfo("Removed", f"{movie.get('name', 'Movie')} removed from favorites.")
                        else:
                            # Add it in its original format
                            favorites.append(movie_id)
                            messagebox.showinfo("Added", f"{movie.get('name', 'Movie')} added to favorites.")

                        user_data["favorites"] = favorites

                        with open("movie_app/db/users.json", "w") as f:
                            json.dump(users_data, f, indent=4)

                        print(f"Current favorites after toggle: {favorites}")  # Debug print
                        
                        # Refresh the view based on current view
                        if hasattr(self, 'search_box') and self.search_box.winfo_exists():
                            # We're in search view - just refresh current view
                            self.show_search_view()
                        else:
                            # We're likely in favorites view - refresh that
                            self.show_favorites_view()
                        return

            messagebox.showerror("Error", "User not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error toggling favorite: {str(e)}")
    
    def display_search_results(self, results):
        """Display movie search results as clickable cards with posters."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            no_results_label = tk.Label(self.results_frame, text="No results found", font=("Arial", 12))
            no_results_label.pack(pady=10)
            return

        # Create a scrollable frame for results
        canvas = tk.Canvas(self.results_frame)
        scrollbar = tk.Scrollbar(self.results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Set up grid for movie cards
        columns = 2  # Using fewer columns to allow more space for each movie
        row = 0
        col = 0

        # Load the user's favorites from the database
        favorite_ids = set()
        try:
            with open("movie_app/db/users.json", "r") as f:
                users_data = json.load(f)
                
            # Find user by ID and get their favorites
            for username, user_data in users_data.items():
                if user_data.get("id") == self.user_id:
                    favorite_ids = set(user_data.get("favorites", []))
                    break
        except Exception as e:
            print(f"Error loading favorites: {str(e)}")

        for movie in results:
            movie_id = movie.get("id")
            title = movie.get("name", "Untitled") 
            image_url = movie.get("image_url")
            
            # Create card frame
            card_frame = tk.Frame(scrollable_frame, bd=1, relief=tk.SOLID, padx=10, pady=10, width=250)
            card_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
            # Display poster image
            if image_url:
                try:
                    # Use requests to fetch the image
                    response = requests.get(image_url, stream=True, timeout=5)
                    response.raise_for_status()
                    
                    # Convert the image data
                    img_data = Image.open(io.BytesIO(response.content))
                    img_data = img_data.resize((150, 225), Image.LANCZOS)  # LANCZOS is better for downsampling
                    photo = ImageTk.PhotoImage(img_data)
                    
                    # Create and place the image label
                    img_label = tk.Label(card_frame, image=photo)
                    img_label.image = photo  # Keep reference to prevent garbage collection
                    img_label.pack(pady=(0, 10))
                    
                    print(f"Successfully loaded image for {title}")
                except Exception as e:
                    print(f"Error loading image for {title}: {str(e)}")
                    # Display placeholder on error
                    placeholder = Image.new("RGB", (150, 225), color=(200, 200, 200))
                    photo = ImageTk.PhotoImage(placeholder)
                    img_label = tk.Label(card_frame, image=photo)
                    img_label.image = photo
                    img_label.pack(pady=(0, 10))
            else:
                # No image URL provided
                placeholder = Image.new("RGB", (150, 225), color=(200, 200, 200))
                photo = ImageTk.PhotoImage(placeholder)
                img_label = tk.Label(card_frame, image=photo)
                img_label.image = photo
                img_label.pack(pady=(0, 10))
            
            # Display movie title
            title_label = tk.Label(card_frame, text=title, font=("Arial", 12, "bold"), wraplength=200)
            title_label.pack(pady=(0, 10))
            
            # Add favorite button
            is_favorite = movie_id in favorite_ids
            favorite_text = "⭐ Remove from Favorites" if is_favorite else "⭐ Add to Favorites"
            favorite_btn = tk.Button(
                card_frame, 
                text=favorite_text, 
                command=lambda m=movie: self.toggle_favorite(m)
            )
            favorite_btn.pack(pady=5)
            
            # Add view details button
            details_btn = tk.Button(
                card_frame,
                text="📋 View Details",
                command=lambda m=movie: self.show_movie_detail(m)
            )
            details_btn.pack(pady=5)
            
            # Make card clickable
            card_frame.bind("<Button-1>", lambda e, m=movie: self.show_movie_detail(m))
            img_label.bind("<Button-1>", lambda e, m=movie: self.show_movie_detail(m))
            title_label.bind("<Button-1>", lambda e, m=movie: self.show_movie_detail(m))
            
            # Update row/column for next card
            col += 1
            if col >= columns:
                col = 0
                row += 1        
    
    def remove_favorite_by_id(self, movie_id):
        try:
            with open("movie_app/db/users.json", "r") as f:
                users_data = json.load(f)

            for user_data in users_data.values():
                if user_data["id"] == self.user_id:
                    if movie_id in user_data["favorites"]:
                        user_data["favorites"].remove(movie_id)
                        with open("movie_app/db/users.json", "w") as f:
                            json.dump(users_data, f, indent=4)

                        messagebox.showinfo("Removed", f"Movie {movie_id} removed from favorites.")
                        self.show_favorites_view()
                        return
                    else:
                        messagebox.showwarning("Not Found", "Movie ID not in favorites.")
                        return
        except Exception as e:
            messagebox.showerror("Error", f"Error removing favorite: {str(e)}")
    
    def show_favorites_view(self):
        """Display the user's favorite movies in a grid layout with clickable cards."""
        for widget in self.content_panel.winfo_children():
            widget.destroy()
            
        # Header
        tk.Label(self.content_panel, text="⭐ Your Favorites", font=("Arial", 14), bg="#ecf0f1").pack(pady=20)
        
        # Create results frame
        results_frame = tk.Frame(self.content_panel)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a scrollable frame for results
        canvas = tk.Canvas(results_frame)
        scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Show loading indicator
        loading_label = tk.Label(scrollable_frame, text="Loading favorites...", font=("Arial", 12))
        loading_label.pack(pady=20)
        self.update()  # Force update to show loading message
        
        try:
            # Load favorite IDs from user data
            favorite_ids = []
            try:
                with open("movie_app/db/users.json", "r") as f:
                    users_data = json.load(f)
                
                # Handle both dictionary and list format for users data
                if isinstance(users_data, dict):
                    # Dictionary format (username: user_data)
                    for username, user_data in users_data.items():
                        if user_data.get("id") == self.user_id:
                            favorite_ids = user_data.get("favorites", [])
                            break
                else:
                    # List format (list of user objects)
                    for user_data in users_data:
                        if user_data.get("id") == self.user_id:
                            favorite_ids = user_data.get("favorites", [])
                            break
            
            except Exception as e:
                print(f"Error loading user data: {str(e)}")
                
            # Convert all IDs to strings for consistent comparison
            favorite_ids = [str(fav_id) for fav_id in favorite_ids]
            print(f"Favorite IDs (converted to strings): {favorite_ids}")
            
            if not favorite_ids:
                loading_label.destroy()
                tk.Label(scrollable_frame, text="You have no favorites yet!", font=("Arial", 12)).pack(pady=20)
                return
            
            # Use the search service to fetch movie details
            favorited_movies = []
            
            # Use search service to fetch movie details for each favorite ID
            for fav_id in favorite_ids:
                try:
                    print(f"Fetching details for movie ID: {fav_id}")
                    # Use the search service directly to get movie details
                    movie_data = self.search_service.get_movie_by_id(fav_id)
                    
                    if movie_data:
                        # Ensure the movie has an ID field
                        if "id" not in movie_data:
                            movie_data["id"] = fav_id
                        
                        # Get image URL using search service
                        if "poster" in movie_data:
                            movie_data["image_url"] = movie_data["poster"]
                        else:
                            movie_data["image_url"] = self.search_service.get_movie_image(fav_id)
                        
                        # Add the complete movie data to our list
                        favorited_movies.append(movie_data)
                        print(f"Successfully fetched movie details for ID: {fav_id}")
                    else:
                        # If we couldn't get details, create a placeholder
                        placeholder_movie = {
                            "id": fav_id,
                            "name": f"Movie #{fav_id}",
                            "image_url": None  # No image available
                        }
                        favorited_movies.append(placeholder_movie)
                        print(f"Created placeholder for movie ID: {fav_id}")
                except Exception as e:
                    print(f"Error fetching individual movie with ID {fav_id}: {str(e)}")
                    # Create a placeholder for the movie
                    placeholder_movie = {
                        "id": fav_id,
                        "name": f"Movie #{fav_id}",
                        "image_url": None
                    }
                    favorited_movies.append(placeholder_movie)
            
            # Remove loading message
            loading_label.destroy()
            
            # If no movies were found at all
            if not favorited_movies:
                tk.Label(scrollable_frame, text="Could not load favorite movies.", font=("Arial", 12)).pack(pady=20)
                return
            
            # Set up grid for movie cards
            columns = 2
            row = 0
            col = 0
                
            # Display each favorite movie
            for movie in favorited_movies:
                movie_id = movie.get("id")
                title = movie.get("name", "") or movie.get("title", f"Movie #{movie_id}")  # Get title from either field
                image_url = movie.get("image_url") or movie.get("poster")  # Get image from either field
                
                print(f"Displaying favorite: {title} (ID: {movie_id}) - Image URL: {image_url}")
                
                # Create card frame
                card_frame = tk.Frame(scrollable_frame, bd=1, relief=tk.SOLID, padx=10, pady=10, width=250)
                card_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
                
                # Display poster image
                if image_url:
                    try:
                        # Use requests to fetch the image
                        response = requests.get(image_url, stream=True, timeout=5)
                        response.raise_for_status()
                        
                        # Convert the image data
                        img_data = Image.open(io.BytesIO(response.content))
                        img_data = img_data.resize((150, 225), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img_data)
                        
                        # Create and place the image label
                        img_label = tk.Label(card_frame, image=photo)
                        img_label.image = photo  # Keep reference
                        img_label.pack(pady=(0, 10))
                        
                        print(f"Successfully loaded image for {title}")
                    except Exception as e:
                        print(f"Error loading image for {title}: {str(e)}")
                        # Display placeholder on error
                        placeholder = Image.new("RGB", (150, 225), color=(200, 200, 200))
                        photo = ImageTk.PhotoImage(placeholder)
                        img_label = tk.Label(card_frame, image=photo)
                        img_label.image = photo
                        img_label.pack(pady=(0, 10))
                else:
                    # No image URL provided
                    placeholder = Image.new("RGB", (150, 225), color=(200, 200, 200))
                    photo = ImageTk.PhotoImage(placeholder)
                    img_label = tk.Label(card_frame, image=photo)
                    img_label.image = photo
                    img_label.pack(pady=(0, 10))
                    print(f"Using placeholder image for {title} (no image URL available)")
                
                # Display movie title
                title_label = tk.Label(card_frame, text=title, font=("Arial", 12, "bold"), wraplength=200)
                title_label.pack(pady=(0, 10))
                
                # Add remove button
                favorite_btn = tk.Button(
                    card_frame, 
                    text="⭐ Remove from Favorites", 
                    command=lambda m=movie: self.toggle_favorite(m)
                )
                favorite_btn.pack(pady=5)
                
                # Add view details button
                details_btn = tk.Button(
                    card_frame,
                    text="📋 View Details",
                    command=lambda m=movie: self.show_movie_detail(m)
                )
                details_btn.pack(pady=5)
                
                # Make card clickable
                card_frame.bind("<Button-1>", lambda e, m=movie: self.show_movie_detail(m))
                img_label.bind("<Button-1>", lambda e, m=movie: self.show_movie_detail(m))
                title_label.bind("<Button-1>", lambda e, m=movie: self.show_movie_detail(m))
                
                # Update row/column for next card
                col += 1
                if col >= columns:
                    col = 0
                    row += 1
                    
        except FileNotFoundError:
            loading_label.destroy()
            tk.Label(scrollable_frame, text="User database not found.", font=("Arial", 12)).pack(pady=20)
        except json.JSONDecodeError:
            loading_label.destroy()
            tk.Label(scrollable_frame, text="User database is corrupted.", font=("Arial", 12)).pack(pady=20)
        except Exception as e:
            loading_label.destroy()
            tk.Label(scrollable_frame, text=f"Error loading favorites: {str(e)}", font=("Arial", 12)).pack(pady=20)
            print(f"Exception in favorites view: {str(e)}")

if __name__ == "__main__":
    app = MovieApp()
    app.mainloop()
