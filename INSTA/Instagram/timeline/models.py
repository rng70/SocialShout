from django.db import models

# Create your models here.

class PostImage(models.Model):
    postid = models.IntegerField()
    image = models.ImageField(upload_to = "Post")

    def __str__(self):
        return str(self.postid) + ' created' 
    
