# API Integration Guide — Sentinela Democrática

**Purpose**: Guide for integrating frontend with backend APIs  
**API Base URL**: `http://localhost:8000/api/v1` (development)  
**Authentication**: JWT Bearer tokens

---

## 🔌 API Client Setup

### Configuration

```typescript
// lib/api.ts
import axios, { AxiosInstance, AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor: Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor: Handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## 🔐 Authentication Endpoints

### Login
```
POST /auth/login
```

**Request**:
```typescript
interface LoginRequest {
  email: string
  password: string
}

// API Call
const response = await api.post('/auth/login', {
  email: 'user@example.com',
  password: 'password123'
})
```

**Response**:
```typescript
interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
  user: {
    id: string
    email: string
    name: string
    role: 'USER' | 'ADMIN' | 'SUPER_ADMIN'
  }
}

// Save token
localStorage.setItem('auth_token', response.data.access_token)
localStorage.setItem('refresh_token', response.data.refresh_token)
```

**Usage in React**:
```typescript
import { useMutation } from '@tanstack/react-query'

function LoginForm() {
  const loginMutation = useMutation({
    mutationFn: (credentials) => api.post('/auth/login', credentials),
    onSuccess: (response) => {
      localStorage.setItem('auth_token', response.data.access_token)
      navigate('/dashboard')
    },
    onError: (error) => {
      toast({ title: 'Login failed', description: error.message, variant: 'destructive' })
    }
  })

  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      loginMutation.mutate({ email, password })
    }}>
      {/* form fields */}
    </form>
  )
}
```

---

### Logout
```
POST /auth/logout
```

```typescript
const handleLogout = async () => {
  await api.post('/auth/logout')
  localStorage.removeItem('auth_token')
  localStorage.removeItem('refresh_token')
  navigate('/login')
}
```

---

## 👥 Target Management

### List Targets
```
GET /targets?page=1&limit=20&search=query&status=active
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20)
- `search`: Search query
- `status`: Filter by status (active, inactive, archived)
- `sort`: Sort field (name, created_at, updated_at)
- `order`: Sort order (asc, desc)

**Response**:
```typescript
interface Target {
  id: string
  name: string
  type: string  // Person, Organization, Event
  status: string
  description: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  created_at: string
  updated_at: string
  metrics: {
    mentions_count: number
    sentiment_score: number
    trend: 'up' | 'down' | 'stable'
  }
}

interface ListResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  pages: number
}
```

**React Hook**:
```typescript
import { useQuery } from '@tanstack/react-query'

export function useTargets(page = 1, search = '') {
  return useQuery({
    queryKey: ['targets', page, search],
    queryFn: async () => {
      const response = await api.get('/targets', {
        params: { page, search, limit: 20 }
      })
      return response.data
    }
  })
}

// Usage
function TargetList() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useTargets(page)

  return (
    <div>
      {data?.data.map(target => (
        <TargetCard key={target.id} target={target} />
      ))}
      <Pagination
        current={page}
        total={data?.pages}
        onChange={setPage}
      />
    </div>
  )
}
```

---

### Get Target Details
```
GET /targets/{id}
```

```typescript
export function useTarget(id: string) {
  return useQuery({
    queryKey: ['targets', id],
    queryFn: async () => {
      const response = await api.get(`/targets/${id}`)
      return response.data
    }
  })
}

// Usage
function TargetDetail({ targetId }: { targetId: string }) {
  const { data: target, isLoading } = useTarget(targetId)

  if (isLoading) return <LoadingSpinner />

  return (
    <div>
      <h1>{target?.name}</h1>
      <p>{target?.description}</p>
      <RiskBadge level={target?.risk_level} />
    </div>
  )
}
```

---

### Create Target
```
POST /targets
```

**Request**:
```typescript
interface CreateTargetRequest {
  name: string
  type: string
  description?: string
  risk_level?: string
  metadata?: Record<string, any>
}

const createMutation = useMutation({
  mutationFn: (data: CreateTargetRequest) =>
    api.post('/targets', data),
  onSuccess: (response) => {
    queryClient.invalidateQueries({ queryKey: ['targets'] })
    toast({ title: 'Target created', variant: 'success' })
  }
})
```

---

### Update Target
```
PUT /targets/{id}
```

```typescript
const updateMutation = useMutation({
  mutationFn: (data: Partial<Target>) =>
    api.put(`/targets/${data.id}`, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['targets'] })
  }
})
```

---

### Delete Target
```
DELETE /targets/{id}
```

```typescript
const deleteMutation = useMutation({
  mutationFn: (id: string) =>
    api.delete(`/targets/${id}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['targets'] })
  }
})
```

---

## 🚨 Alert Management

### List Alerts
```
GET /alertas?page=1&limit=20&status=new&severity=high
```

```typescript
interface Alert {
  id: string
  title: string
  description: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: 'new' | 'acknowledged' | 'resolved'
  target_id: string
  created_at: string
  updated_at: string
}

export function useAlerts(filters = {}) {
  return useQuery({
    queryKey: ['alerts', filters],
    queryFn: async () => {
      const response = await api.get('/alertas', { params: filters })
      return response.data
    }
  })
}
```

---

### Create Alert
```
POST /alertas
```

```typescript
interface CreateAlertRequest {
  title: string
  description: string
  severity: string
  target_id: string
}

const createAlertMutation = useMutation({
  mutationFn: (data: CreateAlertRequest) =>
    api.post('/alertas', data)
})
```

---

### Mark Alert as Read
```
PATCH /alertas/{id}/read
```

```typescript
const markReadMutation = useMutation({
  mutationFn: (alertId: string) =>
    api.patch(`/alertas/${alertId}/read`)
})
```

---

## 📊 Analysis & Reports

### Get Dashboard Summary
```
GET /dashboard
```

```typescript
interface DashboardData {
  total_targets: number
  active_alerts: number
  recent_mentions: number
  risk_distribution: Record<string, number>
  trending_topics: Array<{ topic: string; count: number }>
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await api.get('/dashboard')
      return response.data
    }
  })
}
```

---

### Get Analytics
```
GET /analytics?metric=mentions&target_id=123&date_range=7d
```

**Query Parameters**:
- `metric`: Type of metric (mentions, sentiment, engagement, etc.)
- `target_id`: Filter by target
- `date_range`: Time period (1d, 7d, 30d, 90d, 1y)
- `granularity`: Data granularity (hourly, daily, weekly)

```typescript
interface AnalyticsData {
  metric: string
  data: Array<{
    date: string
    value: number
  }>
  summary: {
    total: number
    average: number
    trend: number
  }
}

export function useAnalytics(metric: string, targetId?: string) {
  return useQuery({
    queryKey: ['analytics', metric, targetId],
    queryFn: async () => {
      const response = await api.get('/analytics', {
        params: { metric, target_id: targetId }
      })
      return response.data
    }
  })
}
```

---

## 📄 Reports

### List Reports
```
GET /relatorios?page=1&limit=10
```

---

### Generate Report
```
POST /relatorios
```

```typescript
interface GenerateReportRequest {
  title: string
  type: string
  target_ids: string[]
  date_range: { start: string; end: string }
  include_sections: string[]
}
```

---

### Get Report
```
GET /relatorios/{id}
```

---

### Export Report
```
GET /relatorios/{id}/export?format=pdf
```

```typescript
const handleExport = async (reportId: string) => {
  const response = await api.get(`/relatorios/${reportId}/export?format=pdf`, {
    responseType: 'blob'
  })
  
  // Download file
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = `report-${reportId}.pdf`
  link.click()
}
```

---

## 🌐 Network Analysis

### Get Network Graph
```
GET /rede/graph?target_id=123&depth=2
```

```typescript
interface NetworkNode {
  id: string
  label: string
  type: string
  size: number
  color: string
}

interface NetworkLink {
  source: string
  target: string
  strength: number
  type: string
}

interface NetworkData {
  nodes: NetworkNode[]
  links: NetworkLink[]
}

export function useNetworkGraph(targetId: string) {
  return useQuery({
    queryKey: ['network', targetId],
    queryFn: async () => {
      const response = await api.get('/rede/graph', {
        params: { target_id: targetId, depth: 2 }
      })
      return response.data
    }
  })
}
```

---

## 💰 Subscription & Payment

### Get Plans
```
GET /planos
```

```typescript
interface Plan {
  id: string
  name: string
  price: number
  currency: string
  features: string[]
  stripe_price_id: string
}

export function usePlans() {
  return useQuery({
    queryKey: ['plans'],
    queryFn: async () => {
      const response = await api.get('/planos')
      return response.data
    }
  })
}
```

---

### Checkout
```
POST /checkout
```

```typescript
interface CheckoutRequest {
  user_id: string
  package_slug: string
  price_id: string
}

const checkoutMutation = useMutation({
  mutationFn: (data: CheckoutRequest) =>
    api.post('/checkout', data),
  onSuccess: (response) => {
    // Redirect to Stripe
    window.location.href = response.data.checkout_url
  }
})
```

---

## ⚙️ Admin Endpoints

### Get Users List
```
GET /admin/users?page=1&limit=20
```

**Requires**: ADMIN role

```typescript
const { data: users } = useQuery({
  queryKey: ['admin', 'users'],
  queryFn: async () => {
    const response = await api.get('/admin/users')
    return response.data
  },
  enabled: user?.role === 'ADMIN'  // Only fetch if admin
})
```

---

### Get Finance Dashboard
```
GET /admin/finance/dashboard
```

---

## 🔄 Error Handling

### Standard Error Response
```typescript
interface APIError {
  error: string
  detail: string
  status_code: number
  timestamp: string
}

// Handle errors
api.interceptors.response.use(
  response => response,
  error => {
    const errorData: APIError = error.response?.data

    switch (error.response?.status) {
      case 400:
        toast({ title: 'Invalid input', description: errorData.detail })
        break
      case 401:
        // Handle unauthorized
        navigate('/login')
        break
      case 403:
        toast({ title: 'Forbidden', description: 'You do not have permission' })
        break
      case 404:
        toast({ title: 'Not found', description: 'Resource not found' })
        break
      case 500:
        toast({ title: 'Server error', description: 'Please try again later' })
        break
    }

    return Promise.reject(error)
  }
)
```

---

## 📡 Real-time Updates (WebSockets)

For real-time alerts and notifications:

```typescript
export function useRealtimeAlerts(targetId: string) {
  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(
      `ws://localhost:8000/ws/alerts?target_id=${targetId}`
    )

    ws.onmessage = (event) => {
      const alert = JSON.parse(event.data)
      queryClient.setQueryData(['alerts'], (old: any) => [
        alert,
        ...(old || [])
      ])
    }

    return () => ws.close()
  }, [targetId])
}
```

---

## ✅ Best Practices

### 1. Query Organization
```typescript
// hooks/useTargets.ts - All target-related queries
export function useTargets() { /* ... */ }
export function useTarget(id: string) { /* ... */ }
export function useTargetMetrics(id: string) { /* ... */ }

// In components
import { useTargets, useTarget } from '@/hooks/useTargets'
```

### 2. Error Handling
```typescript
function MyComponent() {
  const { data, isLoading, error } = useQuery({ /* ... */ })

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  if (!data) return <EmptyState />

  return <div>{/* render data */}</div>
}
```

### 3. Optimistic Updates
```typescript
const updateMutation = useMutation({
  mutationFn: (data) => api.put(`/targets/${data.id}`, data),
  onMutate: (newData) => {
    // Optimistically update UI
    queryClient.setQueryData(['targets', newData.id], newData)
  },
  onError: () => {
    // Revert on error
    queryClient.invalidateQueries({ queryKey: ['targets'] })
  }
})
```

### 4. Dependent Queries
```typescript
export function useTargetWithAlerts(targetId: string) {
  const { data: target } = useTarget(targetId)
  
  const { data: alerts } = useQuery({
    queryKey: ['alerts', targetId],
    queryFn: () => api.get(`/targets/${targetId}/alerts`),
    enabled: !!targetId  // Only fetch when targetId exists
  })

  return { target, alerts }
}
```

---

## 📚 Resources

- **Axios Docs**: https://axios-http.com/
- **React Query Docs**: https://tanstack.com/query/latest
- **Backend API Docs**: http://localhost:8000/docs (Swagger)
- **Authentication Guide**: See ARCHITECTURE.md
