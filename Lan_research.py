import customtkinter as ctk
import cv2
import socket
import threading
import pickle
import struct
import numpy as np
from PIL import Image, ImageTk
import time
from tkinter import filedialog, messagebox
import pyautogui
import os
import pyaudio
import wave
import io
import subprocess
import json
from tkinter import scrolledtext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import hashlib
import secrets

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SecurityManager:
    """Handles encryption and decryption of messages and files"""
    
    def __init__(self):
        self.key = None
        self.cipher = None
        self.shared_secret = None
        
    def generate_session_key(self, password="ZeroConnect2024"):
        """Generate encryption key from password"""
        password_bytes = password.encode('utf-8')
        salt = b'ZeroConnectSalt!'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        self.key = key
        self.cipher = Fernet(key)
        return key
    
    def encrypt_data(self, data):
        """Encrypt data (string or bytes)"""
        if not self.cipher:
            return data
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data"""
        if not self.cipher:
            return encrypted_data
        
        try:
            return self.cipher.decrypt(encrypted_data)
        except:
            return encrypted_data

class PeerDiscovery:
    """Handles peer discovery on the local network"""
    
    def __init__(self, callback):
        self.callback = callback
        self.peers = {}
        self.discovery_port = 9998
        self.running = False
        self.broadcast_socket = None
        self.listen_socket = None
        
    def start_discovery(self):
        """Start peer discovery service"""
        self.running = True
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.listen_for_peers, daemon=True).start()
    
    def stop_discovery(self):
        """Stop peer discovery service"""
        self.running = False
        if self.broadcast_socket:
            self.broadcast_socket.close()
        if self.listen_socket:
            self.listen_socket.close()
    
    def broadcast_presence(self):
        """Broadcast presence to network"""
        try:
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            while self.running:
                message = {
                    "type": "peer_announcement",
                    "name": getattr(self.callback, 'user_name', {}).get() or "Anonymous",
                    "ip": self.get_local_ip(),
                    "port": 9999
                }
                
                data = json.dumps(message).encode('utf-8')
                # Broadcast immediately on start, then every 3 seconds
                self.broadcast_socket.sendto(data, ('<broadcast>', self.discovery_port))
                time.sleep(3)  # Reduced from 5 to 3 for faster discovery
                
        except Exception as e:
            print(f"Broadcast error: {e}")
    
    def listen_for_peers(self):
        """Listen for peer announcements"""
        try:
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listen_socket.bind(('', self.discovery_port))
            
            while self.running:
                try:
                    data, addr = self.listen_socket.recvfrom(1024)
                    message = json.loads(data.decode('utf-8'))
                    
                    if message.get('type') == 'peer_announcement':
                        peer_ip = message.get('ip')
                        peer_name = message.get('name', 'Unknown')
                        
                        # Don't add ourselves and validate IP
                        if peer_ip != self.get_local_ip() and peer_ip:
                            self.peers[peer_ip] = {
                                'name': peer_name,
                                'last_seen': time.time()
                            }
                            
                            # Update GUI immediately
                            if hasattr(self.callback, 'update_peer_list'):
                                self.callback.update_peer_list(self.peers)
                                
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"Listen error detail: {e}")
                
        except Exception as e:
            print(f"Listen socket error: {e}")
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def cleanup_old_peers(self):
        """Remove peers that haven't been seen recently"""
        current_time = time.time()
        peers_to_remove = []
        
        for ip, info in self.peers.items():
            if current_time - info['last_seen'] > 15:
                peers_to_remove.append(ip)
        
        for ip in peers_to_remove:
            del self.peers[ip]
        
        if hasattr(self.callback, 'update_peer_list'):
            self.callback.update_peer_list(self.peers)

class ZeroConnect:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("ZeroConnect - Secure P2P Communication Platform")
        
        # Initialize security
        self.security_manager = SecurityManager()
        self.security_manager.generate_session_key()
        
        # Initialize peer discovery
        self.peer_discovery = PeerDiscovery(self)
        self.available_peers = {}
        
        # Get screen dimensions for responsive sizing
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Responsive window sizing (80% of screen, with min/max limits)
        self.window_width = max(1000, min(int(screen_width * 0.8), 1920))
        self.window_height = max(700, min(int(screen_height * 0.85), 1080))
        
        # Center window on screen
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        self.window.minsize(900, 650)
        
        # Responsive sizing factors
        self.is_large_screen = screen_width >= 1920
        self.is_medium_screen = 1366 <= screen_width < 1920
        self.is_small_screen = screen_width < 1366
        
        # Dynamic sizing based on screen
        if self.is_large_screen:
            self.sidebar_width = 350
            self.font_size_large = 18
            self.font_size_normal = 14
            self.font_size_small = 12
            self.button_height = 45
            self.spacing = 15
        elif self.is_medium_screen:
            self.sidebar_width = 300
            self.font_size_large = 16
            self.font_size_normal = 12
            self.font_size_small = 10
            self.button_height = 40
            self.spacing = 12
        else:
            self.sidebar_width = 280
            self.font_size_large = 14
            self.font_size_normal = 11
            self.font_size_small = 9
            self.button_height = 35
            self.spacing = 10
       
        # Core state
        self.is_connected = False
        self.is_video_on = False
        self.is_screen_sharing = False
        self.is_audio_muted = False
        self.is_audio_on = False
        self.peer_name = "Peer"
        self.cap = None
        self.client_socket = None
        self.server_socket = None
        
        # Audio settings
        self.audio_format = pyaudio.paInt16
        self.audio_channels = 1
        self.audio_rate = 44100
        self.audio_chunk = 1024
        self.audio_input = None
        self.audio_output = None
        self.pyaudio_instance = None
        
        # PiP state
        self.pip_mode = False
        self.pip_dragging = False
        self.pip_x = 20
        self.pip_y = 20
        self.last_mouse_x = 0
        self.last_mouse_y = 0
       
        # Frame buffers
        self.latest_remote_frame = None
        self.latest_screen_frame = None
        
        # Settings
        self.auto_start_video = False
        self.video_quality = "Medium"
        
        # Modern color scheme
        self.primary_color = "#0066cc"
        self.secondary_color = "#1a1a1a"
        self.accent_color = "#00b4d8"
        self.danger_color = "#e63946"
        self.success_color = "#06d6a0"
        self.warning_color = "#ffd60a"
        self.sidebar_bg = "#0d1b2a"
        self.card_bg = "#1b263b"
       
        self.setup_gui()
        self.setup_network()
        self.setup_audio()
        
        # Start peer discovery
        self.peer_discovery.start_discovery()
        threading.Thread(target=self.peer_cleanup_timer, daemon=True).start()
        
        # Bind window resize event
        self.window.bind("<Configure>", self.on_window_resize)
    
    def on_window_resize(self, event):
        """Handle window resize to maintain layout"""
        if event.widget == self.window:
            # Layout is now automatic with pack, no need for manual positioning
            pass
    
    def peer_cleanup_timer(self):
        """Periodically cleanup old peers"""
        while True:
            time.sleep(8)  # Reduced from 10 to 8 for faster cleanup
            self.peer_discovery.cleanup_old_peers()
    
    def update_peer_list(self, peers):
        """Update the peer list in the GUI"""
        if hasattr(self, 'peer_combo'):
            self.window.after(0, lambda: self._update_peer_combo(peers))
        self.available_peers = peers
    
    def _update_peer_combo(self, peers):
        """Update peer combobox in main thread"""
        try:
            peer_list = []
            if peers:
                for ip, info in peers.items():
                    peer_list.append(f"{info['name']} ({ip})")
            
            if not peer_list:
                peer_list = ["No peers discovered..."]
            
            # Store current values
            current = self.peer_combo.get()
            
            # Update values
            self.peer_combo.configure(values=peer_list)
            
            # Restore or set new selection
            if current in peer_list:
                self.peer_combo.set(current)
            elif peer_list and peer_list[0] != "No peers discovered...":
                # Auto-select first peer if available
                self.peer_combo.set(peer_list[0])
                # Auto-fill IP
                self.on_peer_select(peer_list[0])
            else:
                self.peer_combo.set("No peers discovered...")
                
        except Exception as e:
            print(f"Error updating peer list: {e}")
    
    def on_peer_select(self, choice):
        """Handle peer selection"""
        if "No peers" in choice or not choice:
            return
        
        try:
            ip = choice.split('(')[1].split(')')[0]
            self.peer_ip.delete(0, 'end')
            self.peer_ip.insert(0, ip)
        except:
            pass
    
    def refresh_peers(self):
        """Refresh peer list"""
        self.log_message("🔍 Refreshing peer list...", "system")
        self._update_peer_combo(self.available_peers)
    
    def setup_audio(self):
        """Initialize PyAudio"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.log_message("Audio system initialized", "system")
        except Exception as e:
            self.log_message(f"Audio initialization failed: {e}", "error")
            self.pyaudio_instance = None
       
    def setup_gui(self):
        """Setup main GUI with responsive design"""
        self.main_container = ctk.CTkFrame(self.window, fg_color=self.secondary_color)
        self.main_container.pack(fill="both", expand=True)
        
        self.setup_sidebar(self.main_container)
        self.setup_main_content(self.main_container)
    
    def setup_sidebar(self, parent):
        """Setup scrollable sidebar with all controls"""
        sidebar_container = ctk.CTkFrame(parent, width=self.sidebar_width, fg_color=self.sidebar_bg)
        sidebar_container.pack(side="left", fill="y", padx=0, pady=0)
        sidebar_container.pack_propagate(False)
        
        self.sidebar_scroll = ctk.CTkScrollableFrame(
            sidebar_container,
            fg_color=self.sidebar_bg,
            scrollbar_button_color=self.primary_color,
            scrollbar_button_hover_color=self.accent_color
        )
        self.sidebar_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.create_sidebar_header()
        self.create_profile_section()
        self.create_peer_section()
        self.create_connection_section()
        self.create_media_section()
        self.create_file_section()
        self.create_quick_settings()
    
    def create_sidebar_header(self):
        """Create sidebar header with app branding"""
        header_frame = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        header_frame.pack(fill="x", padx=self.spacing, pady=(self.spacing, self.spacing*2))
        
        logo_label = ctk.CTkLabel(
            header_frame,
            text="⚡",
            font=("Arial", 32),
            text_color=self.accent_color
        )
        logo_label.pack()
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="ZeroConnect",
            font=("Arial", self.font_size_large, "bold"),
            text_color="white"
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Secure P2P Platform",
            font=("Arial", self.font_size_small),
            text_color="#778da9"
        )
        subtitle_label.pack()
        
        separator = ctk.CTkFrame(header_frame, height=2, fg_color="#415a77")
        separator.pack(fill="x", pady=self.spacing)
    
    def create_profile_section(self):
        """Create user profile section"""
        profile_frame = self.create_section_frame("👤 Profile")
        
        self.user_name = ctk.CTkEntry(
            profile_frame,
            placeholder_text="Your display name",
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color=self.card_bg,
            border_color=self.primary_color
        )
        self.user_name.pack(fill="x", padx=self.spacing, pady=self.spacing//2)
        
        status_container = ctk.CTkFrame(profile_frame, fg_color="transparent")
        status_container.pack(fill="x", padx=self.spacing, pady=self.spacing//2)
        
        self.status_indicator = ctk.CTkLabel(
            status_container,
            text="●",
            font=("Arial", 16),
            text_color=self.danger_color
        )
        self.status_indicator.pack(side="left", padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(
            status_container,
            text="Disconnected",
            font=("Arial", self.font_size_small),
            text_color="#778da9"
        )
        self.status_label.pack(side="left")
        
        ip_label = ctk.CTkLabel(
            profile_frame,
            text=f"🌐 Your IP: {self.get_local_ip()}",
            font=("Arial", self.font_size_small),
            text_color="#778da9"
        )
        ip_label.pack(pady=(0, self.spacing))
    
    def create_peer_section(self):
        """Create peer discovery section"""
        peer_frame = self.create_section_frame("🔍 Peer Discovery")
        
        refresh_container = ctk.CTkFrame(peer_frame, fg_color="transparent")
        refresh_container.pack(fill="x", padx=self.spacing, pady=(0, self.spacing//2))
        
        refresh_btn = ctk.CTkButton(
            refresh_container,
            text="🔄 Refresh",
            command=self.refresh_peers,
            height=30,
            font=("Arial", self.font_size_small),
            fg_color="#415a77",
            hover_color="#556f8a"
        )
        refresh_btn.pack(side="right")
        
        self.peer_combo = ctk.CTkComboBox(
            peer_frame,
            values=["Searching for peers..."],
            command=self.on_peer_select,
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color=self.card_bg,
            border_color=self.primary_color,
            button_color=self.primary_color,
            button_hover_color=self.accent_color
        )
        self.peer_combo.pack(fill="x", padx=self.spacing, pady=self.spacing//2)
        
        manual_label = ctk.CTkLabel(
            peer_frame,
            text="Or enter IP manually:",
            font=("Arial", self.font_size_small),
            text_color="#778da9"
        )
        manual_label.pack(padx=self.spacing, pady=(self.spacing, self.spacing//2))
        
        self.peer_ip = ctk.CTkEntry(
            peer_frame,
            placeholder_text="192.168.1.x",
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color=self.card_bg,
            border_color=self.primary_color
        )
        self.peer_ip.pack(fill="x", padx=self.spacing, pady=(0, self.spacing))
    
    def create_connection_section(self):
        """Create connection controls"""
        conn_frame = self.create_section_frame("🔌 Connection")
        
        self.connect_btn = ctk.CTkButton(
            conn_frame,
            text="Connect",
            command=self.toggle_connection,
            height=self.button_height,
            font=("Arial", self.font_size_normal, "bold"),
            fg_color=self.success_color,
            hover_color="#05c896"
        )
        self.connect_btn.pack(fill="x", padx=self.spacing, pady=self.spacing)
        
        security_label = ctk.CTkLabel(
            conn_frame,
            text="🔒 AES-256 Encrypted",
            font=("Arial", self.font_size_small),
            text_color=self.success_color
        )
        security_label.pack(pady=(0, self.spacing))
    
    def create_media_section(self):
        """Create media controls"""
        media_frame = self.create_section_frame("📹 Media Controls")
        
        self.video_btn = ctk.CTkButton(
            media_frame,
            text="📹 Video",
            command=self.toggle_video,
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color=self.primary_color,
            hover_color=self.accent_color
        )
        self.video_btn.pack(fill="x", padx=self.spacing, pady=self.spacing//2)
        
        self.audio_btn = ctk.CTkButton(
            media_frame,
            text="🎤 Audio",
            command=self.toggle_audio_transmission,
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color="#e67e22",
            hover_color="#d35400"
        )
        self.audio_btn.pack(fill="x", padx=self.spacing, pady=self.spacing//2)
        
        self.screen_btn = ctk.CTkButton(
            media_frame,
            text="🖥️ Screen Share",
            command=self.toggle_screen,
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color="#8e44ad",
            hover_color="#7d3c98"
        )
        self.screen_btn.pack(fill="x", padx=self.spacing, pady=self.spacing//2)
        
        self.pip_btn = ctk.CTkButton(
            media_frame,
            text="📱 Picture-in-Picture",
            command=self.toggle_pip_mode,
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        self.pip_btn.pack(fill="x", padx=self.spacing, pady=(self.spacing//2, self.spacing))
    
    def create_file_section(self):
        """Create file transfer section"""
        file_frame = self.create_section_frame("📁 File Transfer")
        
        self.file_btn = ctk.CTkButton(
            file_frame,
            text="📤 Send File",
            command=self.send_file,
            height=self.button_height,
            font=("Arial", self.font_size_normal),
            fg_color="#f39c12",
            hover_color="#e67e22"
        )
        self.file_btn.pack(fill="x", padx=self.spacing, pady=self.spacing)
    
    def create_quick_settings(self):
        """Create quick settings section"""
        settings_frame = self.create_section_frame("⚙️ Quick Settings")
        
        self.auto_video_var = ctk.BooleanVar()
        auto_video_check = ctk.CTkCheckBox(
            settings_frame,
            text="Auto-start video",
            variable=self.auto_video_var,
            font=("Arial", self.font_size_small),
            fg_color=self.primary_color,
            hover_color=self.accent_color
        )
        auto_video_check.pack(padx=self.spacing, pady=self.spacing//2, anchor="w")
        
        settings_btn = ctk.CTkButton(
            settings_frame,
            text="⚙️ All Settings",
            command=self.open_settings,
            height=35,
            font=("Arial", self.font_size_normal),
            fg_color="#415a77",
            hover_color="#556f8a"
        )
        settings_btn.pack(fill="x", padx=self.spacing, pady=self.spacing)
    
    def create_section_frame(self, title):
        """Create a styled section frame"""
        section = ctk.CTkFrame(self.sidebar_scroll, fg_color=self.card_bg, corner_radius=10)
        section.pack(fill="x", padx=5, pady=self.spacing//2)
        
        title_label = ctk.CTkLabel(
            section,
            text=title,
            font=("Arial", self.font_size_normal, "bold"),
            text_color="white",
            anchor="w"
        )
        title_label.pack(fill="x", padx=self.spacing, pady=(self.spacing, self.spacing//2))
        
        return section
    
    def setup_main_content(self, parent):
        """Setup main content area with tabview"""
        self.content_frame = ctk.CTkFrame(parent, fg_color=self.secondary_color)
        self.content_frame.pack(side="right", fill="both", expand=True, padx=self.spacing, pady=self.spacing)
        
        self.tabview = ctk.CTkTabview(
            self.content_frame,
            segmented_button_fg_color=self.card_bg,
            segmented_button_selected_color=self.primary_color,
            segmented_button_selected_hover_color=self.accent_color,
            segmented_button_unselected_color=self.card_bg,
            segmented_button_unselected_hover_color="#2d3e50"
        )
        self.tabview.pack(fill="both", expand=True)
        
        self.setup_chat_tab()
        self.setup_video_tab()
        self.setup_screen_tab()
    
    def setup_chat_tab(self):
        """Setup chat tab"""
        chat_tab = self.tabview.add("💬 Chat")
        
        chat_container = ctk.CTkFrame(chat_tab, fg_color=self.card_bg)
        chat_container.pack(fill="both", expand=True, padx=self.spacing, pady=self.spacing)
        
        chat_header = ctk.CTkFrame(chat_container, height=50, fg_color=self.sidebar_bg)
        chat_header.pack(fill="x", padx=self.spacing, pady=(self.spacing, 0))
        chat_header.pack_propagate(False)
        
        self.chat_status = ctk.CTkLabel(
            chat_header,
            text="🔒 Secure encrypted chat",
            font=("Arial", self.font_size_normal, "bold"),
            text_color="white"
        )
        self.chat_status.pack(expand=True)
        
        self.chat_display = ctk.CTkTextbox(
            chat_container,
            state="disabled",
            font=("Arial", self.font_size_normal),
            fg_color=self.secondary_color,
            border_width=0,
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=self.spacing, pady=self.spacing)
        
        input_frame = ctk.CTkFrame(chat_container, fg_color="transparent")
        input_frame.pack(fill="x", padx=self.spacing, pady=(0, self.spacing))
        
        self.chat_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message...",
            font=("Arial", self.font_size_normal),
            height=40,
            fg_color=self.secondary_color,
            border_color=self.primary_color
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, self.spacing))
        self.chat_entry.bind("<Return>", lambda e: self.send_message())
        
        send_btn = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_message,
            width=80,
            height=40,
            font=("Arial", self.font_size_normal),
            fg_color=self.success_color,
            hover_color="#05c896"
        )
        send_btn.pack(side="right")
    
    def setup_video_tab(self):
        """Setup video call tab"""
        video_tab = self.tabview.add("📹 Video")
        
        self.video_container = ctk.CTkFrame(video_tab, fg_color="#000000")
        self.video_container.pack(fill="both", expand=True, padx=self.spacing, pady=self.spacing)
        
        # Create resizable paned window for videos
        self.video_paned = ctk.CTkFrame(self.video_container, fg_color="#000000")
        self.video_paned.pack(fill="both", expand=True)
        
        # Remote video frame (top)
        self.remote_video_frame = ctk.CTkFrame(self.video_paned, fg_color="#1a1a1a")
        self.remote_video_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        remote_header = ctk.CTkFrame(self.remote_video_frame, fg_color="transparent", height=30)
        remote_header.pack(fill="x", pady=(5, 0))
        remote_header.pack_propagate(False)
        
        remote_label = ctk.CTkLabel(
            remote_header,
            text="Peer Video",
            font=("Arial", self.font_size_small),
            text_color="#778da9"
        )
        remote_label.pack(side="left", padx=10)
        
        fullscreen_hint = ctk.CTkLabel(
            remote_header,
            text="(Double-click for fullscreen)",
            font=("Arial", self.font_size_small-2),
            text_color="#556f8a"
        )
        fullscreen_hint.pack(side="right", padx=10)
        
        self.remote_video = ctk.CTkLabel(
            self.remote_video_frame,
            text="📹 Waiting for peer video...",
            fg_color=self.card_bg,
            font=("Arial", self.font_size_large),
            text_color="#778da9"
        )
        self.remote_video.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Bind double-click for fullscreen
        self.remote_video.bind("<Double-Button-1>", lambda e: self.toggle_video_fullscreen("remote"))
        
        # Draggable separator with better visibility
        separator_container = ctk.CTkFrame(self.video_paned, fg_color="#000000", height=20)
        separator_container.pack(fill="x")
        separator_container.pack_propagate(False)
        
        self.separator = ctk.CTkFrame(
            separator_container, 
            fg_color=self.accent_color, 
            height=6,
            cursor="sb_v_double_arrow"
        )
        self.separator.pack(fill="x", padx=5, pady=7)
        
        self.separator.bind("<Button-1>", self.start_drag)
        self.separator.bind("<B1-Motion>", self.on_drag)
        self.separator.bind("<ButtonRelease-1>", self.end_drag)
        
        # Add hover effect for separator
        self.separator.bind("<Enter>", lambda e: self.separator.configure(fg_color="#90e0ef"))
        self.separator.bind("<Leave>", lambda e: self.separator.configure(fg_color=self.accent_color))
        
        # Local video frame (bottom)
        self.local_video_frame = ctk.CTkFrame(self.video_paned, fg_color="#1a1a1a", height=200)
        self.local_video_frame.pack(fill="both", expand=False, padx=5, pady=5)
        
        local_header = ctk.CTkFrame(self.local_video_frame, fg_color="transparent", height=30)
        local_header.pack(fill="x", pady=(5, 0))
        local_header.pack_propagate(False)
        
        local_label = ctk.CTkLabel(
            local_header,
            text="Your Video",
            font=("Arial", self.font_size_small),
            text_color="#778da9"
        )
        local_label.pack(side="left", padx=10)
        
        local_hint = ctk.CTkLabel(
            local_header,
            text="(Double-click for fullscreen)",
            font=("Arial", self.font_size_small-2),
            text_color="#556f8a"
        )
        local_hint.pack(side="right", padx=10)
        
        self.local_video = ctk.CTkLabel(
            self.local_video_frame,
            text="Your camera will appear here",
            fg_color=self.card_bg,
            font=("Arial", self.font_size_small),
            text_color="#778da9"
        )
        self.local_video.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Bind double-click for fullscreen
        self.local_video.bind("<Double-Button-1>", lambda e: self.toggle_video_fullscreen("local"))
        
        # Video fullscreen state
        self.video_fullscreen = False
        self.fullscreen_type = None
        self.dragging_separator = False
    
    def start_drag(self, event):
        """Start dragging separator"""
        self.dragging_separator = True
        self.drag_start_y = event.y_root
        self.local_frame_start_height = self.local_video_frame.winfo_height()
        self.separator.configure(fg_color="#90e0ef")  # Highlight during drag
    
    def on_drag(self, event):
        """Handle separator dragging"""
        if not self.dragging_separator:
            return
            
        try:
            delta = self.drag_start_y - event.y_root
            new_height = max(100, min(600, self.local_frame_start_height + delta))
            self.local_video_frame.configure(height=new_height)
        except Exception as e:
            print(f"Drag error: {e}")
    
    def end_drag(self, event):
        """End dragging separator"""
        self.dragging_separator = False
        self.separator.configure(fg_color=self.accent_color)
    
    def toggle_video_fullscreen(self, video_type):
        """Toggle fullscreen mode for video"""
        if not self.video_fullscreen:
            # Enter fullscreen
            self.video_fullscreen = True
            self.fullscreen_type = video_type
            
            if video_type == "remote":
                # Hide local video and separator
                self.local_video_frame.pack_forget()
                self.separator.pack_forget()
                # Make remote video fill entire space
                self.remote_video_frame.pack(fill="both", expand=True, padx=5, pady=5)
            else:
                # Hide remote video and separator
                self.remote_video_frame.pack_forget()
                self.separator.pack_forget()
                # Make local video fill entire space
                self.local_video_frame.pack(fill="both", expand=True, padx=5, pady=5)
                self.local_video_frame.configure(height=0)  # Remove height constraint
        else:
            # Exit fullscreen
            self.video_fullscreen = False
            self.fullscreen_type = None
            
            # Restore normal layout
            self.remote_video_frame.pack_forget()
            self.local_video_frame.pack_forget()
            self.separator.pack_forget()
            
            self.remote_video_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.separator.pack(fill="x", padx=5)
            self.local_video_frame.pack(fill="both", expand=False, padx=5, pady=5)
            self.local_video_frame.configure(height=200)
    
    def setup_screen_tab(self):
        """Setup screen sharing tab"""
        screen_tab = self.tabview.add("🖥️ Screen")
        
        screen_container = ctk.CTkFrame(screen_tab, fg_color="#000000")
        screen_container.pack(fill="both", expand=True, padx=self.spacing, pady=self.spacing)
        
        self.screen_display = ctk.CTkLabel(
            screen_container,
            text="🖥️ No screen being shared",
            fg_color=self.card_bg,
            font=("Arial", self.font_size_large),
            text_color="#778da9"
        )
        self.screen_display.pack(fill="both", expand=True)
    
    def position_local_video_overlay(self):
        """Position local video overlay in bottom-right"""
        # Not needed anymore as we use a fixed layout
        pass
    
    def open_settings(self):
        """Open settings dialog"""
        settings_win = ctk.CTkToplevel(self.window)
        settings_win.title("ZeroConnect Settings")
        settings_win.geometry("600x700")
        settings_win.transient(self.window)
        settings_win.grab_set()
        
        # Center settings window
        settings_win.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 600) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 700) // 2
        settings_win.geometry(f"+{x}+{y}")
        
        # Scrollable settings content
        settings_scroll = ctk.CTkScrollableFrame(
            settings_win,
            fg_color=self.secondary_color
        )
        settings_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Settings sections
        self.create_settings_security(settings_scroll)
        self.create_settings_video(settings_scroll)
        self.create_settings_audio(settings_scroll)
        self.create_settings_network(settings_scroll)
        
        # Save button
        save_frame = ctk.CTkFrame(settings_win, fg_color=self.secondary_color)
        save_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        save_btn = ctk.CTkButton(
            save_frame,
            text="💾 Save Settings",
            command=lambda: self.save_settings(settings_win),
            height=45,
            font=("Arial", self.font_size_normal, "bold"),
            fg_color=self.success_color,
            hover_color="#05c896"
        )
        save_btn.pack(fill="x")
    
    def create_settings_security(self, parent):
        """Create security settings section"""
        section = self.create_settings_section(parent, "🔐 Security")
        
        ctk.CTkLabel(
            section,
            text="Encryption Password:",
            font=("Arial", self.font_size_normal),
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        
        self.encryption_password = ctk.CTkEntry(
            section,
            placeholder_text="Enter encryption password",
            show="*",
            height=self.button_height,
            fg_color=self.card_bg
        )
        self.encryption_password.pack(fill="x", pady=5)
        self.encryption_password.insert(0, "ZeroConnect2024")
    
    def create_settings_video(self, parent):
        """Create video settings section"""
        section = self.create_settings_section(parent, "📹 Video")
        
        # Video quality
        ctk.CTkLabel(
            section,
            text="Video Quality:",
            font=("Arial", self.font_size_normal),
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        
        self.video_quality_combo = ctk.CTkComboBox(
            section,
            values=["Low", "Medium", "High"],
            height=self.button_height,
            fg_color=self.card_bg
        )
        self.video_quality_combo.set("Medium")
        self.video_quality_combo.pack(fill="x", pady=5)
        
        # Resolution
        ctk.CTkLabel(
            section,
            text="Resolution:",
            font=("Arial", self.font_size_normal),
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        
        self.resolution_combo = ctk.CTkComboBox(
            section,
            values=["480p", "720p", "1080p"],
            height=self.button_height,
            fg_color=self.card_bg
        )
        self.resolution_combo.set("720p")
        self.resolution_combo.pack(fill="x", pady=5)
    
    def create_settings_audio(self, parent):
        """Create audio settings section"""
        section = self.create_settings_section(parent, "🔊 Audio")
        
        ctk.CTkLabel(
            section,
            text="Sample Rate:",
            font=("Arial", self.font_size_normal),
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        
        self.sample_rate_combo = ctk.CTkComboBox(
            section,
            values=["22050", "44100", "48000"],
            height=self.button_height,
            fg_color=self.card_bg
        )
        self.sample_rate_combo.set("44100")
        self.sample_rate_combo.pack(fill="x", pady=5)
    
    def create_settings_network(self, parent):
        """Create network settings section"""
        section = self.create_settings_section(parent, "🌐 Network")
        
        ctk.CTkLabel(
            section,
            text="Port:",
            font=("Arial", self.font_size_normal),
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        
        self.port_entry = ctk.CTkEntry(
            section,
            height=self.button_height,
            fg_color=self.card_bg
        )
        self.port_entry.insert(0, "9999")
        self.port_entry.pack(fill="x", pady=5)
    
    def create_settings_section(self, parent, title):
        """Create a settings section frame"""
        section = ctk.CTkFrame(parent, fg_color=self.card_bg, corner_radius=10)
        section.pack(fill="x", pady=10)
        
        title_label = ctk.CTkLabel(
            section,
            text=title,
            font=("Arial", self.font_size_normal, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=15, pady=(15, 5))
        
        content = ctk.CTkFrame(section, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 15))
        
        return content
    
    def save_settings(self, window):
        """Save all settings"""
        self.auto_start_video = self.auto_video_var.get()
        self.video_quality = self.video_quality_combo.get()
        
        if self.encryption_password.get():
            self.security_manager.generate_session_key(self.encryption_password.get())
        
        self.log_message("⚙️ Settings saved successfully", "system")
        window.destroy()
    
    # PiP Methods
    def toggle_pip_mode(self):
        """Toggle Picture-in-Picture mode"""
        self.pip_mode = not self.pip_mode
        
        if self.pip_mode:
            self.create_pip_window()
            self.pip_btn.configure(text="📱 Exit PiP", fg_color=self.danger_color)
            self.tabview.set("💬 Chat")
        else:
            if hasattr(self, 'pip_window'):
                self.pip_window.destroy()
            self.pip_btn.configure(text="📱 Picture-in-Picture", fg_color="#6c757d")
    
    def create_pip_window(self):
        """Create PiP window"""
        self.pip_window = ctk.CTkToplevel(self.window)
        self.pip_window.title("ZeroConnect PiP")
        self.pip_window.geometry("320x240")
        self.pip_window.resizable(False, False)
        self.pip_window.attributes("-topmost", True)
        
        pip_frame = ctk.CTkFrame(self.pip_window, fg_color="#000000")
        pip_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.pip_video = ctk.CTkLabel(
            pip_frame,
            text="Peer Video",
            fg_color=self.card_bg
        )
        self.pip_video.pack(fill="both", expand=True)
        
        # Close button
        close_btn = ctk.CTkButton(
            self.pip_window,
            text="✕",
            width=30,
            height=30,
            command=self.toggle_pip_mode,
            fg_color=self.danger_color
        )
        close_btn.place(relx=0.95, rely=0.05, anchor="ne")
    
    # Network Methods
    def setup_network(self):
        """Setup network sockets"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', 9999))
            self.server_socket.listen(1)
            threading.Thread(target=self.wait_for_connection, daemon=True).start()
            self.log_message("🌐 Server started - Ready for connections", "system")
        except Exception as e:
            self.log_message(f"Network setup failed: {e}", "error")
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def wait_for_connection(self):
        """Wait for incoming connections"""
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                if not self.is_connected:
                    self.client_socket = client_socket
                    self.is_connected = True
                    self.update_status()
                    self.send_data(4, self.user_name.get() or "Anonymous")
                    threading.Thread(target=self.receive_data, daemon=True).start()
                    threading.Thread(target=self.display_frames, daemon=True).start()
                    self.log_message(f"🔗 Connected from {addr[0]}", "system")
                    
                    if self.auto_start_video:
                        self.toggle_video()
                else:
                    client_socket.close()
            except OSError:
                # Server socket closed
                break
            except Exception as e:
                print(f"Accept error: {e}")
                break
    
    def toggle_connection(self):
        """Toggle connection state"""
        if not self.is_connected:
            self.connect_to_peer()
        else:
            self.disconnect()
    
    def connect_to_peer(self):
        """Connect to a peer"""
        try:
            host = self.peer_ip.get().strip()
            if not host:
                self.show_notification("⚠️ Error", "Please enter an IP address!")
                return
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            self.client_socket.connect((host, 9999))
            self.client_socket.settimeout(None)
            
            self.is_connected = True
            self.update_status()
            self.send_data(4, self.user_name.get() or "Anonymous")
            threading.Thread(target=self.receive_data, daemon=True).start()
            threading.Thread(target=self.display_frames, daemon=True).start()
            
            self.log_message(f"🔗 Connected to {host}", "system")
            
            if self.auto_start_video:
                self.toggle_video()
            
        except Exception as e:
            self.log_message(f"Connection failed: {e}", "error")
            self.show_notification("⚠️ Failed", f"Could not connect to {host}")
    
    def disconnect(self):
        """Disconnect from peer"""
        was_connected = self.is_connected
        peer_name = self.peer_name
        
        self.is_connected = False
        self.is_video_on = False
        self.is_screen_sharing = False
        self.is_audio_on = False
        
        self.stop_audio_transmission()
        
        if self.client_socket:
            try:
                if was_connected:
                    # Send disconnect notification
                    self.send_data(8, "disconnect")
                self.client_socket.close()
            except:
                pass
            finally:
                self.client_socket = None
        
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            finally:
                self.cap = None
        
        # Clear video displays
        try:
            self.window.after(0, lambda: self.clear_video_display(self.remote_video, "📹 Waiting for peer video..."))
            self.window.after(0, lambda: self.clear_video_display(self.local_video, "Your camera will appear here"))
            self.window.after(0, lambda: self.clear_video_display(self.screen_display, "🖥️ No screen being shared"))
        except:
            pass
        
        self.update_status()
        
        if was_connected:
            self.log_message(f"🔌 Disconnected from {peer_name}", "system")
            # Show notification window for peer disconnect
            try:
                self.window.after(0, lambda: self.show_notification(
                    "⚠️ Disconnected", 
                    f"{peer_name} has disconnected from the session"
                ))
            except:
                pass
    
    def update_status(self):
        """Update connection status display"""
        if self.is_connected:
            self.status_indicator.configure(text_color=self.success_color)
            self.status_label.configure(text="Connected", text_color="white")
            self.connect_btn.configure(text="Disconnect", fg_color=self.danger_color)
            self.peer_ip.configure(state="disabled")
            self.peer_combo.configure(state="disabled")
            self.chat_status.configure(text=f"🔒 Chatting with {self.peer_name}")
        else:
            self.status_indicator.configure(text_color=self.danger_color)
            self.status_label.configure(text="Disconnected", text_color="#778da9")
            self.connect_btn.configure(text="Connect", fg_color=self.success_color)
            self.peer_ip.configure(state="normal")
            self.peer_combo.configure(state="normal")
            self.video_btn.configure(text="📹 Video")
            self.screen_btn.configure(text="🖥️ Screen Share")
            self.audio_btn.configure(text="🎤 Audio")
    
    def send_data(self, data_type, data):
        """Send data to peer"""
        if not self.is_connected or not self.client_socket:
            return
        
        try:
            if data_type in [3, 5]:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                data = self.security_manager.encrypt_data(data)
            elif isinstance(data, str):
                data = data.encode('utf-8')
            elif data_type in [1, 10]:
                data = pickle.dumps(data)
            
            header = struct.pack("!II", data_type, len(data))
            self.client_socket.sendall(header + data)
        except BrokenPipeError:
            print("Send error: Peer disconnected")
            self.disconnect()
        except ConnectionResetError:
            print("Send error: Connection reset")
            self.disconnect()
        except Exception as e:
            print(f"Send error: {e}")
            # Don't disconnect on every error, might be temporary e:
            self.log_message(f"Send error: {e}", "error")
            self.disconnect()
    
    def receive_data(self):
        """Receive data from peer"""
        while self.is_connected:
            try:
                header = self.recv_all(8)
                if not header:
                    break
                
                data_type, data_size = struct.unpack("!II", header)
                data = self.recv_all(data_size)
                if not data:
                    break
                
                self.process_data(data_type, data)
                
            except ConnectionResetError:
                self.log_message("⚠️ Peer disconnected unexpectedly", "system")
                break
            except Exception as e:
                if "10054" not in str(e):  # Ignore force close errors
                    self.log_message(f"Connection error: {e}", "error")
                break
        
        # Clean disconnect
        if self.is_connected:
            self.log_message("🔌 Peer disconnected", "system")
            self.disconnect()
    
    def recv_all(self, size):
        """Receive exact amount of data"""
        data = b""
        while len(data) < size:
            packet = self.client_socket.recv(min(size - len(data), 4096))
            if not packet:
                return None
            data += packet
        return data
    
    def process_data(self, data_type, data):
        """Process received data"""
        if data_type == 1:  # Video
            self.latest_remote_frame = pickle.loads(data)
        elif data_type == 2:  # Audio
            if self.audio_output and not self.is_audio_muted:
                try:
                    decrypted = self.security_manager.decrypt_data(data)
                    self.audio_output.write(decrypted)
                except:
                    pass
        elif data_type == 3:  # Message
            try:
                decrypted = self.security_manager.decrypt_data(data)
                message = decrypted.decode('utf-8')
                self.log_message(f"{self.peer_name}: {message}", "peer")
            except:
                pass
        elif data_type == 4:  # Peer name
            self.peer_name = data.decode('utf-8')
            self.update_status()
            self.log_message(f"✅ Connected to {self.peer_name}", "system")
        elif data_type == 5:  # File
            self.receive_file(data)
        elif data_type == 8:  # Disconnect
            self.log_message(f"👋 {self.peer_name} disconnected", "system")
            self.disconnect()
        elif data_type == 10:  # Screen
            self.latest_screen_frame = pickle.loads(data)
    
    # Media Methods
    def toggle_video(self):
        """Toggle video transmission"""
        self.is_video_on = not self.is_video_on
        
        if self.is_video_on:
            if not self.is_connected:
                self.is_video_on = False
                self.show_notification("⚠️ Error", "Connect to peer first!")
                return
            
            self.video_btn.configure(text="📹 Stop Video", fg_color=self.danger_color)
            threading.Thread(target=self.send_video, daemon=True).start()
        else:
            self.video_btn.configure(text="📹 Video", fg_color=self.primary_color)
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # Clear local video display
            self.window.after(0, lambda: self.clear_video_display(self.local_video, "Your camera will appear here"))
            self.log_message("📹 Video stopped", "system")
    
    def toggle_screen(self):
        """Toggle screen sharing"""
        self.is_screen_sharing = not self.is_screen_sharing
        
        if self.is_screen_sharing:
            if not self.is_connected:
                self.is_screen_sharing = False
                self.show_notification("⚠️ Error", "Connect to peer first!")
                return
            
            self.screen_btn.configure(text="🖥️ Stop Sharing", fg_color=self.danger_color)
            threading.Thread(target=self.send_screen, daemon=True).start()
        else:
            self.screen_btn.configure(text="🖥️ Screen Share", fg_color="#8e44ad")
            
            # Clear screen display
            self.window.after(0, lambda: self.clear_video_display(self.screen_display, "🖥️ No screen being shared"))
            self.log_message("🖥️ Screen sharing stopped", "system")
    
    def clear_video_display(self, label, text):
        """Clear video display and show default text"""
        try:
            label.configure(image=None, text=text)
            if hasattr(label, 'image'):
                label.image = None
        except Exception as e:
            print(f"Clear display error: {e}")
    
    def toggle_audio_transmission(self):
        """Toggle audio transmission"""
        if not self.pyaudio_instance:
            self.show_notification("⚠️ Error", "Audio not available!")
            return
            
        self.is_audio_on = not self.is_audio_on
        
        if self.is_audio_on:
            if not self.is_connected:
                self.is_audio_on = False
                self.show_notification("⚠️ Error", "Connect to peer first!")
                return
            
            self.audio_btn.configure(text="🎤 Stop Audio", fg_color=self.danger_color)
            self.start_audio_transmission()
        else:
            self.audio_btn.configure(text="🎤 Audio", fg_color="#e67e22")
            self.stop_audio_transmission()
    
    def start_audio_transmission(self):
        """Start audio streams"""
        try:
            self.audio_input = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_rate,
                input=True,
                frames_per_buffer=self.audio_chunk
            )
            
            self.audio_output = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_rate,
                output=True,
                frames_per_buffer=self.audio_chunk
            )
            
            threading.Thread(target=self.send_audio, daemon=True).start()
            self.log_message("🎤 Audio started", "system")
            
        except Exception as e:
            self.log_message(f"Audio error: {e}", "error")
            self.is_audio_on = False
            self.audio_btn.configure(text="🎤 Audio", fg_color="#e67e22")
    
    def stop_audio_transmission(self):
        """Stop audio streams"""
        try:
            if self.audio_input:
                try:
                    self.audio_input.stop_stream()
                    self.audio_input.close()
                except:
                    pass
                finally:
                    self.audio_input = None
            
            if self.audio_output:
                try:
                    self.audio_output.stop_stream()
                    self.audio_output.close()
                except:
                    pass
                finally:
                    self.audio_output = None
        except Exception as e:
            print(f"Stop audio error: {e}")
    
    def send_audio(self):
        """Send audio data"""
        while self.is_audio_on and self.is_connected and self.audio_input:
            try:
                data = self.audio_input.read(self.audio_chunk, exception_on_overflow=False)
                encrypted = self.security_manager.encrypt_data(data)
                self.send_data(2, encrypted)
            except Exception as e:
                print(f"Send audio error: {e}")
                time.sleep(0.01)
                continue
    
    def send_video(self):
        """Send video stream"""
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            quality = 70
            if hasattr(self, 'video_quality_combo'):
                q = self.video_quality_combo.get().lower()
                quality = 50 if q == "low" else 90 if q == "high" else 70
            
            while self.is_video_on and self.is_connected:
                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        break
                    
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                    self.send_data(1, buffer)
                    self.display_frame(self.local_video, frame)
                    time.sleep(0.033)
                except Exception as e:
                    print(f"Video frame error: {e}")
                    continue
                
        except Exception as e:
            self.log_message(f"Video error: {e}", "error")
        finally:
            if self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None
    
    def send_screen(self):
        """Send screen share"""
        try:
            while self.is_screen_sharing and self.is_connected:
                try:
                    screenshot = pyautogui.screenshot()
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    frame = cv2.resize(frame, (1280, 720))
                    
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    self.send_data(10, buffer)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Screen frame error: {e}")
                    continue
                
        except Exception as e:
            self.log_message(f"Screen share error: {e}", "error")
    
    def display_frames(self):
        """Display video frames"""
        while self.is_connected:
            try:
                if self.latest_remote_frame is not None:
                    try:
                        frame = cv2.imdecode(self.latest_remote_frame, cv2.IMREAD_COLOR)
                        
                        if not self.pip_mode:
                            self.display_frame(self.remote_video, frame, large=True)
                        elif hasattr(self, 'pip_video'):
                            self.display_frame(self.pip_video, frame)
                        
                        self.latest_remote_frame = None
                    except Exception as e:
                        print(f"Remote frame display error: {e}")
                
                if self.latest_screen_frame is not None:
                    try:
                        frame = cv2.imdecode(self.latest_screen_frame, cv2.IMREAD_COLOR)
                        self.display_frame(self.screen_display, frame, large=True)
                        self.latest_screen_frame = None
                    except Exception as e:
                        print(f"Screen frame display error: {e}")
                
                time.sleep(0.03)
            except Exception as e:
                print(f"Display frames error: {e}")
                time.sleep(0.1)
                continue
    
    def display_frame(self, label, frame, large=False):
        """Display a video frame using CTkImage for proper scaling"""
        try:
            if frame is None:
                return
            
            # Get the actual widget size for adaptive sizing
            label.update_idletasks()
            widget_width = label.winfo_width()
            widget_height = label.winfo_height()
            
            # Use widget size if available, otherwise use defaults
            if widget_width > 10 and widget_height > 10:
                width = max(100, widget_width - 4)
                height = max(75, widget_height - 4)
            elif large:
                width, height = 800, 600
            else:
                width, height = 300, 180
            
            # Convert frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((width, height), Image.LANCZOS)
            
            # Use CTkImage to avoid scaling warnings
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))
            
            self.window.after(0, lambda: self.update_label_ctk(label, ctk_img))
        except Exception as e:
            pass
    
    def update_label_ctk(self, label, ctk_image):
        """Update label with CTkImage"""
        try:
            label.configure(image=ctk_image, text="")
            label.image = ctk_image  # Keep reference
        except:
            pass
    
    # Chat Methods
    def send_message(self):
        """Send chat message"""
        message = self.chat_entry.get().strip()
        if message and self.is_connected:
            self.send_data(3, message)
            self.log_message(f"You: {message}", "user")
            self.chat_entry.delete(0, "end")
        elif message:
            self.show_notification("⚠️ Error", "Connect to peer first!")
    
    def log_message(self, message, msg_type="system"):
        """Log message to chat"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            
            if msg_type == "user":
                prefix = "👤"
            elif msg_type == "peer":
                prefix = "👥"
            elif msg_type == "system":
                prefix = "⚙️"
            else:
                prefix = "ℹ️"
            
            formatted = f"[{timestamp}] {prefix} {message}\n"
            
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", formatted)
            self.chat_display.configure(state="disabled")
            self.chat_display.see("end")
        except:
            pass
    
    # File Transfer
    def send_file(self):
        """Send a file"""
        if not self.is_connected:
            self.show_notification("⚠️ Error", "Connect to peer first!")
            return
        
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:
                self.show_notification("⚠️ Error", "File too large (max 100MB)")
                return
            
            self.log_message(f"📤 Sending: {os.path.basename(file_path)}", "system")
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            file_info = {
                'name': os.path.basename(file_path),
                'data': file_data,
                'size': file_size
            }
            
            serialized = pickle.dumps(file_info)
            self.send_data(5, serialized)
            self.log_message(f"📤 File sent: {file_info['name']}", "system")
            
        except Exception as e:
            self.log_message(f"File send error: {e}", "error")
    
    def receive_file(self, encrypted_data):
        """Receive a file"""
        try:
            decrypted = self.security_manager.decrypt_data(encrypted_data)
            file_info = pickle.loads(decrypted)
            
            self.log_message(f"📥 Incoming: {file_info['name']}", "system")
            
            save_path = filedialog.asksaveasfilename(
                initialfile=file_info['name'],
                defaultextension=os.path.splitext(file_info['name'])[1]
            )
            
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(file_info['data'])
                self.log_message(f"📥 Saved: {file_info['name']}", "system")
                self.show_notification("📥 Received", f"Saved: {os.path.basename(save_path)}")
        except Exception as e:
            self.log_message(f"File receive error: {e}", "error")
    
    # Utility Methods
    def show_notification(self, title, message):
        """Show notification popup"""
        notif = ctk.CTkToplevel(self.window)
        notif.title(title)
        notif.geometry("350x150")
        notif.transient(self.window)
        notif.grab_set()
        
        x = self.window.winfo_x() + (self.window.winfo_width() - 350) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 150) // 2
        notif.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(notif, fg_color=self.card_bg)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=title, font=("Arial", 16, "bold")).pack(pady=(0, 10))
        ctk.CTkLabel(frame, text=message, font=("Arial", 12)).pack(pady=(0, 20))
        
        ctk.CTkButton(
            frame,
            text="OK",
            command=notif.destroy,
            fg_color=self.primary_color
        ).pack()
        
        notif.after(3000, notif.destroy)
    
    def quick_ai_command(self, command):
        """Execute quick AI command"""
        self.ai_message_entry.delete(0, 'end')
        self.ai_message_entry.insert(0, command)
        self.send_ai_message()
    
    def clear_ai_chat(self):
        """Clear AI chat"""
        self.ai_chat_display.configure(state='normal')
        self.ai_chat_display.delete('1.0', 'end')
        self.ai_chat_display.configure(state='disabled')
        self.add_ai_message("AI", "Chat cleared. How can I help you?")
    
    def send_ai_message(self):
        """Send message to AI"""
        message = self.ai_message_entry.get().strip()
        if not message:
            return
        
        self.add_ai_message("You", message)
        self.ai_message_entry.delete(0, 'end')
        
        self.ai_status.configure(text="🟡 AI Thinking...", text_color=self.warning_color)
        self.ai_message_entry.configure(state='disabled')
        
        threading.Thread(target=self.process_ai_request, args=(message,), daemon=True).start()
    
    def process_ai_request(self, message):
        """Process AI request using Ollama"""
        try:
            response = subprocess.run(
                ['ollama', 'run', 'gemma3:270m', message],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False
            )
            
            if response.returncode == 0:
                ai_response = response.stdout.strip()
                lines = ai_response.splitlines()
                clean_lines = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('>>>') and not line.startswith('> '):
                        clean_lines.append(line)
                
                ai_response = '\n'.join(clean_lines) if clean_lines else "I received your message but couldn't generate a response."
                self.window.after(0, lambda: self.handle_ai_response(ai_response, False))
            else:
                error_msg = response.stderr.strip() or "Unknown error occurred"
                self.window.after(0, lambda: self.handle_ai_response(f"Error: {error_msg}", True))
                
        except subprocess.TimeoutExpired:
            self.window.after(0, lambda: self.handle_ai_response("Request timed out. Please try a simpler question.", True))
            
        except FileNotFoundError:
            self.window.after(0, lambda: self.handle_ai_response("Ollama not found. Please install Ollama and the 'gemma3:270m' model.", True))
            
        except Exception as e:
            self.window.after(0, lambda: self.handle_ai_response(f"Error: {str(e)}", True))
    
    def handle_ai_response(self, response, is_error):
        """Handle AI response"""
        self.ai_message_entry.configure(state='normal')
        
        if is_error:
            self.ai_status.configure(
                text="🔴 Error Occurred",
                text_color=self.danger_color
            )
        else:
            self.ai_status.configure(
                text="🟢 ZeroConnect AI Ready",
                text_color=self.success_color
            )
        
        self.add_ai_message("AI", response)
    
    def add_ai_message(self, sender, message):
        """Add message to AI chat"""
        timestamp = time.strftime("%H:%M:%S")
        
        self.ai_chat_display.configure(state='normal')
        
        if sender == "You":
            self.ai_chat_display.insert('end', f"[{timestamp}] You: {message}\n\n")
        else:
            self.ai_chat_display.insert('end', f"[{timestamp}] AI: {message}\n\n")
        
        self.ai_chat_display.configure(state='disabled')
        self.ai_chat_display.see('end')
    
    def on_close(self):
        """Handle window close"""
        # Stop peer discovery first
        self.peer_discovery.stop_discovery()
        
        # Stop audio
        self.is_audio_on = False
        self.stop_audio_transmission()
        
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
        
        # Disconnect from peer
        if self.is_connected:
            self.disconnect()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Close PiP window
        if hasattr(self, 'pip_window'):
            try:
                if self.pip_window.winfo_exists():
                    self.pip_window.destroy()
            except:
                pass
        
        # Destroy main window
        try:
            self.window.destroy()
        except:
            pass
    
    def run(self):
        """Run the application"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create AI Assistant button (floating in top right)
        self.ai_button = ctk.CTkButton(
            self.window,
            text="🤖 AI",
            width=60,
            height=40,
            corner_radius=20,
            font=("Arial", 12, "bold"),
            command=self.toggle_ai_panel,
            fg_color=self.primary_color,
            hover_color=self.accent_color
        )
        self.ai_button.place(relx=0.98, rely=0.02, anchor='ne')
        self.ai_button.lift()
        self.ai_panel_visible = False
        
        # Periodically update peer list display
        def update_peers():
            if hasattr(self, 'peer_combo'):
                self._update_peer_combo(self.available_peers)
            self.window.after(2000, update_peers)  # Reduced from 3000 to 2000ms
        
        update_peers()
        
        # Welcome message
        self.log_message("⚡ Welcome to ZeroConnect!", "system")
        self.log_message("Connect to a peer to start secure communication", "system")
        
        self.window.mainloop()
    
    # AI Assistant Methods (Integrated Panel)
    def toggle_ai_panel(self):
        """Toggle AI assistant panel"""
        if not self.ai_panel_visible:
            self.show_ai_panel()
        else:
            self.hide_ai_panel()
    
    def show_ai_panel(self):
        """Show AI panel by resizing window and adding panel"""
        # Create AI panel if doesn't exist
        if not hasattr(self, 'ai_panel'):
            self.create_ai_panel()
        
        # Show the panel
        self.ai_panel.pack(side="right", fill="y", padx=(self.spacing, 0), pady=0, before=self.content_frame)
        
        # Update button
        self.ai_button.configure(text="✕ AI", fg_color=self.danger_color)
        self.ai_panel_visible = True
        
        # Animate showing
        self.window.update_idletasks()
    
    def hide_ai_panel(self):
        """Hide AI panel"""
        if hasattr(self, 'ai_panel'):
            self.ai_panel.pack_forget()
        
        self.ai_button.configure(text="🤖 AI", fg_color=self.primary_color)
        self.ai_panel_visible = False
    
    def create_ai_panel(self):
        """Create AI assistant integrated panel"""
        # Calculate panel width
        panel_width = max(300, min(380, int(self.window_width * 0.22)))
        
        self.ai_panel = ctk.CTkFrame(
            self.main_container,
            width=panel_width,
            fg_color=self.sidebar_bg,
            corner_radius=0
        )
        self.ai_panel.pack_propagate(False)
        
        # Header
        header = ctk.CTkFrame(
            self.ai_panel,
            height=60,
            fg_color=self.primary_color,
            corner_radius=0
        )
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Header content
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=15, pady=10)
        
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(side='left', fill='y')
        
        icon = ctk.CTkLabel(title_frame, text="🤖", font=("Arial", 24))
        icon.pack(side='left', padx=(0, 8))
        
        title = ctk.CTkLabel(
            title_frame,
            text="AI Assistant",
            font=("Arial", self.font_size_normal, "bold"),
            text_color="white"
        )
        title.pack(side='left')
        
        # Status indicator
        status_container = ctk.CTkFrame(
            self.ai_panel,
            fg_color=self.card_bg,
            corner_radius=8,
            height=40
        )
        status_container.pack(fill='x', padx=10, pady=10)
        status_container.pack_propagate(False)
        
        self.ai_status = ctk.CTkLabel(
            status_container,
            text="🟢 ZeroConnect AI Ready",
            font=("Arial", self.font_size_small, "bold"),
            text_color=self.success_color
        )
        self.ai_status.pack(expand=True)
        
        # Chat display
        chat_frame = ctk.CTkFrame(self.ai_panel, fg_color="transparent")
        chat_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.ai_chat_display = ctk.CTkTextbox(
            chat_frame,
            wrap='word',
            state='disabled',
            fg_color=self.secondary_color,
            font=("Arial", self.font_size_small),
            border_width=2,
            border_color=self.primary_color,
            corner_radius=8
        )
        self.ai_chat_display.pack(fill='both', expand=True)
        
        # Input area
        input_container = ctk.CTkFrame(self.ai_panel, fg_color="transparent")
        input_container.pack(fill='x', padx=10, pady=(0, 10))
        
        self.ai_message_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Ask me anything...",
            fg_color=self.secondary_color,
            border_color=self.primary_color,
            border_width=2,
            height=40,
            corner_radius=20,
            font=("Arial", self.font_size_small)
        )
        self.ai_message_entry.pack(fill='x', pady=(0, 8))
        self.ai_message_entry.bind('<Return>', lambda e: self.send_ai_message())
        
        # Send button
        send_btn = ctk.CTkButton(
            input_container,
            text="➤ Send",
            command=self.send_ai_message,
            height=35,
            fg_color=self.accent_color,
            hover_color=self.primary_color,
            corner_radius=17,
            font=("Arial", self.font_size_small, "bold")
        )
        send_btn.pack(fill='x')
        
        # Quick actions
        quick_label = ctk.CTkLabel(
            self.ai_panel,
            text="Quick Actions:",
            font=("Arial", self.font_size_small-1),
            text_color="#778da9"
        )
        quick_label.pack(padx=10, pady=(5, 5))
        
        quick_frame = ctk.CTkFrame(self.ai_panel, fg_color="transparent")
        quick_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        quick_buttons = [
            ("❓", "How can you help me?"),
            ("⚙️", "What features are available?"),
            ("🔐", "How does encryption work?")
        ]
        
        for text, command in quick_buttons:
            btn = ctk.CTkButton(
                quick_frame,
                text=text,
                width=int((panel_width - 40) / 3),
                height=32,
                command=lambda c=command: self.quick_ai_command(c),
                fg_color=self.card_bg,
                hover_color=self.primary_color,
                corner_radius=8,
                font=("Arial", 16)
            )
            btn.pack(side='left', padx=2)
        
        # Clear button
        clear_btn = ctk.CTkButton(
            self.ai_panel,
            text="🗑️ Clear Chat",
            command=self.clear_ai_chat,
            height=32,
            fg_color=self.danger_color,
            hover_color="#c0392b",
            corner_radius=8,
            font=("Arial", self.font_size_small)
        )
        clear_btn.pack(fill='x', padx=10, pady=(5, 10))
        
        # Welcome message
        welcome_msg = """Welcome! 🤖

I can help you with:
• Feature explanations
• Troubleshooting
• Security info
• Usage tips

Ask me anything!"""
        
        self.add_ai_message("AI", welcome_msg)


if __name__ == "__main__":
    # Dependency check
    required = {
        'cryptography': 'cryptography',
        'customtkinter': 'customtkinter',
        'cv2': 'opencv-python',
        'pyaudio': 'pyaudio',
        'pyautogui': 'pyautogui',
        'PIL': 'Pillow'
    }
    
    missing = []
    for module, package in required.items():
        try:
            if module == 'cv2':
                import cv2
            elif module == 'PIL':
                from PIL import Image, ImageTk
            elif module == 'cryptography':
                from cryptography.fernet import Fernet
            else:
                __import__(module)
        except ImportError:
            missing.append(f"  - {package} (pip install {package})")
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(pkg)
        print("\n💡 Install with: pip install cryptography customtkinter opencv-python pyaudio pyautogui Pillow")
        exit(1)
    
    try:
        print("⚡ Starting ZeroConnect - Secure P2P Communication Platform")
        print("=" * 60)
        app = ZeroConnect()
        app.run()
    except KeyboardInterrupt:
        print("\n⚠️  Application interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()