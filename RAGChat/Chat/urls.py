
from django.urls import path
from . import views

urlpatterns = [
    path('documents/', views.PDFUploadAPI.as_view(), name='api_upload'),

]