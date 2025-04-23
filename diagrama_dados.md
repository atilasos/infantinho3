# Diagrama Conceitual de Dados – Infantinho 3.0

> Este documento descreve as principais entidades e relações do sistema, servindo como referência viva para implementação e evolução do projeto.

---

## Organização das Entidades

### Entidades do MVP
- **User** (utilizador, com papéis)
- **Class** (turma)
- **Post** (blog/diário de turma)
- **Comment** (comentários nos posts)
- **ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark** (listas de verificação de aprendizagens)

### Entidades para Fases Futuras
- **GuardianRelation** (ligação encarregado-aluno)
- **IndividualPlan, PlanTask** (PIT – Plano Individual de Trabalho)
- **Project, ProjectTask** (Projetos cooperativos)
- **CouncilDecision, StudentProposal** (Conselho de turma e propostas)

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
        string name
        string email
        string password
        string role (Aluno/Professor/Admin/Encarregado)
        string photo
        datetime created_at
        datetime last_login
        string status (convidado, ativo, etc)
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
    
    User ||--o{ Class : "alunos"
    User ||--o{ Class : "professores"
    User ||--o{ GuardianRelation : "é encarregado de"
    Class ||--o{ User : "alunos"
    Class ||--o{ User : "professores"
    
    Post {
        int id
        int turma_id
        int autor_id
        string titulo
        text conteudo
        datetime publicado_em
        string categoria
    }
    
    Comment {
        int id
        int post_id
        int autor_id
        text conteudo
        datetime publicado_em
    }
    
    Post ||--o{ Comment : "tem"
    Class ||--o{ Post : "possui posts"
    User ||--o{ Post : "autor"
    User ||--o{ Comment : "autor"
    
    ChecklistTemplate {
        int id
        string nome
        int ano
    }
    ChecklistItem {
        int id
        int template_id
        string descricao
        int ordem
    }
    ChecklistStatus {
        int id
        int template_id
        int aluno_id
        float percent_complete
        datetime updated_at
    }
    ChecklistMark {
        int id
        int status_id
        int item_id
        bool concluido
        datetime data
        int marcado_por
    }
    ChecklistTemplate ||--o{ ChecklistItem : "tem"
    ChecklistTemplate ||--o{ ChecklistStatus : "status de"
    ChecklistStatus ||--o{ ChecklistMark : "marcações"
    ChecklistItem ||--o{ ChecklistMark : "é marcado em"
    User ||--o{ ChecklistStatus : "progresso"
    
    IndividualPlan {
        int id
        int aluno_id
        int turma_id
        string periodo
        string status
        text objetivos
        text autoavaliacao
        text avaliacao_prof
    }
    PlanTask {
        int id
        int plano_id
        string descricao
        string disciplina
        string estado
        text evidencias
        text avaliacao
    }
    IndividualPlan ||--o{ PlanTask : "tem tarefas"
    User ||--o{ IndividualPlan : "PITs"
    Class ||--o{ IndividualPlan : "PITs da turma"
    
    Project {
        int id
        int turma_id
        string titulo
        text descricao
        string estado
        datetime data_inicio
        datetime data_fim
        string produto_final
    }
    ProjectTask {
        int id
        int projeto_id
        string descricao
        int responsavel_id
        string estado
        datetime data_limite
    }
    Project ||--o{ ProjectTask : "tem tarefas"
    Project ||--o{ User : "integrantes"
    Class ||--o{ Project : "projetos"
    
    CouncilDecision {
        int id
        int turma_id
        datetime data
        text descricao
        string categoria
        string status
        int responsavel_id
    }
    StudentProposal {
        int id
        int turma_id
        int autor_id
        text texto
        datetime data_submissao
        string status
    }
    Class ||--o{ CouncilDecision : "decisões"
    Class ||--o{ StudentProposal : "propostas"
    User ||--o{ CouncilDecision : "responsável"
    User ||--o{ StudentProposal : "autor"
```

---

## Notas
- Este diagrama é um ponto de partida e pode ser ajustado conforme a implementação evoluir.
- Algumas relações podem ser refinadas (ex: papéis múltiplos, permissões, histórico de alterações).
- Campos podem ser expandidos para refletir requisitos específicos (ex: internacionalização, anexos, etc).

> Atualize este documento sempre que houver mudanças relevantes nos modelos de dados. 