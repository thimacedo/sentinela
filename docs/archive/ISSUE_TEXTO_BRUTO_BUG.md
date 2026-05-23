# 🔴 PROBLEMA IDENTIFICADO: Comentários Exibindo Username ao Invés do Texto

## Diagnóstico

### Sintoma
Cards no dashboard mostram apenas o username (ex: "esquerdapiauiense") ao invés do comentário real.

### Causa Raiz
No arquivo `src/core/ui.js` (linha ~270), a renderização usa:
```javascript
"${alerta.texto_bruto || 'Conteúdo indisponível...'}"
```

Mas o campo `texto_bruto` está vazio ou contém apenas o username.

### Dados de Exemplo (dados_latest.csv)
```csv
id | author_username | texto_bruto | text
---|---|---|---
... | esquerdapiauiense | esquerdapiauiense | esquerdapiauiense
```

**Problema:** `texto_bruto` deveria conter o conteúdo do comentário, mas contém apenas o username.

---

## 🔍 Raiz do Problema (Backend)

### Cadeia de Dados
1. **Scraper** (`sentinela_scraper/instagram.py`) coleta do Instagram
2. **TextProcessor** (`processing/text_processor.py`) processa/limpa
3. **DataMiner** (`processing/data_miner.py`) mineração
4. **Normalização** (`core/normalizer.py`) normaliza nomes de colunas
5. **API** (`api/index.py`) expõe os dados

### Pontos Críticos de Verificação

#### 1. **Instagram Scraper** (`sentinela_scraper/instagram.py`)
   - ✓ Verificar se `texto_bruto` está sendo populado corretamente
   - ✓ Confirmar que não está sendo truncado/sobrescrito

#### 2. **TextProcessor** (`processing/text_processor.py`)
   - ✓ Verificar método `clean_text()` 
   - ✓ Confirmar que não está limpando demais (removendo todo o conteúdo)

#### 3. **Normalizer** (`core/normalizer.py`)
   - ✓ Verificar se há mapeamento incorreto entre `texto_bruto` ↔ `text`
   - ✓ Confirmar campo `owner_username` está sendo preservado

#### 4. **Database** (Supabase)
   - ✓ Verificar schema: `texto_bruto` deve ser TEXT, não VARCHAR(50)
   - ✓ Verificar se há constraint que trunca em 255 chars

#### 5. **API Response** (`api/index.py`)
   - ✓ Método `get_active_alerts()` está retornando o campo correto?

---

## 📋 Plano de Correção por Fase

### FASE 1: Validação de Dados
**Responsável:** Worker de Validação  
**Tempo:** Imediato

```python
# scripts/validate_text_field.py
# Verificar registros onde texto_bruto é vazio ou = owner_username
```

### FASE 2: Correção no TextProcessor
**Responsável:** TextProcessor Worker  
**Tempo:** 1-2 ciclos

```python
# processing/text_processor.py
# Garantir que clean_text() não remove todo conteúdo
# Adicionar validação: if len(cleaned_text) == 0, manter original
```

### FASE 3: Correção na Coleta
**Responsável:** Instagram Scraper  
**Tempo:** Próximo batch

```python
# sentinela_scraper/instagram.py
# Verificar extração de texto do comentário
# Confirmar que não está extraindo author ao invés do text
```

### FASE 4: Correção de Histórico
**Responsável:** Batch Cleanup Job  
**Tempo:** Post-hotfix

```sql
-- Migration para reprocessar registros com texto_bruto vazio
-- Tentar recuperar dados de API ou marcar para re-coleta
```

### FASE 5: Frontend
**Responsável:** UI/Dashboard  
**Tempo:** Imediato

```javascript
// src/core/ui.js
// Fallback para campos alternativos se texto_bruto vazio:
// 1. alerta.text (mapeamento normalizado)
// 2. alerta.comentario (se disponível)
// 3. "Comentário sem conteúdo recuperável"
```

---

## 🛠️ Checklist de Ações

- [ ] **URGENTE:** Implementar fallback no UI (5 min)
- [ ] Verificar schema Supabase (`comentarios` table)
- [ ] Auditar TextProcessor.clean_text()
- [ ] Verificar scraper de Instagram
- [ ] Criar script de validação de dados
- [ ] Executar batch cleanup se necessário
- [ ] Testar com novo batch de coleta

---

## 🚨 Impacto

- **Severidade:** ALTA (Perda de inteligência funcional)
- **Usuários Afetados:** Todos os usuários do dashboard
- **Dados Afetados:** Comentários sem conteúdo legível desde ~2026-05-05
- **Estimativa de Recuperação:** Dados do histórico podem estar perdidos

---

## 📊 Próximas Ações Recomendadas

1. Correção imediata: Fallback no UI
2. Investigação: Verificar qual step quebrou os dados
3. Prevenção: Adicionar validação de dados em pipeline
4. Recovery: Batch cleanup de registros afetados

