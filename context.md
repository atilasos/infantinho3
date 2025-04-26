# Plano Detalhado de Desenvolvimento do Portal Educativo "Infantinho 3.0"

## Visão Geral do Projeto e Objetivos
O **Infantinho 3.0** será um portal educativo destinado ao **Colégio Infante Dom Henrique (pré-escolar até 9.º ano)**, alinhado com o **Modelo Pedagógico do Movimento da Escola Moderna (MEM)**. O principal objetivo é **facilitar a gestão cooperada da aprendizagem**, fornecendo versões digitais dos instrumentos pedagógicos do MEM, incluindo **listas de verificação de aprendizagens**, **Planos Individuais de Trabalho (PIT)**, **planos de projeto**, **diário de turma** e **registo de decisões do conselho de turma**. Além disso, o portal integrará **agentes de Inteligência Artificial (IA)** para apoiar a criação de conteúdos e orientar alunos e professores de forma contextualizada.

**Objetivos específicos e requisitos chave:**
- **Gestão de Turmas e Utilizadores:** Permitir a criação e gestão de turmas; gerir utilizadores com diferentes perfis (**alunos, professores, encarregados de educação (pais) e administradores**).
- **Ferramentas Cooperativas do MEM:** Disponibilizar versões digitais de instrumentos do MEM: listas de verificação do trabalho de aprendizagem, PIT, planos de projetos cooperativos, diário de turma e registo de decisões dos conselhos de cooperação educativa ([Modelo Pedagógico do MEM – Movimento da Escola Moderna](https://www.escolamoderna.pt/modelo-pedagogico/#:~:text=Esta%20avalia%C3%A7%C3%A3o%20assenta%20numa%20negocia%C3%A7%C3%A3o,em%20Conselho%20de%20Coopera%C3%A7%C3%A3o%20Educativa)).
- **Blog/Diário de Turma:** Implementar um blog para cada turma, estruturado por sessões (aulas ou semanas), que funcione como diário de turma para registo de atividades, reflexões e produções.
- **Participação Ativa dos Alunos:** Os alunos podem **criar posts no blog**, **propor e autoavaliar PITs**, **participar em projetos** e **interagir com agentes de IA** educativos.
- **Ferramentas do Professor:** Professores podem **criar turmas**, **gerir membros**, **avaliar/validar PITs** e **validar aprendizagens** (através das listas de verificação e outros instrumentos).
- **Agentes de IA Colaborativos:** Integrar agentes de IA (por ex., assistentes virtuais) que **comunicam entre si e aprendem com os dados guardados**, oferecendo apoio contextualizado a alunos e professores. A atuação da IA deve estar alinhada com os documentos pedagógicos orientadores (Perfil dos Alunos à Saída da Escolaridade Obrigatória, Aprendizagens Essenciais, Decretos-Lei n.º 54 e 55/2018 aplicados na Madeira, princípios da Educação Dehoniana e resultados do projeto de mestrado pré-existente).
- **Autenticação Federada:** Implementar autenticação através das contas **Microsoft escolares (Office 365/Azure AD)** da instituição. Todos os utilizadores que se registam inicialmente entram como **“convidados”** com acesso limitado.
- **Controlo de Acesso e Configurações:** Professores e administradores posteriormente atribuem os papéis adequados a cada utilizador (por exemplo, associar um convidado à sua turma como aluno, promover um professor, etc.). O administrador global pode configurar **domínios de email permitidos** para registo, selecionar o **modelo de IA** a utilizar (por exemplo, OpenAI GPT ou Google PaLM) e definir a **língua padrão** do portal.
- **Internacionalização:** A interface será desenvolvida em **Português Europeu**, mas com suporte pleno à internacionalização para fácil tradução para outras línguas no futuro.
- **Código e Qualidade:** O sistema será desenvolvido em **Python** (utilizando frameworks web adequados), com o código comentado em inglês para manter padrões internacionais. Serão incluídos **scripts de testes automáticos** para garantir qualidade e **scripts de povoamento de dados** fictícios para demonstrações e validação das funcionalidades.

**Escopo do MVP:** O **Produto Viável Mínimo (MVP)** irá conter as funcionalidades essenciais para uso inicial: **módulo de blog/diário de turma** e **listas de verificação de aprendizagens** (gestão básica de utilizadores/turmas incluída). As restantes funcionalidades (PIT, projetos, conselhos de turma, IA avançada, etc.) serão planeadas para fases subsequentes, mas já descritas neste plano para assegurar uma visão global do projeto.

---

## Arquitetura do Sistema e Tecnologias Propostas
**Visão Geral da Arquitetura:** O Infantinho 3.0 será uma aplicação **web** modular, acessível via navegador em computadores e dispositivos móveis. A arquitetura seguirá uma estrutura em camadas para separar preocupações:
- **Frontend (Interface do Utilizador):** Construído com HTML5, CSS3 e JavaScript. Poderá usar um framework front-end moderno (por exemplo, **React** ou **Vue.js**) para interfaces interativas, ou utilizar rendering do lado do servidor via framework Python web (e.g. templates Django) se preferido. A decisão dependerá da necessidade de interatividade em tempo real; para início, um sistema de templates server-side será mais simples, migrando para um front-end mais dinâmico conforme as funcionalidades de IA e colaboração em tempo real cresçam.
- **Backend (Lógica de Servidor):** Desenvolvido em **Python**, usando um framework web robusto como **Django** ou **FastAPI**. 
  - Se utilizar **Django**, aproveitamos o seu ORM para modelar os dados (SQLite ou PostgreSQL no desenvolvimento, PostgreSQL em produção), sistema de autenticação integrado (que pode ser adaptado para OAuth2 com Microsoft) e o seu suporte nativo a i18n.
  - Alternativamente, **FastAPI** oferece desempenho e facilidade para expor APIs (útil para integrações de IA ou um front-end SPA), porém exigiria integrar manualmente componentes como ORM (SQLAlchemy) e autenticação. 
  - *Decisão:* Optaremos inicialmente por **Django**, pela rapidez de desenvolvimento, módulo de administração embutido e ecosistema de plugins (por ex., integração fácil com **Microsoft OAuth2** via biblioteca social-auth-app-django). Poderemos expor APIs REST/GraphQL conforme necessário (por exemplo, para o front-end ou agentes de IA internos) usando Django REST Framework se aplicável.
- **Base de Dados:** Relacional, usando **PostgreSQL** (pela confiabilidade e suporte a tipos JSON para eventualmente guardar algumas estruturas flexíveis, como histórico de interações de IA). Os modelos de dados irão abranger Utilizadores, Turmas, Posts (Blog), Comentários (se aplicável), Planos (PIT), Tarefas do Plano, Projetos, Listas de Verificação, Itens da Lista, etc., conforme detalhado adiante.
- **Integração com Microsoft (SSO):** Utilizaremos OAuth2/OpenID Connect para autenticar via contas Microsoft. Por exemplo, no Django poderemos configurar a autenticação usando o Azure Active Directory:
  - Registrar a aplicação no Azure AD do colégio para obter **Client ID/Secret**.
  - Usar biblioteca como **python-social-auth** ou **MSAL (Microsoft Authentication Library)** para manejar o fluxo OAuth2. Ao autenticar, verificar o domínio de email do utilizador retornado (`@colegioinfante...`).
  - Se o domínio não corresponder a nenhum dos permitidos configurados pelo admin, negar acesso ou mantê-lo apenas como convidado não confirmado.
  - Uma vez autenticado, criar ou atualizar o utilizador na base de dados local com estado *convidado*, até que um professor/admin lhe atribua papel definitivo.
- **Interface de Administração:** O administrador terá um **painel de configuração** onde pode definir parâmetros globais:
  - Domínios de email permitidos (e.g. `@infantedomhenrique.edu.pt`).
  - Modelo de IA escolhido e respetivas credenciais de API (por exemplo, chave da API da OpenAI ou credenciais da Google AI).
  - Língua padrão (inicialmente PT-PT) e opções de internacionalização disponíveis.
  - Gestão global de utilizadores e turmas (possibilidade de criar/manipular qualquer turma ou conta, caso necessário).
- **Camada de IA:** Será modular para permitir troca do provedor. Iremos criar um componente de serviço (por exemplo, `ai_service.py`) que fornece métodos para interação com modelos **OpenAI GPT** ou **Google Vertex AI** (PaLM) de forma transparente. Este componente:
  - Lê a configuração atual (modelo selecionado).
  - Formata as **prompts** de entrada com contexto necessário (perfil do aluno, documentos base, etc.).
  - Envia a requisição à API apropriada (OpenAI ou Google) usando as credenciais configuradas.
  - Recebe e processa a resposta, retornando ao portal (ou a outros agentes).
  - Permite fácil substituição ou expansão (por exemplo, adicionar modelos open-source locais no futuro, garantindo privacidade dos dados).
- **Comunicação entre Componentes:** O sistema inicialmente funcionará de forma síncrona (requisições HTTP entre front-end e back-end). No futuro, para suporte a **comunicação entre agentes de IA** e possivelmente notificações em tempo real (ex: atualização de um PIT ao vivo), poderemos introduzir:
  - **WebSockets** (usando Django Channels ou FastAPI with websockets) para atualizações em tempo real.
  - Um **message broker** (ex: RabbitMQ ou Redis Pub/Sub) se quisermos arquitetar agentes de IA comunicando de forma assíncrona ou para fila de tarefas (por ex., geração de relatório pesado em background).
  - No MVP, isso não é estritamente necessário; as interações de IA podem ser feitas on-demand via chamadas REST simples.
- **Segurança e Privacidade:** Implementaremos controle de acesso rigoroso:
  - *Autorização:* Com base nos papéis, usando decorators ou middleware para restringir endpoints (ex: apenas professores da turma podem aprovar PITs, apenas alunos daquela turma podem postar no blog da turma, etc.).
  - *Validação de Dados:* Em todo input de utilizador (postagens, nomes, etc.) para prevenir injeções ou conteúdo indevido.
  - *Proteção de Dados:* Considerando que dados de alunos são sensíveis, garantir conformidade com **RGPD**. Dados enviados a serviços de IA externos serão anonimizados sempre que possível (ex.: não enviar nomes completos ou informações pessoais nos prompts).
  - *Backups e Logs:* Prever rotina de backup da base de dados e logs de auditoria de ações importantes (ex.: quem atribuiu determinado papel a um usuário, mudanças em notas ou avaliações).
- **Desempenho e Escalabilidade:** Inicialmente, uma única instância do aplicativo pode servir todo o colégio (escopo relativamente pequeno). No entanto, projetamos o sistema para possível uso mais amplo, então:
  - Otimizar consultas via ORM (índices em colunas de junção, uso cuidadoso de pré-busca/pre-fetching de dados relacionados).
  - Cachear conteúdo estático e possivelmente algumas queries frequentes (ex: checklist de aprendizagens que é igual para todos os alunos do mesmo ano).
  - Usar armazenamento de sessão adequado (cookies assinados ou tabela dedicada) para suportar múltiplos servidores se necessário.
  - Escalabilidade vertical (melhorar servidor) ou horizontal (multiplicar instâncias) fácil de conseguir dado uso de tecnologias standard (banco de dados separado, stateless app servers).
- **Internacionalização:** Desde o início, o código e interface serão preparados para i18n:
  - Textos apresentados ao utilizador envoltos em funções de tradução (`gettext` do Django, por exemplo).
  - Armazenar textos específicos (como títulos de posts) preferencialmente em formato Unicode e sem suposições de língua.
  - Separar **locale** PT-PT para tradução. O Português Europeu será o primeiro locale completo. Poderemos criar um locale EN-US para testar a troca de idioma.
- **Documentação e Comentários:** O código Python será comentado em inglês para clareza com a comunidade de desenvolvimento global. Exemplo:
  ```python
  # Model for Individual Work Plan (PIT)
  class IndividualPlan(models.Model):
      student = models.ForeignKey(User, on_delete=models.CASCADE)
      status = models.CharField(max_length=20, choices=PIT_STATUS_CHOICES, default='draft')  # e.g., draft, submitted, approved
      # ... other fields
  ```
  Os **manuais de utilizador** e documentação funcional serão em Português, focados nos educadores e alunos do colégio.

**Tabela Comparativa – Tecnologias/Componentes:**

| Componente               | Opção 1                        | Opção 2                 | Decisão no Projeto     |
|--------------------------|--------------------------------|-------------------------|------------------------|
| **Framework Backend**    | Django (bateria completa de ferramentas, ORM, admin, i18n integrados) | FastAPI + libs (mais leve, ótimo para APIs e micro-serviços) | **Django** (rápido desenvolvimento e consistência) |
| **Base de Dados**        | PostgreSQL (robusto, escalável) | MySQL/MariaDB (equivalente), SQLite (dev) | **PostgreSQL** (produção), SQLite (desenvolvimento simples) |
| **Auth Microsoft**       | python-social-auth, MSAL (Django integration) | Implementar OAuth2 manualmente | **Social-auth/MSAL** (menor esforço e testado) |
| **Frontend**             | Django Templates + JQuery (simples) | React/Vue SPA (mais interação) | **Django Templates** (no MVP; pode evoluir p/ SPA) |
| **IA (Modelo)**          | OpenAI GPT-4 (estado da arte, suporte amplo) | Google PaLM (Vertex AI) | **Configuração**: selecionável. *Default:* OpenAI GPT (maturidade em 2025) |
| **Comunicação em tempo real** | Django Channels (WebSocket) | Polling/Ajax simples | **Ajax/REST** (no início; avaliar WebSocket para chat IA no futuro) |

*Justificativa:* As escolhas acima equilibram **rapidez de implementação** e **flexibilidade futura**. Django fornece uma base sólida para cumprir os requisitos básicos (autenticação, models para blog/PIT, admin interface). Tecnologias adicionais (WebSockets, front-end SPA) serão introduzidas quando necessário, evitando complexidade desnecessária no MVP.

---

## Gestão de Utilizadores e Turmas (Autenticação e Autorização)
Esta seção detalha como será implementada a **estrutura de utilizadores**, **papéis** (roles) e **turmas (classes)** no portal.

### 3.1 Modelo de Utilizador e Perfis
- **Contas Unificadas:** Será utilizado um único modelo de utilizador (User) que abrange alunos, professores, encarregados de educação e administradores, distinguindo-os pelo **papel** atribuído. Podemos aproveitar o modelo de usuário padrão do Django (`AbstractUser`) estendendo-o para incluir campos específicos (por ex., papel atual, ou usar grupos/permissões).
- **Campos do Utilizador:** Nome, email (usado como username, associado à conta Microsoft), foto de perfil (poderemos obter via Microsoft Graph API se disponível), data de criação, último login, e estado/convite.
- **Estado "Convidado":** Todos os novos utilizadores autenticados via SSO Microsoft entram como *convidado* por padrão. Isto implica permissões mínimas (apenas visualizar conteúdo público ou solicitar acesso). O perfil exibirá uma marca "Convidado – acesso limitado".
- **Perfis de Aluno/Professor/Admin:** Em termos de implementação, utilizaremos provavelmente o sistema de **Groups/Permissions** do Django:
  - Criar grupos "Aluno", "Professor", "Administrador", "EncarregadoEdu".
  - Atribuir utilizadores a um destes grupos conforme seu papel. (Um professor também pode ter filhos no colégio – poderíamos permitir múltiplos papéis, mas para simplificar, se um utilizador for pai e professor, podemos ter duas contas separadas ou um modo de associação múltipla. Decisão: tratar *encarregado de educação* como um campo separado que liga um utilizador a um ou mais alunos, em vez de um grupo exclusivo.)
- **Ligação Encarregado de Educação:** Modelar uma relação, por exemplo:
  - Tabela `GuardianRelation` com campos: aluno (User), encarregado (User), parentesco (pai/mãe/tutor).
  - Isto permite que um encarregado possa ver informações dos seus educandos, sem precisar de um grupo separado com permissões globais de "parent". Em vez disso, definiremos regras de acesso: *se user X está listado como encarregado de Y, então pode ver determinados conteúdos de Y* (ex: posts do filho, listas de verificação do filho, feedback do professor relativo ao filho, etc.).

### 3.2 Criação e Gestão de Turmas
- **Modelo Turma (Class):** Incluirá campos como: nome da turma (ex: "5.ºA 2025"), ano escolar/ciclo (para referência), e professor(es) associados. Uma turma terá relação muitos-para-muitos com Utilizadores (alunos da turma). Exemplo simplificado em Django:
  ```python
  class Class(models.Model):
      name = models.CharField(max_length=50)  # ex: "5º A"
      year = models.IntegerField()  # ex: 2025 (ano letivo ou ano de escolaridade?)
      teachers = models.ManyToManyField(User, related_name="classes_taught")
      students = models.ManyToManyField(User, related_name="classes_attended")
  ```
  - Podemos incluir chave estrangeira para um **coordenador de turma** (professor principal) caso necessário, ou assumir que o primeiro professor associado é o responsável.
- **Administração de Turmas:** Os **professores** (e admin) podem criar novas turmas e adicionar/remover alunos. Funcionalidades específicas:
  - **Criar Turma:** Formulário para admin/professor definir nome da turma e selecionar professores responsáveis. Ao criar, gera-se um código de turma ou convite.
  - **Adicionar Alunos:** Duas formas:
    1. **Por convite/código:** O professor fornece um código de inscrição para a turma; quando um aluno convidado entra com esse código, ganha acesso à turma (o sistema atualiza seu papel de convidado para aluno dessa turma).
    2. **Atribuição direta:** No painel da turma, o professor ou admin busca pelo email/nome do aluno (dentre usuários convidados existentes ou cria novo placeholder) e adiciona-o. Isso dispara uma notificação para o aluno.
  - **Remover/Transferir Aluno:** Permitir que um professor remova um aluno da sua turma (por ex., em caso de engano ou mudança de turma). O registro do aluno não é apagado, apenas a associação. Poderá ser transferido para outra turma se necessário.
  - **Encarregados de Educação:** O professor ou admin pode também associar encarregados aos alunos da turma (caso o sistema não obtenha isso automaticamente de uma base de dados escolar externa).
- **Fluxo de Atribuição de Papéis:**
  1. O utilizador autentica-se com sucesso via Microsoft -> conta criada/atualizada como convidado.
  2. Um **administrador** revisa periodicamente a lista de convidados *sem turma*:
     - Se identificar um professor (pelo domínio de email ou manualmente), atribui-lhe papel de Professor (grupo correspondente). Esse utilizador passa a poder criar e gerenciar turmas.
     - Se identificar um aluno, pode **ou** atribuí-lo diretamente a uma turma (o que automaticamente muda seu papel para Aluno desse ano), **ou** deixar que o professor o adicione conforme o processo acima.
     - Para encarregados: se o email estiver na lista de permitidos e não pertence a alunos/professores (ex: pais têm outro domínio ou padrão identificável), o admin pode marcá-lo como Encarregado de Educação e ligar ao(s) seu(s) educando(s).
  3. Um **professor** que cria uma turma poderá convidar usuários convidados pelo email (o sistema envia email com link) ou aprovar solicitações de ingresso.
- **Permissões e Restrições:** Abaixo, uma tabela resumindo o que cada papel pode fazer no sistema (quando devidamente associado a uma turma):

| Ação / Funcionalidade              | Aluno (na turma) | Professor (da turma)    | Encarregado (do aluno) | Administrador | Convidado (não atribuído) |
|------------------------------------|------------------|-------------------------|------------------------|---------------|--------------------------|
| Autenticar (SSO Microsoft)         | ✔️ (cria conta convidado) | ✔️ (cria conta convidado) | ✔️ (convidado) | ✔️ (admin definido) | ✔️ (lim. acesso) |
| Aceder à turma (conteúdos)         | ✔️ (sua turma)   | ✔️ (todas sob sua resp)  | ✔️ (conteúdos do filho) | ✔️ (todas)    | ❌ (nenhuma turma)       |
| Criar post no blog da turma        | ✔️               | ✔️ (e editar de alunos) | ❌ (somente ler)        | ✔️ (qualquer turma) | ❌                      |
| Comentar posts (se habilitado)     | ✔️               | ✔️                      | ✔️ (feedback)           | ✔️            | ❌                      |
| Propor Plano Individual (PIT)      | ✔️ (próprio)     | ❌ (propõe para si?)     | ❌                     | ❌            | ❌                      |
| Avaliar/Autoavaliar PIT            | ✔️ (autoavaliar seu) | ✔️ (avaliar alunos)   | ❌                     | ✔️ (todos)    | ❌                      |
| Criar Plano de Projeto             | ✔️ (em grupo/próprio) | ✔️ (orientar projetos) | ❌                     | ✔️            | ❌                      |
| Atualizar Listas de Verificação (próprias) | ✔️ (sua lista, marcar itens) | ✔️ (dos alunos, validar itens) | ❌ | ✔️ (todos) | ❌ |
| Registar Decisão de Conselho       | ✔️ (se for secretário designado) | ✔️ (coordenar e validar) | ❌ | ✔️ | ❌ |
| Interagir com IA (assistente)      | ✔️ (tutor IA aluno) | ✔️ (assistente IA prof.) | ❌ (não aplicável) | ✔️ (ambos) | ❌ (talvez demo apenas) |
| Criar/gerir turmas                 | ❌               | ✔️ (suas turmas)        | ❌                     | ✔️ (todas)    | ❌                      |
| Gerir utilizadores (atribuir papéis) | ❌             | ❌ (pode convidar para sua turma) | ❌ | ✔️ (tudo) | ❌ |

*Legenda:* ✔️=Permitido, ❌=Negado. (Observação: Encarregado de educação tem **acesso em leitura** às produções do(s) seu(s) educando(s) e comunicados da turma, mas não interage ativamente na plataforma.)

- **Exemplo de Fluxo – Aluno entra na turma:** Maria entra com seu email escolar, vira convidada. O professor da turma 7.ºB adiciona o email de Maria à turma 7.ºB; Maria agora ao entrar no portal vê acesso à turma 7.ºB com papel de Aluna (pode criar posts, ver planos, etc.). O sistema notificou Maria e seu encarregado (se associado) da entrada na turma.
- **Exemplo de Fluxo – Professor novo:** João (professor) autentica-se. O admin nota o domínio do email de João (@infantedomhenrique.pt, por exemplo, indicando funcionário) e promove-o a Professor. João agora tem opção de criar turma. Ele cria a turma "3.ºC 2025" e convida alunos via código ou email. Os alunos aceitam o convite e são associados como Alunos de 3.ºC.
- **Gestão de Perfis:** Cada utilizador terá uma página de perfil básica (nome, papel, turmas associadas, eventualmente um campo bio ou interesses para uso futuro pela IA). Encarregados verão no seu perfil a lista de alunos sob sua tutela.

### 3.3 Autenticação via Microsoft e Fluxo de Login
- **Configuração OAuth:** O admin configura no portal os detalhes da app Microsoft (Tenant ID, Client ID, Client Secret, etc.). No código, definimos endpoints de callback para o OAuth2. O botão "Login com Microsoft" redireciona para a página Microsoft de login da organização.
- **Recebendo Resposta:** Após login, Microsoft retorna um token JWT com info do utilizador (nome, email). O backend valida o token (biblioteca MSAL cuida disso) e extrai o email e nome:
  - Verifica domínio do email contra a lista permitida:
    - Se o domínio não estiver permitido, ou seja externo (ex: gmail.com), pode recusar autenticação *ou* permitir acesso apenas a uma área restrita (por ex., talvez um encarregado com email externo – para isso, melhor limitar a domínios conhecidos de pais).
    - Se permitido, prossegue.
  - Busca o utilizador no DB local por email. Se existe, atualiza dados básicos; se não, cria utilizador com estado convidado.
- **Pós-Login:** Se o utilizador é novo (convidado):
  - Mostra-lhe uma tela de boas-vindas explicando que seu acesso é limitado até ser associado a uma turma ou papel. Eventualmente, se existir um **fluxo de auto-inscrição**, poderíamos perguntar "Você é aluno ou encarregado? Qual a sua turma ou filho?" para auxiliar o admin/professor. Mas inicialmente, manteremos a atribuição manual para controle.
- **Logout:** Invalidação de sessão local e redirecionamento (o logout do Azure AD geralmente não é forçado).

### 3.4 Configurações do Administrador
No painel de admin (que pode ser uma seção protegida ou simplesmente usar o **Django admin interface** para início):
- **Domínios e Permissões:** Campo para lista de domínios de email autorizados para alunos/professores (ex: `@infantedomh.edu.pt`) e possivelmente para encarregados (ex: permitir qualquer ou listar domínios comuns de provedores).
- **Modelos de IA:** Opção para selecionar provedor de IA:
  - *OpenAI:* requer chave API. Campos para inserir a API Key e escolher modelo (ex: GPT-3.5 vs GPT-4).
  - *Google:* requer credenciais (talvez um JSON de serviço ou API key), e identificação do modelo (ex: PaLM 2).
  - Poderá haver uma opção "Nenhum/Desativado" se o colégio preferir não ativar IA inicialmente.
- **Língua Padrão:** Selecionar PT-PT ou outra língua. (No MVP só PT estará totalmente traduzido, mas a estrutura permite adicionar EN, etc. Mudança aqui define o locale default para novos usuários, podendo cada utilizador ainda escolher individualmente no futuro.)
- **Outras Configurações:** Logótipo do colégio, cores (customização básica de tema), e toggles para funcionalidades (por ex: “ativar módulo de projetos” – se desativado, esconder menus referentes a projetos até estar implementado).

Com a gestão de utilizadores e turmas estabelecida, podemos avançar para os módulos pedagógicos específicos (blog/diário, listas, planos, etc.), que usarão essa infraestrutura de autenticação e autorização. 

---

## Módulo de Blog e Diário de Turma
Este módulo abrange a criação de um **blog por turma** que servirá, entre outras coisas, como **diário de bordo da turma**. Aqui, alunos e professores podem publicar posts relativos às sessões de aula, atividades, projetos ou qualquer conteúdo de partilha no contexto da turma.

### 4.1 Estrutura e Funcionalidades do Blog
- **Modelo de Dados (Post):** Criaremos um modelo `Post` com campos:
  - **turma** (chave estrangeira para Turma, indicando a que turma o post pertence),
  - **autor** (FK para Utilizador; poderá ser aluno ou professor da turma),
  - **título** (curto, opcional para diário de turma – poderíamos usar data ou tema da sessão como título),
  - **conteúdo** (texto rico, para relatos, reflexões, anexos),
  - **data/hora de publicação**,
  - **categoria/tipo** (poderemos categorizar posts, ex: "Diário de Turma", "Trabalho de Aluno", "Aviso", etc., para filtragem).
- **Criação de Posts:** 
  - **Professor:** Pode criar posts para resumo de cada sessão de aula ou recados. Ex: após uma aula, o professor publica um **Diário de Turma** relatando o que foi feito, dificuldades e sucessos, talvez escrito em colaboração com os alunos (no MEM muitas vezes um aluno secretário faz a ata do dia).
  - **Aluno:** Pode criar posts para compartilhar uma descoberta, resultado de um projeto, texto produzido ou reflexões. Pode também ser permitido usarem o blog para publicar **semanalmente um resumo do seu trabalho** (como parte da avaliação formativa).
  - O editor de texto será **rico (Rich Text)** para permitir formatação básica, listas, negrito, anexar imagens ou links. Podemos integrar uma biblioteca como CKEditor ou TipTap para campos ricos no Django.
- **Visibilidade:** Por padrão, os posts de turma são visíveis apenas para membros da turma (alunos, professores da turma, e encarregados dos alunos dessa turma). Admin pode ver todos. Poderemos no futuro ter *partilha pública* de certos posts (por exemplo, projetos concluídos que o colégio queira divulgar), mas por segurança de dados dos menores, inicialmente tudo fechado dentro do portal.
- **Listagem e Organização:** 
  - Na página principal da turma, haverá uma seção "Blog/Diário". Os posts serão listados em ordem cronológica inversa (mais recentes primeiro), agrupados por mês ou por semana para fácil navegação.
  - Pode-se filtrar por categoria (ex: ver só "Diário de Turma" ou só "Projetos").
  - Um calendário simples poderia destacar os dias com posts (indicando que naquele dia houve um diário escrito).
- **Comentários:** Implementaremos ou não comentários conforme necessidade:
  - Poderíamos permitir **comentários** nos posts (ex: colegas dando feedback no texto de um aluno, ou pais comentando em posts do professor). Isso incentiva interação, mas requer moderação.
  - No MVP, podemos incluir comentários apenas para membros internos (alunos/professores da turma) e não para encarregados (para evitar pressão sobre alunos). Ou permitir encarregados comentar mas com etiqueta.
  - Modelo `Comment`: FK para Post, autor (User), conteúdo, timestamp. Nesting de comentários não necessário (flat thread simples).
- **Notificações:** Quando um post é publicado:
  - Os membros da turma recebem notificação (isso pode ser um email automático e/ou notificação in-app). Usar email via SMTP O365 configurado pelo colégio.
  - O encarregado recebe notificação de posts marcados como "Diário de Turma" ou "Aviso".
  - Se comentários habilitados, notificar autor do post sobre novos comentários.
- **Exemplo de Uso (Diário de Turma):** A professora Joana, ao fim do dia, orienta os alunos a escreverem juntos um resumo. O aluno secretário escreve: *"Hoje discutimos o capítulo 3 de História, fizemos um debate sobre...".* Ele publica esse texto no blog da turma marcando como **Diário de Turma**. Todos os colegas e seus encarregados podem ler e ficar a par.
- **Exemplo de Uso (Post de Aluno):** O aluno Pedro concluiu um poema no seu PIT de Língua Portuguesa e decide publicá-lo no blog para compartilhar. Outros colegas podem ler e talvez comentar elogiando ou sugerindo melhorias (prática de partilha de produções do MEM).
- **Controle de Qualidade:** Para evitar abuso:
  - Professores podem **editar ou remover** posts inadequados. Os alunos têm liberdade, mas o professor atua como moderador final no blog da sua turma.
  - No caso de comentários, também permitir remover comentários.
  - Logs de moderação guardam quem removeu o quê, para transparência.
- **Implementação Técnica:** 
  - Criar views para **listar posts** (filtrando por turma e permissão) e **criar/editar post** (formulário).
  - Reutilizar o sistema de autenticação: assegurar via decorator que somente membros da turma acessam.
  - Integrar o editor de texto (por exemplo, Django CKEditor plugin) para o campo de conteúdo.
  - Salvar imagens eventualmente enviadas para ilustração no servidor (configurar media storage).
  - A URL do blog de uma turma pode ser `/turmas/<id_turma>/blog/` listando posts e `/turmas/<id_turma>/blog/post/<id>` para ver um post específico.
  - Para comentários, uma opção via AJAX para submeter sem recarregar a página seria conveniente (usando uma pequena view API para receber novo comentário).

### 4.2 Diário de Turma como Ferramenta Cooperativa
No contexto MEM, o **Diário de Turma** é importante para a reflexão coletiva. No Infantinho 3.0:
- Vamos criar uma **categoria** ou tag especial "Diário de Turma" para posts que correspondem a atas de reuniões de conselho ou resumos diários. Assim, podemos facilmente listar somente estes quando for necessário (ex: para avaliações, ou para rever a história da turma).
- O **formato** desses posts pode ser padronizado: por exemplo, ao criar um post de Diário, oferecer campos orientadores:
  - *Data:* (preenchido automaticamente, ou referindo-se à semana se for semanal)
  - *Presentes/Ausentes:* lista de alunos presentes (poderia ser preenchida automaticamente se integrarmos lista de presenças no futuro).
  - *Resumo das Atividades:* campo texto.
  - *Tarefas assumidas:* campo para listar o que ficou decidido (que também pode ser duplicado no módulo de conselho de turma, ver adiante).
- Apesar de termos esse formato, tecnicamente continua sendo armazenado em `Post.content` mas podemos gerá-lo via template.
- **Exemplo (Diário Postado):** No dia 10/10/2025, o Diário de Turma do 6.ºA tem:
  - *Atividades:* "Leitura coletiva do conto X; Resolução de problemas de matemática sobre frações em grupos; Apresentação do projeto de ciências do grupo B."
  - *Observações:* "Notou-se grande colaboração entre os alunos durante a atividade de matemática..."
  - *Decisões:* "Ficou decidido em Conselho de Turma que faremos uma visita de estudo ao museu no próximo mês."
  - Este conteúdo fica registrado num post categorizado como Diário de Turma e será referenciado também na seção de decisões (ver módulo de conselho abaixo).

Com o blog funcional, temos já um meio de comunicação e registro diário. O MVP prevê este módulo completo. A seguir, incorporaremos as **Listas de Verificação**, outra parte crucial do MVP.

---

## Módulo de Listas de Verificação de Aprendizagens
As **Listas de Verificação** no MEM são instrumentos onde alunos e professores registram o progresso nas aprendizagens, tipicamente por domínio curricular, monitorando o que foi **contratualizado em conselho** e o que já foi atingido ([Modelo Pedagógico do MEM – Movimento da Escola Moderna](https://www.escolamoderna.pt/modelo-pedagogico/#:~:text=Esta%20avalia%C3%A7%C3%A3o%20assenta%20numa%20negocia%C3%A7%C3%A3o,em%20Conselho%20de%20Coopera%C3%A7%C3%A3o%20Educativa)). No Infantinho 3.0, implementaremos listas de verificação digitais para cada aluno/turma, permitindo acompanhamento contínuo das metas de aprendizagem.

### 5.1 Estrutura das Listas de Verificação
- **Modelo de Dados:**
  - Teremos um modelo `ChecklistTemplate` que representa uma lista de verificação genérica (por exemplo, "Português 5.º ano", "Matemática 7.º ano"). Este contém:
    - Nome da lista (disciplina ou área),
    - Ano/nível aplicável (poderá ser por ano escolar ou ciclo),
    - Conjunto de **itens** (cada item é um objetivo ou conteúdo a dominar). Poderá ser um relacionamento para uma tabela `ChecklistItem` com texto do objetivo e uma ordem.
    - (Opcional: referência ao documento curricular de onde veio, ex: tag "AE" para Aprendizagens Essenciais).
  - Um modelo `ChecklistStatus` para o progresso de um **aluno específico** numa checklist:
    - Referência para o Template,
    - Referência para o Aluno (e possivelmente para a Turma/Ano),
    - Marcações de cada item: podemos armazenar um mapa de item->estado (ex: um JSON {item1: true, item2: false, ...}) ou criar uma tabela relacional `ChecklistMark` com (aluno, item, estado, data, quem marcou).
    - Campos de resumo: % completo, última atualização.
  - Desta forma, cada aluno terá uma instância de ChecklistStatus para cada lista (disciplina) relevante. Ex: um aluno do 5.º ano terá listas de verificação de Português, Matemática, Estudo do Meio, etc.
- **Populando os Itens:** Para não depender de input manual de todos os itens:
  - Iremos **pré-carregar** as *Aprendizagens Essenciais (AE)* de cada disciplina/ano como itens de checklist. Talvez usar um script de povoamento com esses dados oficiais (se disponíveis via CSV ou inseridos do projeto de mestrado). 
  - O administrador pode editar os templates ou criar novos. Por exemplo, incorporar itens específicos do colégio (ex: "Educação Dehoniana: Participa em ação solidária" poderia ser uma lista extra).
- **Visualização:** A interface para alunos e professores permitirá visualizar as listas:
  - Por disciplina: exibir todos os itens com um indicador (checkbox) marcado ou não.
  - Itens podem ter 3 estados: *Não iniciado*, *Em progresso/Parcial*, *Domínio/Concluído*. (No mínimo binário sim/não, mas poderemos ter um estado intermediário para indicar que já trabalhou aquilo mas não atingiu domínio completo).
  - Exibir data ou evidência da última marcação (ex: item "Sabe multiplicar frações" concluído em 12/Nov/2025).
- **Marcação e Validação:**
  - **Aluno:** pode marcar um item como concluído quando sente que o domina (autoavaliação). Isso é importante para a *auto-regulação da aprendizagem* no MEM.
  - **Professor:** vê as marcações dos alunos. Pode validar ou retificar. Por exemplo, se um aluno marcou algo mas nas evidências não demonstra domínio, o professor pode reverter a marcação ou adicionar um comentário de que precisa reforçar.
  - **Contrato em Conselho:** Idealmente, itens que foram definidos como objetivos no Conselho de Cooperação Educativa (reuniões de turma) teriam um destaque. Poderíamos implementar um campo booleano "contratualizado" em `ChecklistItem` ou no status individual para indicar que aquele item está no plano atual da turma. Por exemplo, no conselho do mês decidiram focar em 5 itens de Matemática – esses ficam marcados para todos os alunos como objetivos do período.
- **Interface de Gestão:**
  - Na página de cada aluno (visão do professor) ou na página da turma, o professor pode selecionar uma disciplina e ver **um quadro resumo de todos os alunos**:
    - Linhas = alunos, Colunas = itens principais (ou vice-versa), com checkmarks. Se muitos itens, talvez mostrar % ou barras de progresso por aluno e abrir detalhe por aluno.
    - Isso permite identificar quem já concluiu o quê e quem precisa de apoio, implementando a ideia de *mapas de registo coletivo* que complementam o PIT ([TEA.txt](file://file-4MLGD26XVHiNrZeJejhghH#:~:text=trabalho%20de%20produ%C3%A7%C3%A3o%20e%20de,%C2%AA%20s%C3%A9rie)).
  - O aluno, no seu painel pessoal, tem a seção "As minhas aprendizagens" com a lista de disciplinas. Clicando numa, vê os itens e marca/desmarca conforme a sua auto-perceção, adicionando opcionalmente uma nota ou evidência (ex: anexo de trabalho realizado) ao marcar concluído.
  - Poderemos permitir anexar evidências (um link para um post do blog, um ficheiro, etc., demonstrando aquela aprendizagem).
- **Notificações e Histórico:**
  - Quando um aluno marca um item, o professor recebe notificação (ex: "Joana afirma ter concluído objetivo X de Ciências").
  - O professor pode então validar: clicar em "validar" ou deixar comentário. Uma validação positiva poderia travar a marcação (ou seja, fica oficialmente concluído), enquanto uma negativa reabre o item.
  - Manter um histórico das mudanças de estado para fins de acompanhamento e reflexão com o aluno (ex: "Desmarcado pelo professor em 15/Nov, reforçar e voltar a tentar. Marcado novamente e validado em 30/Nov").
- **Exemplo de Uso:** 
  - O aluno Carlos, do 8.º ano, vai à sua lista de verificação de Matemática e vê o item "Sabe resolver sistemas de equações lineares". Após terminar um conjunto de exercícios no PIT e apresentar a resolução correta ao professor, Carlos marca esse item como **concluído**. O sistema registra e o professor Paulo vê a atualização, concorda e marca como **validado**.
  - Na reunião de conselho de turma, ao analisar o progresso, nota-se que Carlos ainda tem 2 itens críticos a trabalhar em Matemática (visualizado no quadro coletivo). Eles entram no acordo de focar naqueles itens no próximo PIT de Carlos.
- **Técnica de Implementação:**
  - Criar as tabelas `ChecklistTemplate`, `ChecklistItem`, `ChecklistStatus` conforme descrito.
  - Scripts de migração ou seed para popular as Aprendizagens Essenciais de cada ano/disciplina como templates e items. (Possivelmente, escrever um *script Python* para ler um ficheiro de texto/CSV fornecido com esses conteúdos).
  - Views:
    - **Aluno**: View que lista disciplinas -> itens. Ao submeter mudanças (checkbox tick/untick), uma request POST atualiza o status.
    - **Professor (turma)**: View que lista alunos vs % concluído por disciplina; clicando numa disciplina, lista itens vs alunos (pode ser em tabela ou em lista por aluno).
    - **Admin**: interface para criar/edit templates caso necessário.
  - Autorizações: aluno só pode alterar seu status, professor pode alterar status de seus alunos, admin tudo.
  - UI/UX: usar cores ou ícones para diferenciar estados (e.g. caixa vazia = não feito, meio preenchida = em progresso, check marcado = concluído; talvez usar três estados em vez de binário). 
  - Consideração: para MVP talvez usar binário simples (não feito/feito) e posteriormente introduzir estado intermédio se necessário.

Com as listas de verificação implementadas, teremos atendido uma peça central do MEM – monitoramento contínuo do currículo customizado por aluno. O MVP se completa com Blog + Listas. Nos próximos módulos, detalhamos funcionalidades a desenvolver após o MVP: **Planos Individuais de Trabalho (PIT)**, **Projetos** e **Conselhos de Turma**, além da integração de **IA**.

---

## Módulo de Planos Individuais de Trabalho (PIT)
Os **Planos Individuais de Trabalho (PIT)** são instrumentos semanais ou mensais onde cada aluno planeia as tarefas que vai realizar de forma autónoma, em alinhamento com os objetivos de aprendizagem definidos. O portal irá digitalizar o PIT, permitindo que alunos proponham seus planos, façam autoavaliação e que professores (e possivelmente colegas) os acompanhem e avaliem.

### 6.1 Estrutura do PIT e Ciclos de Trabalho
- **Modelo de Dados (PIT):** Criaremos um modelo `IndividualPlan` (PIT) com atributos:
  - **aluno** (FK para Utilizador),
  - **turma** (FK Turma, redundante mas útil para query rápida por turma),
  - **período**: uma identificação do ciclo de trabalho (por exemplo, semana ou mês e ano, ou um número sequencial de PIT). Podemos usar datas: campos `data_inicio` e `data_fim` do plano, ou simplesmente um rótulo textual ("Semana 5 - Out 2025").
  - **status**: estado do plano – *rascunho*, *submetido* (pelo aluno, para avaliação), *aprovado* (pelo professor), *concluído* (após execução), *avaliado* (feedback final dado).
  - **objetivos gerais**: campo texto para o aluno escrever o que pretende focar (ex: "Melhorar ortografia e concluir o livro X").
  - **autoavaliação geral**: campo texto para reflexão final do aluno após período.
  - **avaliação professor**: campo texto para feedback final do professor.
- **Modelo de Tarefas do PIT:** Um PIT consiste em várias tarefas/atividades planejadas. Teremos um modelo `PlanTask` com:
  - **plano** (FK para PIT),
  - **descrição** da tarefa (texto curto, e.g. "Ler capítulo 4 do livro Y e resumir"),
  - **disciplina/área** relacionada (opcional, escolha dentre disciplinas ou "Projeto"),
  - **estado**: *pendente*, *em andamento*, *feito* (marcado pelo aluno quando completa), *validado* (marcado pelo professor se verifica qualidade).
  - **evidências**: talvez um link ou referência (ex: se a tarefa gerar um documento ou post, indicar onde está).
  - **avaliação**: comentários específicos do professor sobre aquela tarefa (preenchido na avaliação final).
- **Relação com Listas de Verificação:** Poderemos ligar as tarefas aos itens de aprendizagem:
  - Por exemplo, ao adicionar uma tarefa, o aluno pode selecionar qual objetivo da lista de verificação ela atende (ex: tarefa "Exercícios de frações" liga-se ao item "Dominar frações"). Assim, quando marcada como feita e validada, o sistema pode sugerir marcar aquele item na checklist.
  - Modelar isso via um campo ManyToMany entre `PlanTask` e `ChecklistItem` (ou diretamente armazenar o item id).
- **Ciclo Temporal:** 
  - Para 1.º ciclo (1º ao 4º ano) costuma ser semanal, para 2º,3º ciclo (5º-9º ano) mensal ([TEA.txt](file://file-4MLGD26XVHiNrZeJejhghH#:~:text=constam%20tamb%C3%A9m%20todas%20as%20outras,de%20estudo%20aut%C3%B3nomo%2C%20atrav%C3%A9s%20de)). Podemos configurar a duração do PIT por turma. Por simplicidade, permitir que cada turma ou professor defina o período do ciclo (uma config na turma: `plan_duration = 'weekly' or 'monthly'`).
  - O sistema pode **gerar automaticamente um novo PIT vazio** para cada aluno no início de cada ciclo, como rascunho, para incentivá-lo a preencher. Ou o aluno clica "Novo PIT" e escolhe o período que deseja planear.
- **Fluxo de Utilização:**
  1. **Planeamento:** O aluno edita seu PIT (estado *rascunho*) adicionando tarefas. Pode salvar e continuar ao longo de um ou dois dias.
     - Pode consultar o **PIT anterior** (haverá acesso ao histórico de PITs) e ver as sugestões dadas pelo professor e colegas no final do último PIT, para guiar o novo.
     - O aluno finaliza preenchendo objetivos gerais para o ciclo.
     - Quando pronto, **submete** (status -> submetido).
  2. **Negociação/Aprovação:** O professor recebe notificação de que o aluno X submeteu seu plano.
     - O professor abre o PIT e revê. Pode adicionar comentários em tarefas específicas ou nos objetivos gerais.
     - Se algo não está alinhado (ex: o aluno esqueceu uma área importante), o professor pode **devolver para revisão** (status volta a rascunho com comentários do que ajustar) ou ele próprio editar pequenas coisas (caso a cultura da turma permita o professor co-construir).
     - Quando satisfeito, marca como **aprovado**. Poderíamos ter um campo para indicar se isso foi discutido em Conselho de Turma (talvez no diário).
  3. **Execução:** Durante o período, o aluno trabalha nas tarefas.
     - Ele pode marcar cada tarefa como *em andamento* ou *feita* conforme progride.
     - Pode adicionar **notas ou anexos** em cada tarefa (ex: upload de um ficheiro, ou link para um documento Google se preferirem externos).
     - O professor e até colegas podem acompanhar: por exemplo, um colega tutor pode ver o PIT do outro (se for cooperativo, mas isso talvez só se designado; em MEM alunos por vezes trabalham em pares no TEA).
     - Os agentes de **IA** também podem interagir aqui: por exemplo, se o aluno está com dificuldade, ele pode pedir ajuda ao assistente virtual, que consultando as tarefas sugere dicas (ver secção de IA).
  4. **Fecho e Avaliação:** Ao fim do ciclo, o aluno abre o PIT e escreve sua **autoavaliação**: reflete o que conseguiu, onde teve dificuldades, o que aprendeu de cada tarefa.
     - Marca o PIT como **concluído**. Isso notifica o professor.
     - O professor então avalia: vai tarefa por tarefa, verifica as evidências ou produtos (pode já ter acompanhado via blog ou anexos).
     - Insere **avaliação/progresso** em cada tarefa (ex: "bom trabalho", "rever conceitos", etc. opcional) e um **feedback global** no PIT.
     - Marca o PIT como **avaliado/encerrado**. Nesse momento, o sistema pode gerar um **resumo**: por exemplo, listar as tarefas concluídas e sugerir itens de verificação a marcar (o professor ou aluno podem diretamente abrir a checklist e marcar os itens relacionados).
     - Também prepara o terreno para o próximo ciclo: o professor pode escrever **sugestões para o próximo plano** (havia referência a um campo de sugestões no modelo de PIT físico ([TEA.txt](file://file-4MLGD26XVHiNrZeJejhghH#:~:text=da%20vida%20escolar%20de%20um,de%20estudo%20aut%C3%B3nomo%2C%20atrav%C3%A9s%20de))). Podemos implementar isso como parte do feedback do professor – ex: últimas linhas "Sugestões para próximo PIT: ...". O sistema pode carregar essas sugestões na interface de criação do próximo PIT como lembrete.
  5. **Revisão Cooperativa:** Em Conselho de Turma ou momentos de partilha, podem comparar PITs:
     - O portal pode permitir visualizar lado a lado (ou em lista) alguns *indicadores agregados* dos PITs: quantas tarefas planeadas vs concluídas por aluno, quais tipos de tarefas foram mais escolhidas (ex: leitura, escrita, matemática...), etc., para discussão coletiva.
     - Isso incentivará responsabilização e ajuda entre pares (por ex: se um aluno realizou muitas tarefas, e outro menos, discutir estratégias).

- **Interface:**
  - **Aluno:** Uma página "Meu Plano Atual" com formulário para editar (lista de tarefas e campos de texto). Interface amigável, talvez permitindo arrastar para reordenar tarefas em prioridade.
  - **Professor:** Uma página listando todos os alunos da turma e o estado de seus planos (ex: tabela: Aluno X - submetido, Aluno Y - em execução, Aluno Z - pendente...). O professor pode clicar em cada para ver detalhes e aprovar/avaliar. Poderia ter um recurso de **filtro por estado** para facilitar (ver todos que já submeteram, etc.).
  - Possibilidade de **imprimir/exportar** um PIT preenchido (em PDF) para registro físico ou assinatura, caso necessário.
- **Notificações:** 
  - Quando o aluno submete -> professor notificado.
  - Quando professor aprova -> aluno notificado (via portal ou email: "Seu PIT foi aprovado, boa sorte nas tarefas!").
  - Quando prazo do ciclo está acabando e aluno não concluiu -> enviar lembrete ao aluno.
  - Quando professor avalia e fecha -> aluno recebe feedback disponível.
- **Exemplo de Uso Resumido:**
  - Ana (aluna do 6.º ano) planeia 4 tarefas no seu PIT da semana: 1) Ler um capítulo de Geografia, 2) Fazer exercícios de matemática, 3) Escrever uma redação, 4) Terminar um desenho para projeto de artes. Ela submete. O professor revê e aprova, sugerindo que ela peça ajuda a um colega na tarefa 2. Ana executa durante a semana, marca como feitas as que termina. No fim, escreve que conseguiu tudo menos os exercícios completamente. O professor avalia: elogia a leitura e redação, indica erros nos exercícios a rever e sugere focar mais matemática no próximo PIT. Ana e professor validam juntos alguns itens nas listas de verificação de Geografia (relativo ao capítulo lido) e de Português (redação).
- **Técnica de Implementação:**
  - Criar modelos `IndividualPlan` e `PlanTask` conforme descrito, migrar BD.
  - Views e templates:
    - **Aluno**: view para criar/editar (rascunho) e submeter, view para visualizar (read-only) um PIT aprovado ou avaliado.
    - **Professor**: view para lista geral (overview de estados), view para aprovar (que mostra form de leitura com botão aprovar/devolver), view para avaliar (form com campos de feedback).
    - **Permissões:** aluno pode ver apenas seus PITs; professor apenas da sua turma; admin todos.
  - Utilizar formulários dinâmicos (Formsets no Django) para adicionar múltiplas tarefas de uma vez de forma intuitiva.
  - Integrar com **Listas de Verificação**: por exemplo, ao marcar tarefa como concluída, oferecer botão "Atualizar aprendizagem" que leva diretamente ao item relacionado na checklist.
  - **Validações:** 
    - Evitar duplicação: um aluno só deve ter um PIT por período por turma; se tentar criar outro no mesmo período, impedir.
    - Garantir data atual dentro do período para permitir marcações (após fim do período, impedir editar exceto avaliação).
    - Campos obrigatórios: pelo menos X tarefas ou objetivos definidos? (No MEM espera-se sempre ter plano preenchido, mas não forçaremos número mínimo exceto se desejado).
  - **Dados Fictícios para Teste:** Prever no script de povoamento a criação de alguns PITs exemplo para alunos, para testar fluxos (um já avaliado, um em curso, etc.).

Com o módulo PIT, o portal apoiará a **diferenciação pedagógica individual** e o acompanhamento contínuo, peças fundamentais do MEM ([TEA.txt](file://file-4MLGD26XVHiNrZeJejhghH#:~:text=constam%20tamb%C3%A9m%20todas%20as%20outras,de%20estudo%20aut%C3%B3nomo%2C%20atrav%C3%A9s%20de)) ([TEA.txt](file://file-4MLGD26XVHiNrZeJejhghH#:~:text=trabalho%20de%20produ%C3%A7%C3%A3o%20e%20de,%C2%AA%20s%C3%A9rie)). A seguir, expandiremos para projetos cooperativos e o conselho de turma.

---

## Módulo de Projetos Cooperativos (Planos de Projeto)
No MEM, além do trabalho individual, promove-se o **trabalho de projeto cooperativo** sobre temas de estudo, produção artística, pesquisa científica ou intervenção social ([Modelo Pedagógico do MEM – Movimento da Escola Moderna](https://www.escolamoderna.pt/modelo-pedagogico/#:~:text=Trabalho%20de%20aprendizagem%20curricular%20por,projetos%20cooperativos)). O Infantinho 3.0 incluirá um módulo para **planos de projeto em grupo**, permitindo que alunos organizem projetos coletivos com orientação do professor.

### 7.1 Estrutura e Funcionalidades dos Projetos
- **Modelo de Dados (Projeto):** Criar um modelo `Project` com:
  - **turma** (FK Turma),
  - **título do projeto**,
  - **descrição/tema** (objetivos do projeto, pergunta de partida, etc.),
  - **integrantes** (ManyToMany para Utilizadores, referenciando os alunos participantes; um professor orientador pode ser inferido como o professor da turma ou campo separado se necessário),
  - **estado**: *ativo/em andamento*, *concluído*, *cancelado*.
  - **data início** e **data fim (prevista)**.
  - **produto final previsto** (ex: "maquete", "relatório", "apresentação", etc.).
- **Plano de Trabalho do Projeto:** Semelhante ao PIT, um projeto pode ter tarefas e fases. Podemos reutilizar o modelo `PlanTask` ou criar um específico `ProjectTask`:
  - Tarefa com descrição, responsável (um dos alunos do grupo ou "todos"), data limite, estado.
  - Alternativamente, integrar com uma ferramenta de gestão tipo "Kanban" simples: colunas *Por fazer*, *Em progresso*, *Feito* e cartões para tarefas (mas isso pode ser complexidade extra; inicialmente, listas simples de tarefas bastam).
- **Repositório de Materiais:** Permitir que o grupo anexe arquivos ou links relevantes (ex: pesquisas, rascunhos). Poderia ser um simples campo de comentários ou uma integração com Google Drive/OneDrive via link.
- **Blog/Registo de Projeto:** Poderíamos usar o blog existente mas filtrar por projeto. Em vez disso, mais simples:
  - Cada projeto pode ter um **mini-blog ou log**: os membros podem registrar progresso, dificuldades, e o professor pode acompanhar. Isso pode ser realizado ou reutilizando o modelo Post com um campo de ligação a projeto, ou criar um `ProjectUpdate` similar a post.
  - Assim, no espaço do projeto veriam uma timeline de atualizações.
- **Visibilidade:** Por padrão, um projeto é visível apenas para os membros do projeto e professores. No final, quando concluído, pode-se apresentar para a turma inteira ou público – poderemos permitir marcar um projeto como "compartilhado publicamente" para a turma/ver no blog geral.
- **Fluxo de Utilização:**
  1. **Criação do Projeto:** Pode ser iniciado por alunos (com aprovação do professor) ou pelo professor designando um grupo. Um aluno ou grupo de alunos submete uma ideia de projeto (título e descrição). O professor aprova e eventualmente complementa orientações.
  2. **Planeamento:** Uma vez aprovado, os alunos detalham o plano: dividem tarefas, pesquisam referências (que podem subir na plataforma), definem cronograma. O professor revê e aconselha (pode comentar nas tarefas ou descrição).
  3. **Execução:** Os alunos trabalham no projeto ao longo de várias sessões. Usam a seção de updates para relatar avanços. Podem marcar tarefas como concluídas. Reúnem evidências (fotos de trabalho em progresso, textos, dados coletados).
  4. **Conselho de Cooperação:** Os projetos podem ser acompanhados também nos conselhos de turma. Ex: a turma discute o andamento dos projetos, alunos de outros grupos podem ajudar com ideias. Podem registrar no diário decisões relacionadas (como reconfigurar um grupo ou tema).
  5. **Conclusão:** Quando o projeto termina, os alunos publicam o **produto final** (por ex, um relatório em PDF, um vídeo, etc.), possivelmente no blog da turma para todos verem. O professor avalia o projeto (pode escrever um feedback ou preencher rubric se houver).
  6. **Autoavaliação de Projeto:** Os membros do grupo podem também escrever uma autoavaliação conjunta do projeto, ou individual sobre o trabalho em equipe (essa funcionalidade pode ser incorporada via comentários ou campos finais).
- **Interface:**
  - **Página da Turma – Projetos:** Lista de todos os projetos ativos e concluídos na turma. Mostrar título, alunos do grupo, status e um progresso (ex: % tarefas concluídas).
  - **Página do Projeto:** Mostra detalhes (descrição, membros), lista de tarefas (com opção de marcar feitas, adicionar novas se permitido, etc.), e a timeline de atualizações com data.
  - **Formulário:** Para criar projeto (disponível para professor e talvez para aluno com permissão). Para editar detalhes (provavelmente apenas professor ou com aprovação se alunos editarem).
  - **Notificações:** Quando um aluno cria ou pede um projeto, notificar professor; quando professor aprova, notificar membros; quando um membro adiciona update ou completa tarefa, notificar outros membros; etc.
- **Exemplo de Uso:** 
  - Grupo do 9.ºA quer fazer um projeto de ciências sobre energias renováveis. Eles criam no portal um projeto "Energias Renováveis no Dia-a-Dia" descrevendo que vão investigar como aproveitar energia solar na escola. O professor aprova. Eles listam tarefas: "Pesquisa bibliográfica", "Entrevistar técnico", "Construir protótipo de painel solar", cada uma atribuída a diferentes membros. Durante as semanas seguintes, eles registram no projeto as notas das reuniões do grupo, resultados intermediários (fotos do protótipo). No final, sobem um relatório PDF e um vídeo demonstrativo. O professor avalia e marca o projeto como concluído, publicando o post final no blog da turma para toda a comunidade escolar ler sobre o projeto.
- **Implementação Técnica:**
  - Models: `Project`, `ProjectTask` (ou reuso de PlanTask com um FK genérico que pode apontar a Project ou PIT, mas isso pode complicar, talvez manter separado por clareza).
  - Views:
    - List projects (require login + membership in that class).
    - Detail project (with subcomponents: tasks and updates).
    - Create/edit project (permissions: teacher or students with approval).
  - Possibly reuse parts of PIT interface for tasks.
  - Use of AJAX to update tasks quickly (mark done).
  - Link with other modules: A project could also link to items da checklist (ex: um projeto de escrita longa pode cobrir vários objetivos de Português; mas talvez não tão necessário, pois checklists são mais individuais).
  - Ensure performance: tasks per project is small scale, nothing heavy.

O módulo de projetos promove a **aprendizagem cooperativa em grupo** complementando o trabalho individual do PIT. 

---

## Conselho de Turma e Registo de Decisões (Gestão Cooperativa)
No MEM, o **Conselho de Turma** (ou "Conselho de Cooperação Educativa") é uma assembleia regular onde alunos e professor avaliam o trabalho, resolvem problemas da vida da turma e **contratualizam objetivos e regras** ([Modelo Pedagógico do MEM – Movimento da Escola Moderna](https://www.escolamoderna.pt/modelo-pedagogico/#:~:text=Esta%20avalia%C3%A7%C3%A3o%20assenta%20numa%20negocia%C3%A7%C3%A3o,em%20Conselho%20de%20Coopera%C3%A7%C3%A3o%20Educativa)). O Infantinho 3.0 deve permitir **registar as decisões** desses conselhos e ajudar na sua implementação.

### 8.1 Funcionalidades Previstas para o Conselho
- **Agendamento de Conselhos:** Possibilidade de marcar no sistema quando ocorrem conselhos de turma (ex: semanalmente). Apenas para referência, ou notificação aos alunos. (Não essencial, mas útil).
- **Ordem de Trabalhos e Participação:** Poderíamos disponibilizar uma pauta pré-definida que pode ser preenchida antes/durante o conselho:
  - Ex: "Avaliação das atividades da semana, Discussão de problemas, Propostas de melhoria, Definição de tarefas/objetivos para próxima semana, Outros assuntos".
  - Isso pode ser um formulário que o professor ou um aluno-secretário preenche durante a reunião.
- **Registo de Decisões:** O resultado mais importante são as **decisões e propostas aprovadas**. Implementação:
  - Modelo `CouncilDecision` com campos: turma, data, descrição da decisão, categoria (ex: **Regra**, **Objetivo de Aprendizagem**, **Atividade**, **Outro**), e quem foi responsável por executá-la se aplicável.
  - Essas decisões podem ter relação com outros módulos:
    - Se categoria **Objetivo de Aprendizagem**, poderíamos ligar a um item de checklist marcado como foco ou a uma tarefa futura de PIT.
    - Se **Regra/Procedimento** (ex: "Manter a sala limpa, turnos de limpeza"), isso não se liga a outro módulo mas fica registrado.
    - Se **Atividade/Evento** (ex: "Organizar feira de ciências"), pode gerar um Projeto ou Tarefa atribuída.
  - Campo de situação: pendente, em andamento, cumprido.
- **Ata do Conselho:** Poderíamos simplesmente usar o **Diário de Turma** (blog) para escrever a ata, o que já cobrimos. No entanto, extrair as decisões-chave para um local estruturado facilita acompanhamento. Por isso, o fluxo pode ser:
  - No final da ata (post do diário) de um Conselho, o secretário lista "Decisões tomadas:" e pontua 1, 2, 3.
  - Mais tarde, o professor ou secretário vai ao módulo Conselho e insere cada decisão formalmente, para que fique no sistema de acompanhamento.
- **Acompanhamento das Decisões:** 
  - Na página da turma, uma seção **Conselho/Decisões** lista as decisões pendentes ou em vigor. Por ex: "Regra: Falar um de cada vez nas apresentações – **Em vigor desde 10/Out**"; "Objetivo: Todos lerem um livro este mês – **a cumprir até 30/Nov**".
  - Conforme são cumpridas, marcam-se como concluídas (ex: passado o prazo, ou verificado o cumprimento).
  - Se uma decisão envolve tarefas (ex: "João e Maria irão preparar a apresentação da visita de estudo"), talvez criamos automaticamente um mini-projeto ou atribuimos no PIT deles.
- **Participação dos Alunos:** 
  - Idealmente, qualquer aluno pode adicionar **propostas** de pauta antes do conselho, para serem discutidas. Poderíamos implementar um pequeno form de **Propostas do Aluno**:
    - O aluno escreve uma proposta (ex: "Trocar os grupos de lugar", "Ter mais tempo de TEA na quarta-feira").
    - Essa proposta fica visível ao professor (pode moderar) e é levada ao próximo conselho.
    - Depois do conselho, registra-se se foi aprovada ou não (e vira uma decisão se aprovada).
  - Isso engaja os alunos na gestão democrática.
- **Exemplo de Uso:** 
  - Conselho de turma do 7.ºA em 15/Nov: discutem a indisciplina no TEA. Decisão: "Cada aluno terá um sinal na mesa indicando 'não incomodar' durante TEA, decidido por todos". Isso é registrado como Regra. Também definem um objetivo: "Até próximo conselho, cada aluno concluirá pelo menos 2 tarefas do PIT" (Objetivo de Aprendizagem). Essas decisões são inseridas. Na semana seguinte, o professor verifica se o objetivo foi cumprido (via checklists/PIT) e atualiza o status. No conselho seguinte, se cumprido, marcam como concluído.
- **Integração com IA:** 
  - Uma ideia futura: o assistente de IA pode observar as decisões e lembrar os alunos delas ("Lembra-te que no último conselho decidiram X, estás a cumprir?").
  - Ou ajudar a redigir a ata do conselho em linguagem formal a partir de notas soltas do secretário.
- **Implementação Técnica:**
  - `CouncilDecision` model com fields: turma, date, text, category, status, maybe responsible (FK User if applicable).
  - `StudentProposal` model: turma, author (User), text, date_submitted, status (pending, taken_to_council, approved_rejected).
  - Views:
    - List decisions (for class, visible to all class members, but only teacher/admin can mark status changes).
    - Add decision (teacher or designated student).
    - List proposals (for teacher, and possibly visible to class).
    - Add proposal (student).
    - Option to convert proposal to decision after council.
  - For UI simplicity, we might not build a complex scheduling system. Assume councils happen regularly and teacher just handles proposals and decisions manually in system.
  - Use the Blog diary to capture the narrative, and the decisions module for tracking items.

Este módulo reforça o pilar da **gestão democrática** da turma, assegurando que o portal não é só ferramenta de estudo individual mas também de organização coletiva.

---

## Integração de Agentes de Inteligência Artificial (IA)
Uma funcionalidade avançada do Infantinho 3.0 será a incorporação de **agentes de IA** para apoiar alunos e professores. Esses agentes atuarão como **assistentes virtuais personalizados**, comunicando entre si e aprendendo com os dados disponíveis no portal, de forma a oferecer **apoio contextualizado e alinhado pedagogicamente** aos utilizadores.

### 9.1 Visão Geral dos Agentes IA e seus Papéis
Pretende-se implementar uma **arquitetura multi-agente**:
- **Assistente do Aluno (Tutor IA):** Agente projetado para interagir diretamente com o aluno. Fornece ajuda em tarefas, explica conteúdos, sugere recursos, orienta o aluno quando este está planeando ou executando seu PIT ou projeto. Este tutor virtual deverá **respeitar o perfil individual do aluno** (por ex., se o aluno tem Necessidades Educativas Especiais indicadas no Decreto 54, o agente adota estratégias inclusivas; se o aluno já dominou certo conteúdo, não repetirá explicações básicas).
- **Assistente do Professor (Coach IA):** Agente para o professor, auxiliando no planejamento e avaliação. Por exemplo, pode sugerir atividades diferenciadas para alunos com dificuldades, propor enunciados de exercícios ou gerar um resumo do progresso da turma. Também pode analisar dados (listas de verificação, PITs) e alertar o professor de padrões (ex: "Muitos alunos com dificuldade em frações").
- **Coordenador de IA (Meta-Agente):** Opcionalmente, um agente interno que não interage com humanos diretamente, mas **coordena a comunicação** entre os agentes acima e garante que as respostas sigam as diretrizes pedagógicas:
  - Este meta-agente teria acesso aos **documentos base** (Perfil dos Alunos, Aprendizagens Essenciais, Decretos 54/55, Educação Dehoniana, conteúdo do projeto de mestrado) e monitoraria as sugestões dos outros agentes, refinando-as para alinhamento.
  - Ex: se o Tutor IA fosse sugerir algo desalinhado com as Aprendizagens Essenciais, o meta-agente ajustaria a resposta.
- Em prática inicial, poderemos implementar apenas dois "modos" de IA (um quando aluno pergunta, outro quando professor pergunta) e manualmente incorporar as diretrizes nos prompts, em vez de uma comunicação entre bots complexa. Mas a arquitetura será pensada para evoluir nisso.

### 9.2 Implementação Técnica da IA
- **Integração com APIs Externas:** Usaremos serviços de IA existentes (OpenAI GPT-4/GPT-3.5, ou Google Vertex AI PaLM) via suas APIs. A escolha é configurável pelo admin:
  - Através do nosso módulo `ai_service`, passaremos prompts e parâmetros. Exemplo usando OpenAI in Python (conceitual):
    ```python
    import openai
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[ 
           {"role": "system", "content": system_prompt},
           {"role": "user", "content": user_message}
        ],
        temperature=0.7
    )
    reply = response['choices'][0]['message']['content']
    ```
  - Para Google, utilizar client adequado (likely via Google Cloud SDK).
- **Contexto e Prompts Inteligentes:** A chave do sucesso do agente é fornecer contexto suficiente:
  - Construiremos **prompts dinâmicos** que incluem dados relevantes:
    - Para o Tutor IA do aluno: incluir no prompt informações como *perfil do aluno* (ano, resultados recentes, preferências se conhecidas), *resumo do PIT atual do aluno* (tarefas planejadas, dificuldades marcadas), *itens da checklist dominados ou não* ("o aluno ainda não domina divisões por duas casas"), *documentos pedagógicos relevantes* (talvez um resumo de expectativas para a idade - do Perfil dos Alunos).
    - Para o Coach IA do professor: incluir *resumo da turma* (nº de alunos, média de progresso, problemas em destaque), *caso específico* se pergunta for sobre um aluno concreto, e *linhas orientadoras* (ex: "sugere estratégias dentro do Decreto 54 para inclusão de aluno X com dislexia").
  - **Manter Conversação:** Idealmente, a interação é conversacional. Então, para cada chat com IA, armazenaremos o histórico de diálogo (pelo menos durante a sessão atual) para enviar nas próximas chamadas, assim o agente lembra do contexto.
  - **Exemplo de Prompt do Tutor IA:**
    ```
    Sistema: "És um tutor virtual experiente, ajudando um aluno do 7.º ano dentro do modelo da Escola Moderna. 
    Leva em conta o perfil do aluno: tem 13 anos, gosta de Ciências, dificuldade em Matemática (frações).
    Objetivos atuais do aluno: melhorar frações e terminar leitura do livro X. 
    Deve incentivar autonomia, dar dicas mas não soluções diretas, e referir às aprendizagens essenciais.
    Usa linguagem simples e positiva. Segue os princípios da educação Dehoniana (valores de respeito, solidariedade)."
    Aluno: "Não consigo resolver este problema de frações, é muito difícil." 
    ```
    Com isso, esperamos que a IA responda orientando calmamente, talvez sugerindo rever um conceito ou dividir o problema, etc.
  - **Exemplo de Prompt do Coach IA:**
    ```
    Sistema: "És um assistente para um professor do 5.º ano, dentro de um modelo de pedagogia cooperada.
    Ajuda a planejar atividades e a identificar necessidades dos alunos.
    Perfil da turma: 20 alunos, muitos interesses em leitura, dificuldade geral em matemática.
    Hoje o professor quer planejar o próximo projeto integrando várias disciplinas e assegurar que todos participem.
    Lembra-o do decreto 55 (flexibilidade curricular) se necessário e do perfil dos alunos.
    "
    Professor: "Preciso de ideias para um projeto interdisciplinar envolvendo ciências e matemática."
    ```
    A IA poderia sugerir um projeto de jardim escolar medindo crescimento de plantas (envolve ciências, registo de medidas - matemática).
- **Treino e Aprendizado Contínuo:** "Aprender com os dados guardados" implica possivelmente:
  - **Fine-tuning local:** A medida que se usam as IA, podemos armazenar Q&A ou feedback do usuário para ajustar prompts ou treinar modelos específicos. Por exemplo, perceber que certo tipo de sugestão foi mal recebida e ajustar.
  - **Dados para IA:** Poderemos alimentar internamente documentos como o **Perfil dos Alunos** e **Aprendizagens Essenciais** para que o agente possa citar esses documentos. Isso pode ser feito inserindo resumos nos prompts ou utilizando técnicas de **retrieval augmentation**: 
    - Ex: antes de responder, buscar num índice local (podemos indexar textos dos documentos base) trechos relevantes e incluí-los no prompt.
  - Com o crescimento dos dados (posts, decisões, PITs), poderíamos treinar um modelo local de recomendação, mas isso excede escopo imediato. Inicialmente, rely on GPT's knowledge and our prompt engineering.
- **Interface com Usuário:**
  - Integrar um **chatbot UI** no portal:
    - Por exemplo, um ícone "Assistente IA" que abre um chat. Dependendo se o usuário é aluno ou professor, invoca o agente correspondente.
    - O chat deve mostrar claramente que é uma **IA experimental** e pode errar, e instruir a usá-la com consciência.
    - Também permitir feedback: após resposta, o usuário pode marcar se foi útil ou não, para monitorização de qualidade.
  - Para contextos específicos, podemos lançar o chat com um contexto:
    - Dentro de um PIT: botão "Pedir ajuda a IA" que já prepara um prompt com a tarefa em questão.
    - Dentro de um projeto: "Ideias para este projeto" botão para professor ou aluno.
- **Limites e Moderação:**
  - É crucial que a IA **não substitua** o professor nem viole princípios. Para isso:
    - Aplicar *filtros de conteúdo* das APIs (OpenAI e Google têm políticas).
    - Restringir que tipo de perguntas? (Se aluno tentar obter resposta exata de um teste, o IA deve preferir ensinar método).
    - Registrar logs das conversas (privadas, mas acessíveis ao admin se necessário para auditar problemas).
  - A IA deve **seguir os documentos de referência**: por ex., não dar conselhos pedagógicos contrários ao que diz o Perfil do Aluno. Podemos inserir um "não contradizer as seguintes normas..." no prompt.
- **Exemplo de Interação Real:**
  - Aluno: "O que devo fazer agora? Já terminei minhas tarefas do PIT cedo."
  - Tutor IA analisa: aluno completou 100% do PIT, checklists mostram que ainda não dominou "divisão de decimais". O agente responde: "Vejo que terminaste tudo o que planeaste, parabéns! 😀 Que tal antecipares a aprendizagem de divisão de decimais? Esse é um conteúdo que ainda podes reforçar. Podes tentar este desafio: ... (propõe um problema simples). Se precisares de ajuda, estou aqui."
  - Professor: "Como posso ajudar o Tiago que tem dislexia a acompanhar a leitura do texto X?"
  - Coach IA: (Consultando mentalmente Decreto 54 e estratégias de inclusão) "Para apoiar o Tiago, podes fornecer-lhe o texto em formato áudio e garantir que tenha mais tempo para ler. No modelo inclusivo do Decreto-Lei 54/2018, é importante dar diferentes formas de representação do conteúdo. Talvez um resumo antecipado ou mapa de ideias do texto possa ajudá-lo a compreender antes da leitura detalhada. Também podes parear ele com um colega tutor. Queres que eu elabore um pequeno resumo ou mapa do texto para ele?"
- **Implementação Progressiva:**
  - No MVP, a integração de IA pode ser **limitada ou mesmo simulada**, dado ser complexa. Podemos entregar um MVP com ganchos prontos para IA, e ativar num protótipo controlado:
    - Ex: Fornecer um chat com respostas fixas ou um FAQ se não integrar IA real imediatamente.
    - Mas dado que o requisito pede IA, tentaremos pelo menos integrar uma **chamada simples ao OpenAI GPT-3.5** no MVP para um caso de uso (por exemplo, geração de sugestão de atividade).
  - Em fases seguintes, expandir para os cenários completos acima descritos.

### 9.3 Configuração e Administração da IA
- Fornecer opções no painel admin para:
  - **Chave API**: inserir/alterar.
  - **Modelo**: selecionar entre disponíveis (listados via API, ex GPT-4 vs GPT-3.5).
  - **Língua de Resposta**: por padrão, o agente responde em Português Europeu. Mas se internacionalizar, poder querer escolher língua de interação da IA.
  - **Ativar/desativar agentes**: talvez um controle para desligar temporariamente acesso à IA (caso custos ou política).
- **Custos:** Informar ao administrador sobre implicações (uso de tokens da API tem custo, então talvez restringir uso excessivo, ex: limitar consultas por minuto ou por usuário).
- **Testes de Qualidade:** Escrever **testes automatizados** para alguns prompts (usando chamadas mockadas da IA) para garantir formato e presença de contexto. E ter professores avaliando respostas em beta.

A integração de IA, se bem sucedida, diferenciará fortemente o portal, mas também requer monitorização constante e refinamento conforme feedback de usuários.

---

## Internacionalização e Localização (I18N/L10N)
Desde o início, o Infantinho 3.0 será concebido com suporte a múltiplas línguas, embora **Português Europeu** seja a língua padrão e alvo inicial. A **internacionalização (i18n)** garante que o texto da interface pode ser traduzido sem alterar código, e a **localização (l10n)** refere-se a fornecer traduções e ajustes culturais para idiomas específicos.

### 10.1 Estratégia de Internacionalização
- **Framework de i18n:** Usaremos o suporte nativo do framework web (no Django, o sistema de internacionalização com `gettext`). Todo o texto apresentado em templates HTML ou mensagens de erro/sucesso no código backend será marcado para tradução:
  - Exemplo em Django template: 
    ```html
    <h1>{% trans "Plano Individual de Trabalho" %}</h1>
    ```
    Em Python:
    ```python
    from django.utils.translation import gettext as _
    messages.success(request, _("Plano submetido com sucesso."))
    ```
- **Ficheiros de Tradução:** Manteremos um arquivo de mensagens **pt** (Português) e poderemos iniciar um **en** (Inglês) para teste. O português será tanto o texto fonte como o primeiro locale (podemos optar por escrever texto fonte em inglês e traduzir para português, mas dado o público, talvez seja mais natural escrever diretamente em PT nas views e depois extrair para arquivo pt, e eventualmente traduzir para en).
- **Elementos a traduzir:**
  - Rótulos de botões, títulos de páginas, mensagens flash, textos de ajuda.
  - Conteúdos fixos dos módulos (ex: nomes das categorias padrão dos posts, ou estados das tarefas).
  - O conteúdo produzido pelos usuários (posts de blog, etc.) **não** é traduzido automaticamente, fica no idioma em que foi escrito.
- **Moedas, Formatos, etc.:** Como o contexto é local (Portugal), usaremos formatos de data/hora PT (DD/MM/AAAA) e separadores decimais PT. Mas usaremos as utilidades do framework para que isso mude conforme locale se altere.
- **Testar com outro idioma:** Após implementar toda interface em PT, mudaremos o locale para EN (criar um esboço de tradução) para verificar se todas as strings estavam marcadas corretamente. Essa verificação garante que no futuro tradução para, por exemplo, *Português do Brasil* ou *Espanhol* seja viável sem dor.
- **Seleção de Idioma pelos Utilizadores:** 
  - No MVP, pode não ser necessário, mas futuramente: Usuário pode escolher idioma preferido no perfil. Se não escolher, usa default (PT).
  - Uma opção simples: um menu no rodapé para trocar entre PT/EN para ver interface.
- **Considerações regionais:** Português Europeu vs Brasileiro tem diferenças. Caso surja interesse, poderemos ter `pt_PT` e `pt_BR` separados. O sistema de locale do Django suporta bem variações regionais.
- **Exemplo de Implementação:** 
  - Ao criar uma view do tipo:
    ```python
    def new_post(request, class_id):
        # ...
        if success:
            messages.success(request, _("Post criado com sucesso."))
        else:
            messages.error(request, _("Erro ao criar o post. Tente novamente."))
        # ...
    ```
    Estas mensagens vão para o arquivo django.po para tradução. Em pt_PT.po, traduziríamos as mesmas para assegurar consistência (neste caso, já estão em PT, mas digamos que optássemos por manter código-fonte em EN, então aqui escreveria "Post created successfully." e traduziria).
- **Documentação e Comentários no Código:** Permanecerão em inglês mesmo, conforme requisito, mas isso não impacta a UI. Os comentários não são expostos ao utilizador final.

### 10.2 Localização de Conteúdos de IA
- Como a IA também interage em PT, iremos garantir que os prompts do sistema fornecidos estão em Português correto (Europeu). Se usarmos documentos de referência em PT, melhor ainda.
- Se no futuro quisermos permitir que o assistente IA fale outros idiomas (por ex, para prática de línguas com alunos), podemos configurá-lo para isso por sessão. Mas, por padrão, manterá PT.
- Qualquer texto fixo que a IA devolva porque foi instruída (ex: "Parabéns pelo seu progresso!") convém estar ou traduzido ou definirmos no prompt que deve responder em PT.

A internacionalização garantirá que o Infantinho 3.0 possa ser adotado por outras escolas ou contextos linguísticos com mínimo esforço de tradução, estendendo seu impacto.

---

## Testes Automatizados e Dados de Demonstração
Para assegurar a qualidade e facilitar a manutenção, o projeto incluirá **testes automáticos abrangentes** e **scripts para popular a base de dados com dados fictícios** (seeding), simulando situações reais.

### 11.1 Estratégia de Testes Automatizados
Dividiremos os testes em algumas categorias:
- **Testes de Unidade (Unit Tests):** Testar funções e métodos isolados, especialmente:
  - Regras de negócio nas models (ex: métodos que calculam % concluído da checklist, ou que verificam se um aluno pode marcar um item).
  - Funções utilitárias, formatação de prompts de IA (ex: garantir que `build_student_prompt()` inclui certos elementos).
  - Validação de formulários (ex: garantir que não posso criar PIT sem tarefas).
- **Testes de Integração/Funcionais:** Usando talvez ferramentas do próprio Django (`Client`) para simular requests, ou Selenium/Playwright para testes end-to-end da interface. Cobrir casos:
  - **Autenticação e Papéis:** Login simulado (poderemos mockar a resposta OAuth no ambiente de teste), verificar que um convidado não acessa uma turma sem permissão, que um professor pode acessar sua turma e não outra.
  - **Fluxo do Blog:** Aluno cria post -> verificar que aparece na listagem, professor edita -> verificar alteração, comentário adicionado -> notificação enviada (podemos verificar enfileiramento de email ou mensagem).
  - **Listas de Verificação:** Marcação de item por aluno -> estado pendente validação, professor valida -> verificar estado mudado e talvez que uma sugestão de item concluído reflita em algum outro lugar.
  - **PIT Workflow:** Criar PIT -> submissão -> aprovação -> conclusão -> avaliação:
    - Podemos simular esse fluxo inteiro num teste, com asserts em cada etapa (status changes, correct permissions).
  - **Projeto:** similar, criando projeto, adicionando membros, etc.
  - **Decisões do Conselho:** Propor -> transformar em decisão -> verificar listagem.
  - **IA (se possível):** Mockar chamadas à API do OpenAI:
    - Ex: configurar o `ai_service` para, em testes, não chamar a internet mas retornar respostas pré-definidas. Testar que ao chamar o endpoint do chatbot com uma pergunta X, obtemos uma resposta (mock) formatada e armazenada no histórico.
  - **Internacionalização:** Talvez um teste que muda o locale e verifica se uma página contém o texto traduzido esperado.
- **Testes de Interface (UI/UX):** Embora difíceis de automatizar todos, podemos usar frameworks de teste end-to-end para simular um navegador:
  - Ex: com Selenium, abrir o site, logar, clicar em "Novo Post", preencher formulário, submeter, ver sucesso. Ou usar ferramentas mais modernas como **Playwright** que podem ser programadas para fluxo.
  - Esses testes garantem que a integração front-back está OK.
- **Cobertura de Testes:** Almejar pelo menos 80% de cobertura de código. Utilizar ferramentas (coverage.py) para identificar partes não testadas.

Escreveremos testes preferencialmente em **pytest** ou no framework de teste do Django. Os testes residirão numa pasta `tests/` organizada por módulo (tests for blog, tests for PIT, etc.).

### 11.2 Scripts de Populamento de Dados (Seed)
Para fins de desenvolvimento, demonstração (e para testes manuais e automatizados), criaremos um script que insere dados fictícios realistas:
- **Utilizadores de Exemplo:**
  - 1 Admin (por ex: admin@infantinho3.local, senha conhecida se login normal ou via SSO stub).
  - 2 Professores (ex: prof_ana@escola, prof_bruno@escola) já com papel atribuído.
  - 1-2 Turmas (ex: "5A_2025" com professor Ana, "9B_2025" com professor Bruno).
  - 5-10 Alunos por turma (nomes de teste, ex: aluno1@escola ...). Alguns podem ter encarregados associados (pais fictícios com email externo).
- **Conteúdos de Exemplo:**
  - Para cada turma, alguns Posts:
    - Posts de diário: gerar 2-3 diaries com conteúdos lorem ipsum adaptados a contexto escolar.
    - Posts de alunos: cada aluno posta um pequeno texto (pode até usar a API da IA offline ou um lorem).
  - Comentários: alguns comentários entre alunos/prof no blog.
  - Listas de verificação: templates já estarão carregados (via outro script ou migration). Marcar aleatoriamente alguns itens para cada aluno para simular progresso diferente (ex: aluno A dominou 30%, aluno B 50%).
  - PITs: gerar um PIT corrente para cada aluno:
    - Com 3-5 tarefas variadas (texto gerado aleatoriamente mas com sentido: "Exercícios de Matemática página X", "Leitura do capítulo Y").
    - Alguns PITs marcar como já submetidos, outros aprovados, alguns até avaliados com feedback, para demonstrar as telas em diferentes estados.
    - Possivelmente um histórico: gerar PITs passados (um ou dois) para alguns alunos para ver histórico.
  - Projetos: criar 1 projeto por turma:
    - Ex: turma 5A projeto "Horta Escolar" com 3 alunos, algumas tarefas definidas, estado ativo.
    - turma 9B projeto "Jornal da Escola" com 5 alunos, concluído, com resultados (e possivelmente um post final no blog).
  - Decisões de Conselho: adicionar 2-3 decisões para cada turma:
    - Ex: regra de comportamento, objetivo coletivo, evento marcado.
    - Diferentes status (um já cumprido, um pendente).
  - Propostas de alunos: talvez 1-2 pendentes.
- **Execução:** 
  - O script `populate_demo_data.py` poderá ser executado via linha de comando. Em Django, podemos fazê-lo como um custom command (`python manage.py populate_demo`) ou simples script que se importa no shell.
  - Ele deverá ser idempotente (capaz de rodar sem duplicar dados, talvez limpando antes os fictícios).
- **Uso nos Testes:** 
  - Podemos aproveitar partes do script nos testes de integração para rapidamente criar objetos necessários. Porém, é melhor que os testes criem o mínimo necessário usando factories para ser independentes.
- **Documentação dos Dados:** 
  - Fornecer talvez uma documentação ou comentário no script dizendo quais logins existem (para quem testar manualmente poder entrar com professor x, aluno y).
  - Garantir que nenhuma informação real sensível seja usada; tudo fictício.

### 11.3 Ferramentas de Teste e Integração Contínua
- Configurar um pipeline de CI (por ex. GitHub Actions) para rodar os testes em cada commit. Assim, problemas podem ser detectados cedo.
- Opcional: integrar cobertura e qualidade (pylint/flake8 for linting).
- Com o aumento de integração IA, possivelmente marcar testes de IA separados, pois chamá-la real pode ser instável; preferir mocks ou utilizar um modo “stub” do `ai_service` que retorna respostas determinísticas.

Através de testes robustos e dados de demonstração, garantimos que o Infantinho 3.0 é confiável e podemos mostrar suas funcionalidades facilmente para obtenção de feedback de utilizadores reais (professores e alunos) antes de avançar para produção final.

## Plano de Implementação por Fases e MVP
Por fim, sintetizamos as etapas de desenvolvimento do projeto em fases, destacando o conteúdo do MVP e as evoluções posteriores. Isso ajuda a gerir a complexidade e entregar valor incrementalmente.

### 12.1 Fase 0 – Planeamento e Configuração Inicial
- **Revisão de Requisitos:** Confirmar todos os requisitos com stakeholders (direção do colégio, professores MEM) para alinhar expectativas.
- **Setup do Repositório e Ambiente:** Configurar repositório Git; preparar ambiente de desenvolvimento (Python 3.x, Django, DB local). Configurar integração contínua (testes automáticos pipeline).
- **Modelagem Inicial:** Desenhar esquema de base de dados (entidades e relações principais) e arquitetação de componentes.
- **Protótipo de UI Wireframes:** (Opcional mas útil) Esboçar telas principais em papel ou ferramenta para feedback precoce dos professores quanto à usabilidade.

### 12.2 Fase 1 – Autenticação e Gestão Básica de Utilizadores/Turmas
- **Integração SSO Microsoft:** Implementar login/logout via Azure AD. Testar com alguns emails.
- **Modelos User e Turma:** Criar modelos, grupos de permissão e relações (aluno em turma, etc.). Criar algumas views básicas: lista de turmas do professor, página de turma vazia.
- **Painel Admin Config (mínimo):** Interface (pode ser Django admin default) para admin validar usuários e atribuir papéis. Testar fluxo: convidado -> aluno.
- *Entrega parcial:* Possibilidade de um professor fazer login e criar uma turma, e um aluno convidado ser adicionado.

### 12.3 Fase 2 – Módulo de Blog/Diário de Turma (MVP Parte 1)
- **Modelo Post e Comentário:** Criar e migrar.
- **Views do Blog:** listar posts por turma, criar post, visualizar post, editar/remover (com permissões).
- **Editor de texto rico:** Integrar CKEditor ou similar.
- **Notificações simples:** Enviar email ao criar post (se configurar email dev).
- **Testes:** Escrever testes de criação de post, permissão (aluno só na sua turma).
- *Entrega:* Blog funcional dentro de uma turma. Validar com um professor e aluno reais se possível.

### 12.4 Fase 3 – Módulo de Listas de Verificação (MVP Parte 2)
- **Modelo Checklist e Items:** Implementar modelos e pre-carregar templates de 1 ou 2 disciplinas para teste.
- **UI Aluno:** Página para aluno marcar objetivos. UI Professor: visão geral e validação.
- **Vincular a Blog/PIT:** Ainda não, mas verificar se todos entendem uso isolado.
- **Testes:** Aluno marca -> professor valida, etc.
- *Entrega:* Listas ativas por aluno, professor consegue monitorizar. Isso conclui o **MVP**: sistema de blog + checklists utilizável.

### 12.5 Fase 4 – Feedback MVP e Ajustes
- **Revisão com Utilizadores Piloto:** Apresentar MVP a alguns professores MEM e recolher feedback em termos de usabilidade, melhorias necessárias antes de prosseguir (iterar design se preciso).
- **Correções e Melhorias Rápidas:** Qualquer bug ou ajuste essencial no MVP antes de adicionar complexidade.

### 12.6 Fase 5 – Módulo PIT (Planos Individuais de Trabalho)
- **Modelos PIT e PlanTask:** Criar, migrar.
- **Views Aluno:** criar/editar PIT (rascunho, submissão).
- **Views Professor:** aprovação de PIT, visualização.
- **Autoavaliação e Avaliação:** Formulários finais para aluno e professor.
- **Notificações e Restrições de datas:** Implementar notificações básicas (email ou in-app) para submissão e avaliação. Garantir que só um PIT por período.
- **Testes:** Fluxos principais e corner cases (ex: dois alunos submetem ao mesmo tempo).
- *Entrega:* Módulo PIT pronto. Integração leve com checklists (ex: botão para abrir checklist).

### 12.7 Fase 6 – Módulo Projetos Cooperativos
- **Modelos Projeto e ProjectTask:** Criar.
- **Views Projeto:** criar projeto (prof/aluno), adicionar membros, listar projetos, detalhe com tarefas e updates.
- **Permissões de edição:** Apenas membros editam.
- **Testes:** Criar projeto, adicionar update, etc.
- *Entrega:* Grupos podem gerir seus projetos no portal.

### 12.8 Fase 7 – Módulo Conselho de Turma
- **Modelos Decisões e Propostas:** Criar e migrar.
- **Views:** Form para aluno propor (ligado à turma), lista de propostas (professor marca como discutida/aprovada), formulário de decisão, lista de decisões.
- **Ligação com Diário:** Talvez automatizar: se um post de diário for marcado como "contém decisões", parsear ele e sugerir decisões (pode ser sofisticado; inicialmente, inserção manual pelos professores).
- **Testes:** Propor -> aprovar -> ver decisão listada etc.
- *Entrega:* Registo de decisões funcionando, complementando os diários.

### 12.9 Fase 8 – Integração de IA (Protótipo)
- **Infraestrutura IA:** Implementar `ai_service` com capacidade de chamar API (provavelmente OpenAI GPT-3.5) usando chave de teste.
- **Interface Chat:** Colocar um botão de chat e um modal simples para conversa. Implementar para aluno e professor com prompts estáticos ou simples.
- **Contexto Básico:** Fornecer ao menos o nome do utilizador, papel e talvez um texto fixo do sistema como prompt (ex: "You are a helpful tutor..." em PT).
- **Testes (Manuais principalmente):** Ensaiar perguntas simples.
- *Entrega:* Demonstração de um chat básico com IA funcionando. (Nesta fase, respostas podem ser genéricas; a personalização e robustez vêm nas próximas fases.)

### 12.10 Fase 9 – Aprimoramento dos Agentes de IA
- **Melhoria de Prompts:** Incorporar dados reais nos prompts (ex: integrar com funções para pegar resumo do PIT do aluno, ou status das listas).
- **Comunicação entre Agentes:** Se viável, implementar um pipeline onde, por exemplo, a pergunta do aluno é primeiro processada pelo meta-agente (que adiciona guidelines) e depois responde. Ou simplesmente integrar as guidelines no prompt do tutor.
- **Aprendizagem de Preferências:** Gravar logs e possibilitar admin ver q&a. Ajustar onde necessário as respostas via prompt engineering.
- **Escolha de Modelo:** Testar também com Google API para ver diferenças e talvez oferecer como opção (comparar custo/qualidade).
- **Avaliação da IA:** Recolher feedback de alguns usuários sobre utilidade das respostas e ajustar.
- *Entrega:* IA mais contextual. Documentar para o colégio como funciona e limites (importante para expectativas).

### 12.11 Fase 10 – Internacionalização Completa
- **Traduções:** Congelar strings e extrair para ficheiro .po. Completar tradução PT-PT (se codebase estava em EN, traduzir para PT; se estava em PT, consideramos isso como principal).
- **Adicionar EN (ou outro) como teste:** Traduzir 20% das strings para EN para ver troca.
- **Interface de troca de idioma:** simples menu drop-down.
- **Testes:** Verificar páginas-chave em EN para layout (textos maiores/menores).
- *Entrega:* Versão PT-PT finalizada, com mecanismo pronto para outros idiomas.

### 12.12 Fase 11 – Refinação, Testes Finais e Deploy Piloto
- **Teste de Carga Leve:** Com dados de demonstração (e talvez duplicando dados para simular 300 alunos), testar desempenho básico.
- **Segurança:** Fazer revisão de segurança (uso de HTTPS, cookies secure, verificar que não há endpoints abertos sem auth, etc.). Se possível, teste de penetração básico ou uso de scanners.
- **Depuração de Bugs:** Resolver quaisquer bugs encontrados nos testes integrados finais.
- **Preparar Deployment:** Escrever scripts de implantação (Dockerfile/docker-compose, ou guia para servidor). Configurar servidor de produção (Ubuntu + Gunicorn + Nginx, por ex.) e base de dados PostgreSQL.
- **Formação e Documentação:** Preparar material de apoio para os utilizadores finais (pequenos tutoriais de "como criar PIT", etc.). Dar uma sessão de formação aos professores do colégio.
- **Deploy Piloto:** Lançar a aplicação para uma ou duas turmas piloto para uso real durante um período curto (1 mês, por exemplo), recolhendo feedback contínuo.

### 12.13 Fase 12 – Revisão Pós-Piloto e Expansão
- **Feedback Real:** Com base no uso real, ajustar funcionalidades (talvez UI improvements, ou ajustar lógica de PIT de semanal para quinzenal, etc.).
- **Correções e Melhorias:** Entrar num ciclo ágil de melhorias. Eventualmente planejar funcionalidades extra se solicitadas (ex: integração com sistema de notas da escola, ou gamificação).
- **Escala Completa:** Disponibilizar para todas as turmas do colégio. Monitorizar desempenho e uso.