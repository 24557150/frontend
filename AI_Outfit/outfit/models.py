from django.db import models


# Create your models here.

class ClosetImage(models.Model):
    # 你自己定義的欄位，例如：
    image = models.ImageField(upload_to='closet/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class MimicImage(models.Model):
    image = models.ImageField(upload_to='mimic/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class RecommendationResult(models.Model):
    top = models.CharField(max_length=100)
    bottom = models.CharField(max_length=100)
    shoes = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

