# Otimização de Ingestão e IA (PASA) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Otimizar a velocidade de ingestão do Instagram, adicionar validação prévia de comentários, atualizar o schema para scores de confiança e evidências, e apresentar esses dados com uma UX/UI profissional no dashboard.

**Architecture:** A validação e limpeza ocorrerão no `InstagramWorker`. Adicionaremos uma migração no Supabase para as novas colunas. Atualizaremos o `PasaClassificationService` para garantir o output estruturado da IA (confidence_score e evidence_extracted). Por fim, o `src/core/app.js` será modificado para renderizar o indício de forma fluida.

**Tech Stack:** Python, FastAPI, Supabase (PostgreSQL), Vanilla JS (Frontend).

---

### Task 1: Adicionar Novas Colunas no Supabase

**Files:**
- Create: `supabase/migrations/20260516000001_add_confidence_and_evidence.sql`

- [ ] **Step 1: Criar a migração para adicionar as colunas**

Crie o arquivo com a query para adicionar as colunas `confidence_score` e `evidence_extracted` na tabela `comentarios`.

```sql
-- supabase/migrations/20260516000001_add_confidence_and_evidence.sql

ALTER TABLE comentarios
ADD COLUMN IF NOT EXISTS confidence_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS evidence_extracted TEXT;
```

- [ ] **Step 2: Commit**

```bash
git add supabase/migrations/20260516000001_add_confidence_and_evidence.sql
git commit -m "db: add confidence_score and evidence_extracted to comentarios"
```

### Task 2: Embutir Validação e Otimizar o InstagramWorker

**Files:**
- Modify: `app/workers/instagram_worker.py`

- [ ] **Step 1: Otimizar o processamento e validação de comentários**

Substitua a implementação dos métodos de limpeza e sanitização para descartar ruído prematuramente. No método `run`, vamos ajustar o delay (reduzindo levemente para ganhar 25% de performance) e no `_scrape_section` vamos melhorar a filtragem.

```python
# Modifique o _sanitize_comment para preencher as novas colunas e limpar melhor
    def _sanitize_comment(self, raw_comment: dict, content_type: str = "POST") -> dict:
        text = str(raw_comment.get('text', ''))[:2000]
        texto_limpo = self._limpar_texto(text)
        
        id_externo = str(raw_comment.get('id', ''))
        if not id_externo or id_externo == 'None':
             hash_input = f"{getattr(self, 'current_target', 'unknown')}_{content_type}_{text}"
             id_externo = f"ig_gen_{hashlib.md5(hash_input.encode()).hexdigest()[:16]}"

        namespace = uuid.NAMESPACE_URL
        id_interno = str(uuid.uuid5(namespace, f"instagram.com/{id_externo}"))
        
        return {
            'id': id_interno,
            'id_externo': id_externo,
            'texto_bruto': text,
            'texto_limpo': texto_limpo, 
            'autor_username': str(raw_comment.get('ownerUsername', 'unknown')),
            'candidato_id': getattr(self, 'current_target', 'unknown'),
            'data_coleta': raw_comment.get('timestamp') or datetime.now(timezone.utc).isoformat(),
            'plataforma': 'instagram',
            'rede_social': 'instagram',
            'processado_ia': False,
            'tipo_conteudo': content_type,
            'confidence_score': 0,
            'evidence_extracted': None
        }
```

Atualize também o método `run` para usar um delay otimizado e descartar dados inócuos:
Busque pela linha `sleep_time = random.uniform(2.0, 5.0)` e mude para:

```python
            # 2. Rate Limiting Humano Otimizado (-25% tempo total médio)
            sleep_time = random.uniform(1.5, 3.5)
```

No método `_scrape_section`, adicione o filtro para descartar imediatamente comentários vazios após a limpeza:

```python
        comments = []
        for rc in raw_data:
            texto = rc.get('text', '')
            texto_limpo = self._limpar_texto(texto)
            if not texto_limpo or not is_valid_comment(texto):
                continue
            
            content_type = "REEL" if section == "reels" else "POST"
            comments.append(self._sanitize_comment(rc, content_type))
            
        return comments
```

- [ ] **Step 2: Commit**

```bash
git add app/workers/instagram_worker.py
git commit -m "perf: optimize InstagramWorker delay and embed pre-validation"
```

### Task 3: Atualizar o Motor de IA e Classificação para Extrair Indício e Score

**Files:**
- Modify: `core/classification_service.py`
- Modify: `core/ai_service.py`

- [ ] **Step 1: Atualizar o System Prompt**

No arquivo `core/classification_service.py`, atualize a string de retorno do `get_system_prompt()`:

```python
    def get_system_prompt(self) -> str:
        """Retorna o System Prompt baseado no MCF v2.0 definitivo."""
        manual = self._load_manual()
        return f"""
Você é um Analista de Linguística Analítica do Sistema Sentinela Democrática.
Siga RIGOROSAMENTE o manual abaixo para classificar os comentários.

{manual}

IMPORTANTE: Toda resposta DEVE ser um JSON válido contendo obrigatoriamente as chaves:
- "is_hate" (boolean)
- "categoria_ia" (string, usar "NEUTRO" se não houver risco)
- "confidence_score" (int de 0 a 100)
- "evidence_extracted" (string com o trecho exato que justifica a classificação, ou vazio)
"""
```

- [ ] **Step 2: Atualizar o Parser de Veredito**

Na função `parse_verdict` em `core/classification_service.py`, adicione os novos campos no dicionário retornado:

```python
            return {
                "id": data.get("id"),
                "category": cat,
                "categoria_ia": cat,
                "is_hate": is_hate,
                "rotulo": "hate" if is_hate else "not_hate",
                "direcao_odio": data.get("direcao_odio"),
                "ccf_density": float(data.get("ccf_density", 0.0)),
                "ccf_sync": float(data.get("ccf_sync", 0.0)),
                "ccf_performativity": float(data.get("ccf_performativity", 0.0)),
                "confidence": float(data.get("confidence_score", data.get("confianca_ia", 0))),
                "confianca_ia": float(data.get("confidence_score", data.get("confianca_ia", 0))),
                "confidence_score": int(data.get("confidence_score", 0)),
                "evidence_extracted": str(data.get("evidence_extracted", data.get("reason", ""))),
                "reason": str(data.get("evidence_extracted", data.get("reason", "Análise PASA v42"))),
                "pasa_version": self.VERSION
            }
```

- [ ] **Step 3: Garantir que a persistência inclua as colunas**

No arquivo `core/ai_service.py`, na função `run_batch_classification()`, certifique-se de que os novos campos sejam enviados na atualização (ao final do batch):

Mude a seção `updates.append(...)` para:

```python
                updates.append({
                    "id": c['id'],
                    "is_hate": res.get('is_hate', False),
                    "categoria_ia": res.get('categoria_ia', 'NEUTRO'),
                    "direcao_odio": res.get('direcao_odio'),
                    "ccf_density": res.get('ccf_density', 0.0),
                    "ccf_sync": res.get('ccf_sync', 0.0),
                    "ccf_performativity": res.get('ccf_performativity', 0.0),
                    "confianca_ia": res.get('confianca_ia', 0.0),
                    "confidence_score": res.get('confidence_score', 0),
                    "evidence_extracted": res.get('evidence_extracted', ''),
                    "processado_ia": True if engine != 'fail' else False
                })
```

- [ ] **Step 4: Commit**

```bash
git add core/classification_service.py core/ai_service.py
git commit -m "feat(ai): enforce structured JSON with confidence_score and evidence_extracted"
```

### Task 4: Atualizar UI/UX Profissional no Frontend

**Files:**
- Modify: `src/core/app.js`

- [ ] **Step 1: Incluir colunas no fetch de comentários**

Na função `fetchComments`, atualize o `.select()` para buscar as novas colunas:

```javascript
        const { data: comments, error } = await supabase
            .from('comentarios')
            .select('id,id_externo,autor_username,texto_limpo,texto_bruto,data_coleta,data_publicacao,is_hate,categoria_ia,direcao_odio,confianca_ia,confidence_score,evidence_extracted,processado_ia,candidato_id,plataforma')
            .order('data_coleta', { ascending: false })
            .limit(100);
```

- [ ] **Step 2: Renderizar Indícios e Score Visualmente**

No método `renderCommentCard(comment)`, ajuste a lógica do confidence e a renderização do HTML para exibir a evidência com design profissional:

```javascript
    // No início do método, use confidence_score preferencialmente
    const confidence = comment.confidence_score !== undefined && comment.confidence_score !== null 
        ? comment.confidence_score 
        : (comment.confianca_ia ? (comment.confianca_ia * 100).toFixed(1) : 0);
    
    // ...

    // Dentro do bloco if (comment.is_hate === true && comment.categoria_ia)
    // Adicione a renderização da evidência, se existir
    let evidenceHtml = '';
    if (comment.is_hate === true && comment.evidence_extracted) {
        evidenceHtml = `
            <div class="mt-3 bg-white bg-opacity-50 rounded p-3 border border-danger-100">
                <p class="text-xs font-semibold text-danger-800 mb-1 flex items-center gap-1">
                    <i data-lucide="microscope" class="w-3 h-3"></i> Indício Analítico:
                </p>
                <p class="text-xs text-danger-900 italic font-medium">"${comment.evidence_extracted}"</p>
            </div>
        `;
    }

    // No retorno (return `...`), ajuste o quoteClass e insira o evidenceHtml:
    return `
        <div class="post-card hover:shadow-lg transition-shadow duration-200">
            <div class="flex">
                <div class="w-1 ${borderColor} flex-shrink-0"></div>
                <div class="flex-1 p-5">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-base-100 flex items-center justify-center text-xs font-bold text-base-500 overflow-hidden">
                                <img src="/assets/sentinela_small.webp" class="w-full h-full object-cover">
                            </div>
                            <div>
                                <span class="text-sm font-bold text-base-800"> @${comment.autor_username || 'Anônimo'}</span>
                                <span class="text-xs font-bold ${badgeClass} px-2 py-0.5 rounded-full uppercase tracking-wider">
                                    ${badgeText}
                                </span>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="text-xs font-mono text-base-400 block">
                                ${timeAgo(timestamp)}
                            </span>
                            <div class="flex flex-col items-end mt-1">
                                <span class="text-[10px] font-bold ${confidenceClass} block">
                                    Confiança: ${confidence}%
                                </span>
                                <div class="w-16 h-1.5 bg-base-200 rounded-full mt-1 overflow-hidden">
                                    <div class="h-full ${confidenceClass.replace('text-', 'bg-')}" style="width: ${confidence}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="${quoteClass} border-l-2 rounded-r-lg p-4 mb-4">
                        <p class="text-sm italic leading-relaxed">"${text}"</p>
                        ${evidenceHtml}
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-4">
                            <span class="flex items-center gap-1 text-xs font-bold uppercase ${iconColor}">
                                <i data-lucide="shield-alert" class="w-3 h-3"></i> 
                                ${comment.categoria_ia || 'N/A'}
                            </span>
                            <span class="flex items-center gap-1 text-xs font-bold text-base-400 uppercase">
                                <i data-lucide="share-2" class="w-3 h-3"></i> 
                                ${(comment.candidato_id || 'IG')}
                            </span>
                        </div>
                        ${comment.is_hate === true ? `
                            <div class="flex gap-2">
                                <button onclick="window.auditComment('${comment.id}', 'not_hate')" 
                                        class="btn btn-sm btn-outline text-xs h-8 px-2">
                                    Falso Positivo
                                </button>
                                <button onclick="window.auditComment('${comment.id}', 'hate')" 
                                        class="btn btn-sm btn-primary text-xs h-8 px-2">
                                    Padrão Ouro
                                </button>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
```

- [ ] **Step 3: Commit**

```bash
git add src/core/app.js
git commit -m "ui: implement professional display for confidence score and analytical evidence"
```
