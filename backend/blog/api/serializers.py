"""Serializers powering the headless blog endpoints."""
from django.utils.html import strip_tags
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from blog.models import Post
from users.api.serializers import UserSerializer


class PostSerializer(serializers.ModelSerializer):
    autor = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    turma_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = Post
        fields = [
            'id',
            'turma_id',
            'autor',
            'titulo',
            'conteudo',
            'categoria',
            'status',
            'publicado_em',
            'approved_by',
            'approved_at',
            'removido',
            'motivo_remocao',
        ]
        read_only_fields = (
            'autor',
            'status',
            'publicado_em',
            'approved_by',
            'approved_at',
            'removido',
            'motivo_remocao',
        )

    def create(self, validated_data):
        request = self.context['request']
        validated_data['autor'] = request.user
        return super().create(validated_data)


class PublicPostSerializer(serializers.ModelSerializer):
    autor = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'titulo',
            'conteudo',
            'categoria',
            'publicado_em',
            'turma_id',
            'autor',
            'excerpt',
        ]

    @extend_schema_field(serializers.JSONField())
    def get_autor(self, obj):
        author = obj.autor
        if not author:
            return None
        full_name = author.get_full_name()
        return {
            'name': full_name or author.username,
            'role': getattr(author, 'role', None),
        }

    @extend_schema_field(serializers.CharField())
    def get_excerpt(self, obj):
        plain = strip_tags(obj.conteudo or '').replace('\r', ' ').replace('\n', ' ')
        if len(plain) <= 240:
            return plain
        return f"{plain[:237].rstrip()}…"
