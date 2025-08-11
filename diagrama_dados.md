# Diagrama Conceitual de Dados – Infantinho 3.0

> Este documento descreve as principais entidades e relações do sistema, servindo como referência viva para implementação e evolução do projeto.

---

## Organização das Entidades

### Entidades do MVP (implementadas)
- **User** (custom, com papéis e status)
- **Class** (turma)
- **Post**, **Comment**, **ModerationLog** (blog/diário e moderação)
- **ChecklistTemplate**, **ChecklistItem**, **ChecklistStatus**, **ChecklistMark** (listas de verificação)
- **DiarySession**, **DiaryEntry** (diário MEM por colunas)

### Entidades adicionais (já implementadas ou planeadas)
- Já implementadas: **GuardianRelation**, **PreApprovedStudent**, **IndividualPlan**, **PlanTask**, **Project**, **ProjectTask**, **CouncilDecision**, **StudentProposal**, **FeedbackItem** (infantinho_feedback)
- Planeadas: camada IA (`ai_service`) e integrações futuras

> **Nota:** O diagrama já inclui todas as entidades previstas para o projeto completo. Implemente no código apenas o necessário para cada fase, mas mantenha a arquitetura preparada para expansão.

---

## Sugestão de Organização de Apps Django

- `users/` — Gestão de utilizadores, perfis, papéis, relações de encarregado
- `classes/` — Gestão de turmas (Class)
- `blog/` — Blog/diário de turma (Post, Comment)
- `checklists/` — Listas de verificação (ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark)
- `pit/` — Planos Individuais de Trabalho (IndividualPlan, PlanTask)
- `projects/` — Projetos cooperativos (Project, ProjectTask)
- `council/` — Conselho de turma (CouncilDecision, StudentProposal)
- `ai_service/` — Integração com serviços de IA (futuro)

> **Dica:**
> - Cada app deve conter apenas os modelos, views e lógica relacionados ao seu domínio.
> - Use relações explícitas entre apps (ex: FK para User, Class) para manter o sistema modular.
> - Prefira nomes claros e consistentes para facilitar manutenção e onboarding de novos devs.

---

## Entidades Principais

```mermaid
erDiagram
    User {
        int id
        string username
        string email
        string role
        string status
        string photo
        datetime last_login
    }

    Class {
        int id
        string name
        int year
    }

    GuardianRelation {
        int id
        int aluno_id
        int encarregado_id
        string parentesco
    }

    PreApprovedStudent {
        int id
        string email
        int class_instance_id
        int added_by_id
        string status
        int claimed_by_id
        datetime date_added
        datetime date_claimed
    }

    Post {
        int id
        int turma_id
        int autor_id
        string titulo
        text conteudo
        string image
        string attachment
        datetime publicado_em
        string status
        int approved_by_id
        datetime approved_at
        string categoria
        bool removido
        int removido_por_id
        datetime removido_em
        string motivo_remocao
    }

    Comment {
        int id
        int post_id
        int autor_id
        text conteudo
        datetime publicado_em
        bool removido
        int removido_por_id
        datetime removido_em
        string motivo_remocao
    }

    ModerationLog {
        int id
        string acao
        int user_id
        int post_id
        int comment_id
        datetime data
        string motivo
        text conteudo_snapshot
    }

    DiarySession {
        int id
        int turma_id
        date start_date
        date end_date
        string status
        datetime created_at
        datetime updated_at
    }

    DiaryEntry {
        int id
        int session_id
        string column
        text content
        int author_id
        datetime created_at
    }

    ChecklistTemplate {
        int id
        string name
        text description
        datetime created_at
    }
    ChecklistItem {
        int id
        int template_id
        string code
        text text
        int order
    }
    ChecklistStatus {
        int id
        int template_id
        int student_id
        int student_class_id
        float percent_complete
        datetime updated_at
    }
    ChecklistMark {
        int id
        int status_record_id
        int item_id
        string mark_status
        int marked_by_id
        datetime marked_at
        bool teacher_validated
        text comment
    }

    IndividualPlan {
        int id
        int student_id
        int student_class_id
        string period_label
        date start_date
        date end_date
        string status
        text general_objectives
        text self_evaluation
        text teacher_evaluation
        datetime created_at
        datetime updated_at
    }
    PlanTask {
        int id
        int plan_id
        string description
        string subject
        string state
        string evidence_link
        text teacher_feedback
        int order
        datetime created_at
        datetime updated_at
    }

    Project {
        int id
        int student_class_id
        string title
        text description
        string state
        date start_date
        date end_date
        string product_description
        datetime created_at
        datetime updated_at
    }
    ProjectTask {
        int id
        int project_id
        string description
        int responsible_id
        date due_date
        string state
        int order
        datetime created_at
        datetime updated_at
    }

    CouncilDecision {
        int id
        int student_class_id
        date date
        text description
        string category
        string status
        int responsible_id
        datetime created_at
        datetime updated_at
    }
    StudentProposal {
        int id
        int student_class_id
        int author_id
        text text
        date date_submitted
        string status
    }

    FeedbackItem {
        int id
        int author_id
        string category
        text content
        string page_url
        int turma_id
        string status
        datetime created_at
        datetime updated_at
    }

    User ||--o{ Class : "students"
    User ||--o{ Class : "teachers"
    User ||--o{ GuardianRelation : "é encarregado de"
    Class ||--o{ Post : "posts"
    Class ||--o{ DiarySession : "diary"
    Class ||--o{ ChecklistStatus : "checklists"
    Class ||--o{ Project : "projects"
    Class ||--o{ CouncilDecision : "decisões"
    Class ||--o{ StudentProposal : "propostas"
    Class ||--o{ FeedbackItem : "feedback"
    Post ||--o{ Comment : "tem"
    Post ||--o{ ModerationLog : "log"
    Comment ||--o{ ModerationLog : "log"
    ChecklistTemplate ||--o{ ChecklistItem : "tem"
    ChecklistTemplate ||--o{ ChecklistStatus : "statuses"
    ChecklistStatus ||--o{ ChecklistMark : "marks"
    IndividualPlan ||--o{ PlanTask : "tarefas"
    Project ||--o{ ProjectTask : "tarefas"
    ```

---

## Notas
- Este diagrama reflete os modelos reais atuais no repositório (Django 5.2).
- Ajuste contínuo recomendado conforme evoluírem permissões, histórico e integrações.

> Atualize este documento sempre que houver mudanças relevantes nos modelos de dados. 