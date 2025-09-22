# Notificações Infantinho 3.0

As notificações do portal estão centralizadas no módulo `core.notifications.dispatch_notification`, garantindo que emails e integrações futuras (webhook) partilham a mesma lógica.

## Fluxos atuais

- **PIT**
  - Submissão do aluno → professores são avisados (`pit_submission`).
  - Decisão do professor → aluno recebe aprovação/devolução (`pit_student_status`).
  - Autoavaliação do aluno → professores notificados (`pit_self_evaluation`).
  - Avaliação do professor → aluno recebe feedback (`pit_teacher_evaluation`).
- Outros módulos podem reutilizar `dispatch_notification(...)` fornecendo `category` e `metadata` relevantes.

## Como funciona

```python
from core.notifications import dispatch_notification

dispatch_notification(
    subject='[Infantinho] Novo PIT',
    message='Detalhes da atualização...',
    recipients=['professor@escola.pt'],
    category='pit_submission',
    metadata={'plan_id': 12, 'class_id': 5},
)
```

- Emails são enviados via `DEFAULT_FROM_EMAIL`.
- Quando `NOTIFICATION_WEBHOOK_URL` for definido nas `settings`, será feito um POST JSON com o mesmo payload. Falhas no webhook são registadas mas não bloqueiam o fluxo.

## Próximos passos sugeridos

1. Enriquecer `metadata` com identificadores funcionais (UUIDs) para integração com CRM/Teams.
2. Armazenar histórico das notificações para auditoria.
3. Criar templates de email (HTML) por categoria.
