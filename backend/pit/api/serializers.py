"""Serializers for the PIT headless API."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from pit.models import IndividualPlan, PlanTask, PitTemplate, PlanSuggestion
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
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=PitTemplate.objects.all(),
        source='template',
        required=False,
        allow_null=True,
        write_only=True,
    )
    template = serializers.SerializerMethodField()
    student_class = serializers.SerializerMethodField()
    origin_plan_id = serializers.IntegerField(source='origin_plan.id', read_only=True)
    suggestions = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()

    class Meta:
        model = IndividualPlan
        fields = [
            'id',
            'student',
            'student_class_id',
            'student_class',
            'template',
            'template_id',
            'template_version',
            'origin_plan_id',
            'suggestions_imported',
            'pendings_imported',
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
            'suggestions',
            'sections',
        ]
        read_only_fields = (
            'status',
            'created_at',
            'updated_at',
            'self_evaluation',
            'teacher_evaluation',
            'template',
            'template_version',
            'origin_plan_id',
            'suggestions_imported',
            'pendings_imported',
            'suggestions',
            'sections',
            'student_class',
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

    def get_template(self, obj):
        if not obj.template:
            return None
        return {
            'id': obj.template_id,
            'name': obj.template.name,
            'version': obj.template.version,
        }

    def get_student_class(self, obj):
        if not obj.student_class_id or not obj.student_class:
            return None
        return {
            'id': obj.student_class_id,
            'name': obj.student_class.name,
            'year': obj.student_class.year,
        }

    def get_suggestions(self, obj):
        suggestions = obj.suggestions.all().order_by('order', 'id')
        return [
            {
                'id': suggestion.id,
                'text': suggestion.text,
                'origin': suggestion.origin,
                'is_pending': suggestion.is_pending,
                'order': suggestion.order,
                'template_suggestion_id': suggestion.template_suggestion_id,
                'from_task_id': suggestion.from_task_id,
                'created_at': suggestion.created_at,
            }
            for suggestion in suggestions
        ]

    def get_sections(self, obj):
        sections = obj.sections.all().order_by('order', 'id')
        return [
            {
                'id': section.id,
                'title': section.title,
                'area_code': section.area_code,
                'order': section.order,
                'template_section_id': section.template_section_id,
            }
            for section in sections
        ]
