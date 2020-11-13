from django.db import models

# Create your models here.

class ProfileImage(models.Model):
    userid = models.IntegerField()
    image = models.ImageField(upload_to = "Profile")

    def __str__(self):
        return str(self.userid) + ' created' 