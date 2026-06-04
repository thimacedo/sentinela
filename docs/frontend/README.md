# Frontend Documentation — Sentinela Democrática

**Version**: 52.4.5  
**Framework**: Next.js 16.2.6 / React 19  
**Last Updated**: 2026-06-04

---

## 📋 Overview

Sentinela's frontend is a modern Next.js application that provides **real-time political intelligence monitoring** and **civic information** to researchers, journalists, and citizens.

### 🎯 Core Purpose

Transform raw intelligence data from the backend into accessible, actionable information for:
- **Researchers**: Analyzing political trends and discourse
- **Journalists**: Fact-checking and investigative reporting
- **Citizens**: Understanding political narratives and risks
- **Admins**: Managing system data and configurations

---

## 🏗️ Architecture Overview

```
frontend/
├── app/                      # Next.js App Router (pages)
│   ├── admin/               # Admin dashboard pages
│   ├── alertas/             # Alert management
│   ├── alvos/               # Target/person profiles
│   ├── analise/             # Analysis tools
│   ├── dossies/             # Dossier pages
│   ├── estatisticas/        # Statistics dashboards
│   ├── relatorios/          # Reports
│   ├── rede/                # Network visualization
│   ├── metodologia/         # Methodology documentation
│   └── page.tsx             # Home page
├── components/              # React components
│   ├── ui/                  # Base UI components (Button, Card, etc.)
│   ├── home/                # Home page components
│   ├── ads/                 # Advertisement components
│   ├── pricing/             # Pricing page components
│   └── warroom/             # War room interface
├── hooks/                   # Custom React hooks
├── lib/                     # Utility functions
├── public/                  # Static assets
└── styles/                  # Global styles (Tailwind)
```

### 🔄 Data Flow

```
User Interaction
      ↓
Component Event Handler
      ↓
Zustand State Management
      ↓
React Query (API Call)
      ↓
Backend API (FastAPI)
      ↓
Database (Supabase/PostgreSQL)
      ↓
Response
      ↓
State Update → Re-render
```

---

## 🛠️ Tech Stack

### Core Framework
| Tool | Version | Purpose |
|------|---------|---------|
| **Next.js** | 16.2.6 | Meta framework for React |
| **React** | 19.2.4 | UI library |
| **React DOM** | 19.2.4 | React rendering |
| **TypeScript** | 5.x | Type safety |

### State Management & Data Fetching
| Tool | Version | Purpose |
|------|---------|---------|
| **Zustand** | 5.0.13 | Lightweight state management |
| **React Query** | 5.100.11 | Server state management, caching, sync |
| **Supabase JS** | 2.106.0 | Backend integration |

### UI & Styling
| Tool | Version | Purpose |
|------|---------|---------|
| **Tailwind CSS** | 4.x | Utility-first CSS |
| **shadcn/ui** | 4.7.0 | Component library (Button, Card, Modal, etc.) |
| **Lucide React** | 1.16.0 | Icon library |
| **Recharts** | 3.8.1 | Data visualization |
| **React Force Graph** | 1.29.1 | Network graph visualization |

### Utilities
| Tool | Version | Purpose |
|------|---------|---------|
| **class-variance-authority** | 0.7.1 | Component style variants |
| **clsx** | 2.1.1 | Conditional className joining |
| **React Markdown** | 10.1.0 | Markdown rendering |
| **QR Code React** | 4.2.0 | QR code generation |

---

## 📦 Dependencies

### Installation
```bash
cd /workspace/frontend
npm install
```

### Key Dependencies Details

**React Query** (TanStack Query)
- Handles server state, caching, and synchronization
- Provides hooks like `useQuery`, `useMutation`
- Automatic refetching and background sync

**Zustand**
- Lightweight alternative to Redux
- Used for client state (UI state, user preferences)
- Simple hook-based API

**Supabase**
- PostgreSQL database client
- Built-in authentication
- Real-time subscriptions
- RLS (Row-Level Security) policies

---

## 🚀 Getting Started

### Development

```bash
# Install dependencies
npm install

# Set environment variables (see .env.local)
cp .env.example .env.local
# Edit .env.local with your API keys

# Run development server
npm run dev
# → Open http://localhost:3000
```

### Build for Production

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

---

## 📁 Directory Structure Details

### `app/` - Pages

Next.js App Router structure. Each folder = route, `page.tsx` = page content.

```
app/
├── admin/              # /admin/* - Admin dashboard
├── alertas/            # /alertas/* - Alert management
├── alvos/              # /alvos/* - Target profiles (searches, individuals)
├── analise/            # /analise/* - Analysis tools
├── dossies/            # /dossies/* - Dossier documents
├── estatisticas/       # /estatisticas/* - Statistics/dashboards
├── relatorios/         # /relatorios/* - Reports
├── rede/               # /rede/* - Network visualization
├── metodologia/        # /metodologia/* - Methodology docs
├── planos/             # /planos/* - Subscription plans
├── lgpd/               # /lgpd/* - Privacy policy
├── privacidade/        # /privacidade/* - Privacy notices
├── termos/             # /termos/* - Terms of service
├── layout.tsx          # Global layout wrapper
├── page.tsx            # Home page (/)
└── globals.css         # Global styles
```

### `components/` - Reusable Components

```
components/
├── ui/                 # Base UI components
│   ├── Button.tsx      # Button component
│   ├── Card.tsx        # Card component
│   ├── Modal.tsx       # Modal dialog
│   ├── Input.tsx       # Input field
│   └── ...             # Other base components
├── home/               # Home page components
│   ├── NewsHeader.tsx  # Headline section
│   ├── HighlightCards.tsx # Featured stories
│   ├── EventTimeline.tsx   # Event timeline
│   └── ...
├── pricing/            # Pricing page components
├── ads/                # Advertisement components
└── warroom/            # War room interface components
```

### `hooks/` - Custom React Hooks

Reusable logic extracted into hooks.

```
hooks/
├── useAuth.ts          # Authentication context
├── useAlerts.ts        # Alert management
├── useFetch.ts         # Data fetching helpers
└── ...
```

### `lib/` - Utility Functions

```
lib/
├── api.ts              # API client setup
├── constants.ts        # Constants
├── utils.ts            # Helper functions
└── supabase.ts         # Supabase client initialization
```

---

## 🔐 Authentication

### Flow

1. **Login**: User enters credentials
2. **Supabase Auth**: Credentials verified against Supabase auth
3. **JWT Token**: Access token returned
4. **Local Storage**: Token stored for API requests
5. **API Calls**: Token sent in `Authorization: Bearer` header
6. **Refresh**: Automatic refresh when expired

### Protected Routes

```typescript
// Example: Protected page component
import { useAuth } from '@/hooks/useAuth'

export default function AdminPage() {
  const { user, loading } = useAuth()
  
  if (loading) return <LoadingSpinner />
  if (!user) return <Redirect to="/login" />
  
  return <AdminDashboard />
}
```

---

## 📡 API Integration

### Backend URL

```
Development: http://localhost:8000
Production: https://api.sentinela.com
```

### Example API Calls

```typescript
// Using React Query
import { useQuery } from '@tanstack/react-query'

export function useTargets() {
  return useQuery({
    queryKey: ['targets'],
    queryFn: async () => {
      const response = await fetch('/api/v1/targets', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.json()
    }
  })
}

// In component
function TargetList() {
  const { data, isLoading, error } = useTargets()
  
  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>
  
  return (
    <ul>
      {data?.map(target => (
        <li key={target.id}>{target.name}</li>
      ))}
    </ul>
  )
}
```

---

## 🎨 Styling

### Tailwind CSS

- **Utility-first**: Use Tailwind classes directly in components
- **Config**: `tailwind.config.ts`
- **Global**: `app/globals.css`

### shadcn/ui Components

Pre-built, accessible components:

```typescript
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function Example() {
  return (
    <Card>
      <h2>Title</h2>
      <Button>Click me</Button>
    </Card>
  )
}
```

---

## ⚙️ Configuration Files

### `next.config.ts`
Next.js configuration (redirects, rewrites, etc.)

### `tailwind.config.ts`
Tailwind CSS theme customization

### `tsconfig.json`
TypeScript compiler options

### `.env.local`
Environment variables (development only)

```env
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📈 Performance Optimization

### Image Optimization
```typescript
import Image from 'next/image'

<Image
  src="/image.png"
  alt="Description"
  width={400}
  height={300}
/>
```

### Code Splitting
Next.js automatically splits code at page boundaries.

### Caching
React Query handles HTTP caching and deduplication.

---

## 🧪 Testing

Tests located in `__tests__/` directory.

```bash
npm test
```

---

## 🐛 Debugging

### Browser DevTools
- React DevTools: Inspect component tree
- Network tab: Monitor API calls
- Console: Check errors

### Logging
```typescript
console.log('Debug info:', data)
```

### Next.js Debug Mode
```bash
NODE_OPTIONS='--inspect' npm run dev
```

---

## 📝 Common Patterns

### Fetch Data with React Query
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['key'],
  queryFn: () => api.fetch('/endpoint')
})
```

### State Management with Zustand
```typescript
const useStore = create(set => ({
  count: 0,
  increment: () => set(state => ({ count: state.count + 1 }))
}))
```

### Protected Component
```typescript
const ProtectedComponent = ({ children }) => {
  const { user } = useAuth()
  return user ? children : <LoginRequired />
}
```

---

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm i -g vercel
vercel
```

### Docker
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci && npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

---

## 📚 Additional Resources

- **Next.js Docs**: https://nextjs.org/docs
- **React Docs**: https://react.dev
- **Tailwind CSS**: https://tailwindcss.com
- **shadcn/ui**: https://ui.shadcn.com
- **Supabase**: https://supabase.com/docs

---

## 📞 Support

For frontend-specific issues or questions, refer to:
1. Component documentation (see COMPONENTS.md)
2. Architecture details (see ARCHITECTURE.md)
3. API integration guide (see API_INTEGRATION.md)
