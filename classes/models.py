from django.db import models
from users.models import User

class Class(models.Model):
    name = models.CharField(max_length=50)
    year = models.IntegerField()
    students = models.ManyToManyField(User, related_name='classes_attended')
    teachers = models.ManyToManyField(User, related_name='classes_taught')

    def __str__(self):
        return f"{self.name} ({self.year})"
