# Wireframes de Baixa Fidelidade – Infantinho 3.0

## Filosofia e Princípios

Estes wireframes foram desenhados para o MVP do portal educativo **Infantinho 3.0**, guiados pelos princípios do projeto:
- **Simplicidade e clareza**: cada página prioriza o essencial, evitando distrações e excesso de opções.
- **Modularidade e escalabilidade**: componentes reutilizáveis e estrutura preparada para expansão futura.
- **Separação de papéis**: fluxos distintos para alunos, professores, administradores e encarregados de educação.
- **Acessibilidade e responsividade**: layouts adaptáveis a computador, tablet e telemóvel, com foco em contraste, tamanho de clique e navegação por teclado.
- **Internacionalização**: todos os textos e rótulos são pensados para fácil tradução e adaptação cultural.
- **Evolução incremental**: MVP enxuto, mas cada página já prevê pontos de expansão.

---

## Política de Autenticação

- **Alunos e Professores:** Devem obrigatoriamente usar o início de sessão federado via Microsoft (Azure AD/Office 365) com a conta escolar.
- **Encarregados de Educação (Pais) e Administradores:** Podem (ou devem) ter a opção de início de sessão local (email/palavra-passe) ou outro método alternativo, pois podem não ter conta Microsoft escolar.
- O sistema deve garantir que alunos/professores não consigam criar conta local e que pais/admins possam recuperar a palavra-passe localmente.

---

## Mapa de Navegação

```
[Página de Início de Sessão]
   ↓
[Painel Inicial] ←→ [Administração de Utilizadores/Turmas]
   ↓
[Página de Turma]
   ↓           ↓
[Diário de Turma] [Lista de Verificação de Aprendizagens]
   ↓
[Página de Criação de Publicação]
```

---

## 1. Página de Início de Sessão

**Público:** Todos os utilizadores

- Dois métodos de autenticação:
  - **Entrar com Microsoft** (para alunos e professores)
  - **Entrar com Email/Palavra-passe** (para pais/encarregados/admins)
- Mensagens claras orientando cada público.
- O fluxo de "Recuperar palavra-passe" só se aplica ao início de sessão local.
- Preparada para internacionalização e acessibilidade.

**Wireframe:**
```
+-------------------------------------------------------+
|                    Infantinho 3.0 Logo               |
|-------------------------------------------------------|
|                                                       |
|   [ Entrar com Microsoft ]                            |
|      (Alunos e Professores)                           |
|                                                       |
|   [ Entrar com Email/Palavra-passe ]                  |
|      (Pais/Encarregados/Admin)                        |
|                                                       |
|   Recuperar palavra-passe                             |
|                                                       |
+-------------------------------------------------------+
```

- **Nota:** O botão "Entrar com Microsoft" redireciona para o início de sessão federado Azure AD. O botão "Entrar com Email/Palavra-passe" abre um formulário tradicional.
- **Mensagem de apoio:** "Alunos e professores: usem a conta Microsoft escolar. Pais e administradores: usem o início de sessão por email."

---

## 2. Painel Inicial

**Público:** Alunos, Professores, Administradores

- Menu lateral persistente, painel principal com cartões de turmas.
- Componentes reutilizáveis: cartão de turma, botão de ação, campo de pesquisa.
- Pronto para expansão: notificações, atalhos para projetos, integração com IA.
- Layout responsivo e preparado para navegação por teclado.

O painel inicial combina um menu lateral fixo e um painel principal com cartões de turmas, seguindo a hierarquia recomendada em wireframes de baixa fidelidade. O menu lateral exibe ícones e rótulos para as secções principais (Painel, Turmas, Listas de Verificação, Definições). No painel central, cada cartão de turma mostra o nome, número de alunos e botões de acesso rápido ao diário de turma e à lista de verificação.

```
+--------------------------------------------------------------+
| [≡] Infantinho 3.0                                           |
|--------------------------------------------------------------|
| Painel      |                                             🔍|
| Turmas      |  Bem-vindo(a), Prof. Silva!                       |
| Listas de   |                                                   |
| Verificação |  ┌──────────────────────────────┐  ┌──────────┐   |
| Definições  |  │ Turma 4.º A                  │  │ Nova     │   |
|             |  │ Alunos: 20                   │  │ Publicação│   |
|             |  │ [Diário]  [Lista de Verificação]│           |
|             |  └──────────────────────────────┘                |
|             |  ┌──────────────────────────────┐                |
|             |  │ Turma 5.º B                  │                |
|             |  │ Alunos: 18                   │                |
|             |  │ [Diário]  [Lista de Verificação]│            |
|             |  └──────────────────────────────┘                |
|             |                                                   |
+--------------------------------------------------------------+
```

- **Menu lateral**: navegação persistente com destaque da secção ativa   
- **Painel principal**: cartões que priorizam ações-chave (Diário, Lista de Verificação)   
- **Pesquisa rápida**: campo no topo para localizar turmas ou publicações   

---

## 3. Página de Turma (Diário de Turma)

**Público:** Alunos, Professores, Encarregados (leitura)

- Divisão clara entre diário de turma e lista de membros.
- Botão "Nova Publicação" visível apenas para quem tem permissão.
- Coluna lateral pode crescer para incluir chat, agenda ou arquivos.
- Publicações e observações preparadas para anexos e internacionalização.

Na página de turma, dividimos verticalmente o espaço entre **Diário de Turma** e **Lista de Membros**, conforme recomendações de wireframe para fluxos claros de leitura. O Diário exibe publicações recentes com título, autor e data, seguido de um botão de "Nova Publicação". A coluna lateral lista alunos e professores, permitindo navegação direta.

```
+--------------------------------------------------------------+
| ‹ Voltar   Turma 4.º A                                      |
|--------------------------------------------------------------|
|  [Nova Publicação]                                          |
|                                                              |
|  • Publicação: "Visita ao museu" – Ana (12/04/2025)          |
|    [Ler Mais]                                               |
|                                                              |
|  • Publicação: "Projeto de ciências" – João (10/04/2025)      |
|    [Ler Mais]                                               |
|                                                              |
+--------------------------------------------------------------+
| Alunos:                                                     |
|  - João Silva                                              |
|  - Maria Fernandes                                         |
|  ...                                                       |
| Professores:                                               |
|  - Prof. Silva                                             |
|--------------------------------------------------------------|
```

- **Botão "Nova Publicação"**: destacado no topo para incentivar contribuições   
- **Listagem de publicações**: formato de lista para leitura rápida   
- **Coluna lateral**: lista de membros para referência e gestão de turmas   

---

## 4. Página de Criação de Publicação

**Público:** Alunos, Professores

- Modal ou página dedicada, campos alinhados verticalmente.
- Dropdown de categoria pode ser expandido para tags e anexos.
- Botões de ação padronizados em todo o sistema.
- Preparada para validação de campos e mensagens de erro acessíveis.

A tela de criação de publicação é apresentada em modal ou página dedicada, com campos para título, conteúdo (textarea) e categoria (dropdown), alinhados verticalmente para fluidez do preenchimento. Ao final, um botão "Publicar" e outro "Cancelar" oferecem controle ao usuário.

```
+--------------------------------------------------------------+
| [X] Criar Nova Publicação                                    |
|--------------------------------------------------------------|
| Título:   [________________________]                        |
| Categoria:[ v Selecione…          ]                        |
| Conteúdo:                                                  |
| [                                              ]           |
| [                                              ]           |
| [                                              ]           |
|                                                            |
|     [ Publicar ]         [ Cancelar ]                     |
+--------------------------------------------------------------+
```

- **Modal/Página limpa**: foco no formulário sem distrações   
- **Dropdown de categoria**: permite organizar publicações por turma ou tema   
- **Botões de ação**: hierarquia visual clara entre ações principais e secundárias   

---

## 5. Página de Lista de Verificação de Aprendizagens (Aluno)

**Público:** Alunos

- Lista de objetivos com checkboxes e estado.
- Filtros simples, mas preparados para busca avançada no futuro.
- Componentes reutilizáveis: item de lista de verificação, dropdown de estado.
- Layout responsivo, preparado para internacionalização e acessibilidade.

Para alunos, a lista de verificação é apresentada como lista de objetivos com checkboxes e estado selecionável (Não Iniciada, Em Progresso, Para Avaliar, Concluída). Cada item inclui título, descrição curta e estado atual, permitindo filtragem por estado.

```
+--------------------------------------------------------------+
| ‹ Voltar   Lista de Verificação – 4.º A                      |
|--------------------------------------------------------------|
| [Filtro: Todos ▼]  [Filtrar]                                 |
|                                                              |
| ☐ Matemática: Operações básicas                              |
|    Estado: [Em Progresso ▼]                                  |
|                                                              |
| ☐ Português: Comentário de texto                             |
|    Estado: [Não Iniciada ▼]                                  |
|                                                              |
| ☐ Ciências: Ciclo da água                                   |
|    Estado: [Para Avaliar ▼]                                  |
+--------------------------------------------------------------+
```

- **Checkbox & dropdown de estado**: permitem atualização rápida pelo aluno   
- **Filtro de estado**: possibilita foco em itens pendentes ou para avaliação   
- **Layout responsivo**: projetado para tablets com espaços de toque adequados   

---

## 5.1 Página de Lista de Verificação de Aprendizagens – Detalhe (Português, 6.º ano)

### Funcionalidades principais
- Navegação por disciplina (menu suspenso no topo)
- Agrupamento dos objetivos por domínio/tema (ex: Oralidade, Leitura, Escrita, Gramática)
- Lista longa de objetivos, cada um com:
  - Código e descrição
  - Estado (Não Iniciado, Em Progresso, Concluído)
  - Checkbox ou botão "Preciso de apoio" (editável pelo aluno, visível a todos)
- Contador de objetivos concluídos
- Filtro por estado e pesquisa rápida (opcional)
- Possibilidade de expandir/recolher grupos de objetivos

### Wireframe textual (Aluno)

```
+--------------------------------------------------------------+
| Disciplina: [ Português ▼ ]                                  |
| Objetivos concluídos: 12                                     |
|--------------------------------------------------------------|
| [Pesquisar objetivo...] [Filtro: Todos ▼]                    |
|                                                              |
| ▼ Oralidade                                                  |
|   [OC1] Esclarecer, com fundamentação adequada, sentidos...  |  Estado: [Não Iniciado ▼]  [ ] Preciso de apoio
|   [OC2] Distinguir factos de opiniões...                     |  Estado: [Em Progresso ▼]  [x] Preciso de apoio
|   ...                                                        |
|                                                              |
| ▼ Escrita                                                    |
|   [E1] Escrever textos de caráter narrativo...               |  Estado: [Concluído ✔]     [ ] Preciso de apoio
|   ...                                                        |
+--------------------------------------------------------------+
```
- O aluno pode marcar/desmarcar "Preciso de apoio" em cada objetivo.
- O estado "Preciso de apoio" é visível a todos os colegas e ao professor.

### Wireframe textual (Professor)

```
+--------------------------------------------------------------+
| Disciplina: [ Português ▼ ]                                  |
| Turma: [6.º A ▼]                                             |
|--------------------------------------------------------------|
| [Pesquisar objetivo...] [Filtro: Todos ▼]                    |
|                                                              |
| ▼ Oralidade                                                  |
|   [OC1] Esclarecer, com fundamentação adequada, sentidos...  |
|     João Silva:   Estado: [Em Progresso ▼]  [x] Precisa de apoio  [ ] Apoio dado
|     Maria Costa:  Estado: [Não Iniciado ▼]  [ ] Precisa de apoio  [ ] Apoio dado
|   ...                                                        |
+--------------------------------------------------------------+
```
- O professor vê quem pediu apoio e pode registar se o apoio foi dado.
- Os colegas também podem ver quem pediu apoio, podendo assim oferecer ajuda.

### Notas
- O agrupamento dos objetivos por domínio/tema segue a estrutura dos códigos (ex: OC = Oralidade Compreensão, OE = Oralidade Expressão, L = Leitura, EL = Educação Literária, E = Escrita, G = Gramática).
- O contador de objetivos concluídos mostra apenas os objetivos marcados como "Concluído".
- O filtro por estado e a pesquisa rápida são opcionais, mas recomendados para listas extensas.
- O campo "Preciso de apoio" pode ser usado para promover colaboração entre alunos e facilitar o acompanhamento pelo professor.

---

## 6. Página de Lista de Verificação de Aprendizagens (Professor)

**Público:** Professores

- Visualização da lista de verificação dos alunos, com botões de validação e campo de observação.
- Filtros por estado, aluno e disciplina podem ser expandidos.
- Botão "Validar Concluído" só aparece para professores.
- Observações podem ser exportadas ou integradas com feedback automatizado (IA).

Os professores visualizam a mesma lista de verificação dos alunos, mas com botões de validação ao lado de itens "Para Avaliar" para marcar como concluídos. É adicionada uma coluna de "Observações" para retroalimentação direta.

```
+--------------------------------------------------------------+
| ‹ Voltar   Lista de Verificação Turma – 4.º A                 |
|--------------------------------------------------------------|
| [Filtro: Para Avaliar ▼]  [Filtrar]                          |
|                                                              |
| ☐ Ciências: Ciclo da água                                   |
|    Aluno: João Silva                                         |
|    Observação: [____________________]  [Validar Concluído]   |
|                                                              |
| ☐ Matemática: Operações básicas                             |
|    Aluno: Maria Fernandes                                    |
|    Observação: [____________________]  [Validar Concluído]   |
+--------------------------------------------------------------+
```

- **Botão "Validar Concluído"**: visível apenas para estado "Para Avaliar"   
- **Campo de observação**: facilita retroalimentação direta ao aluno
- **Filtro por estado**: ajuda professores a priorizar avaliações  

---

## 7. Administração de Utilizadores/Turmas

**Público:** Administradores, Professores (gestão restrita)

- Tabelas padronizadas para listagem, edição e exclusão.
- Abas para separar contextos (utilizadores, turmas, permissões).
- Pronto para expansão: gestão de papéis, permissões granulares, importação/exportação de dados.
- Componentes reutilizáveis: tabela, modal de confirmação, formulário de edição.

Na área administrativa, o layout segue padrão de tabela para listagens de utilizadores e turmas, com botões de ação "Editar", "Excluir" e "Adicionar Novo" citeturn2search0. O menu lateral expande-se com opções específicas de configuração e gestão citeturn2search2.

```
+--------------------------------------------------------------+
| ‹ Voltar   Administração                                     |
|--------------------------------------------------------------|
| [Utilizadores]  [Turmas]                                     |
|                                                              |
| Utilizadores:                                               |
|  ID | Nome            | Papel       | Ações                  |
|  01 | João Silva      | Aluno       | [Editar] [Excluir]     |
|  02 | Prof. Silva     | Professor   | [Editar] [Excluir]     |
|  …   …                …             …                       |
| [Adicionar Novo Utilizador]                                   |
+--------------------------------------------------------------+
|                                                              |
| Turmas:                                                     |
|  ID | Nome Turma      | Nº Alunos   | Ações                  |
|  01 | 4.º A           | 20          | [Editar] [Excluir]     |
|  …   …                …             …                       |
| [Adicionar Nova Turma]                                         |
+--------------------------------------------------------------+
```

- **Abas "Utilizadores" e "Turmas"**: separam contextos para gerenciamento claro  
- **Tabelas com botões de ação**: consistentes com padrões de interface   
- **Botões "Adicionar Novo"**: posicionados no final de cada seção para expandir a lista   

---

## Componentes Reutilizáveis
- **Cartão de Turma**: usado no painel inicial e em seletores de turma.
- **Tabela de Utilizadores/Turmas**: padrão para todas as listagens administrativas.
- **Modal de Confirmação**: para ações críticas (excluir, sair de turma).
- **Dropdown de Estado**: usado em listas de verificação, publicações, filtros.

---

## Notas de Escalabilidade e Internacionalização
- Todos os textos devem ser extraídos para arquivos de tradução.
- Layouts preparados para textos longos e línguas com palavras maiores.
- Estrutura modular permite adicionar novos módulos (projetos, PIT, conselhos) sem refatoração pesada.

---

## Evolução Futura
- **Painel**: pode incluir notificações, integração com agentes de IA, atalhos para projetos e conselhos.
- **Diário de Turma**: anexos, publicações públicas, integração com calendário.
- **Lista de Verificação**: exportação de progresso, gráficos, integração com PIT.
- **Administração**: permissões avançadas, relatórios, integração com sistemas externos.
- **Acessibilidade**: testes contínuos de contraste, navegação por teclado, suporte a leitores de tela.

---

> Estes wireframes são um ponto de partida. Devem ser revisados e evoluídos conforme feedback dos utilizadores e crescimento do portal.