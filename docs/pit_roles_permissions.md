# Perfis e permissões – PIT Digital (Wave A)

## Perfis suportados

| Perfil        | Descrição resumida                                      |
|---------------|----------------------------------------------------------|
| Admin         | Direção/coordenação; acesso completo a todos os dados.  |
| Professor     | Docente associado às turmas; gere PIT das suas turmas.  |
| Aluno         | Cria/edita o próprio PIT; acompanha feedback dos docs.  |
| Encarregado   | Responsável pelo aluno; acesso apenas em modo leitura.  |

## Operações principais (API / UI)

### Planos (`/api/pit/plans`)
- **Aluno**: criar, editar enquanto `draft/submitted`, submeter, autoavaliar, exportar PDF do próprio plano.
- **Professor**: listar planos das suas turmas, aprovar/devolver, avaliar, consultar histórico.
- **Encarregado**: leitura dos planos dos educandos; sem alterações.
- **Admin**: acesso total.

### Tarefas (`/api/pit/tasks`)
- **Aluno**: gerir tarefas do seu plano (CRUD, ordenação).
- **Professor**: pode atualizar tarefas do aluno da turma (feedback, validação); remove/ajusta quando necessário.
- **Encarregado**: não cria nem altera tarefas.
- **Admin**: acesso total.

## Fluxo de aprovação resumido
1. **Aluno** gera PIT semanal → estado `draft`.
2. Ajusta objetivos/tarefas; pode submeter → `submitted`.
3. **Professor** avalia:
   - Aprova → `approved` (plano em execução),
   - ou devolve → `draft` (aluno revê).
4. **Aluno** regista autoavaliação → `concluded`.
5. **Professor** deixa devolução final → `evaluated` (processo fechado).

## Auditoria
- Middleware `core.middleware.AuditLogMiddleware` regista mutações (POST/PUT/PATCH/DELETE) com utilizador, rota e payload.
- Eventos-chave do PIT (submissão, decisões, tarefas) geram `PlanLogEntry` associados ao plano.

## Seeds/demo
- `python backend/manage.py demo_data --reset` cria:
  - 1 admin, 1 professor, alunos por turma e respetivos encarregados.
  - PIT por aluno: versão ativa (estados distribuídos) e histórico avaliado, com tarefas predefinidas.
  - Projetos, checklists, diário e decisões de conselho coerentes com o novo modelo.

