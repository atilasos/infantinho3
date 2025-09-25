# Sprint 1 — Wave A (PIT Digital MVP)

**Janela sugerida:** 2 semanas (10 dias úteis)

**Meta:** Entregar o núcleo funcional do PIT semanal: modelo versionado, geração/edição de plano com transporte inicial, exportação PDF mínima e permissões reforçadas.

## Objetivos Sprint

1. Disponibilizar endpoint + UI para criação do PIT semanal a partir do modelo (H1).
2. Permitir edição estruturada de tarefas/áreas com validações básicas (H2).
3. Gerar PDF simples do PIT (H7).
4. Garantir controlo de acesso e auditoria de alterações (H8).

## Backlog do Sprint

| Ordem | Item | Descrição | Estimativa (t-shirt) | Observações |
| --- | --- | --- | --- | --- |
| S1-01 | Refactor modelos PIT | Criar `PitTemplate`, ajustar `IndividualPlan`, migrar dados demo | L | Base para restantes tasks |
| S1-02 | Serviço geração PIT semanal | Endpoint `/pit/plans/generate`, transporte de sugestões/pendentes (stub se necessário) | L | Depende do S1-01 |
| S1-03 | UI criação wizarizada | Página Next com fluxo gerar→revisar→editar datas | L | Reutiliza endpoint S1-02 |
| S1-04 | Editor tarefas com validações | CRUD + reorder drag-and-drop + etiquetas simples | L | Requer componente DnD |
| S1-05 | Exportação PDF básica | Serviço backend + botão UI (somente campos principais) | M | Depende de dados S1-02/S1-04 |
| S1-06 | Permissões reforçadas + logs | Atualizar DRF permissions, middleware auditoria, testes | M | Transversal |
| S1-07 | Atualizações seeds/demo | Ajustar fixtures/templates para novas entidades | S | Em paralelo |
| S1-08 | Testes e QA | Unit + integration + E2E (Cypress/Playwright), checklist A11y base | M | Concluir sprint |

## Sequência sugerida

1. **Dia 1–3:** S1-01 (modelos/template) → S1-07 (seeds). Parear backend.
2. **Dia 3–5:** S1-02 (geração PIT) + iniciar S1-06 (permissões/logs).
3. **Dia 4–8:** S1-03 e S1-04 (frontend). Ajustes backend conforme necessário.
4. **Dia 6–9:** S1-05 (PDF) + finalizar S1-06.
5. **Dia 9–10:** S1-08 (testes completos, QA manual, revisão A11y, retro técnica).

## Critérios de Aceitação Sprint

- Ao clicar "Criar PIT" (aluno) o sistema gera plano com datas da semana, sugestões/pendentes e referencia versão do modelo.
- Aluno consegue editar tarefas por área, reorganizar, etiquetar disciplina e guardar (autosave ou guardar manual) com validações.
- Professor consegue abrir plano em modo leitura e ver transporte.
- Exportação PDF gera ficheiro A4 com capa, resumo e listas de tarefas/sugestões em <3s.
- Logs registam alterações de estado/tarefa com autor, timestamp, valores antigos/novos.
- Permissões: aluno só vê/edita os seus PIT; professor só vê turmas atribuídas; outros perfis bloqueados.
- Testes unitários e E2E passam; checklist A11y (contraste, labels, navegação teclado) sem regressões.

## Riscos & Mitigação

- **Complexidade modelo/templates**: alinhar cedo com equipa pedagógica. Produzir versão mínima (áreas + sugestões). Documentar limites.
- **Drag-and-drop**: avaliar lib DnD (ex.: `@dnd-kit`) vs. nativo. Se bloquear, fallback com botões up/down.
- **Geração PDF**: validar compatibilidade do runtime (WeasyPrint x wkhtmltopdf). Plan B: HTML-to-PDF via Puppeteer.
- **Integração Conselho**: se transporte não estiver pronto, criar stub e flag “pendente conselho” para Wave C.

## Checklist técnico

- [ ] Migração Django aplicada localmente com dados demo.
- [ ] Endpoint geração documentado (OpenAPI) e testado.
- [ ] Componentes React tipados (TypeScript) e lint ok.
- [ ] Testes: `pytest pit`, `npm run lint`, `npm run test` (frontend) e E2E básico.
- [ ] Métricas: log criar/editar/exportar PIT (para dashboards futuros).
- [ ] Documento de release sprint (resumo + instruções). 

