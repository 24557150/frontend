from django.db import models

# Create your models here.
from django.db import models
import os
from django.utils.timezone import now



def user_directory_path(instance, filename):
    return f'closet/{instance.user_id}/{instance.category}/{filename}'

class ClosetItem(models.Model):
    user_id = models.CharField(max_length=64)
    category = models.CharField(max_length=32, blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user_id} - {self.category} - {self.image.name}' 