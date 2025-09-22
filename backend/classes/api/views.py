"""API endpoints for managing classes/turmas."""
from django.contrib.auth import get_user_model
from rest_framework import permissions, status, decorators, response, viewsets

from classes.models import Class
from core.permissions import IsAuthenticatedAndActive
from .serializers import ClassSerializer, ClassMembershipUpdateSerializer

User = get_user_model()


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.prefetch_related('students', 'teachers').order_by('year', 'name')
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_permissions(self):
        if self.action in {'create', 'update', 'partial_update', 'destroy', 'assign_members'}:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @decorators.action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def assign_members(self, request, pk=None):
        turma = self.get_object()
        serializer = ClassMembershipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_ids = serializer.validated_data.get('student_ids', [])
        teacher_ids = serializer.validated_data.get('teacher_ids', [])

        if student_ids:
            students = User.objects.filter(id__in=student_ids, role='aluno', is_active=True)
            turma.students.set(students)
        if teacher_ids:
            teachers = User.objects.filter(id__in=teacher_ids, role='professor', is_active=True)
            turma.teachers.set(teachers)
        turma.save()
        return response.Response(ClassSerializer(turma, context={'request': request}).data, status=status.HTTP_200_OK)
