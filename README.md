# 🤖 RAG FAQ Chatbot - Intelligent Web Chatbot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.2+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)

A modern, intelligent FAQ chatbot built with **Retrieval-Augmented Generation (RAG)** technology. This full-stack application combines the power of large language models with your custom knowledge base to provide accurate, contextual responses.

## 🌟 Features

### Core Capabilities
- **🧠 RAG-Powered Intelligence**: Combines retrieval and generation for accurate responses
- **📚 Multi-Format Document Support**: PDF, TXT, DOCX, and more
- **🔍 Semantic Search**: Advanced vector similarity search with embeddings
- **💬 Real-Time Chat**: WebSocket-based instant messaging
- **🎨 Modern UI**: Responsive design with Tailwind CSS
- **🔐 Secure Authentication**: JWT-based auth with role management

### Advanced Features
- **📊 Admin Dashboard**: Document management and analytics
- **🌐 Multi-Language Support**: French and English
- **📱 Mobile Responsive**: Works seamlessly on all devices
- **⚡ High Performance**: Optimized for speed and scalability
- **🔄 Real-Time Updates**: Live chat with typing indicators
- **📈 Analytics**: Conversation metrics and user feedback

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI       │    │   Vector DB     │
│   (Port 3000)   │────│   Backend       │────│   (ChromaDB)    │
│                 │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   PostgreSQL    │    │   Redis         │
│   (Reverse      │    │   (Database)    │    │   (Cache)       │
│   Proxy)        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- OpenAI API Key or Hugging Face API Key

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/rag-faq-chatbot.git
cd rag-faq-chatbot
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Launch with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📋 Environment Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/rag_chatbot
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Vector Database
CHROMA_DB_PATH=./data/chroma_db
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Application
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=["http://localhost:3000"]
```

## 🔧 Development

### Project Structure
```
rag-faq-chatbot/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configurations
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── data/               # Data storage
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom hooks
│   │   └── context/        # React contexts
│   └── public/             # Static assets
└── docker-compose.yml      # Docker configuration
```

### Running Tests

#### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

#### Frontend Tests
```bash
cd frontend
npm test
```

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 Usage

### 1. Document Upload
- Access the admin panel at `/admin`
- Upload your FAQ documents (PDF, TXT, DOCX)
- Documents are automatically processed and indexed

### 2. Chat Interface
- Navigate to the main chat interface
- Ask questions about your uploaded documents
- Receive intelligent, contextual responses

### 3. Admin Features
- Monitor chat analytics
- Manage document library
- Review user feedback
- Configure system settings

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh

### Chat
- `POST /api/v1/chat/message` - Send message
- `GET /api/v1/chat/history` - Get chat history
- `WebSocket /api/v1/chat/ws` - Real-time chat

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/` - List documents
- `DELETE /api/v1/documents/{id}` - Delete document

### Admin
- `GET /api/v1/admin/analytics` - Get analytics
- `GET /api/v1/admin/users` - Manage users

## 🎨 Customization

### Styling
The frontend uses Tailwind CSS for styling. Customize the theme in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#10B981',
        // Add your custom colors
      }
    }
  }
}
```

### AI Models
Configure different AI models in `backend/app/core/config.py`:

```python
# OpenAI GPT
OPENAI_MODEL = "gpt-3.5-turbo"

# Hugging Face
HF_MODEL = "microsoft/DialoGPT-medium"

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

## 🚀 Deployment

### Docker Production
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript
- Write tests for new features
- Update documentation

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
docker-compose ps
# Reset database
docker-compose down -v && docker-compose up -d
```

**Frontend Build Issues**
```bash
# Clear node modules
rm -rf node_modules package-lock.json
npm install
```

**API Rate Limits**
- Check your OpenAI API usage
- Implement request caching
- Use a different model if needed



## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python framework
- [React](https://reactjs.org/) for the frontend framework
- [OpenAI](https://openai.com/) for the language models
- [ChromaDB](https://www.trychroma.com/) for vector database
- [Tailwind CSS](https://tailwindcss.com/) for styling



**⭐ Star this repository if you find it helpful!**
