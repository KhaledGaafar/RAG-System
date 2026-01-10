import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async


from .models import PDFDocument
from .utils import RAGService, LLMService

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)

class JWTAuthMixin:
    async def get_user_from_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if user_id:
                return await database_sync_to_async(User.objects.get)(id=user_id)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return AnonymousUser()
        return AnonymousUser()


class ChatConsumer(JWTAuthMixin,AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.document_id = None

    async def connect(self):
        try:
            await self.accept()

            query_params = self.scope.get('query_string', b'').decode()
            params = dict(p.split('=') for p in query_params.split('&') if '=' in p)
            token = params.get('token')

            if not token:
                headers = dict(self.scope.get('headers', []))
                protocol_header = headers.get(b'sec-websocket-protocol', b'').decode()
                if protocol_header:
                    parts = protocol_header.split()
                    token = parts[1] if len(parts) > 1 else parts[0]

            if not token:
                await self._send_error("Authentication required", 4001)
                await self.close(code=4001)
                return

            self.user = await self.get_user_from_token(token)

            if isinstance(self.user, AnonymousUser):
                await self._send_error("Invalid token", 4001)
                await self.close(code=4001)
                return


            query_params = self.scope.get('query_string', b'').decode()
            params = dict(p.split('=') for p in query_params.split('&') if '=' in p)
            self.document_id = params.get('document_id')

            if self.document_id:
                try:
                    await self._validate_document_access(self.document_id)
                except Exception as e:
                    await self._send_error(str(e), 4003)
                    await self.close(code=4003)
                    return


            await self._send_message({
                'type': 'connection_established',
                'message': 'Connected to PDF Chat. You can now ask questions about your documents.'
            })

            logger.info(f"WebSocket connected: user={self.user.id}")

        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            await self._send_error("Connection failed", 4000)
            await self.close(code=4000)

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: user={self.user}, code={close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'query')

            if message_type == 'query':
                await self._handle_query(data)
            else:
                await self._send_error(f"Unknown message type: {message_type}", 4004)

        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format", 4005)
        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}")
            await self._send_error("Message processing failed", 4006)

    async def _handle_query(self, data):
        query = data.get('query', '').strip()

        if not query:
            await self._send_error("Query cannot be empty", 4007)
            return

        await self._send_message({
            'type': 'processing',
            'message': 'Searching documents...'
        })

        try:
            rag_service = RAGService(self.user, self.document_id)
            context_results = await sync_to_async(rag_service.search)(query)

            if not context_results:
                await self._send_message({
                    'type': 'response',
                    'response': "I couldn't find relevant information in your documents.",
                    'complete': True
                })
                return

            context_texts = [f"Result {res['content']}"
                             for res in context_results]

            await self._generate_streaming_response(query, context_texts, context_results)

        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            await self._send_error(f"Failed to process query: {str(e)}", 4008)

    async def _generate_streaming_response(self, query, context_texts, context_results):
        try:
            llm_service = LLMService()

            response = await sync_to_async(llm_service.generate_response)(
                query,
                context_texts,
            )

            await self._send_message({
                'type': 'response',
                'response': response,
                'complete': True
            })

        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            await self._send_error(f"Failed to generate response: {str(e)}", 4009)

    async def _validate_document_access(self, document_id):
        try:
            document = await sync_to_async(PDFDocument.objects.get)(
                id=document_id,
                user=self.user,
            )
            return document
        except PDFDocument.DoesNotExist:
            raise Exception("Document not found or not processed")

    async def _send_message(self, data):

        await self.send(text_data=json.dumps(data))

    async def _send_error(self, message, code=None):
        error_data = {
            'type': 'error',
            'message': message,
            'code': code
        }
        await self.send(text_data=json.dumps(error_data))







