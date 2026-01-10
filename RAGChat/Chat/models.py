from django.db import models
from django.contrib.auth.models import User

# Create your models here.

def user_pdf_path(instance,filename):
    return f'users{instance.user.id}/pdfs/{filename}'

class PDFDocument(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    title=models.CharField(max_length=255)
    pdf_file=models.FileField(upload_to=user_pdf_path)
    uploaded_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['-uploaded_at']
        indexes=[models.Index(fields=['user'])]

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class DocumentChunk(models.Model):
    document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='chunks')
    text = models.TextField()




