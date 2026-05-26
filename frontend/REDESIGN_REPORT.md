# 📰 Redesign Frontend Sentinela - UX/UI Report

## Visão Geral

Transformação do frontend de "War Room Tático" para **"Centro de Informação Cívica"** que melhor reflete a função informativa do Sentinela Democrática.

---

## Problema Identificado

### Frontend Atual
- **Ton**: "Operacional", "Tático", "Militar" (PASA v54, war room)
- **Público-alvo**: Peritos/analistas técnicos
- **Design**: Muito tecnicista, pouco acessível
- **Narrativa**: Dados brutos sem contexto

### Por Que Isso Não Funciona

Sentinela é um projeto de **vigilância cívica e transparência democrática**, não um sistema operacional. O público-alvo deveria incluir:

✅ Jornalistas investigativos
✅ Pesquisadores acadêmicos  
✅ Ativistas e sociedade civil
✅ Cidadãos comuns interessados em transparência

**Todos precisam entender os dados e seus significados**, não apenas técnicos.

---

## Solução Proposta: "Newsroom Informativo"

### Mudanças Principais

#### 1️⃣ **Hierarquia de Informação**
```
ANTES: Dados brutos → Tabelas → Gráficos
DEPOIS: Headline → Contexto → Insight → Dados → Ação
```

**Novo componente**: `NewsHeader` (manchete informativa, não "operacional")

#### 2️⃣ **Destaques do Dia com Narrativa**
```
ANTES: Alertas em tabelas tácticas
DEPOIS: Cards com histórias, contexto e palavras-chave
```

**Novo componente**: `HighlightCards` (jornalístico, visual, educativo)

#### 3️⃣ **Timeline Temporal (Storytelling)**
```
ANTES: Eventos desconexos
DEPOIS: Linha cronológica que mostra progressão e padrões
```

**Novo componente**: `EventTimeline` (narrativa temporal clara)

#### 4️⃣ **Insights Educativos (Explicação)**
```
ANTES: "Confiança: 85%" (sem contexto)
DEPOIS: Insight + Confiança + Contas Envolvidas + Ação
```

**Novo componente**: `InsightBox` (educativo, não técnico)

#### 5️⃣ **Perfis de Candidatos (Contexto)**
```
ANTES: Nenhum perfil ou contexto
DEPOIS: Bio, métricas, tendências, alertas recentes
```

**Novo componente**: `CandidateProfile` (humanizado, contextualizado)

#### 6️⃣ **Transparência Metodológica**
```
ANTES: Nada explicado
DEPOIS: Seção sobre limites, metodologia e responsabilidades
```

**Novo componente**: `MethodologyBox` (honestidade sobre limites)

#### 7️⃣ **Mudanças Visuais**

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Tom** | "PASA v54.0 - Módulo de Inteligência" | "Observatório de Discurso Cívico" |
| **Cor Primária** | Tática (verde/vermelho em preto) | Editorial (azul/emerald em azul-escuro) |
| **Tipografia** | Mono (código) | Mix (headlines sem-serifa, corpo sans) |
| **Ícones** | Militares/técnicos | Emojis informativos (📰 📊 🚨 👤) |
| **Linguagem** | Técnica, jargão | Acessível, explicativa |
| **Cards** | Brutais, densos | Respiros, hierarquia clara |

---

## Componentes Criados

### 1. `NewsHeader.tsx` 
**Propósito**: Manchete principal + contexto do dia
- Headline atrativo
- Pequenas estatísticas (alertas, monitorados, posts)
- Destaque do dia com severidade

**Uso**:
```tsx
<NewsHeader 
  todayHighlight={{ title: "...", description: "...", severity: "critical" }}
  stats={{ todayAlerts: 47, candidatesMonitored: 312, newPosts: 45628 }}
/>
```

### 2. `HighlightCards.tsx`
**Propósito**: Destaques do dia em formato jornalístico
- Título intrigante
- Resumo do que aconteceu
- Palavras-chave mais frequentes
- Contagem de alertas
- Severidade visual

**Uso**:
```tsx
<HighlightCards stories={[
  { 
    title: "Pico de 340% em posts com linguagem de ódio",
    summary: "Campanha intensificou discurso hostil...",
    topWords: ["ódio", "violência"],
    severity: "critical"
  }
]}/>
```

### 3. `EventTimeline.tsx`
**Propósito**: Cronograma de eventos com narrativa temporal
- Visualização de progressão (linha temporal)
- Conexão entre eventos
- Contexto temporal explícito
- Filtros por período (24h, 7d, 30d)

**Uso**:
```tsx
<EventTimeline 
  events={[...]}
  period="24h"
/>
```

### 4. `InsightBox.tsx`
**Propósito**: Explicação educativa de padrões
- Tipo de insight (tendência, anomalia, padrão, alerta)
- Descrição em linguagem simples
- Insights com "💡 Insight: ..."
- Confiança e fontes
- Candidatos envolvidos

**Uso**:
```tsx
<InsightBox
  type="trend"
  title="Discurso de Ódio em Crescimento"
  insight="Correlaciona com intensificação da campanha"
  confidence={92}
  sources={12400}
/>
```

### 5. `CandidateProfile.tsx`
**Propósito**: Contexto humanizado de cada candidato
- Avatar/foto
- Bio
- Métricas principais com tendências (📈📉)
- Alertas recentes
- Data de monitoramento

**Uso**:
```tsx
<CandidateProfile
  candidateName="João Silva"
  party="Partido X"
  metrics={[{ label: "Posts", value: 1240 }]}
  recentAlerts={[...]}
/>
```

### 6. `MethodologyBox.tsx`
**Propósito**: Transparência sobre como o projeto funciona
- O que fazemos
- Limitações importantes
- Metodologia técnica
- Links para documentação

**Uso**:
```tsx
<MethodologyBox />
```

### 7. `page-novo.tsx` (Nova Home)
**Propósito**: Integração de todos os componentes em fluxo informativo
- Seções bem definidas
- Fluxo narrativo claro
- CTAs para outras ferramentas
- Footer com links

---

## Fluxo de Usuário Redesenhado

### Antes (War Room)
```
Entra no site
    ↓
"PASA v54.0 - Panorama Operacional"
    ↓
Vê tabelas numéricas denso
    ↓
Confuso: "O que isso significa?"
    ↓
Sai ou vai direto para Perícia (pular home)
```

### Depois (Newsroom)
```
Entra no site
    ↓
"Tendências no Discurso Político Brasileiro"
    ↓
Vê headlines atrativas e contexto
    ↓
Explore: "Pico de 340% em ódio detectado"
    ↓
Entende: "João Silva intensificou discurso hostil"
    ↓
Decide: Clicar em perfil, relatório ou análise forense
```

---

## Paleta de Cores Redesenhada

### Antes (Tático)
- Fundo: `#020817` (preto)
- Destaque: `#10b981` (verde tático)
- Perigo: `#f87171` (vermelho)
- Superfície: `#0f172a` (azul-escuro brutal)

### Depois (Editorial)
- Fundo: `#020617` → `#0f172a` gradient (mais cinzas)
- Destaque: `#3b82f6` (azul informativo)
- Sucesso: `#10b981` (verde, mas menos dominante)
- Perigo: `#ef4444` (vermelho mais ameno)
- Avisos: `#f59e0b` (âmbar)
- Superfície: `#1e293b` (cinza-azulado, menos agressivo)

---

## Padrões de Design Aplicados

### 1. Progressive Disclosure
Mostra o essencial primeiro, permite exploração profunda depois.

### 2. Visual Hierarchy
- H1: Manchetes
- H2: Seções
- H3: Artigos
- Corpo: Descrição
- Notas: Meta-informação

### 3. Data Storytelling
Transforma dados em narrativa:
- "34% ódio" → "Discurso de Ódio em Crescimento 28%"
- "847 contas" → "Padrão de Coordenação Detectado com 847 contas"

### 4. Affordances Claras
- Botões dizem exatamente o que fazem
- Links são subcores (azul)
- Avisos têm ícones diferenciados

### 5. Micro-interações
- Cards mudam cor ao hover
- Ícones expressam tom (📰 = jornalístico, 🔬 = análise, ⚠️ = alerta)

---

## Implementação Passo a Passo

### Fase 1: Componentes Base ✅ FEITO
- [x] NewsHeader.tsx
- [x] HighlightCards.tsx
- [x] EventTimeline.tsx
- [x] InsightBox.tsx
- [x] CandidateProfile.tsx
- [x] MethodologyBox.tsx

### Fase 2: Integração
- [ ] Trocar `app/page.tsx` pelo novo `page-novo.tsx`
- [ ] Atualizar `layout.tsx` metadata
- [ ] Adaptar Sidebar para novo tom
- [ ] Testar responsividade

### Fase 3: Conexão com Backend
- [ ] Conectar NewsHeader aos dados reais
- [ ] Popular HighlightCards com API
- [ ] Carregar EventTimeline do banco
- [ ] Trazer CandidateProfile data
- [ ] Atualizar stats em tempo real

### Fase 4: Refinamentos
- [ ] Testes de acessibilidade (WCAG)
- [ ] Performance (Lighthouse)
- [ ] Responsividade mobile
- [ ] Temas claro/escuro

---

## Mudanças na Sidebar

### Antes
```
PANORAMA (tático)
PERÍCIA (técnico)
ALVOS (administrativo)
ALERTAS (operacional)
REDE (tecnicista)
DOSSIÊS (burocrático)
```

### Depois
```
🏠 INICIO (home informativa)
📊 ANÁLISE (forense, mas educativa)
👥 CANDIDATOS (perfis e contexto)
🚨 ALERTAS (contextualizados)
🌐 TENDÊNCIAS (timeline global)
📁 RELATÓRIOS (gerar dossiês)
```

---

## Benefícios do Redesign

### Para Jornalistas
✅ Histórias prontas para investigação
✅ Contexto imediato
✅ Dados confiáveis com metodologia clara

### Para Pesquisadores
✅ Dados bem organizados
✅ Insights automatizados
✅ Facilita hipóteses iniciais

### Para Ativistas
✅ Educativo, não técnico
✅ Claro sobre limitações
✅ Ação imediata (alertas, compartilhar)

### Para Cidadãos
✅ Acessível e compreensível
✅ Explica conceitos
✅ Encoraja leitura crítica

---

## Próximos Passos

1. **Teste com usuários reais**: Mostrar prototipo para jornalistas/pesquisadores
2. **Integração com API**: Trazer dados reais
3. **Mobilidade**: Testar em smartphone/tablet
4. **Acessibilidade**: Validar WCAG AA
5. **Performance**: Otimizar imagens, código-split

---

## Arquivos Criados

```
frontend/components/home/
├── NewsHeader.tsx
├── HighlightCards.tsx
├── EventTimeline.tsx
├── InsightBox.tsx
├── CandidateProfile.tsx
└── MethodologyBox.tsx

frontend/app/
├── page-novo.tsx (novo, pronto para teste)
└── page.tsx (mantém para comparação)
```

---

**Próxima ação**: Você quer testar agora substituindo `page.tsx`, ou prefere fazer ajustes antes?
