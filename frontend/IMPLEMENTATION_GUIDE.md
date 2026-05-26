# 🚀 Guia de Implementação - Sentinela Newsroom UX/UI

## Resumo Executivo

Você recebeu:
- ✅ 6 componentes React novos (NewsHeader, HighlightCards, EventTimeline, InsightBox, CandidateProfile, MethodologyBox)
- ✅ Nova página home (`page-novo.tsx`) com fluxo informativo completo
- ✅ Documentação visual e de design (este arquivo)
- ✅ Relatório UX/UI detalhado

**Próxima ação**: Ativar o novo design substituindo `app/page.tsx` ou testando em paralelo.

---

## 🎯 Objetivo

Transformar o frontend de **"War Room Tático"** para **"Centro de Informação Cívica"** que reflete a função informativa real do Sentinela Democrática.

---

## 📦 O Que Você Tem

### Componentes Criados

```
frontend/components/home/
├── NewsHeader.tsx              # Manchete + stats do dia
├── HighlightCards.tsx          # Destaques em formato jornalístico
├── EventTimeline.tsx           # Cronograma de eventos
├── InsightBox.tsx              # Análises educativas
├── CandidateProfile.tsx        # Perfis humanizados de candidatos
└── MethodologyBox.tsx          # Transparência metodológica
```

### Páginas

```
frontend/app/
├── page.tsx                    # Home ATUAL (war room)
└── page-novo.tsx               # Home NOVA (newsroom) ← pronto para testar
```

### Documentação

```
frontend/
├── REDESIGN_REPORT.md          # Análise completa do problema/solução
├── REDESIGN_VISUAL_GUIDE.md    # Guia visual de layout e componentes
└── IMPLEMENTATION_GUIDE.md     # Este arquivo
```

---

## 🧪 Como Testar

### Opção 1: Teste em Paralelo (RECOMENDADO)

Mantenha ambas as versões ativas:

```bash
# 1. Abra dois terminais

# Terminal 1: Frontend rodando
cd frontend
npm run dev
# Acessa http://localhost:3000 → page.tsx (atual)

# 2. Em outro navegador/aba:
# Para ver o novo design sem substituir:
# Crie um arquivo temporário:

# Terminal 2:
cd frontend
# Crie uma rota temporária para testar
cat > app/preview/page.tsx << 'EOF'
// Copie conteúdo de page-novo.tsx aqui
EOF

npm run dev
# Acessa http://localhost:3000/preview → page-novo.tsx (novo)
```

### Opção 2: Substituição Completa

Se quiser ativar já:

```bash
cd frontend

# Backup da versão atual
cp app/page.tsx app/page-old.tsx

# Ativar novo design
cp app/page-novo.tsx app/page.tsx

# Remover arquivo temporário
rm app/page-novo.tsx

npm run dev
# Acessa http://localhost:3000 → novo design
```

### Opção 3: Git/Branches (MAIS SEGURO)

```bash
# Crie branch para testar
git checkout -b feature/newsroom-redesign

# Substitua
cp app/page-novo.tsx app/page.tsx
rm app/page-novo.tsx

# Commit
git add -A
git commit -m "feat: ativar novo design informativo (newsroom)"

# Voltar ao antigo se precisar
git checkout main
```

---

## 🔧 Próximos Passos de Implementação

### Fase 1: Estrutura ✅ FEITO

Componentes estruturais criados e page nova pronta.

**Arquivos criados**:
- NewsHeader.tsx
- HighlightCards.tsx
- EventTimeline.tsx
- InsightBox.tsx
- CandidateProfile.tsx
- MethodologyBox.tsx
- page-novo.tsx

### Fase 2: Integração com API (AGORA)

Substituir dados mockados pelos reais:

#### 2.1 NewsHeader - Trazer stats reais

**Arquivo**: `frontend/app/page.tsx` ou `components/home/NewsHeader.tsx`

**Antes (mock)**:
```tsx
const [stats, setStats] = useState({
  todayAlerts: 47,
  candidatesMonitored: 312,
  newPosts: 45628,
});
```

**Depois (com API)**:
```tsx
import { useQuery } from '@tanstack/react-query';

export default function NewsHeader() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/stats');
      return res.json();
    },
  });

  return (
    <div>
      <div className="text-3xl">{stats?.todayAlerts || 0}</div>
      {/* resto ... */}
    </div>
  );
}
```

#### 2.2 HighlightCards - Trazer destaques

**Arquivo**: `components/home/HighlightCards.tsx`

**Endpoint esperado**: `GET /api/v1/dashboard/highlights`

**Resposta esperada**:
```json
[
  {
    "id": "1",
    "candidate": "João Silva",
    "title": "Pico de 340% em ódio",
    "summary": "...",
    "alertCount": 2843,
    "severity": "critical",
    "timestamp": "2024-05-26T14:32:00",
    "topWords": ["ódio", "violência"]
  }
]
```

**Implementação**:
```tsx
const { data: stories = [] } = useQuery({
  queryKey: ['highlights'],
  queryFn: () => fetch('/api/v1/dashboard/highlights').then(r => r.json()),
  refetchInterval: 60000, // atualiza a cada minuto
});
```

#### 2.3 EventTimeline - Trazer eventos

**Endpoint**: `GET /api/v1/dashboard/events?period=24h`

**Resposta**:
```json
[
  {
    "id": "1",
    "timestamp": "2024-05-26T14:32:00",
    "candidate": "João Silva",
    "title": "Pico detectado",
    "description": "...",
    "alertLevel": "critical",
    "postsCount": 2843,
    "engagementMetric": 75
  }
]
```

#### 2.4 CandidateProfile - Trazer dados de candidatos

**Endpoint**: `GET /api/v1/candidates`

**Resposta**:
```json
[
  {
    "id": "1",
    "name": "João Silva",
    "party": "Partido X",
    "position": "Senador",
    "bio": "...",
    "metrics": [
      { "label": "Posts Monitorados", "value": 1240, "trend": "up" }
    ],
    "recentAlerts": [...]
  }
]
```

### Fase 3: Refinamento Visual (OPICIONAL)

Se quiser ajustar cores ou componentes:

#### 3.1 Cores da Paleta

**Arquivo**: `frontend/app/globals.css` ou `tailwind.config.ts`

Adicione customizações:
```css
:root {
  /* Editorial Colors */
  --color-editorial-primary: #3b82f6; /* azul */
  --color-editorial-success: #10b981;
  --color-editorial-warning: #f59e0b;
  --color-editorial-danger: #ef4444;
}
```

#### 3.2 Tipografia

Se quiser mudar fonts (recomendo manter Inter):

```tsx
// app/layout.tsx
import { Inter, Playfair_Display } from 'next/font/google';

const serif = Playfair_Display({ subsets: ['latin'] }); // Headlines
const sans = Inter({ subsets: ['latin'] }); // Corpo
```

#### 3.3 Componentes Customizados

**Se precisar mudar estilo de um card**:

```tsx
// Antes (vermelho brilhante)
className="bg-red-500/10 border-red-500/30"

// Depois (mais suave)
className="bg-red-500/5 border-red-500/20"
```

---

## 📊 Checklist de Integração

- [ ] **Fase 1 - Estrutura**
  - [x] NewsHeader.tsx criado
  - [x] HighlightCards.tsx criado
  - [x] EventTimeline.tsx criado
  - [x] InsightBox.tsx criado
  - [x] CandidateProfile.tsx criado
  - [x] MethodologyBox.tsx criado
  - [x] page-novo.tsx pronto

- [ ] **Fase 2 - Integração API**
  - [ ] NewsHeader conectado a `/api/v1/dashboard/stats`
  - [ ] HighlightCards conectado a `/api/v1/dashboard/highlights`
  - [ ] EventTimeline conectado a `/api/v1/dashboard/events`
  - [ ] CandidateProfile conectado a `/api/v1/candidates`
  - [ ] Dados atualizando em tempo real

- [ ] **Fase 3 - Testes**
  - [ ] Layout responsivo em mobile/tablet/desktop
  - [ ] Performance (Lighthouse > 85)
  - [ ] Sem erros no console
  - [ ] Acessibilidade WCAG AA

- [ ] **Fase 4 - Deploy**
  - [ ] Substituir page.tsx (ou manter em branch)
  - [ ] Testar em staging
  - [ ] Fazer deploy em produção

---

## 🎨 Customização Avançada

### Mudar Headlines

**NewsHeader.tsx**:
```tsx
<h1 className="text-5xl font-bold text-white leading-tight">
  Tendências no Discurso Político Brasileiro
</h1>
```

Mude para:
```tsx
<h1 className="text-5xl font-bold text-white leading-tight">
  Monitor de Transparência Cívica
</h1>
```

### Mudar Ícones

**HighlightCards.tsx**: Está usando strings simples:
```tsx
<h2 className="text-2xl font-bold text-white">📰 Destaques Hoje</h2>
```

Para usar lucide-react icons:
```tsx
import { Newspaper } from 'lucide-react';

<Newspaper className="w-6 h-6" />
```

### Mudar Cores de Severidade

**HighlightCards.tsx**:
```tsx
const getSeverityStyle = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-500/10 border-red-500/30'; // ← mude aqui
    // ...
  }
};
```

---

## 🐛 Troubleshooting

### Erro: "Cannot find module NewsHeader"

**Solução**:
```bash
# Verifique se o caminho está correto
ls frontend/components/home/NewsHeader.tsx

# Se não existir, o arquivo pode estar em outro lugar
find . -name "NewsHeader.tsx"
```

### Componentes não carregando dados

**Solução**:
```tsx
// Adicione console.log para debugar
console.log('Stats:', stats);
console.log('Loading:', isLoading);
console.log('Error:', error);

// Verifique se a query está correta
const { data, error, isLoading } = useQuery({
  queryKey: ['key-name'],
  queryFn: async () => { /* ... */ }
});
```

### Layout quebrado em mobile

**Solução**:
```tsx
// Adicione breakpoints Tailwind
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* Conteúdo */}
</div>
```

### Performance lenta

**Solução**:
```tsx
// Use lazy loading para images
import Image from 'next/image';
import dynamic from 'next/dynamic';

// Lazy load componentes pesados
const CandidateProfile = dynamic(() => import('./CandidateProfile'), {
  loading: () => <div>Carregando...</div>
});
```

---

## 📚 Referências

- [Next.js 16 Docs](https://nextjs.org/docs)
- [React Query (TanStack Query) Docs](https://tanstack.com/query/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Lucide React Icons](https://lucide.dev/)

---

## 🎯 Success Metrics

Após implementação, você deve ter:

✅ **Página Home Informativa**
- Manchete clara sobre função do Sentinela
- Destaques do dia em formato jornalístico
- Explicações educativas, não apenas dados

✅ **Melhor Acessibilidade**
- Público além de técnicos/analistas
- Linguagem clara e contextual
- Navegação intuitiva

✅ **Dados Narrativos**
- Histórias ao invés de números puros
- Insights explicados
- Padrões claramente identificados

✅ **Transparência**
- Metodologia visível
- Limitações reconhecidas
- Responsabilidade clara

---

## 🚀 Deploy

### Vercel (Configurado)

```bash
# Push para main/production
git add -A
git commit -m "feat: ativar novo design newsroom"
git push origin main

# Vercel fará deploy automático
# Monitore em https://vercel.com/dashboard
```

### Manual Check

```bash
# Antes de fazer push
npm run build
npm run start

# Testar localmente
curl http://localhost:3000
```

---

## 💬 Feedback e Iteração

Após ativar o novo design:

1. **Colete feedback** de usuários reais
2. **Meça métricas**: Cliques, tempo na página, bounce rate
3. **Itere**: Faça ajustes baseado em dados
4. **A/B teste**: Se necessário, compare com versão anterior

---

## 📞 Suporte

Se tiver dúvidas durante implementação:

1. Revise `REDESIGN_REPORT.md` para contexto completo
2. Veja `REDESIGN_VISUAL_GUIDE.md` para referência visual
3. Verifique código dos componentes (`frontend/components/home/`)
4. Execute testes: `npm run dev` e explore localmente

---

**Status**: 🟢 Pronto para implementação

**Próximo passo**: Escolha entre teste em paralelo (opção 1) ou ativar direto (opção 2).
