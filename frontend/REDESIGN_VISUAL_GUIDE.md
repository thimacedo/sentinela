# 🎨 Guia Visual do Redesign - Sentinela Newsroom

## Layout Estrutural

```
┌─────────────────────────────────────────────────────────────────┐
│ [Logo] Sentinela                    🔍 🔔 ⚙️  Logout         │ ← Sidebar (Redesenhada)
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 📊 Observatório de Discurso Cívico                              │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                   │
│ Tendências no Discurso Político Brasileiro                       │ ← NewsHeader
│                                                                   │
│ Acompanhe em tempo real os padrões de discurso de ódio...       │
│                                                                   │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ ⚠️ 47 Alertas│ │ 👥 312 Monit.│ │ 📈 45.6k Posts           │ ← Stats Boxes
│ │ Críticos     │ │ Ativos       │ │ Em 24h       │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🚨 CRÍTICO                                                  │ │
│ │ Pico de 340% em discurso de ódio detectado                  │ │
│ │ João Silva amplificou significativamente linguagem hostil    │ │
│ │ nas últimas 48 horas. 2.843 posts com marcadores críticos.  │ │
│ │ [Ver Detalhes] [Compartilhar]                               │ │ ← Today's Highlight
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 📰 DESTAQUES HOJE                              [Ver tudo →]     │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [JO] João Silva                         [CRÍTICO]            │ │
│ │ Há 3 horas                                                   │ │
│ │                                                              │ │
│ │ Pico de 340% em posts com linguagem de ódio                │ │
│ │ Campanha intensificou discurso hostil contra grupo          │ │
│ │ específico. Análise detectou 2.843 posts críticos em 48h.  │ │
│ │                                                              │ │
│ │ [ódio] [violência] [retaliação] [extermínio]               │ │ ← HighlightCard
│ │                                                              │ │
│ │ 2.843 alertas         [Abrir análise →]                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [MS] Maria Santos                       [ALTO]               │ │
│ │ Há 5 horas                                                   │ │
│ │                                                              │ │
│ │ Padrão de desinformação coordenada identificado             │ │
│ │ Rede de contas amplifica narrativas falsas. Engajamento     │ │
│ │ artificial detectado.                                        │ │
│ │                                                              │ │
│ │ [mentira] [fake] [manipulação]                              │ │
│ │                                                              │ │
│ │ 1.240 alertas         [Abrir análise →]                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 🔬 ANÁLISES E INSIGHTS                                          │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📈 TENDÊNCIA                                                │ │
│ │ Discurso de Ódio em Crescimento                             │ │
│ │ Identificamos aumento consistente em posts com marcadores.  │ │
│ │                                                              │ │
│ │ ┌──────────────────────────────────────┐                   │ │
│ │ │ Aumento Semanal                      │                   │ │
│ │ │ 28%                                  │                   │ │ ← InsightBox
│ │ └──────────────────────────────────────┘                   │ │
│ │                                                              │ │
│ │ 💡 Insight: O crescimento correlaciona com intensificação  │ │
│ │ da campanha. Esperamos picos ainda maiores.                │ │
│ │                                                              │ │
│ │ Confiança: 92% | Fontes: 12.400 posts                       │ │
│ │ [Explorar dados completos →]                                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 📅 LINHA DO TEMPO                    [24h] [7d] [30d]          │
│                                                                   │
│ Cronograma de eventos (Últimas 24 Horas)                        │
│                                                                   │
│        ●─────                                                    │
│        │      14:32 - Hoje                                       │ ← EventTimeline
│        │      Pico detectado em comentários hostis               │
│        │      João Silva: +340% ódio                             │
│        │      2.843 posts | Engajamento: 75%                    │
│        │                                                          │
│        ●────                                                     │
│        │      10:15 - Hoje                                       │
│        │      Atividade coordenada em múltiplas contas           │
│        │      Maria Santos: 847 contas                           │
│        │      1.240 posts | Engajamento: 62%                    │
│        │                                                          │
│        ●                                                          │
│               Ontem 22:44                                         │
│               Normalização de linguagem agressiva                │
│               Pedro Costa: Série de posts progressivos           │
│               456 posts | Engajamento: 48%                      │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 👤 CANDIDATOS MONITORADOS                                       │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [Avatar] João Silva                              ✓ Ativo    │ │
│ │ Partido X • Senador                                          │ │
│ │ Monitorado desde: 15 de Janeiro de 2024                     │ │
│ │                                                              │ │
│ │ Político com 15 anos de carreira. Conhece-se por discurso   │ │
│ │ inflamado.                                                   │ │
│ │                                                              │ │
│ │ ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐          │ │ ← CandidateProfile
│ │ │Posts    │ │Alertas  │ │% Ódio    │ │Engajam.  │          │ │
│ │ │1.240 ↑  │ │23 ↑ 8%  │ │34% ↑ 5%  │ │68% →     │          │ │
│ │ │📈 15%   │ │         │ │          │ │          │          │ │
│ │ └─────────┘ └─────────┘ └──────────┘ └──────────┘          │ │
│ │                                                              │ │
│ │ ⚠️ ALERTAS RECENTES                                         │ │
│ │ 🚨 Pico de 340% em ódio             Há 3 horas             │ │
│ │ 🔴 Padrão coordenado detectado       Há 8 horas             │ │
│ │ ⚡ Aumento em linguagem agressiva    Há 16 horas            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 📖 SOBRE ESTE OBSERVATÓRIO                                      │
│                                                                   │
│ Sentinela monitora padrões de discurso para promover            │
│ transparência. Aqui você encontra análises sobre ódio,          │
│ violência e desinformação.                                       │
│                                                                   │
│ ✅ O Que Fazemos                   ⚠️ Limitações                │
│ • Coleta de posts públicos          • Não substitui análise     │
│ • Identificação de ódio             • Apenas contas públicas    │ ← MethodologyBox
│ • Relatórios forenses               • IA sujeita a erros        │
│ • Alertas contextualizados          • Não visa julgar           │
│                                                                   │
│ 💡 Metodologia                                                   │
│ Coleta: APIs de redes sociais                                    │
│ Processamento: Limpeza e análise semântica (Qwen 2.5)          │
│ Classificação: Protocolo PASA v50                               │
│ Atualização: Tempo real a cada 6 horas                          │
│                                                                   │
│ 📚 Documentação Técnica | 📊 Publicações                         │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 💭 QUER EXPLORAR MAIS?                                          │
│                                                                   │
│ [→ Ir para Perícia Forense] [→ Gerar Relatório] [→ Alertas]    │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Sentinela © 2024 | Transparência democrática                    │
│ Docs | Metodologia | Contato | Privacidade | GitHub             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Variações de Cards

### HighlightCard - Crítico
```
┌─ CRÍTICO ──────────────────────────────────┐
│ [Avatar] João Silva        [CRÍTICO Badge]  │
│ Há 3 horas                                  │
│                                             │
│ Pico de 340% em posts com linguagem de ódio│
│ Campanha intensificou discurso hostil...   │
│                                             │
│ [ódio] [violência] [retaliação]            │
│                                             │
│ 2.843 alertas    [Abrir análise →]         │
└─────────────────────────────────────────────┘
```
**Cor**: Fundo `bg-red-500/10` + Border `border-red-500/30` + Texto `text-red-400`

### HighlightCard - Alto
```
┌─ ALTO ─────────────────────────────────────┐
│ [Avatar] Maria Santos      [ALTO Badge]     │
│ Há 5 horas                                  │
│                                             │
│ Padrão de desinformação coordenada          │
│ Rede de contas amplifica narrativas falsas  │
│                                             │
│ [mentira] [fake] [manipulação]              │
│                                             │
│ 1.240 alertas    [Abrir análise →]         │
└─────────────────────────────────────────────┘
```
**Cor**: Fundo `bg-orange-500/10` + Border `border-orange-500/30` + Texto `text-orange-400`

---

## InsightBox Variações

### Tipo: TREND (Tendência)
```
📈 TENDÊNCIA │ Discurso de Ódio em Crescimento [TREND Badge]

Identificamos aumento consistente em posts com marcadores.

╔════════════════════════════╗
║ Aumento Semanal            ║
║ 28%                        ║
╚════════════════════════════╝

💡 Insight: O crescimento correlaciona com intensificação 
da campanha. Esperamos picos ainda maiores.

Confiança: 92% | Fontes: 12.400 posts
[Explorar dados completos →]
```
**Cor**: Azul (`text-blue-400`, `border-blue-500/30`)

### Tipo: ANOMALY (Anomalia)
```
⚠️ ANOMALIA │ Padrão de Coordenação Detectado [ANOMALY Badge]

Rede de 847 contas amplifica narrativa de forma não-orgânica.

╔════════════════════════════╗
║ Contas Envolvidas          ║
║ 847                        ║
╚════════════════════════════╝

💡 Insight: Recomendação: Investigar origem e financiamento.
Pode indicar operação coordenada.

Confiança: 87% | Fontes: 45.600 posts | Envolvidos: João Silva, Maria Santos
[Explorar dados completos →]
```
**Cor**: Vermelho (`text-red-400`, `border-red-500/30`)

---

## Stats Boxes (Top)

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ ⚠️ ALERTAS HOJE  │  │ 👥 MONITORADOS   │  │ 📈 POSTS 24H     │
│                  │  │                  │  │                  │
│ 47               │  │ 312              │  │ 45.628           │
│                  │  │                  │  │                  │
│ Casos críticos   │  │ Candidatos       │  │ Coletados        │
│ identificados    │  │ sob observação   │  │ em 24h           │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## Roadmap de Implementação Técnica

### 1. Backup e Comparação
```bash
# Manter versão anterior
cp frontend/app/page.tsx frontend/app/page-old.tsx

# Trocar para novo
cp frontend/app/page-novo.tsx frontend/app/page.tsx
```

### 2. Testes
```bash
npm run dev
# Abrir http://localhost:3000
# Verificar:
# - Todas as seções carregam
# - Responsividade mobile
# - Performance (Lighthouse)
```

### 3. Integração com API (Próximo)
```tsx
// Em NewsHeader.tsx, substituir mock por:
const { data: stats } = useQuery(
  ['dashboard-stats'],
  () => fetch('/api/v1/stats').then(r => r.json())
);

// Em HighlightCards.tsx:
const { data: highlights } = useQuery(
  ['highlights'],
  () => fetch('/api/v1/highlights').then(r => r.json())
);

// E assim por diante para cada componente...
```

---

## Checklist de Validação

### Visual
- [ ] Tipografia legível em todos os tamanhos
- [ ] Cores suficientemente contrastadas
- [ ] Ícones aparecem corretamente
- [ ] Espaçamento consistente
- [ ] Nenhum overflow de texto

### Funcional
- [ ] Todos os links funcionam
- [ ] Botões são clicáveis
- [ ] Navegação entre seções suave
- [ ] Sem erros no console
- [ ] Sem warnings não-essenciais

### Responsividade
- [ ] Mobile (320px)
- [ ] Tablet (768px)
- [ ] Desktop (1024px+)
- [ ] Tela ultra-wide (1440px+)

### Performance
- [ ] Lighthouse score > 85
- [ ] Primeira pintura < 1.5s
- [ ] Time to Interactive < 3.5s
- [ ] Sem layout shift (CLS)

### Acessibilidade
- [ ] Contraste mínimo WCAG AA (4.5:1)
- [ ] Teclado navegável
- [ ] Screen reader funcional
- [ ] Sem coisas "apenas visuais"

---

## Comparação: Antes vs. Depois

### Landing (Hero)
**ANTES**:
```
Status: Operacional
Panorama Operacional
SISTEMA SENTINELA // PASA v54.0
Módulo de Inteligência em Tempo Real
```

**DEPOIS**:
```
Observatório de Discurso Cívico
Tendências no Discurso Político Brasileiro
Acompanhe em tempo real os padrões de discurso de ódio...
```

### Tone of Voice
| Aspecto | Antes | Depois |
|---------|-------|--------|
| Primeiro parágrafo | Técnico, jargão | Acessível, contextual |
| Ícones | Nenhum ou genérico | Emojis expressivos |
| Terminologia | "módulo", "inteligência" | "observatório", "discurso" |
| Call-to-action | "Ver detalhes" | "Explorar análise forense" |
| Métricas | Números puros | Narrativas + números |

---

## Próximos Passos Imediatos

1. ✅ **Componentes criados** - NewsHeader, HighlightCards, EventTimeline, InsightBox, CandidateProfile, MethodologyBox
2. ✅ **Page-novo pronto** - Integração de todos os componentes
3. ⏳ **Testar localmente** - `npm run dev` e navegar
4. ⏳ **Conectar à API** - Trazer dados reais dos endpoints
5. ⏳ **Refinar UX** - Ajustes baseado em feedback
6. ⏳ **Deploy** - Fazer rollout da nova home

---

**Quer começar a testar agora? Execute:**
```bash
cd frontend
npm run dev
# Abra http://localhost:3000
```
