from django.db import models
from users.models import User
from classes.models import Class

class Post(models.Model):
    turma = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='posts')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    publicado_em = models.DateTimeField(auto_now_add=True)
    categoria = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.titulo

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    conteudo = models.TextField()
    publicado_em = models.DateTimeField(auto_now_add=True)
