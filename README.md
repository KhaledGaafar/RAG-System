# Mini RAG System with WebSocket Streaming

A lightweight, real-time Retrieval-Augmented Generation (RAG) system built with Django, featuring PDF processing capabilities and streaming chat responses via WebSocket.

## 🎯 Overview

This backend implementation provides a complete RAG pipeline that enables users to upload PDF documents, extract and index their content, and interact with the information through a conversational AI interface. The system leverages JWT authentication for security and WebSocket connections for real-time streaming responses.

## ✨ Features

- **🔐 JWT Authentication** - Secure token-based authentication system
- **📄 PDF Processing** - Automated text extraction and vector storage using TF-IDF vectorization
- **💬 Real-time Chat** - WebSocket-powered chat interface with RAG retrieval
- **⚡ Streaming Responses** - Live streaming of LLM-generated responses
- **🔍 Semantic Search** - Context-aware document retrieval for enhanced responses

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/KhaledGaafar/RAG-System.git
   cd RAGChat
   ```

2. **Create and activate virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Installation may take several minutes due to heavy ML packages*

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```      
   Edit `.env` with your configuration settings

- If there are problems using an external database (PostgreSQL), you can use the default lightweight database (SQLite) by changing the DATABASES configuration in settings to:
   ```bash
   'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
   ```

6. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

The server will be available at `http://127.0.0.1:8000/`

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /auth/users/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password",
  "email": "your_email@example.com"
}
```

#### Login
```http
POST /auth/jwt/create/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Document Management

#### Upload PDF
```http
POST /api/v1/documents/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <pdf_file>
```

**Response:**
```json
{
  "id": "doc_id",
  "filename": "document.pdf",
  "created_at": "2025-01-11T10:00:00Z"
}
```

### WebSocket Chat

#### Connect to Chat
```
ws://localhost:8000/ws/chat/?token=<access_token>
```

**Send Message:**
```json
{
  "query": "What does the document say about...?"
}
```

**Receive Streaming Response:**
```json
{
  "type": "response",
  "content": "Based on the document...",
  "complete": true
}
```

## 🧪 Testing

### Using Postman Collections

Pre-configured Postman collections are available for easy testing:

**REST API Endpoints:**
- [Authentication & PDF Upload Collection](https://www.postman.co/workspace/My-Workspace~88fc94a3-6611-4237-8885-1f3eff4cad96/collection/42832594-ff9072d4-41c7-441a-91cc-c7c72e7a8cef?action=share&creator=42832594)

**WebSocket Testing:**
- [WebSocket Chat Collection](https://www.postman.co/workspace/My-Workspace~88fc94a3-6611-4237-8885-1f3eff4cad96/ws-raw-request/6962f671797e7ba2767b5701?action=share&creator=42832594&ctx=documentation)

### Using Django REST Framework Browsable API

Navigate to any endpoint in your browser while the server is running to access the interactive API explorer:
```
http://127.0.0.1:8000/api/v1/
```

### Manual Testing

You can test endpoints using curl, httpie, or any HTTP client:

```bash
# Register
curl -X POST http://127.0.0.1:8000/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123","email":"test@example.com"}'

# Login
curl -X POST http://127.0.0.1:8000/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

## 🛠️ Technology Stack

- **Framework:** Django + Django REST Framework
- **WebSocket:** Django Channels
- **Authentication:** JWT (Simple JWT)
- **Vector Store:** TF-IDF (scikit-learn)
- **PDF Processing:** PyPDF2/pdfplumber
- **LLM Integration:** Configurable (Grok)

## 🗺️ Roadmap

### Upcoming Features

- [ ] **Frontend Interface** - Simple UI using Django templates for easier testing
- [ ] **Advanced RAG Tools** - Integration with more sophisticated vector stores (Pinecone, Weaviate, ChromaDB)
- [ ] **Multi-LLM Support** - Support for multiple LLM providers (GPT-4, Claude, Llama, etc.)
- [ ] **Docker Support** - Complete containerization for simplified deployment

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

For issues, questions, or contributions, please open an issue in the GitHub repository.

---

**Built with ❤️ using Django and modern RAG techniques**
