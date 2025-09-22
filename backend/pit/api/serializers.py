"""Serializers for the PIT headless API."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from pit.models import IndividualPlan, PlanTask
from users.api.serializers import UserSerializer

User = get_user_model()


class PlanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTask
        fields = [
            'id',
            'plan',
            'description',
            'subject',
            'state',
            'evidence_link',
            'teacher_feedback',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at', 'plan')


class IndividualPlanSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    tasks = PlanTaskSerializer(many=True, read_only=True)
    student_class_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = IndividualPlan
        fields = [
            'id',
            'student',
            'student_class_id',
            'period_label',
            'start_date',
            'end_date',
            'status',
            'general_objectives',
            'self_evaluation',
            'teacher_evaluation',
            'created_at',
            'updated_at',
            'tasks',
        ]
        read_only_fields = (
            'status',
            'created_at',
            'updated_at',
            'self_evaluation',
            'teacher_evaluation',
        )

    def validate_student_class_id(self, value):
        user = self.context['request'].user
        if user.role == 'aluno' and not user.classes_attended.filter(id=value).exists():
            raise serializers.ValidationError('Aluno não pertence à turma indicada.')
        return value

    def create(self, validated_data):
        class_id = validated_data.pop('student_class_id')
        request = self.context['request']
        user = request.user
        plan = IndividualPlan.objects.create(
            student=user,
            student_class_id=class_id,
            **validated_data,
        )
        return plan

    def update(self, instance, validated_data):
        # student_class is immutable post-creation
        validated_data.pop('student_class_id', None)
        return super().update(instance, validated_data)
