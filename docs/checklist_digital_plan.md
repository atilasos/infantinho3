# Backlog Listas de Verificação (LV) Digitais

## Épicos

* **LV1. Modelos e Critérios de LV**
* **LV2. Preenchimento pelo Aluno**
* **LV3. Autoavaliação e Coavaliação entre Pares**
* **LV4. Validação e Feedback do Professor**
* **LV5. Integração com PIT, Projetos e Mapas**
* **LV6. Relatórios, Exportações e Auditoria**
* **LV7. Acessibilidade, Mobile e Offline (PWA)**
* **LV8. Segurança, Permissões e Registos**

## Roadmap (MVP → Incrementos)

* **MVP (S1)**: modelos simples de LV por área/atividade, preenchimento básico pelo aluno, autoavaliação com escala e comentários, validação do professor, ligação a evidências, exportação PDF, permissões essenciais.
* **S2**: coavaliação entre pares, rubricas configuráveis, histórico por critério, integração com PIT e mapas, relatórios básicos.
* **S3**: recomendações automáticas de critérios, validação em lote, dashboards por turma, PWA offline e sincronização, auditoria avançada.

---

## Histórias por papel

### Ótica do Aluno

1. **Selecionar e iniciar uma LV a partir de um modelo**
   Como aluno, quero escolher a LV adequada à tarefa (ex.: comunicação, texto, ficha), para guiar o meu trabalho.
   **Critérios**

* Listagem de modelos com filtro por área/atividade.
* Ao iniciar, a LV herda dados do contexto (tarefa, projeto, data).
* Estado: rascunho → submetida.

2. **Preencher itens e marcar evidências**
   Como aluno, quero marcar cada item da LV e anexar evidências, para comprovar o cumprimento.
   **Critérios**

* Itens como check, escala 1–4, ou texto curto (conforme o modelo).
* Associação de evidências (ficheiro/link) por item ou LV.
* Validação de obrigatórios antes da submissão.

3. **Autoavaliação rápida**
   Como aluno, quero registar uma síntese de autoavaliação no final da LV, para refletir sobre qualidade e próximos passos.
   **Critérios**

* Escala global e comentário final.
* Sugestões pessoais para o próximo ciclo.

4. **Reutilizar uma LV anterior como ponto de partida**
   Como aluno, quero duplicar uma LV anterior, para acelerar preenchimento repetido.
   **Critérios**

* Duplicação só traz estrutura e itens, nunca feedback de terceiros.
* Evidências não são copiadas por defeito.

5. **Ver histórico e progresso por critério**
   Como aluno, quero ver evolução por critério ao longo do tempo, para orientar treino.
   **Critérios**

* Gráfico simples por critério/nível.
* Filtro por período e atividade.

---

### Ótica do Professor

6. **Criar e versionar modelos de LV**
   Como professor, quero definir modelos com itens, tipos de resposta e rubricas, para alinhar expectativas.
   **Critérios**

* Editor de itens (check, escala, texto) e agrupamentos.
* Versionamento datado, publicação por turma/ciclo.
* Pré-visualização em modo aluno.

7. **Validar LV submetidas e dar feedback**
   Como professor, quero rever as LVs dos alunos e dar feedback objetivo, para consolidar aprendizagem.
   **Critérios**

* Lista de LVs por turma/atividade com filtros.
* Comentários por item e gerais; estado Validada/Com reparos.
* Possibilidade de pedir revisão ao aluno.

8. **Coavaliação entre pares com moderação**
   Como professor, quero ativar coavaliação entre pares, para treino de critérios e qualidade.
   **Critérios**

* Atribuição automática/manual de pares.
* Anonimização opcional.
* Professor valida antes de fechar.

9. **Relatórios por critério e por turma**
   Como professor, quero ver distribuição de níveis por critério e turma, para planear intervenções.
   **Critérios**

* KPIs: % critérios cumpridos, média por escala, itens críticos.
* Exportação CSV e PDF.

10. **Integração com PIT e Mapas**
    Como professor, quero que o estado das LVs alimente o PIT e mapas, para regulação cooperada.
    **Critérios**

* LV ligada a tarefas do PIT/projetos.
* Mapas mostram cobertura de LVs por área.

---

## Automatismos desejáveis

* **Sugestões de critérios** com base no tipo de tarefa selecionado.
* **Validação em lote** de LVs iguais numa mesma atividade.
* **Alertas de lacunas**: itens obrigatórios não marcados antes da submissão.
* **Transporte de recomendações** para o próximo PIT quando a LV é de uma comunicação/projeto.
* **Deteção de incoerências**: autoavaliação muito alta com muitos itens não cumpridos.

---

## UI essencial

* **Catálogo de modelos** com busca e filtros.
* **Formulário de LV** de uma coluna, itens agrupados, progress bar e sumário de erros.
* **Painel do professor** com filas: Por validar, Com reparos, Validadas.
* **Relatórios simples** com tendência por critério.
* **Modal de anexar evidência** com preview.

---

## Modelo de dados mínimo

* `ModeloLV { id, nome, versao, area, atividade, itens[] }`
* `ItemModelo { id, enunciado, tipo: check|escala|texto, obrigatorio, rubrica? }`
* `LV { id, alunoId, turmaId, modeloId, versaoModelo, tarefaId?, projetoId?, estado, respostas[], autoavaliacao, evidencias[], createdAt, updatedAt }`
* `Resposta { itemId, valorBool?|valorEscala?|texto? }`
* `Feedback { autorId, alvo: LV|Item, mensagem, createdAt }`
* `Validacao { professorId, estado: validada|reparos, nota? }`

---

## Regras de negócio

* Uma LV só pode ser submetida com todos os **itens obrigatórios** respondidos.
* A **versão do modelo** usada fica congelada na LV.
* Coavaliação só conta após **moderação** do professor.
* Feedback do professor bloqueia alterações, exceto quando marcada como **Com reparos**.
* Cada LV liga-se a **uma tarefa** ou **uma comunicação** do PIT.

---

## Definition of Ready (DoR)

* Modelo definido, itens e tipos confirmados, fluxos de submissão e validação descritos, métricas escolhidas, UX esboçado.

## Definition of Done (DoD)

* Critérios de aceitação satisfeitos, testes unitários e E2E, WCAG 2.2 AA, logs e auditoria, exportações fiáveis, documentação curta.

## Métricas de sucesso

* % de tarefas com LV iniciada e submetida.
* Tempo médio de preenchimento por LV.
* Taxa de reparos vs validadas.
* Cobertura de evidências por LV.
* Atraso médio até feedback do professor.

---

# Plano de Passagem à Execução (MVP LV)

## 1) Planeamento incremental

### 1.1 Dependências

* **LV1** (Modelos) é base de **LV2–LV6**.
* **LV3** (Coavaliação) depende de **LV2** e **LV4**.
* **LV5** (Integração) depende de PIT e projetos disponíveis.
* **LV7** e **LV8** são transversais.

### 1.2 Critérios de priorização

Score = (Valor pedagógico + Impacto em métricas + Urgência) / Complexidade. Empate: escolher menor dependência externa.

### 1.3 Milestones do MVP (S1)

* **M1 Modelos de LV**: CRUD, versão, publicação.
* **M2 Preenchimento do aluno**: formulário e autosave.
* **M3 Autoavaliação e submissão**: escala global, comentário, validações.
* **M4 Feedback/Validação docente**: comentários, estados, pedido de revisão.
* **M5 Evidências e Exportação PDF**: anexos e render.
* **M6 Permissões essenciais**: aluno/professor; logs básicos.

---

## 2) Histórias S1 esmiuçadas

> Estrutura: **Dados**, **Fluxos**, **UI/UX**, **Critérios de aceitação**, **Métricas**, **Dependências**.

### H1 Criar e publicar modelo de LV (M1)

* **Dados**: `ModeloLV`, `ItemModelo`.
* **Fluxos**: criar → pré-visualizar → publicar → versionar.
* **UI/UX**: editor com arrastar-e-largar; tipos de item.
* **Critérios**: versionamento datado; impedir editar versão publicada; clonagem de modelo.
* **Métricas**: nº modelos ativos; tempo de criação.
* **Dependências**: permissões.

### H2 Iniciar LV a partir de modelo (M2)

* **Dados**: `LV`, ligação a `tarefaId/projetoId`.
* **Fluxos**: escolher modelo → iniciar LV → rascunho persistente.
* **UI/UX**: catálogo com filtros.
* **Critérios**: herda contexto; estado rascunho; autosave 10 s.
* **Métricas**: taxa de abandono; erros de criação.
* **Dependências**: H1.

### H3 Preencher itens e anexar evidências (M2, M5)

* **Dados**: `Resposta`, `Evidencia`.
* **Fluxos**: marcar itens → anexar ficheiro/link → validar.
* **UI/UX**: progress bar; sumário de erros; modal de evidência.
* **Critérios**: obrigatórios cumpridos; tipos de item respeitados; upload válido.
* **Métricas**: cobertura de evidências; falhas de upload.
* **Dependências**: H2.

### H4 Autoavaliação e submissão (M3)

* **Dados**: `autoavaliacao{ escala, comentario }`.
* **Fluxos**: preencher → submeter → bloquear edição.
* **UI/UX**: painel final; aviso de itens em falta.
* **Critérios**: impede submissão com obrigatórios por preencher; regista timestamp.
* **Métricas**: % submissões à primeira; tempo até submissão.
* **Dependências**: H3.

### H5 Feedback e validação docente (M4)

* **Dados**: `Feedback`, `Validacao`.
* **Fluxos**: professor comenta → marca estado → opcional "Com reparos" devolve ao aluno.
* **UI/UX**: fila por estado; editor de comentários por item.
* **Critérios**: notificação ao aluno; histórico imutável de feedback; auditoria.
* **Métricas**: SLA de feedback; taxa de reparos.
* **Dependências**: H4.

### H6 Exportação PDF (M5)

* **Dados**: LV completa e feedback.
* **Fluxos**: gerar → rever → descarregar.
* **UI/UX**: botão Exportar; opções de incluir evidências como anexos.
* **Critérios**: render A4 consistente; carimbo de versão do modelo.
* **Métricas**: tempo de geração; falhas.
* **Dependências**: H4/H5.

### H7 Permissões essenciais e logs (M6)

* **Dados**: `Utilizador{ papel }`, `AuditLog`.
* **Fluxos**: aluno cria/edita a sua LV; professor valida; logs de mudanças.
* **UI/UX**: mensagens de acesso negado claras.
* **Critérios**: testes de autorização; logs por operação.
* **Métricas**: incidentes; cobertura de testes.
* **Dependências**: infra/autenticação.

---

## 3) Execução

### 3.1 Board e workflow

* Colunas: Backlog → Pronto → Em curso → Code Review → Teste → Pronto p/ release → Feito.
* Etiquetas: `LV1..LV8`, `M1..M6`, `S1`, `frontend`, `backend`, `infra`, `UX`, `QA`.

### 3.2 Estimativa e capacidade

* T‑shirt: XS=1, S=2, M=3, L=5, XL=8.
* Capacidade exemplo: 2 dev × 2 semanas × 30h foco = 120h ≈ 30–40 SP.

### 3.3 Plano de Sprints (exemplo, 2 semanas)

* **Sprint 1**: H7 Permissões, H1 Modelos, H2 Iniciar LV. Meta: criar e iniciar LVs.
* **Sprint 2**: H3 Preenchimento+Evidências, H4 Submissão. Meta: LVs completas.
* **Sprint 3**: H5 Feedback/Validação, H6 PDF, hardening A11y e logs. Meta: ciclo fechado.

### 3.4 DoR específico

* Protótipo de UI, critérios fechados, dependências mapeadas, métricas definidas, dados e validações descritos, riscos listados.

### 3.5 Riscos e mitigação

* **Complexidade de modelos**: limitar tipos S1; avançados em S2.
* **Carga de feedback**: validação em lote no S2.
* **Privacidade**: minimizar dados pessoais nas evidências; controlos de partilha.
* **Acessibilidade**: testes com leitores de ecrã e navegação por teclado.
* **Sincronização**: fila offline e resolução de conflitos no S3.

### 3.6 Métricas operacionais (MVP)

* % tarefas com LV submetida.
* Tempo até feedback.
* % LVs com evidência anexada.
* Erros de validação por submissão.
* Latência média do PDF.
