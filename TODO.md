# TODO – Roadmap de Desenvolvimento Infantinho 3.0

Este ficheiro serve como guia prático para o desenvolvimento incremental do portal, alinhado ao contexto pedagógico e técnico do projeto. As tarefas estão organizadas por fases, com entregas claras e pontos de validação.

---

## Fase 0 – Planeamento e Configuração Inicial
- [x] 0.1 Rever requisitos com stakeholders (direção, professores MEM)
- [x] 0.2 Configurar repositório Git
- [x] 0.3 Preparar ambiente de desenvolvimento (Python 3.x, Django, DB local)
- [x] 0.4 Configurar integração contínua (pipeline de testes automáticos)
- [x] 0.5 Modelar esquema inicial da base de dados (entidades principais)
- [x] 0.6 Esboçar wireframes das principais telas (opcional, mas recomendado)

## Fase 1 – Autenticação e Gestão Básica de Utilizadores/Turmas
- [x] 1.1 Implementar login/logout via SSO Microsoft (Azure AD)
- [ ] 1.2 Criar modelos User e Turma (incluindo grupos/papéis)
- [ ] 1.3 Views básicas: lista de turmas do professor, página de turma vazia
- [ ] 1.4 Painel admin mínimo para validar utilizadores e atribuir papéis
- [ ] 1.5 Testar fluxo: convidado → aluno/professor
- [ ] 1.6 Entrega parcial: professor pode criar turma, aluno pode ser adicionado

## Fase 2 – Módulo de Blog/Diário de Turma (MVP Parte 1)
- [ ] 2.1 Criar modelos Post e Comentário
- [ ] 2.2 Views: listar posts por turma, criar/editar/remover post (com permissões)
- [ ] 2.3 Integrar editor de texto rico (CKEditor ou similar)
- [ ] 2.4 Notificações simples (email ao criar post, se possível)
- [ ] 2.5 Testes: criação de post, permissões (aluno só na sua turma)
- [ ] 2.6 Validar blog funcional com professor e aluno reais

## Fase 3 – Módulo de Listas de Verificação (MVP Parte 2)
- [ ] 3.1 Implementar modelos Checklist, ChecklistItem, ChecklistStatus
- [ ] 3.2 Pré-carregar templates de 1-2 disciplinas para teste
- [ ] 3.3 UI Aluno: página para marcar objetivos
- [ ] 3.4 UI Professor: visão geral e validação de objetivos dos alunos
- [ ] 3.5 Testes: aluno marca, professor valida
- [ ] 3.6 Entrega: listas ativas por aluno, professor monitoriza

## Fase 4 – Feedback MVP e Ajustes
- [ ] 4.1 Apresentar MVP a professores MEM (validação de usabilidade)
- [ ] 4.2 Recolher feedback e iterar design se necessário
- [ ] 4.3 Corrigir bugs e ajustar funcionalidades essenciais

## Fase 5 – Módulo PIT (Planos Individuais de Trabalho)
- [ ] 5.1 Criar modelos PIT (IndividualPlan) e PlanTask
- [ ] 5.2 Views Aluno: criar/editar PIT, submeter
- [ ] 5.3 Views Professor: aprovar PIT, visualizar
- [ ] 5.4 Formulários de autoavaliação (aluno) e avaliação (professor)
- [ ] 5.5 Notificações básicas (submissão, aprovação, avaliação)
- [ ] 5.6 Garantir restrição: só um PIT por período
- [ ] 5.7 Testes de fluxo principal e casos de concorrência
- [ ] 5.8 Integração leve com checklists (botão para abrir checklist)

## Fase 6 – Módulo Projetos Cooperativos
- [ ] 6.1 Criar modelos Project e ProjectTask
- [ ] 6.2 Views: criar projeto (prof/aluno), adicionar membros, listar/detalhar projetos
- [ ] 6.3 Permissões: só membros editam
- [ ] 6.4 Testes: criar projeto, adicionar update

## Fase 7 – Módulo Conselho de Turma
- [ ] 7.1 Criar modelos CouncilDecision e StudentProposal
- [ ] 7.2 Views: propor pauta (aluno), listar propostas, aprovar/discutir (professor), registar decisão
- [ ] 7.3 Ligação opcional com Diário (parsear posts marcados como decisões)
- [ ] 7.4 Testes: propor, aprovar, listar decisão

## Fase 8 – Integração de IA (Protótipo)
- [ ] 8.1 Implementar `ai_service` para chamada à API (OpenAI GPT-3.5 ou similar)
- [ ] 8.2 Interface de chat (botão/modal para aluno e professor)
- [ ] 8.3 Prompts básicos: nome, papel, texto fixo do sistema
- [ ] 8.4 Testes manuais de perguntas simples

## Fase 9 – Aprimoramento dos Agentes de IA
- [ ] 9.1 Incorporar dados reais nos prompts (ex: resumo do PIT, status das listas)
- [ ] 9.2 Pipeline de meta-agente (se viável) ou guidelines no prompt
- [ ] 9.3 Gravar logs de Q&A, permitir admin ver logs
- [ ] 9.4 Testar Google API como alternativa (opcional)
- [ ] 9.5 Recolher feedback de utilizadores sobre IA
- [ ] 9.6 Documentar funcionamento e limites da IA

## Fase 10 – Internacionalização Completa
- [ ] 10.1 Extrair strings para ficheiro .po
- [ ] 10.2 Completar tradução PT-PT
- [ ] 10.3 Adicionar EN (ou outro) como teste (20% das strings)
- [ ] 10.4 Interface para troca de idioma (menu drop-down)
- [ ] 10.5 Testar páginas-chave em EN

## Fase 11 – Refinação, Testes Finais e Deploy Piloto
- [ ] 11.1 Teste de carga leve (simular 300 alunos)
- [ ] 11.2 Revisão de segurança (HTTPS, cookies, endpoints)
- [ ] 11.3 Depuração de bugs finais
- [ ] 11.4 Preparar scripts de deployment (Dockerfile/docker-compose ou guia)
- [ ] 11.5 Configurar servidor de produção (Ubuntu, Gunicorn, Nginx, PostgreSQL)
- [ ] 11.6 Preparar documentação e tutoriais para utilizadores
- [ ] 11.7 Realizar formação para professores
- [ ] 11.8 Deploy piloto para 1-2 turmas

## Fase 12 – Revisão Pós-Piloto e Expansão
- [ ] 12.1 Recolher feedback real de uso
- [ ] 12.2 Ajustar funcionalidades conforme feedback
- [ ] 12.3 Entrar em ciclo ágil de melhorias
- [ ] 12.4 Planejar funcionalidades extra (ex: integração com sistema de notas, gamificação)
- [ ] 12.5 Escalar para todas as turmas do colégio
- [ ] 12.6 Monitorizar desempenho e uso

---

**Notas:**
- Cada fase pode ser detalhada em subtarefas técnicas conforme necessário.
- Validar entregas com utilizadores reais sempre que possível.
- Manter o código limpo, sem duplicação, e respeitar ambientes (dev, test, prod).
- Scripts de povoamento e testes automáticos devem ser mantidos atualizados a cada módulo. 