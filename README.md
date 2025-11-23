# ⚡ ZeroConnect

> **Secure Peer-to-Peer Communication Platform with End-to-End Encryption**

ZeroConnect is a modern, feature-rich P2P communication application that enables secure video calls, screen sharing, voice chat, and file transfers without relying on central servers. Built with Python and featuring a sleek dark-themed UI.

## ✨ Features

### 🔐 Security First
- **AES-256 Encryption** for all communications
- **PBKDF2 Key Derivation** with 100,000 iterations
- End-to-end encrypted messaging, file transfers, and media streams
- Zero data stored on external servers

### 📹 Video & Audio
- HD video calling with quality controls (480p/720p/1080p)
- Real-time audio streaming with PyAudio
- Picture-in-Picture mode for multitasking
- Fullscreen video support
- Resizable video panels

### 🖥️ Screen Sharing
- Share your entire screen in real-time
- Optimized compression for smooth streaming
- Perfect for presentations and remote support

### 💬 Real-Time Chat
- Encrypted instant messaging
- Timestamp tracking
- Clean, modern chat interface

### 📁 Secure File Transfer
- Send files up to 100MB
- Encrypted file transmission
- Progress tracking

### 🔍 Auto Peer Discovery
- Automatic detection of peers on local network
- UDP broadcasting for zero-configuration setup
- Manual IP entry option

### 🤖 AI Assistant (Optional)
- Integrated AI help using Ollama
- Feature explanations and troubleshooting
- Quick action commands

### 🎨 Modern UI
- Dark-themed, responsive design
- Customizable settings
- Smooth animations and transitions
- Adaptive layouts for different screen sizes

## 🛠️ Technology Stack

- **GUI Framework:** CustomTkinter (modern tkinter)
- **Video Processing:** OpenCV (cv2)
- **Audio:** PyAudio
- **Encryption:** Cryptography (Fernet/AES-256)
- **Networking:** Socket programming (TCP/UDP)
- **Screen Capture:** PyAutoGUI
- **AI Integration:** Ollama (optional)

## 📋 Requirements

### Python Dependencies
```bash
pip install customtkinter opencv-python pyaudio pyautogui Pillow cryptography
```

### System Requirements
- Python 3.8+
- Webcam (for video calls)
- Microphone (for audio)
- Local network connection (for P2P)

### Optional
- Ollama with gemma3:270m model (for AI assistant)

## 🚀 Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/zeroconnect.git
cd zeroconnect
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python zeroconnect.py
```

4. **Connect to a peer**
   - Launch ZeroConnect on both devices
   - Wait for auto-discovery (peers appear in dropdown)
   - Click "Connect" button
   - Start video, audio, or screen sharing!

## 📖 Usage Guide

### Connecting to a Peer
1. **Auto-Discovery:** Peers on the same network appear automatically
2. **Manual:** Enter peer's IP address directly
3. Click "Connect" to establish encrypted connection

### Starting Media
- **Video:** Click "📹 Video" button
- **Audio:** Click "🎤 Audio" button
- **Screen Share:** Click "🖥️ Screen Share" button

### Sending Files
1. Click "📤 Send File"
2. Select file (max 100MB)
3. File is encrypted and sent automatically

### Settings
- Adjust video quality (Low/Medium/High)
- Change audio sample rate
- Configure encryption password
- Set network port

## 🏗️ Architecture

The application follows a layered architecture:

1. **UI Layer:** CustomTkinter-based responsive interface
2. **Core Services:** Security, peer discovery, media management
3. **Network Layer:** TCP for data, UDP for discovery
4. **Data Protocol:** Custom TLV (Type-Length-Value) format

See the architecture diagram for detailed component interaction.

## 🔒 Security Features

- **Encryption Algorithm:** AES-256 (Fernet)
- **Key Derivation:** PBKDF2-HMAC-SHA256
- **Salt:** Unique per session
- **Iterations:** 100,000 (PBKDF2)
- **All data types encrypted:** Messages, files, audio

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

### Development Setup
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 To-Do / Future Features

- [ ] Group video calls (3+ participants)
- [ ] NAT traversal for internet-wide P2P
- [ ] Mobile app version
- [ ] Recording functionality
- [ ] Virtual backgrounds
- [ ] Emoji reactions
- [ ] GIF support in chat
- [ ] Persistent chat history

## ⚠️ Known Limitations

- Currently works on local networks (LAN)
- Maximum file size: 100MB
- Requires port 9999 and 9998 available
- No mobile version yet

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CustomTkinter for modern UI components
- OpenCV for video processing
- Cryptography library for security
- Python community for excellent libraries

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**⚡ ZeroConnect - Secure communication, zero compromises.**
```

## **Topics/Tags for GitHub:**
```
python, p2p, video-call, encryption, aes-256, customtkinter, opencv, screen-sharing, peer-to-peer, secure-chat, real-time-communication, end-to-end-encryption, python-gui, networking, socket-programming, video-streaming, audio-streaming, file-transfer, dark-theme, modern-ui
```

## **Additional Files to Create:**

### `requirements.txt`
```
customtkinter>=5.2.0
opencv-python>=4.8.0
pyaudio>=0.2.13
pyautogui>=0.9.54
Pillow>=10.0.0
cryptography>=41.0.0
numpy>=1.24.0
```

### `.gitignore`
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
venv/
ENV/
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
