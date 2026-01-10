from django.shortcuts import render
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import PDFUploadedSerializer,PDFDocumentSerializer
from .models import PDFDocument
from rest_framework import status
from rest_framework.response import Response
from .utils import PDFProcessor
import threading

# Create your views here.

logger = logging.getLogger(__name__)

class PDFUploadAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):

        try:
            serializer=PDFUploadedSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success':False,
                    'error':'validation failed',
                    'detail':serializer.errors
                },status=status.HTTP_400_BAD_REQUEST)

            pdf_file=serializer.validated_data['file']
            title=serializer.validated_data.get('title',pdf_file.name)

            document=PDFDocument.objects.create(
                user=request.user,
                title=title,
                pdf_file=pdf_file
            )
            self._process_in_background(document)
            return Response({
                'success': True,
                'message': 'PDF uploaded successfully. Processing started.',
                'document': PDFDocumentSerializer(document).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Upload failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        documents = PDFDocument.objects.filter(user=request.user)
        serializer = PDFDocumentSerializer(documents, many=True)
        return Response({
            'success': True,
            'documents': serializer.data
        })
    def _process_in_background(self,document):

        def process():
            try:
                processor=PDFProcessor(document)
                pages = processor.extract_text()
                chunks = processor.chunk_text(pages)
                processor.create_vector_store(chunks)


                document.save()
                logger.info(f"Document {document.id} processed successfully")

            except Exception as e:
               logger.error(f"Processing failed for {document.id}: {str(e)}")
               document.delete()

        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()








