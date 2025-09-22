"""Serializers for class/turma resources."""
from rest_framework import serializers

from classes.models import Class
from users.api.serializers import UserSerializer


class ClassSerializer(serializers.ModelSerializer):
    students = UserSerializer(many=True, read_only=True)
    teachers = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Class
        fields = ['id', 'name', 'year', 'students', 'teachers']


class ClassMembershipUpdateSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='Lista de IDs de alunos associados à turma.'
    )
    teacher_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='Lista de IDs de professores associados à turma.'
    )
