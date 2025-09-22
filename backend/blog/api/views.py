"""ViewSets exposing blog posts for the headless frontend."""
from django.db.models import Q
from rest_framework import permissions, viewsets, generics

from blog.models import Post
from core.permissions import IsAuthenticatedAndActive
from .serializers import PostSerializer, PublicPostSerializer


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedAndActive]
    queryset = Post.objects.select_related('autor', 'turma', 'approved_by').order_by('-publicado_em')
    filterset_fields = ['turma_id', 'status', 'categoria']
    search_fields = ['titulo', 'conteudo']

    def get_queryset(self):
        user = self.request.user
        base_qs = super().get_queryset()
        role = getattr(user, 'role', None)

        if user.is_superuser or role == 'admin':
            return base_qs

        if role == 'professor':
            return base_qs.filter(
                Q(turma__teachers=user) | Q(autor=user)
            ).distinct()

        if role == 'aluno':
            return base_qs.filter(
                Q(turma__students=user, removido=False, status='PUBLISHED') | Q(autor=user)
            ).distinct()

        # Guardians get access to published posts from their dependents' classes
        if role == 'encarregado':
            return base_qs.filter(
                removido=False,
                status='PUBLISHED',
                turma__students__encarregados_relations__encarregado=user,
            ).distinct()

        # Guests -> no access
        return base_qs.none()

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class PublicPostListAPIView(generics.ListAPIView):
    serializer_class = PublicPostSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            Post.objects.select_related('autor', 'turma')
            .filter(status='PUBLISHED', removido=False)
            .order_by('-publicado_em')
        )
