from django.db import models

# Create your models here.
class gscholar(models.Model):

    
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.title