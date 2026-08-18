# 🌊 DriftBridge

**An AI-Powered Multilingual Social Discovery Platform**

DriftBridge is a unique social networking platform that enables users to connect with strangers worldwide through digital bottles, breaking language barriers with AI-powered real-time translation and ensuring safe communication through intelligent content moderation.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Keys Setup](#api-keys-setup)
- [Database Schema](#database-schema)
- [Contributing](#contributing)

---

## ✨ Features

### 🔐 User Authentication & Profiles
- Secure registration and login system
- User profile management with bio, interests, and language preferences
- Trust & reputation system with 6 levels (🌱 Newcomer → 💎 Legend)
- Feature unlocking based on reputation points

### 🍾 Digital Bottle System
- Throw digital bottles with messages into the ocean
- Browse and keep bottles from other users
- Start conversations when bottles are accepted
- AI-powered hate speech detection on bottle messages

### 💬 Real-Time Multilingual Chat
- WebSocket-based real-time messaging
- **AI-powered automatic translation** supporting 15+ languages
- Messages automatically translated to each user's preferred language
- Translation indicator on translated messages
- Conversation history with timestamps

### 📔 Personal Journals
- Create, edit, and delete journal entries
- Three privacy levels:
  - 🔒 **Private** - Only you can see
  - 👥 **Connections** - Only your connections can see
  - 🌍 **Public** - Everyone can see
- Mood tags and custom tags support
- Discover public journals from the community
- View journals shared by your connections

### 📸 24-Hour Stories
- Share temporary stories that expire after 24 hours
- Text-based stories with customizable background colors
- View stories from your connections
- See who viewed your stories
- Visual indicators for unviewed stories

### 🤖 AI-Powered Features
- **Real-Time Translation**: Seamless communication across languages using Google Gemini API
- **Hate Speech Detection**: Automatic content moderation for messages, bottles, and journals
- **Content Safety**: AI analyzes and blocks inappropriate content before posting

### ⭐ Trust & Reputation System
- Earn points for positive actions:
  - Throw bottle: +5 points
  - Keep bottle: +10 points
  - Send message: +2 points
  - Create journal: +15 points
  - Create story: +10 points
- 6 Trust Levels with unique badges
- Feature unlocking:
  - Media sharing: 100+ points
  - Public journals: 50+ points
  - Voice messages: 150+ points
- Progress tracking with visual progress bar

### 🔒 Safety & Privacy
- AI-based content moderation
- User blocking and reporting system
- Privacy controls for journals and stories
- Connection-based content visibility
- Flagged content tracking for admin review

---

## 🛠️ Tech Stack

### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap** - Responsive design
- **Socket.IO Client** - Real-time communication

### Backend
- **Python 3.x**
- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket support
- **Flask-Login** - User authentication
- **Flask-Bcrypt** - Password hashing
- **Flask-Migrate** - Database migrations

### Database
- **MySQL** - Relational database
- **SQLAlchemy** - ORM

### AI & External Services
- **Google Gemini API** - AI translation and content moderation
- **Cloudinary** (configured for future media storage)

---

## 📥 Installation

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/bhumika815/DriftBridge.git
cd DriftBridge
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup MySQL Database
```sql
CREATE DATABASE driftbridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 5: Configure Environment Variables
Create a `.env` file in the project root:
```env
DATABASE_URL=mysql+pymysql://username:password@localhost/driftbridge
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Step 6: Initialize Database
```bash
flask db upgrade
```

### Step 7: Run the Application
```bash
python run.py
```

Visit: `http://127.0.0.1:5000`

---

## ⚙️ Configuration

### Google Gemini API Setup
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add the key to your `.env` file as `GEMINI_API_KEY`

### Cloudinary Setup (Optional - for future media features)
1. Sign up at [Cloudinary](https://cloudinary.com/)
2. Get your Cloud Name, API Key, and API Secret
3. Add them to your `.env` file

---

## 🎯 Usage

### Getting Started
1. **Register** a new account
2. **Complete your profile** with bio, interests, and preferred language
3. **Throw your first bottle** with a message
4. **Browse the bottle pool** and keep interesting bottles
5. **Start chatting** with your connections
6. **Create journals and stories** to share your experiences

### Language Settings
- Go to **Profile** → Select your **Preferred Language**
- All incoming messages will be automatically translated to your language
- Your messages will be translated to the recipient's language

### Earning Reputation Points
- Stay active on the platform
- Throw and keep bottles
- Send messages
- Create journals and stories
- Unlock new features as you level up!

---

## 📁 Project Structure

```
DriftBridge/
├── app/
│   ├── models/           # Database models
│   │   ├── user.py
│   │   ├── bottle.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── journal.py
│   │   ├── story.py
│   │   └── content_flag.py
│   ├── routes/           # Application routes
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── bottle.py
│   │   ├── chat.py
│   │   ├── journal.py
│   │   └── story.py
│   ├── services/         # Business logic
│   │   ├── ai_service.py
│   │   └── reputation_service.py
│   ├── sockets/          # WebSocket handlers
│   │   └── chat_socket.py
│   ├── templates/        # HTML templates
│   ├── static/           # Static files (CSS, JS, images)
│   ├── config.py         # Configuration
│   └── __init__.py       # App factory
├── migrations/           # Database migrations
├── instance/            # Instance-specific files
├── venv/               # Virtual environment
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
├── run.py             # Application entry point
└── README.md          # This file
```

---

## 🗄️ Database Schema

### Key Models

**User**
- Authentication and profile information
- Reputation points and trust level
- Language preferences

**Bottle**
- Digital bottle messages
- Status tracking (available/claimed)
- Sender and receiver references

**Conversation**
- Chat conversations between users
- Created when bottles are kept

**Message**
- Individual chat messages
- Original language tracking
- Real-time delivery via WebSockets

**Journal**
- Personal journal entries
- Privacy settings (private/connections/public)
- Tags and mood tracking

**Story**
- 24-hour temporary stories
- Auto-expiration timestamp
- View tracking

**ContentFlag**
- Flagged inappropriate content
- AI analysis results
- Admin review system

---

## 🔑 API Keys Setup

### Required
- **Google Gemini API** - For AI translation and content moderation
  - Get it from: https://makersuite.google.com/app/apikey
  - Free tier available

### Optional
- **Cloudinary** - For media storage (future feature)
  - Get it from: https://cloudinary.com
  - Free tier: 25GB storage

---

## 🌐 Supported Languages

- English
- Hindi (हिंदी)
- Spanish (Español)
- French (Français)
- German (Deutsch)
- Japanese (日本語)
- Chinese (中文)
- Arabic (العربية)
- Portuguese (Português)
- Russian (Русский)
- Bengali (বাংলা)
- Marathi (मराठी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Gujarati (ગુજરાતી)

---

## 🚀 Deployment

### Recommended Platforms
- **Render.com** - For application hosting
- **PlanetScale** or **AWS RDS** - For MySQL database
- **Cloudinary** - For media storage

### Environment Variables for Production
```env
FLASK_ENV=production
DATABASE_URL=your-production-database-url
SECRET_KEY=generate-a-strong-secret-key
GEMINI_API_KEY=your-gemini-api-key
```

---

## 🤝 Contributing

This is a student project for BSc Computer Science. Contributions, issues, and feature requests are welcome!

### Development Guidelines
1. Follow PEP 8 style guide for Python code
2. Write meaningful commit messages
3. Test features before committing
4. Update documentation for new features

---

## 📄 License

This project is developed as part of academic requirements for BSc Computer Science at R.K. Talreja College.

---

## 👨‍💻 Developer

**Bhumika Nikam**
- Roll No: 2526028
- Program: BSc Computer Science (Sem V)
- College: R.K. Talreja College of Arts, Science & Commerce
- Academic Year: 2026-2027

---

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- Flask community for excellent documentation
- Socket.IO for real-time communication support
- College faculty for guidance and support

---

## 📞 Support

For queries related to this project:
- GitHub Issues: https://github.com/bhumika815/DriftBridge/issues
- Project Repository: https://github.com/bhumika815/DriftBridge

---

**Made with ❤️ for connecting people across languages and cultures**
