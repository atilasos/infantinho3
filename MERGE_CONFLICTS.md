# Relatório de Conflitos - Merge Frontend → Main
**Data:** 2026-02-02 14:30
**Analisado por:** Opus + Agentes Kimi

## 📊 Resumo

| Métrica | Valor |
|---------|-------|
| Ficheiros alterados | 411 |
| Linhas adicionadas | +47,229 |
| Linhas removidas | -10,572 |
| Tipo de merge | **Arquitetura diferente** |

## 🆕 Ficheiros Só em Main (nosso trabalho)

Estes ficheiros precisam ser portados para a nova estrutura:

### AI Assistant (PORTAR → backend/ai/)
```
ai_assistant/ai_service.py          → backend/ai/services/prompting.py (prompts ZDP)
ai_assistant/student_profile.py     → backend/ai/models.py (novo modelo)
ai_assistant/ae_knowledge.py        → backend/ai/services/context.py
ai_assistant/batch_translate_ae.py  → backend/ai/management/commands/
ai_assistant/knowledge/ae/          → backend/ai/knowledge/ae/
ai_assistant/forms.py               → backend/ai/ (adaptar)
ai_assistant/views.py               → backend/ai/views.py (merge)
```

### GitHub/CI (MANTER)
```
.github/ISSUE_TEMPLATE/    ✅ Adicionar ao frontend
.github/PULL_REQUEST_TEMPLATE.md  ✅ Adicionar
.pre-commit-config.yaml    ✅ Adicionar
Makefile                   ✅ Adaptar
```

## 🔄 Estrutura AI no Frontend Branch

```
backend/ai/
├── services/
│   ├── providers.py      # OpenAI + Ollama (já existe)
│   ├── orchestrator.py   # Orquestração (já existe)
│   ├── context.py        # ← Adicionar AE Knowledge aqui
│   ├── prompting.py      # ← Adicionar prompts ZDP aqui
│   ├── quotas.py         # Rate limiting (já existe)
│   ├── router.py         # Routing (já existe)
│   └── cache.py          # Caching (já existe)
├── models.py             # ← Adicionar StudentProfile aqui
└── management/
    └── commands/         # ← Adicionar batch_translate aqui
```

## ⚠️ Conflitos Potenciais

### 1. Migrações
- `ai_assistant/migrations/0001_initial.py` → Recreate para backend/ai/
- `ai_assistant/migrations/0002_*.py` → Recreate

### 2. Settings
- `INSTALLED_APPS`: main tem `ai_assistant`, frontend tem `ai`
- Resolver: remover ai_assistant, manter ai

### 3. URLs
- main: `/ai/chat/`, `/ai/turmas/<id>/chat/`
- frontend: `/api/ai/...` (API REST)
- Resolver: frontend usa API, manter endpoints REST

### 4. Templates
- main: Django templates em ai_assistant/templates/
- frontend: React components em frontend/src/
- Resolver: Portar lógica para React, descartar templates Django

## 🎯 Estratégia de Merge

### Opção Selecionada: Merge Frontend + Port Work

```bash
# 1. Checkout frontend
git checkout origin/frontend -b merge-work

# 2. Cherry-pick commits do main com nosso trabalho
git cherry-pick 5a4cc74  # feat(ai): add AI Assistant
git cherry-pick e450b44  # feat(ae): translate AE
git cherry-pick 252b4bc  # feat(ai): ZDP prompts + profiles

# 3. Resolver conflitos manualmente
# 4. Adaptar código para nova estrutura
# 5. Testar
# 6. Merge para main
```

## ✅ Checklist de Migração

- [ ] Criar branch merge-work
- [ ] Adicionar StudentProfile a backend/ai/models.py
- [ ] Adicionar prompts ZDP a backend/ai/services/prompting.py
- [ ] Adicionar AE knowledge a backend/ai/services/context.py
- [ ] Copiar knowledge/ae/ para backend/ai/
- [ ] Criar management command batch_translate
- [ ] Atualizar migrações
- [ ] Testar Django backend
- [ ] Testar Next.js frontend
- [ ] Merge para main

## 📝 Notas

O branch frontend representa uma evolução significativa da arquitetura.
O trabalho de hoje (ZDP, profiles, AE) é valioso e deve ser preservado.
A melhor estratégia é adotar o frontend como base e portar nosso trabalho.
