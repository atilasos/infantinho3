"""ViewSets for user management and onboarding flows."""
from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets, decorators, response, status

from core.permissions import IsAuthenticatedAndActive
from .serializers import UserSerializer, UserRoleUpdateSerializer

User = get_user_model()


class CurrentUserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):  # pragma: no cover - mapped to /me endpoint
        serializer = UserSerializer(request.user, context={'request': request})
        return response.Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedAndActive]
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action in {'partial_update', 'update'}:
            return [permissions.IsAdminUser()]
        if self.action in {'list', 'retrieve'}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @decorators.action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def promote(self, request, pk=None):
        user = self.get_object()
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get('role')
        status_value = serializer.validated_data.get('status') or 'ativo'
        if role:
            user.promote_to_role(role)
        user.status = status_value
        user.save(update_fields=['status'])
        return response.Response(UserSerializer(user, context={'request': request}).data)

    @decorators.action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return response.Response(status=status.HTTP_204_NO_CONTENT)
