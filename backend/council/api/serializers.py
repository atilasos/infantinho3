"""Serializers for council decisions and student proposals."""
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from council.models import CouncilDecision, StudentProposal
from users.api.serializers import UserSerializer

User = get_user_model()


class CouncilDecisionSerializer(serializers.ModelSerializer):
    responsible = UserSerializer(read_only=True)
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='responsible', required=False, allow_null=True, write_only=True
    )
    student_class_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CouncilDecision
        fields = [
            'id',
            'student_class_id',
            'date',
            'description',
            'category',
            'status',
            'responsible',
            'responsible_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('status', 'created_at', 'updated_at')

    def validate_responsible_id(self, value):
        if not value:
            return value
        class_id = self.initial_data.get('student_class_id') or getattr(self.instance, 'student_class_id', None)
        if class_id:
            attends = getattr(value, 'classes_attended', User.objects.none())
            teaches = getattr(value, 'classes_taught', User.objects.none())
            belongs = attends.filter(id=class_id).exists() or teaches.filter(id=class_id).exists()
            if not belongs:
                raise serializers.ValidationError(_('O responsável deve pertencer à turma.'))
        return value

    def create(self, validated_data):
        student_class_id = validated_data.pop('student_class_id')
        responsible = validated_data.pop('responsible', None)
        from classes.models import Class
        turma = Class.objects.get(pk=student_class_id)
        decision = CouncilDecision.objects.create(student_class=turma, responsible=responsible, **validated_data)
        return decision

    def update(self, instance, validated_data):
        validated_data.pop('student_class_id', None)
        return super().update(instance, validated_data)


class StudentProposalSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    student_class_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = StudentProposal
        fields = [
            'id',
            'student_class_id',
            'author',
            'text',
            'date_submitted',
            'status',
        ]
        read_only_fields = ('date_submitted', 'status')

    def create(self, validated_data):
        student_class_id = validated_data.pop('student_class_id')
        from classes.models import Class
        turma = Class.objects.get(pk=student_class_id)
        proposal = StudentProposal.objects.create(
            student_class=turma,
            author=self.context['request'].user,
            **validated_data,
        )
        return proposal

    def update(self, instance, validated_data):
        validated_data.pop('student_class_id', None)
        return super().update(instance, validated_data)
