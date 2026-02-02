# Próximos Passos - Infantinho 3.0

## ✅ Concluído (2026-02-02)

### Arquitetura
- [x] Migração para arquitetura headless (Django API + Next.js)
- [x] Branch `frontend` promovido para `main`
- [x] Backup do antigo `main` em `main-legacy`

### Backend
- [x] Todas as migrações aplicadas (64 total)
- [x] Testes AI passam (7/7)
- [x] StudentProfile model com ZDP tracking
- [x] Prompts ZDP integrados no prompting.py

### Frontend  
- [x] npm install concluído
- [x] lib/config.ts e lib/utils.ts criados
- [x] Tipos AppUser corrigidos

## 🔄 Em Progresso

### Batch AE Processing
- [ ] Ollama a traduzir AE (1º-9º ano) - lento
- [ ] Verificar output em `backend/ai/knowledge/ae/`

### TypeScript Fixes
- [ ] Corrigir tipos em `checklists/alunos/[studentId]/page.tsx`
- [ ] Sincronizar OpenAPI schema com API real
- [ ] Regenerar tipos: `npm run generate:api`

## 📋 TODO

### Alta Prioridade
1. [ ] Corrigir erros TypeScript restantes no frontend
2. [ ] Testar frontend com `npm run dev`
3. [ ] Verificar integração backend ↔ frontend
4. [ ] Criar superuser: `python manage.py createsuperuser`

### Média Prioridade
5. [ ] Completar batch AE para todos os anos
6. [ ] Criar testes para StudentProfile
7. [ ] Documentar API endpoints
8. [ ] Configurar CORS para desenvolvimento

### Baixa Prioridade
9. [ ] Configurar CI/CD
10. [ ] Setup Docker para produção
11. [ ] Configurar backups automáticos

## 🚀 Comandos Úteis

```bash
# Backend
cd backend
source ../venv/bin/activate
python manage.py runserver 8000

# Frontend
cd frontend
npm run dev

# Testes
cd backend && python manage.py test ai
cd frontend && npm run test:e2e

# Gerar tipos OpenAPI
cd frontend && npm run generate:api
```

## 📝 Notas

- **API Base URL:** http://localhost:8000/api
- **Frontend URL:** http://localhost:3000
- **Admin:** http://localhost:8000/admin

## 🐛 Issues Conhecidos

1. **TypeScript errors:** Tipos OpenAPI desatualizados vs API real
2. **Batch AE lento:** Ollama com llama3.2:3b pode demorar
3. **Frontend lib ignored:** Era gitignored, agora forçado
