"""Serializers for user-facing API endpoints."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_guest = serializers.SerializerMethodField()
    must_change_password = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'status',
            'must_change_password',
            'is_guest',
            'photo',
            'last_login',
            'date_joined',
        ]
        read_only_fields = ('username', 'email', 'status', 'last_login', 'date_joined')

    def get_is_guest(self, obj):
        return obj.is_guest()


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role', 'status']

    def validate(self, attrs):
        status = attrs.get('status')
        role = attrs.get('role')
        if status == 'convidado' and role:
            raise serializers.ValidationError('Guests cannot have an assigned role.')
        if role and role not in dict(User.ROLE_CHOICES):
            raise serializers.ValidationError('Invalid role.')
        return attrs


class GuardianRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, allow_blank=True)
    last_name = serializers.CharField(max_length=150, allow_blank=True)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    student_number = serializers.CharField(max_length=32)
    relationship = serializers.CharField(max_length=50, allow_blank=True, required=False)

    def validate_email(self, value: str) -> str:
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Já existe uma conta com este email.')
        return email

    def validate(self, attrs):
        password1 = attrs.get('password1')
        password2 = attrs.get('password2')
        if not password1 or not password2:
            raise serializers.ValidationError({'password1': 'Password obrigatória.'})
        if password1 != password2:
            raise serializers.ValidationError({'password2': 'As passwords não coincidem.'})

        from django.contrib.auth.password_validation import validate_password

        validate_password(password1)

        student_number = attrs.get('student_number')
        try:
            student = User.objects.get(student_number=student_number)
        except User.DoesNotExist as exc:  # pragma: no cover - handled below
            raise serializers.ValidationError({'student_number': 'Não encontrámos um aluno com esse número.'}) from exc

        if student.role != 'aluno':
            raise serializers.ValidationError({'student_number': 'O número indicado não pertence a um aluno ativo.'})

        attrs['student'] = student
        return attrs

    def create(self, validated_data):
        from users.models import GuardianRelation

        student = validated_data.pop('student')
        password = validated_data.pop('password1')
        validated_data.pop('password2', None)
        relationship = validated_data.pop('relationship', '')
        email = validated_data['email']

        guardian = User.objects.create_user(
            username=email,
            email=email,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=password,
            status='ativo',
        )
        guardian.must_change_password = False
        guardian.save(update_fields=['must_change_password'])
        try:
            guardian.promote_to_role('encarregado')
        except Exception:  # pragma: no cover - fallback when group missing
            guardian.role = 'encarregado'
            guardian.status = 'ativo'
            guardian.save(update_fields=['role', 'status'])

        GuardianRelation.objects.get_or_create(
            aluno=student,
            encarregado=guardian,
            defaults={'parentesco': relationship},
        )

        return guardian
