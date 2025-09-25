# Plano de Alinhamento — PIT Digital

## Objetivo

Garantir que a app PIT atual evolui até cumprir o backlog strategicamente definido para o **PIT Digital**, entregando o MVP (S1) com base no roadmap, épicos e histórias apresentados.

## Âmbito

- Alunos: criação/gestão do PIT semanal, TEA básico, evidências, autoavaliação, histórico.
- Professores: modelo de PIT mínimo, conselho semanal, exportações, permissões.
- Transversal: auditoria, segurança, acessibilidade AA, métricas nucleares.

## Estrutura de Execução

### Waves do MVP (S1)

1. **Wave A — Fundação do PIT**
   - H1 Criar PIT semanal a partir de modelo.
   - H2 Editar áreas e tarefas do PIT.
   - H7 Exportação PDF (versão mínima).
   - H8 Permissões por papel e auditoria básica.
   - Base de dados alinhada com entidades: PIT, Tarefa, Área, Sugestão, Pendentes, Logs.

2. **Wave B — Autonomia do Aluno**
   - H3 Modo TEA com temporizador e mudança de tarefa.
   - H4 Evidências ligadas às tarefas.
   - H5 Autoavaliação diária com timeline e bloqueio de duplicados.

3. **Wave C — Consolidação e Conselho**
   - H6 Conselho semanal com transporte de sugestões.
   - H9 Histórico longitudinal básico.
   - Hardening: acessibilidade AA, exportação final revista, dashboards mínimos de métricas.

### Dependências-chave

- **E8 Modelo de PIT** implementado antes de Wave A.
- **E10 Segurança/Acessibilidade** aplicado continuamente (lint, testes, logs).
- **E9 Exportação** depende da consolidação dos dados em Waves A e C.

## Deliverables por Wave

| Wave | Entregáveis principais | Métricas foco |
| --- | --- | --- |
| A | Modelo e geração de PIT, edição de tarefas, PDF simples, permissões | % PIT criados até 3ª feira, erros de criação |
| B | Sessões TEA, evidências, autoavaliação diária | Tempo médio em TEA, cobertura de evidências, % autoavaliações |
| C | Conselho com transporte, histórico, revisão A11y | Taxa de execução de sugestões, latência histórico |

## Workflow de Projeto

- Board com colunas: *Backlog → Pronto → Em curso → Code Review → Testes → Pronto para release → Done*.
- Etiquetas: `E1…E10`, `Wave-A/B/C`, `frontend`, `backend`, `infra`, `UX`, `QA`.
- Definition of Ready específica: critérios fechados, diagrama de fluxo, requisitos de dados, métrica alvo, mock UX, dependências resolvidas.
- Definition of Done: testes unit/E2E, logs/auditoria, acessibilidade AA, documentação curta, métricas instrumentadas.

## Próximos Passos

1. **Diagnóstico** do estado atual da app PIT versus histórias H1…H9 (implementar/parcial/ausente + riscos).
2. Detalhar backlog da Wave A (ver `docs/pit_wave_a_backlog.md`) e estimar esforço.
3. Sprint 1 focado nos itens da Wave A.
4. Revisões quinzenais das métricas de sucesso: autoavaliações, tempo em TEA, transporte de pendentes, cobertura de evidências.

## Referências

- Backlog completo (épicos, roadmap, histórias) — `docs/backlog_pit_digital.md` *(este ficheiro pode ser criado/atualizado conforme necessário)*.
- Métricas de sucesso: `% alunos com autoavaliação diária`, `tempo médio TEA`, `taxa de transporte de pendentes`, `cobertura de evidências`, `eficácia de parcerias`.
