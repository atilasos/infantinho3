"""Serializers for the diary API."""
from __future__ import annotations

from rest_framework import serializers

from diary.models import DiaryEntry, DiarySession
from classes.models import Class
from users.api.serializers import UserSerializer


class DiaryEntrySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    column_label = serializers.CharField(source='get_column_display', read_only=True)

    class Meta:
        model = DiaryEntry
        fields = ['id', 'column', 'column_label', 'content', 'created_at', 'author']
        read_only_fields = fields


class DiarySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiarySession
        fields = ['id', 'start_date', 'end_date', 'status']
        read_only_fields = fields


class DiaryClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    year = serializers.IntegerField()

    @classmethod
    def from_instance(cls, turma: Class) -> dict:
        return {'id': turma.id, 'name': turma.name, 'year': turma.year}
