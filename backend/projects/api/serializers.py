"""Serializers for cooperative project workflows."""
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from projects.models import Project, ProjectTask
from users.api.serializers import UserSerializer

User = get_user_model()


class ProjectTaskSerializer(serializers.ModelSerializer):
    responsible = UserSerializer(read_only=True)
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='responsible', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = ProjectTask
        fields = [
            'id',
            'project',
            'description',
            'responsible',
            'responsible_id',
            'due_date',
            'state',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('project', 'created_at', 'updated_at')

    def validate_responsible_id(self, value):
        project = self.context.get('project')
        if not project and self.instance:
            project = self.instance.project
        if value and project and not project.members.filter(id=value.id).exists():
            raise serializers.ValidationError(_('Responsável deve ser membro do projeto.'))
        return value


class ProjectSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), write_only=True, required=False
    )
    student_class_id = serializers.IntegerField(write_only=True)
    tasks = ProjectTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'student_class_id',
            'title',
            'description',
            'state',
            'start_date',
            'end_date',
            'product_description',
            'members',
            'member_ids',
            'tasks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('state', 'created_at', 'updated_at')

    def _class_members_queryset(self, class_id):
        from classes.models import Class  # local import to avoid cycles
        turma = Class.objects.get(pk=class_id)
        return (turma.students.all() | turma.teachers.all()).distinct(), turma

    def validate_member_ids(self, value):
        request = self.context['request']
        class_id = request.data.get('student_class_id') or getattr(self.instance, 'student_class_id', None)
        if not class_id:
            return value
        members_qs, _turma = self._class_members_queryset(class_id)
        allowed_ids = set(members_qs.values_list('id', flat=True))
        invalid = [member_id for member_id in value if member_id not in allowed_ids]
        if invalid:
            raise serializers.ValidationError(_('Membros devem pertencer à turma. IDs inválidos: ') + ', '.join(map(str, invalid)))
        return value

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        class_id = validated_data.pop('student_class_id')
        members_qs, turma = self._class_members_queryset(class_id)
        project = Project.objects.create(student_class=turma, **validated_data)
        requester = self.context['request'].user
        if members_qs.filter(id=requester.id).exists():
            project.members.add(requester)
        if member_ids:
            project.members.add(*members_qs.filter(id__in=member_ids))
        project.save()
        return project

    def update(self, instance, validated_data):
        member_ids = validated_data.pop('member_ids', None)
        validated_data.pop('student_class_id', None)
        project = super().update(instance, validated_data)
        if member_ids is not None:
            members_qs, _ = self._class_members_queryset(instance.student_class_id)
            new_members = list(members_qs.filter(id__in=member_ids))
            project.members.set(new_members)
            requester = self.context['request'].user
            if members_qs.filter(id=requester.id).exists():
                project.members.add(requester)
        return project
