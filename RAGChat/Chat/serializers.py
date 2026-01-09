from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PDFDocument

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','username','email']

class PDFDocumentSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)

    class Meta:
        model=PDFDocument
        fields=['id','title','uploaded_at','user']
        read_only_fields=['id','uploaded_at','user']

class PDFUploadedSerializer(serializers.Serializer):
    file=serializers.FileField(
        allow_empty_file=False,
        max_length=100 * 1024 * 1024
    )
    title = serializers.CharField(
        required=False,
        max_length=255,
    )

    def validate_file(self,value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("File must be a PDF")
        max_size= 100*1024*1024
        if value.size>max_size:
            raise serializers.ValidationError("File size must not exceed 100MB")

        return value
