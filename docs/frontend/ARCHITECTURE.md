# Frontend Architecture — Sentinela Democrática

**Framework**: Next.js 16 with React 19  
**Architecture Pattern**: Component-based, Server/Client Components  
**State Management**: Zustand + React Query  

---

## 🏛️ Architecture Overview

### Architectural Layers

```
┌─────────────────────────────────────────────────────┐
│           PRESENTATION LAYER (UI)                   │
│  Pages, Components, Forms, Modals                   │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│       STATE MANAGEMENT LAYER                        │
│  Zustand (client state)  │  React Query (server)    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│           API INTEGRATION LAYER                     │
│  Fetch, Error Handling, Interceptors                │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│       BACKEND API (FastAPI/Python)                  │
│    http://localhost:8000/api/v1/*                   │
└─────────────────────────────────────────────────────┘
```

---

## 📱 Component Hierarchy

### Application Structure

```
App (layout.tsx + Providers)
├── Sidebar
├── Header
└── Main Content
    ├── Home (/page.tsx)
    ├── Admin (/admin/*)
    ├── Targets (/alvos/*)
    ├── Alerts (/alertas/*)
    ├── Analysis (/analise/*)
    └── Reports (/relatorios/*)
```

### Component Types

#### 1. **Page Components** (`app/**/page.tsx`)
- Route-specific containers
- Fetch initial data
- Layout wrapper

```typescript
// app/alvos/page.tsx
export default function TargetsPage() {
  return <TargetList />
}
```

#### 2. **Layout Components**
- Shared structure across routes
- Header, sidebar, footer

```typescript
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Sidebar />
        <main>{children}</main>
      </body>
    </html>
  )
}
```

#### 3. **Feature Components**
- Reusable feature modules
- Located in `components/`

```typescript
components/
├── TargetList.tsx      # Lists targets
├── TargetCard.tsx      # Single target display
└── TargetForm.tsx      # Create/edit target
```

#### 4. **Base/UI Components** (`components/ui/`)
- Atomic building blocks
- No business logic
- Reusable across features

```typescript
components/ui/
├── Button.tsx
├── Card.tsx
├── Input.tsx
├── Modal.tsx
└── Select.tsx
```

---

## 🔄 Data Flow

### Query Flow (Reading Data)

```
User Action
    ↓
useQuery Hook (React Query)
    ↓
GET /api/v1/targets
    ↓
Backend Processes
    ↓
Database Query
    ↓
Response + Caching (React Query)
    ↓
Component Re-render
    ↓
UI Update
```

**Example**:
```typescript
function TargetList() {
  // React Query handles caching, background refetch, etc.
  const { data: targets } = useQuery({
    queryKey: ['targets'],
    queryFn: fetchTargets
  })
  
  return <div>{targets?.map(t => <TargetCard key={t.id} {...t} />)}</div>
}
```

### Mutation Flow (Writing Data)

```
User Action (form submit)
    ↓
useMutation Hook (React Query)
    ↓
POST /api/v1/targets
    ↓
Backend Validation + Processing
    ↓
Database Write
    ↓
Response
    ↓
Invalidate Cache (React Query)
    ↓
Component Re-render
    ↓
Success Toast
```

**Example**:
```typescript
function CreateTargetForm() {
  const queryClient = useQueryClient()
  
  const createMutation = useMutation({
    mutationFn: (data) => api.post('/targets', data),
    onSuccess: () => {
      // Invalidate targets list to refetch
      queryClient.invalidateQueries({ queryKey: ['targets'] })
    }
  })
  
  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      createMutation.mutate(formData)
    }}>
      {/* form fields */}
    </form>
  )
}
```

---

## 💾 State Management

### Zustand (Client State)

**Purpose**: UI state, user preferences, temporary data  
**Location**: `lib/store.ts` or `hooks/useStore.ts`

```typescript
import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme })
}))
```

**Usage**:
```typescript
function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore()
  
  return <div>{sidebarOpen && <Nav />}</div>
}
```

### React Query (Server State)

**Purpose**: Backend data, caching, synchronization  
**Features**:
- Automatic deduplication
- Background refetching
- Cache invalidation
- Optimistic updates

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['targets', { page: 1 }],  // Unique key
  queryFn: () => api.get('/targets?page=1'),
  staleTime: 5 * 60 * 1000,            // 5 min cache
  gcTime: 10 * 60 * 1000,              // 10 min until garbage collect
  retry: 3,                            // Retry on failure
  enabled: !!user                      // Conditional query
})
```

### Combining State Management

```typescript
function TargetDashboard() {
  // Client state
  const { filters, setFilters } = useUIStore()
  
  // Server state
  const { data: targets } = useQuery({
    queryKey: ['targets', filters],
    queryFn: () => api.get('/targets', { params: filters })
  })
  
  return <div>{/* render with both states */}</div>
}
```

---

## 🔌 API Integration

### API Client Setup

```typescript
// lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor: Add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor: Handle errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle token expiration
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### Endpoint Categories

#### Public Endpoints (No Auth Required)
- GET `/api/v1/metodologia` - Methodology docs
- GET `/api/v1/planos` - Pricing plans
- GET `/api/v1/health` - Health check

#### Protected Endpoints (Require Auth)
- GET `/api/v1/targets` - List targets
- POST `/api/v1/targets` - Create target
- GET `/api/v1/alertas` - List alerts
- GET `/api/v1/dossies` - List dossiers

#### Admin Endpoints (Require Admin Role)
- GET `/api/v1/admin/users` - List users
- POST `/api/v1/admin/users/{id}/ban` - Ban user
- GET `/api/v1/admin/finance/dashboard` - Finance dashboard

### Error Handling

```typescript
function useAPI<T>(
  endpoint: string,
  options?: UseQueryOptions<T>
) {
  return useQuery({
    queryKey: [endpoint],
    queryFn: async () => {
      try {
        const response = await api.get(endpoint)
        return response.data
      } catch (error) {
        if (error?.response?.status === 404) {
          throw new Error('Resource not found')
        }
        if (error?.response?.status === 403) {
          throw new Error('Permission denied')
        }
        throw new Error('Failed to fetch data')
      }
    },
    ...options
  })
}
```

---

## 🎯 Routing

### Route Structure

```
/                           Home page
/login                      Login page
/admin                      Admin dashboard
/admin/users                User management
/admin/settings             System settings
/alvos                      Target list
/alvos/search               Target search
/alvos/[id]                 Target detail
/alertas                    Alerts list
/analise                    Analysis tools
/dossies                    Dossiers list
/relatorios                 Reports
/rede                       Network visualization
/metodologia                Methodology documentation
/planos                     Pricing plans
/privacidade                Privacy policy
/termos                     Terms of service
```

### Dynamic Routes

```typescript
// app/alvos/[id]/page.tsx
export default function TargetDetail({ params }: { params: { id: string } }) {
  const { data: target } = useQuery({
    queryKey: ['targets', params.id],
    queryFn: () => api.get(`/targets/${params.id}`)
  })
  
  return <div>{target?.name}</div>
}
```

---

## 🔐 Authentication & Authorization

### Auth Flow

```
1. User enters credentials
   ↓
2. POST /api/v1/auth/login
   ↓
3. Backend returns JWT token
   ↓
4. Store token in localStorage
   ↓
5. Include in all API requests (Authorization header)
   ↓
6. Token refreshed automatically on expiration
```

### Protected Routes

```typescript
// hooks/useAuth.ts
export function useAuth() {
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: fetchCurrentUser,
    staleTime: Infinity  // Don't refetch if already loaded
  })
  
  return { user, isLoading }
}

// components/ProtectedRoute.tsx
export function ProtectedRoute({ children, requiredRole }: Props) {
  const { user } = useAuth()
  
  if (!user) return <Redirect to="/login" />
  if (requiredRole && user.role !== requiredRole) {
    return <Forbidden />
  }
  
  return children
}
```

---

## ♻️ Server vs Client Components

### Server Components (Default in Next.js 16)
```typescript
// app/targets/page.tsx
export default async function TargetsPage() {
  // Can access backend directly
  const targets = await db.targets.findMany()
  
  return <TargetList targets={targets} />
}
```

### Client Components
```typescript
'use client'  // Must declare at top

export default function TargetFilter() {
  // Can use hooks, state, events
  const [search, setSearch] = useState('')
  
  return <input value={search} onChange={e => setSearch(e.target.value)} />
}
```

### Best Practices
- Server: Fetch data, direct DB access
- Client: Interactivity, hooks, browser APIs
- Combine: Server for initial data, Client for interaction

---

## 📊 Data Synchronization

### Real-time Updates (Supabase)

```typescript
function useRealtimeTargets() {
  useEffect(() => {
    // Subscribe to changes
    const subscription = supabase
      .from('targets')
      .on('INSERT', payload => {
        // Update local state
        addTarget(payload.new)
      })
      .subscribe()
    
    return () => subscription.unsubscribe()
  }, [])
}
```

### Background Sync

```typescript
const { data } = useQuery({
  queryKey: ['targets'],
  queryFn: fetchTargets,
  refetchInterval: 30000,  // Every 30 seconds
  refetchIntervalInBackground: true
})
```

---

## 🎨 Styling Architecture

### Tailwind CSS + shadcn/ui

```typescript
// component/Button.tsx
import { Button } from '@/components/ui/button'

export function MyButton() {
  return (
    <Button
      className="bg-blue-500 hover:bg-blue-600"
      variant="outline"
      size="lg"
    >
      Click me
    </Button>
  )
}
```

### Theme System

```typescript
// lib/theme.ts
export const THEME = {
  colors: {
    primary: '#3b82f6',
    danger: '#ef4444',
    success: '#10b981'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '2rem'
  }
}
```

---

## 🧩 Custom Hooks

### Data Fetching Hooks

```typescript
// hooks/useTargets.ts
export function useTargets(filters?: TargetFilters) {
  return useQuery({
    queryKey: ['targets', filters],
    queryFn: () => api.get('/targets', { params: filters }),
    select: data => data.map(t => ({ ...t, label: t.name }))
  })
}

// Usage
function TargetList() {
  const { data: targets } = useTargets({ status: 'active' })
  return <ul>{targets?.map(t => <li>{t.label}</li>)}</ul>
}
```

### Local Storage Hooks

```typescript
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    const stored = localStorage.getItem(key)
    return stored ? JSON.parse(stored) : initialValue
  })
  
  const save = (val: T) => {
    setValue(val)
    localStorage.setItem(key, JSON.stringify(val))
  }
  
  return [value, save] as const
}
```

---

## 🧪 Testing Architecture

### Component Testing
```typescript
// __tests__/components/TargetCard.test.tsx
import { render, screen } from '@testing-library/react'
import { TargetCard } from '@/components/TargetCard'

test('renders target name', () => {
  render(<TargetCard target={{ id: '1', name: 'John Doe' }} />)
  expect(screen.getByText('John Doe')).toBeInTheDocument()
})
```

### Hook Testing
```typescript
// __tests__/hooks/useTargets.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { useTargets } from '@/hooks/useTargets'

test('fetches targets', async () => {
  const { result } = renderHook(() => useTargets())
  
  await waitFor(() => {
    expect(result.current.data).toBeDefined()
  })
})
```

---

## 🚀 Performance Optimization

### Code Splitting
- Automatic per-page in Next.js
- Use `React.lazy()` for dynamic imports

```typescript
const HeavyComponent = dynamic(() => import('@/components/Heavy'))
```

### Image Optimization
```typescript
import Image from 'next/image'

<Image
  src="/image.png"
  alt="Description"
  width={800}
  height={600}
  placeholder="blur"
  priority={isVisible}
/>
```

### Query Caching
```typescript
const { data } = useQuery({
  queryKey: ['targets'],
  queryFn: fetchTargets,
  staleTime: 5 * 60 * 1000,    // 5 minutes
  gcTime: 30 * 60 * 1000        // 30 minutes
})
```

---

## 📋 Dependency Injection

Using React Context for shared services:

```typescript
// lib/providers.ts
const APIContext = React.createContext<APIClient>(null)

export function APIProvider({ children }) {
  const api = new APIClient(baseURL)
  return <APIContext.Provider value={api}>{children}</APIContext.Provider>
}

// In app/layout.tsx
<APIProvider>
  {children}
</APIProvider>

// In components
const api = useContext(APIContext)
```

---

## 📚 Summary

The frontend architecture provides:
- ✅ **Type Safety**: TypeScript throughout
- ✅ **Performance**: Code splitting, caching, optimization
- ✅ **Scalability**: Modular components, clear separation of concerns
- ✅ **Maintainability**: Consistent patterns, documented structure
- ✅ **Developer Experience**: Hot reload, debugging tools, testing setup
