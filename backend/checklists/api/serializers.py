"""Serializers for headless checklist interactions."""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from classes.models import Class
from checklists.models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark
from users.api.serializers import UserSerializer

User = get_user_model()


class ChecklistItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    is_deleted = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = ChecklistItem
        fields = ['id', 'code', 'text', 'order', 'contracted_in_council', 'is_deleted']

    def validate_order(self, value):
        return value if value is not None else 0


class ChecklistTemplateClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'name', 'year']


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, required=False)
    classes = ChecklistTemplateClassSerializer(many=True, read_only=True)
    class_ids = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all(),
        many=True,
        required=False,
        write_only=True,
        source='classes'
    )

    class Meta:
        model = ChecklistTemplate
        fields = [
            'id',
            'name',
            'description',
            'version',
            'is_published',
            'created_by',
            'created_at',
            'updated_at',
            'items',
            'classes',
            'class_ids',
        ]
        read_only_fields = ('created_by', 'created_at', 'updated_at', 'classes')

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        role = getattr(user, 'role', None)
        if request.method in {'POST', 'PUT', 'PATCH'} and role not in {'professor', 'admin'} and not user.is_superuser:
            raise serializers.ValidationError('Apenas professores ou administradores podem gerir modelos de checklist.')
        return super().validate(attrs)

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        classes = validated_data.pop('classes', [])
        template = ChecklistTemplate.objects.create(**validated_data)
        if classes:
            template.classes.set(classes)
        self._sync_items(template, items_data)
        return template

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        classes = validated_data.pop('classes', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if classes is not None:
            instance.classes.set(classes)

        if items_data is not None:
            self._sync_items(instance, items_data)

        return instance

    def _sync_items(self, template: ChecklistTemplate, items_data: list[dict]) -> None:
        existing_items = {item.id: item for item in template.items.all()}
        seen_ids = set()

        for position, item_data in enumerate(items_data, start=1):
            item_id = item_data.pop('id', None)
            is_deleted = item_data.pop('is_deleted', False)
            item_data.setdefault('order', position)

            if item_id and item_id in existing_items:
                seen_ids.add(item_id)
                item = existing_items[item_id]
                if is_deleted:
                    item.delete()
                    continue
                for attr, value in item_data.items():
                    setattr(item, attr, value)
                item.save()
            else:
                if is_deleted:
                    continue
                ChecklistItem.objects.create(template=template, **item_data)

        # Remove items not referenced anymore
        for item_id, item in existing_items.items():
            if item_id not in seen_ids and all(entry.get('id') != item_id for entry in items_data):
                item.delete()


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
    student_class = ChecklistTemplateClassSerializer(read_only=True)
    marks = ChecklistMarkSerializer(many=True, read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=ChecklistTemplate.objects.all(), source='template', write_only=True, required=True
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='aluno'), source='student', write_only=True, required=False, allow_null=True, default=None
    )
    student_class_id = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all(), source='student_class', write_only=True, required=True
    )

    class Meta:
        model = ChecklistStatus
        fields = [
            'id',
            'template',
            'template_id',
            'template_version',
            'student',
            'student_id',
            'student_class',
            'student_class_id',
            'state',
            'student_notes',
            'percent_complete',
            'started_at',
            'submitted_at',
            'updated_at',
            'marks',
        ]
        read_only_fields = (
            'template',
            'template_version',
            'student',
            'student_class',
            'percent_complete',
            'started_at',
            'submitted_at',
            'updated_at',
            'marks',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context['request']
        user = request.user
        role = getattr(user, 'role', None)

        if request.method == 'POST':
            template: ChecklistTemplate = attrs['template']
            student_class: Class = attrs['student_class']
            student = attrs.get('student')

            if role == 'aluno':
                if student and student.id != user.id:
                    raise serializers.ValidationError('Aluno só pode iniciar listas para si próprio.')
                attrs['student'] = user
            elif role == 'professor':
                if not student:
                    raise serializers.ValidationError({'student_id': 'Obrigatório indicar aluno.'})
                if not student_class.teachers.filter(id=user.id).exists():
                    raise serializers.ValidationError('Professor só pode iniciar listas da sua turma.')
            elif not (user.is_superuser or role == 'admin'):
                raise serializers.ValidationError('Perfil sem permissão para criar listas de verificação.')

            if not template.classes.filter(id=student_class.id).exists():
                raise serializers.ValidationError('Template não está associado à turma selecionada.')

            if ChecklistStatus.objects.filter(
                template=template,
                student=attrs['student'],
                student_class=student_class,
            ).exists():
                raise serializers.ValidationError('Lista de verificação já iniciada para este aluno e template.')

        if request.method in {'PUT', 'PATCH'}:
            instance: ChecklistStatus = self.instance
            new_state = attrs.get('state')
            if new_state and new_state != instance.state:
                if new_state == ChecklistStatus.LVState.SUBMITTED and instance.state != ChecklistStatus.LVState.DRAFT:
                    raise serializers.ValidationError('Só é possível submeter uma LV em rascunho.')
                if user.role == 'aluno' and instance.student_id != user.id:
                    raise serializers.ValidationError('Aluno não pode alterar o estado de outra LV.')
                if user.role not in {'aluno', 'professor'} and not (user.is_superuser or role == 'admin'):
                    raise serializers.ValidationError('Perfil sem permissão para alterar estado.')

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        template: ChecklistTemplate = validated_data['template']
        student: User = validated_data['student']
        student_class: Class = validated_data['student_class']

        status = ChecklistStatus.objects.create(
            template=template,
            student=student,
            student_class=student_class,
            template_version=template.version,
            student_notes=validated_data.get('student_notes', ''),
        )
        status.initialise_marks()
        return status

    def update(self, instance: ChecklistStatus, validated_data):
        request = self.context['request']
        user = request.user

        new_state = validated_data.pop('state', None)
        student_notes = validated_data.pop('student_notes', None)
        notes_changed = False

        if student_notes is not None:
            instance.student_notes = student_notes
            notes_changed = True

        if new_state and new_state != instance.state:
            if new_state == ChecklistStatus.LVState.SUBMITTED:
                instance.submit()
            else:
                instance.state = new_state
                instance.save(update_fields=['state', 'updated_at'])
        elif notes_changed:
            instance.save(update_fields=['student_notes', 'updated_at'])

        return instance
