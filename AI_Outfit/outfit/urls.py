# AI_Outfit/outfit/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 加這一行：對應 http://127.0.0.1:8000/
    path('liff/closet/', views.closet_upload_view, name='closet_upload'),
    path('liff/mimic/', views.mimic_upload_view, name='mimic_upload'),
    path('liff/recommend/', views.recommend_result_view, name='recommend_result'),
]