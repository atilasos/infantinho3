"""API endpoints for the class diary."""
from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from diary.models import DiaryEntry, DiarySession
from diary.utils import can_access_diary, can_moderate_diary
from classes.models import Class
from core.permissions import IsAuthenticatedAndActive
from .serializers import DiaryClassSerializer, DiaryEntrySerializer, DiarySessionSerializer


def _build_session_payload(turma: Class, session: DiarySession | None, request) -> dict:
    columns_payload = []
    if session:
        entries = session.entries.select_related('author').order_by('created_at')
        entries_map = {key: [] for key, _ in DiaryEntry.COLUMN_CHOICES}
        for entry in entries:
            entries_map.setdefault(entry.column, []).append(entry)
        for key, label in DiaryEntry.COLUMN_CHOICES:
            serialized = DiaryEntrySerializer(entries_map.get(key, []), many=True, context={'request': request})
            columns_payload.append({'key': key, 'label': label, 'entries': serialized.data})
    else:
        for key, label in DiaryEntry.COLUMN_CHOICES:
            columns_payload.append({'key': key, 'label': label, 'entries': []})

    payload = {
        'class': DiaryClassSerializer.from_instance(turma),
        'session': DiarySessionSerializer(session).data if session else None,
        'columns': columns_payload,
        'can_moderate': can_moderate_diary(request.user, turma),
        'can_add_entries': bool(
            session and session.status == 'ACTIVE' and can_access_diary(request.user, turma)
        ),
    }
    return payload


class ClassDiaryActiveAPIView(APIView):
    """Return the active diary session (if any) for a class."""

    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request, class_id: int, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)

        if not can_access_diary(request.user, turma):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        session = (
            DiarySession.objects.filter(turma=turma, status='ACTIVE')
            .prefetch_related('entries__author')
            .order_by('-start_date')
            .first()
        )

        payload = _build_session_payload(turma, session, request)
        return Response(payload)


class ClassDiarySessionDetailAPIView(APIView):
    """Return a specific diary session (active or archived)."""

    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request, class_id: int, session_id: int, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)

        if not can_access_diary(request.user, turma):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        session = get_object_or_404(
            DiarySession.objects.prefetch_related('entries__author'),
            id=session_id,
            turma=turma,
        )

        payload = _build_session_payload(turma, session, request)
        return Response(payload)


class ClassDiarySessionsListAPIView(APIView):
    """List all sessions for a class (teachers/admin only)."""

    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request, class_id: int, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)

        if not can_moderate_diary(request.user, turma):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        sessions = DiarySession.objects.filter(turma=turma).order_by('-start_date')
        serializer = DiarySessionSerializer(sessions, many=True)
        return Response(serializer.data)


class ClassDiaryEntryAPIView(APIView):
    """Create a diary entry for the active session."""

    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request, class_id: int, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)

        if not can_access_diary(request.user, turma):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        session = (
            DiarySession.objects.filter(turma=turma, status='ACTIVE')
            .order_by('-start_date')
            .first()
        )
        if not session:
            return Response({'detail': 'No active diary session.'}, status=status.HTTP_400_BAD_REQUEST)

        column = request.data.get('column')
        content = (request.data.get('content') or '').strip()

        valid_columns = {key for key, _ in DiaryEntry.COLUMN_CHOICES}
        if column not in valid_columns:
            return Response({'detail': 'Invalid column.'}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({'detail': 'Content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        entry = DiaryEntry.objects.create(
            session=session,
            column=column,
            content=content,
            author=request.user,
        )
        serializer = DiaryEntrySerializer(entry, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClassDiaryStartAPIView(APIView):
    """Archive the current session and start a new one."""

    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request, class_id: int, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)

        if not can_moderate_diary(request.user, turma):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        active_session = (
            DiarySession.objects.filter(turma=turma, status='ACTIVE')
            .order_by('-start_date')
            .first()
        )
        if active_session:
            active_session.status = 'ARCHIVED'
            active_session.end_date = timezone.localdate()
            active_session.save(update_fields=['status', 'end_date'])

        new_session = DiarySession.objects.create(
            turma=turma,
            status='ACTIVE',
            start_date=timezone.localdate(),
        )
        payload = _build_session_payload(turma, new_session, request)
        return Response(payload, status=status.HTTP_201_CREATED)
