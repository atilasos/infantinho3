from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext as _
import json

from .models import Conversation, Message, AIConfig
from .ai_service import ai_service
from classes.models import Class
from pit.models import IndividualPlan
from checklists.models import ChecklistStatus


def get_user_context(user, class_instance=None):
    """Build context dict for the AI based on user data."""
    context = {
        'student_name': user.get_full_name() or user.username,
    }
    
    if class_instance:
        context['class_name'] = class_instance.name
    
    # Get PIT summary if user is a student
    if hasattr(user, 'role') and user.role == 'aluno':
        pit = IndividualPlan.objects.filter(
            student=user
        ).order_by('-created_at').first()
        if pit:
            tasks_done = pit.tasks.filter(state='done').count()
            tasks_total = pit.tasks.count()
            context['pit_summary'] = f"{pit.period_label} - {tasks_done}/{tasks_total} tarefas concluídas"
        
        # Get checklist progress
        checklist_statuses = ChecklistStatus.objects.filter(student=user)
        if checklist_statuses.exists():
            total_items = 0
            completed_items = 0
            for status in checklist_statuses:
                total_items += status.marks.count()
                completed_items += status.marks.filter(mark_status__in=['COMPLETED', 'VALIDATED']).count()
            if total_items > 0:
                pct = int(completed_items / total_items * 100)
                context['checklist_progress'] = f"{completed_items}/{total_items} objetivos ({pct}%)"
    
    return context


def get_user_role(user):
    """Determine the AI role based on user role."""
    if hasattr(user, 'role'):
        if user.role in ['professor', 'admin']:
            return 'professor'
    return 'aluno'


@login_required
def chat_view(request, class_id=None):
    """Main chat interface view."""
    class_instance = None
    if class_id:
        class_instance = get_object_or_404(Class, id=class_id)
    
    # Check if AI is enabled
    if not AIConfig.is_enabled():
        return render(request, 'ai_assistant/disabled.html')
    
    # Get or create conversation
    conversation, created = Conversation.objects.get_or_create(
        user=request.user,
        class_instance=class_instance,
        defaults={}
    )
    
    # Get conversation history
    messages = conversation.messages.all().order_by('created_at')
    
    return render(request, 'ai_assistant/chat.html', {
        'conversation': conversation,
        'messages': messages,
        'class_instance': class_instance,
        'user_role': get_user_role(request.user),
    })


@login_required
@require_http_methods(["POST"])
def send_message(request):
    """Handle sending a message and getting AI response."""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)
        
        # Get conversation
        conversation = get_object_or_404(
            Conversation, 
            id=conversation_id, 
            user=request.user
        )
        
        # Save user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )
        
        # Build message history for AI
        history = []
        for msg in conversation.messages.all().order_by('created_at'):
            if msg.role in ['user', 'assistant']:
                history.append({
                    'role': msg.role,
                    'content': msg.content
                })
        
        # Get context and role
        context = get_user_context(request.user, conversation.class_instance)
        role = get_user_role(request.user)
        
        # Call AI service
        response = ai_service.chat(
            messages=history,
            role=role,
            context=context
        )
        
        # Save assistant response
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response['content'],
            tokens_used=response.get('tokens_used', 0)
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': assistant_msg.id,
                'role': 'assistant',
                'content': response['content'],
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def new_conversation(request, class_id=None):
    """Start a new conversation."""
    class_instance = None
    if class_id:
        class_instance = get_object_or_404(Class, id=class_id)
    
    # Create new conversation
    conversation = Conversation.objects.create(
        user=request.user,
        class_instance=class_instance
    )
    
    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id
    })
