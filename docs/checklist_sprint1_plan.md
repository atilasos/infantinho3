# Sprint 1 — Checklists Digitais (MVP)

**Janela sugerida:** 2 semanas

**Meta:** Disponibilizar o ciclo básico de listas de verificação MEM em modo headless: modelos versionados, preenchimento pelo aluno com autosave, autoavaliação global, validação/feedback docente e permissões essenciais.

## Progresso atual

- ✅ CL1-01 — Editor de modelos headless (CRUD + itens aninhados, versionamento simples e associação a turmas).
- ✅ CL1-02 — Criação de instâncias pelo aluno com autosave de notas, submissão e atualização de objetivos via API/headless UI.
- ⚙️ Próximos: CL1-03/04 (autoavaliação global + feedback docente), CL1-05 (evidências/exportação) e CL1-06/07/08 (permissões, seeds, QA).

## Objetivos Sprint

1. Permitir que professores/admin criem e versionem modelos de LV com itens configuráveis (H1).
2. Garantir formulário de preenchimento para o aluno com estados por item e autosave (H2).
3. Suportar autoavaliação global e submissão (H3).
4. Possibilitar feedback e validação docente com registo de estados e comentários (H4).
5. Manter evidências ligadas a itens/ LV e exportação simples (H5).
6. Reforçar permissões de acordo com o novo fluxograma (H6).

## Backlog Sprint (proposta)

| Ordem | Item | Descrição | Estimativa |
|-------|------|-----------|------------|
| CL1-01 | Editor de modelos | CRUD de `ChecklistTemplate` + itens com versionamento simples | L |
| CL1-02 | API LV e autosave | Endpoints para instâncias de LV do aluno + autosave por item | L |
| CL1-03 | Autoavaliação & submissão | Campos globais, transição `draft → submitted` + validações | M |
| CL1-04 | Feedback docente | Workflow `submitted → validated/reparo`, comentários | M |
| CL1-05 | Evidências + exportação | Upload/link por item, exportação PDF mínima | M |
| CL1-06 | Permissões/logger | Policies por papel e logs principais | S |
| CL1-07 | Seeds/demo | Ajustar `demo_data` com LVs coerentes | S |
| CL1-08 | Testes & QA | Backend + frontend + acessibilidade básica | M |

## Sequência sugerida

1. **Dias 1-3:** CL1-01 (modelos + itens) → CL1-06 (permissões base).
2. **Dias 3-6:** CL1-02 (instâncias aluno + autosave) em paralelo com UI prévia.
3. **Dias 5-8:** CL1-03 e CL1-04 (autoavaliação + feedback docente).
4. **Dias 7-9:** CL1-05 (evidências + exportação) + seeds.
5. **Dia 10:** CL1-08 (tests/QA/documentação).

## Critérios de aceitação Sprint

- Professores/admin conseguem criar/editar modelos com itens de tipos distintos.
- Aluno visualiza e preenche LV em modo autosave, com controlo de obrigatórios.
- Submissão bloqueada sem itens obrigatórios → estados atualizam corretamente.
- Professor revê, comenta e devolve ou valida; estado visível no frontend.
- Evidências ligadas a itens e LV exportada em PDF dentro de 3s.
- Permissões: aluno apenas as suas LV; professor apenas turmas próprias; encarregado leitura; admin total.
- Seeds demo disponibilizam exemplos completos; testes unitários e E2E verdes.

## Riscos & Mitigação

- **Complexidade do editor**: começar com interface simples (lista) e evoluir para drag & drop em incrementos.
- **Uploads/evidências**: usar storage local (dev) com limite de tamanho; planear integração posterior.
- **Sincronização PIT**: por agora apenas link opcional (campo referencial), integração real fica para S2.
- **Exportação**: reutilizar infraestrutura de PDF do PIT (ReportLab) para ganhar tempo.

## Métricas de sucesso

- ≥ 80% das LV demo submetidas sem erros de validação.
- Tempo médio de preenchimento < 5 min (medido via autosave timestamps).
- Zero regressões nas permissões atuais.
