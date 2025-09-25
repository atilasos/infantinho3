# Diagnóstico PIT Digital — Estado Atual vs. MVP (S1)

| # | História (S1) | Estado atual | Observações técnicas | Lacunas principais |
| --- | --- | --- | --- | --- |
| H1 | Criar PIT semanal a partir de modelo | **Parcial** | Existe criação/edição manual vía formulários (`backend/pit/views.py:73`, `forms.py:6`), mas não há modelo versionado nem transporte automático de sugestões/pendentes. O período é livre (`period_label`) e não há validação de datas. | ✅ criação básica<br>⚠️ falta versão de modelo, transporte automático, calendário semanal/guiado, logs de origem. |
| H2 | Editar áreas e tarefas do PIT | **Parcial** | CRUD de tarefas disponível (formset, API REST `PlanTaskViewSet`, `frontend/src/app/pit/page.tsx` lista em modo leitura). Contudo, estados limitados e sem UX de reorganização/etiquetas; não há tagging disciplinar consistente nem validações ricas. | ✅ edição simples + reorder manual via campo `order`<br>⚠️ sem drag & drop, sem etiquetas configuráveis, validações mínimas, UI apenas leitura. |
| H3 | Modo TEA com temporizador e mudança de tarefa | **Ausente** | Não existem modelos nem endpoints para sessões TEA. Nenhuma referência a temporizador, fila de dúvidas ou motivo de mudança. | ⚠️ Implementar `SessaoTEA`, UI temporizador, fila de dúvidas, integração com PIT. |
| H4 | Evidências ligadas às tarefas | **Parcial** | Cada tarefa aceita `evidence_link` único (`models.py:52`) e a UI expõe apenas um link. Não há upload de ficheiros, múltiplas evidências ou histórico de revisões. | ⚠️ Suporte a múltiplos anexos, storage segura, pré-visualização, controlo de versões. |
| H5 | Autoavaliação diária | **Ausente** | Apenas existe campo de autoavaliação final do plano (`self_evaluation`, `plan_self_evaluate`). Não há registo diário, bloqueio de duplicados ou timeline semanal. | ⚠️ Modelar `DailyReflection`, fluxo diário, síntese semanal, métricas. |
| H6 | Conselho semanal + transporte | **Parcial** | App `council` permite registar decisões/propostas (`backend/council/models.py`), mas não há integração com o PIT (sem transporte automático nem ligação às sugestões na criação do plano). PDF não implementado. | ⚠️ Ligar decisões/sugestões ao `IndividualPlan`, interface conselho → PIT, registo de execução. |
| H7 | Exportação PDF (PIT + ata) | **Ausente** | Não existem rotas ou helpers de geração PDF para PIT ou conselho (`rg 'PDF' backend/pit` vazio). | ⚠️ Implementar templates, serviço de exportação, download via frontend. |
| H8 | Permissões por papel & auditoria | **Parcial** | APIs filtram por `role` (`backend/pit/api/views.py:21`) e views usam `group_required`. Há notificações e logs simples, mas falta trilha de alterações (task history), auditoria central e testes de segurança. | ⚠️ Auditar alterações, registo de comentários, testes de autorização abrangentes, gestão de papéis coordenação/admin. |
| H9 | Histórico longitudinal de PIT | **Parcial** | Endpoint lista todos os planos e o frontend mostra histórico em cards (`frontend/src/app/pit/page.tsx`). Não há timeline, navegação por semana, filtros nem pesquisa. | ✅ listagem básica<br>⚠️ falta timeline/filtragem, indicadores, desempenho (<1s). |

## Síntese Geral

- **Cobertura aproximada do MVP**: ~40% (criação/edição + permissões básicas). Funcionalidades de autonomia, conselho e exportação permanecem por entregar.
- **Principais riscos**: inexistência de modelo versionado (impacta H1/H10), ausência de TEA/evidências/autoavaliação granular (afeta métricas chave), falta de exportação/integração com conselho (compromete comunicação semanal).
- **Recomendações imediatas**:
  1. Refatorar modelos para suportar transporte (sugestões/pendentes) e versionamento mínimo antes de avançar com UI.
  2. Planeamento técnico para TEA (nova entidade + timers no frontend) e para evidências (storage, limites, revisões).
  3. Definir estrutura de dados do conselho → PIT para desbloquear transporte e relatórios.
  4. Garantir auditoria/logs ao nível de tarefa/avaliação antes de publicar o MVP.

