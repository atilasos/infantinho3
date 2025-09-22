"""Serializers for headless checklist interactions."""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from checklists.models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark
from users.api.serializers import UserSerializer

User = get_user_model()


class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['id', 'code', 'text', 'order', 'contracted_in_council']


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)

    class Meta:
        model = ChecklistTemplate
        fields = ['id', 'name', 'description', 'items']


class ChecklistMarkSerializer(serializers.ModelSerializer):
    item = ChecklistItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=ChecklistItem.objects.all(), source='item', write_only=True, required=False
    )
    marked_by = UserSerializer(read_only=True)

    class Meta:
        model = ChecklistMark
        fields = [
            'id',
            'status_record',
            'item',
            'item_id',
            'mark_status',
            'teacher_validated',
            'comment',
            'marked_at',
            'marked_by',
        ]
        read_only_fields = ('marked_at', 'marked_by')

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        mark = self.instance
        new_status = attrs.get('mark_status', getattr(mark, 'mark_status', None))

        if mark and mark.status_record.student_id != user.id and user.role == 'aluno':
            raise serializers.ValidationError('Student can only update their own marks.')

        if user.role == 'aluno':
            if new_status == 'VALIDATED':
                raise serializers.ValidationError('Students cannot set mark status to VALIDATED.')
            if 'teacher_validated' in attrs:
                raise serializers.ValidationError('Students cannot change teacher validation flag.')

        if user.role == 'professor':
            if new_status == 'VALIDATED':
                # Normalise to COMPLETED + teacher_validated flag
                attrs['mark_status'] = 'COMPLETED'
                attrs['teacher_validated'] = True

        if user.role not in {'aluno', 'professor'} and not user.is_superuser and user.role != 'admin':
            raise serializers.ValidationError('Role not permitted to update checklist marks.')

        return attrs

    def update(self, instance, validated_data):
        request = self.context['request']
        user = request.user
        mark_status = validated_data.get('mark_status', instance.mark_status)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.marked_by = user

        if user.role == 'professor' and mark_status != 'COMPLETED':
            # Teachers toggling away from completed should drop validation
            instance.teacher_validated = validated_data.get('teacher_validated', False)

        if user.role == 'professor' and mark_status == 'COMPLETED':
            instance.teacher_validated = validated_data.get('teacher_validated', instance.teacher_validated)

        instance.save()
        return instance


class ChecklistStatusSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    template = ChecklistTemplateSerializer(read_only=True)
    marks = ChecklistMarkSerializer(many=True, read_only=True)

    class Meta:
        model = ChecklistStatus
        fields = [
            'id',
            'template',
            'student',
            'student_class_id',
            'percent_complete',
            'updated_at',
            'marks',
        ]
        read_only_fields = fields
