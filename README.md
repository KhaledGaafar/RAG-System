# Mini RAG System with WebSocket Streaming

## Overview
Backend implementation of a RAG system with PDF processing and real-time LLM chat via WebSocket.

## Features
- JWT Authentication
- PDF text extraction and vector storage (using [Your Choice])
- WebSocket chat with RAG retrieval
- Real-time streaming responses

## Setup Instructions
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables (see `.env.example`)
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver`

## API Documentation

### Authentication
- `POST /api/v1/login/` - Get JWT token

### PDF Upload
- `POST /api/v1/upload/` - Upload and index PDF

### WebSocket
- `ws://localhost:8000/ws/chat/` - Connect with JWT token

## Testing Without UI
Use the provided Postman collection or test scripts:
- `test_auth.py` - Authentication tests
- `test_upload.py` - PDF upload tests
- `test_websocket.py` - WebSocket chat tests
