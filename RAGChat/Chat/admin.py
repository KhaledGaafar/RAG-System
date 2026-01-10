from django.contrib import admin
from .models import PDFDocument,DocumentChunk

# Register your models here.
admin.site.register(PDFDocument)
admin.site.register(DocumentChunk)
