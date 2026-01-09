from django.shortcuts import render
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import PDFUploadedSerializer,PDFDocumentSerializer
from .models import PDFDocument
from rest_framework import status
from rest_framework.response import Response

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





