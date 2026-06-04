# Frontend Components Catalog — Sentinela Democrática

**Purpose**: Reference guide for all reusable frontend components  
**Last Updated**: 2026-06-04

---

## 📑 Component Categories

### 1. Base UI Components (`components/ui/`)
Atomic building blocks used across the application.

### 2. Feature Components (`components/*/`)
Business logic components specific to features.

### 3. Page Components (`app/**/page.tsx`)
Route-specific containers.

---

## 🧱 Base UI Components

These foundational components are built with shadcn/ui and Tailwind CSS.

### Button
```typescript
import { Button } from '@/components/ui/button'

// Basic
<Button>Click me</Button>

// Variants
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>

// States
<Button disabled>Disabled</Button>
<Button isLoading>Loading...</Button>
```

**Props**: `variant`, `size`, `disabled`, `className`, `onClick`, `type`

---

### Card
Reusable container component with consistent styling.

```typescript
import { Card } from '@/components/ui/card'

<Card>
  <Card.Header>
    <Card.Title>Title</Card.Title>
    <Card.Description>Subtitle</Card.Description>
  </Card.Header>
  <Card.Content>Content here</Card.Content>
  <Card.Footer>Footer</Card.Footer>
</Card>
```

**Props**: `className`, `children`

---

### Input
Text input field with validation support.

```typescript
import { Input } from '@/components/ui/input'

<Input
  type="text"
  placeholder="Enter text..."
  value={value}
  onChange={e => setValue(e.target.value)}
  disabled={false}
  error="Error message"
/>
```

**Props**: `type`, `placeholder`, `value`, `onChange`, `disabled`, `error`, `className`

---

### Select / Dropdown
Selection component with search capability.

```typescript
import { Select } from '@/components/ui/select'

<Select
  options={[
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' }
  ]}
  value={selected}
  onChange={setSelected}
  placeholder="Select..."
/>
```

**Props**: `options`, `value`, `onChange`, `placeholder`, `disabled`, `isMulti`

---

### Modal / Dialog
Modal overlay for focused user interactions.

```typescript
import { Dialog } from '@/components/ui/dialog'

<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Modal Title</Dialog.Title>
    </Dialog.Header>
    <Dialog.Body>Content</Dialog.Body>
    <Dialog.Footer>
      <Button onClick={() => setIsOpen(false)}>Close</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog>
```

**Props**: `open`, `onOpenChange`, `children`

---

### Badge
Small colored label component.

```typescript
import { Badge } from '@/components/ui/badge'

<Badge variant="default">Status</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="destructive">Error</Badge>
<Badge variant="outline">Outline</Badge>
```

**Props**: `variant`, `className`, `children`

---

### Toast
Notifications for user feedback.

```typescript
import { useToast } from '@/components/ui/use-toast'

function MyComponent() {
  const { toast } = useToast()
  
  const handleSuccess = () => {
    toast({
      title: "Success",
      description: "Operation completed",
      variant: "success"
    })
  }
  
  const handleError = () => {
    toast({
      title: "Error",
      description: "Something went wrong",
      variant: "destructive"
    })
  }
  
  return (
    <>
      <Button onClick={handleSuccess}>Success</Button>
      <Button onClick={handleError}>Error</Button>
    </>
  )
}
```

**Props**: `title`, `description`, `variant` ('default', 'destructive', 'success')

---

### Alert
Alert message boxes for important information.

```typescript
import { Alert } from '@/components/ui/alert'

<Alert variant="default">
  <Alert.Title>Heads up!</Alert.Title>
  <Alert.Description>You can add components to your app using the cli.</Alert.Description>
</Alert>

<Alert variant="destructive">
  <Alert.Title>Error</Alert.Title>
  <Alert.Description>This is an error alert.</Alert.Description>
</Alert>
```

**Props**: `variant`, `children`

---

### Pagination
Navigation for paginated content.

```typescript
import { Pagination } from '@/components/ui/pagination'

<Pagination>
  <Pagination.Content>
    <Pagination.Item>
      <Pagination.Previous href="/page/1" />
    </Pagination.Item>
    {[1, 2, 3, 4, 5].map(page => (
      <Pagination.Item key={page}>
        <Pagination.Link href={`/page/${page}`}>{page}</Pagination.Link>
      </Pagination.Item>
    ))}
    <Pagination.Item>
      <Pagination.Next href="/page/2" />
    </Pagination.Item>
  </Pagination.Content>
</Pagination>
```

**Props**: `children`

---

## 🎨 Feature Components

### Sidebar
Navigation sidebar for main app layout.

```typescript
import { Sidebar } from '@/components/Sidebar'

<Sidebar>
  <Sidebar.Header>
    <Logo />
  </Sidebar.Header>
  <Sidebar.Nav>
    <NavItem href="/alvos">Targets</NavItem>
    <NavItem href="/alertas">Alerts</NavItem>
  </Sidebar.Nav>
  <Sidebar.Footer>
    <UserMenu />
  </Sidebar.Footer>
</Sidebar>
```

**Location**: `components/Sidebar.tsx`  
**Props**: `children`

---

### Header / TopBar
Top navigation bar with branding and user menu.

```typescript
import { Header } from '@/components/Header'

<Header>
  <Header.Logo>Sentinela</Header.Logo>
  <Header.Search />
  <Header.UserMenu />
</Header>
```

**Location**: `components/Header.tsx`  
**Props**: `children`

---

### BuyButton
Subscription/payment button (Stripe integration).

```typescript
import { BuyButton } from '@/components/BuyButton'

<BuyButton
  priceId="price_1Hh..."
  userId="user-123"
  onSuccess={() => toast({ title: 'Subscription successful' })}
/>
```

**Location**: `components/BuyButton.tsx`  
**Props**: `priceId`, `userId`, `onSuccess`, `onError`

---

### ReportCard
Card component for displaying report previews.

```typescript
import { ReportCard } from '@/components/ReportCard'

<ReportCard
  title="Monthly Report"
  date="2026-06-04"
  status="completed"
  onClick={() => navigate(`/reports/${id}`)}
/>
```

**Location**: `components/ReportCard.tsx`  
**Props**: `title`, `date`, `status`, `onClick`, `preview`

---

### ThemeToggle
Dark/light mode switcher.

```typescript
import { ThemeToggle } from '@/components/ThemeToggle'

<ThemeToggle />
```

**Location**: `components/ThemeToggle.tsx`  
**Props**: None

---

### Providers
Context providers for app configuration.

```typescript
import { Providers } from '@/components/Providers'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

**Location**: `components/Providers.tsx`  
**Props**: `children`  
**Includes**: QueryClientProvider, Supabase Provider, Theme Provider

---

### ClientLayoutWrapper
Layout wrapper for client-side features.

```typescript
import { ClientLayoutWrapper } from '@/components/ClientLayoutWrapper'

<ClientLayoutWrapper>
  <Sidebar />
  <main>{children}</main>
</ClientLayoutWrapper>
```

**Location**: `components/ClientLayoutWrapper.tsx`  
**Props**: `children`

---

## 🏠 Home Components (`components/home/`)

### NewsHeader
Hero section with latest news and statistics.

```typescript
import { NewsHeader } from '@/components/home/NewsHeader'

<NewsHeader
  headline="Breaking: Political Statement"
  stats={[
    { label: 'Targets', value: '1,234' },
    { label: 'Alerts', value: '89' }
  ]}
/>
```

**Props**: `headline`, `stats`, `date`

---

### HighlightCards
Featured stories in card format.

```typescript
import { HighlightCards } from '@/components/home/HighlightCards'

<HighlightCards
  cards={[
    {
      title: 'Story Title',
      description: 'Short description',
      category: 'Politics',
      date: '2026-06-04',
      image: '/image.jpg'
    }
  ]}
/>
```

**Props**: `cards`, `onCardClick`

---

### EventTimeline
Chronological timeline of political events.

```typescript
import { EventTimeline } from '@/components/home/EventTimeline'

<EventTimeline
  events={[
    {
      date: '2026-06-04',
      title: 'Event Title',
      description: 'What happened',
      type: 'speech'
    }
  ]}
/>
```

**Props**: `events`, `onEventClick`

---

### InsightBox
Educational analysis boxes.

```typescript
import { InsightBox } from '@/components/home/InsightBox'

<InsightBox
  title="Understanding Political Discourse"
  content="This is an insight about political trends..."
  icon="TrendingUp"
/>
```

**Props**: `title`, `content`, `icon`, `readMoreUrl`

---

### CandidateProfile
Profile card for political figures.

```typescript
import { CandidateProfile } from '@/components/home/CandidateProfile'

<CandidateProfile
  name="John Doe"
  role="Mayor"
  image="/profile.jpg"
  bio="Brief biography"
  metrics={{ mentions: 234, sentiment: 65 }}
/>
```

**Props**: `name`, `role`, `image`, `bio`, `metrics`, `onProfileClick`

---

### MethodologyBox
Explanation of Sentinela methodology.

```typescript
import { MethodologyBox } from '@/components/home/MethodologyBox'

<MethodologyBox
  title="How We Analyze Discourse"
  steps={[
    { title: 'Collection', description: 'We gather data from...' },
    { title: 'Analysis', description: 'Using ML models...' }
  ]}
/>
```

**Props**: `title`, `steps`, `expandable`

---

## 💰 Pricing Components (`components/pricing/`)

### PricingTable
Subscription plans comparison table.

```typescript
import { PricingTable } from '@/components/pricing/PricingTable'

<PricingTable
  plans={[
    {
      name: 'Free',
      price: 0,
      features: ['Feature 1', 'Feature 2'],
      cta: 'Get Started'
    }
  ]}
/>
```

**Props**: `plans`, `onSelectPlan`

---

### FeatureComparison
Side-by-side feature comparison.

```typescript
import { FeatureComparison } from '@/components/pricing/FeatureComparison'

<FeatureComparison
  features={[
    { name: 'API Access', free: false, pro: true },
    { name: 'Support', free: 'Email', pro: '24/7' }
  ]}
/>
```

**Props**: `features`

---

## 🎯 Feature Components

### TargetList
List view of political targets/individuals.

```typescript
import { TargetList } from '@/components/TargetList'

<TargetList
  targets={targetData}
  onSelectTarget={handleSelect}
  filters={activeFilters}
/>
```

**Props**: `targets`, `onSelectTarget`, `filters`, `isLoading`

---

### AlertCard
Individual alert notification card.

```typescript
import { AlertCard } from '@/components/AlertCard'

<AlertCard
  title="New Political Statement"
  timestamp="2 hours ago"
  severity="high"
  onDismiss={handleDismiss}
/>
```

**Props**: `title`, `timestamp`, `severity`, `content`, `onDismiss`

---

### AnalysisChart
Data visualization for analysis.

```typescript
import { AnalysisChart } from '@/components/AnalysisChart'

<AnalysisChart
  data={chartData}
  type="line"
  title="Sentiment Over Time"
/>
```

**Props**: `data`, `type`, `title`, `loading`

---

### NetworkGraph
Network visualization using Force Graph.

```typescript
import { NetworkGraph } from '@/components/NetowrkGraph'

<NetworkGraph
  nodes={nodes}
  links={links}
  onNodeClick={handleNodeClick}
/>
```

**Props**: `nodes`, `links`, `onNodeClick`, `onLinkClick`, `height`, `width`

---

### DossierCard
Dossier document preview card.

```typescript
import { DossierCard } from '@/components/DossierCard'

<DossierCard
  title="Target Dossier"
  target="John Doe"
  lastUpdated="2026-06-01"
  pages={45}
  onOpen={handleOpen}
/>
```

**Props**: `title`, `target`, `lastUpdated`, `pages`, `onOpen`

---

## 🔧 Utility Components

### LoadingSpinner
Loading indicator component.

```typescript
import { LoadingSpinner } from '@/components/LoadingSpinner'

<LoadingSpinner size="lg" />
```

**Props**: `size` ('sm', 'md', 'lg'), `fullScreen`

---

### ErrorBoundary
Error handling component for React errors.

```typescript
import { ErrorBoundary } from '@/components/ErrorBoundary'

<ErrorBoundary fallback={<ErrorPage />}>
  <MyComponent />
</ErrorBoundary>
```

**Props**: `children`, `fallback`, `onError`

---

### EmptyState
Display when no data is available.

```typescript
import { EmptyState } from '@/components/EmptyState'

<EmptyState
  title="No targets found"
  description="Try adjusting your search filters"
  icon="Search"
  action={{ label: 'Clear Filters', onClick: handleClear }}
/>
```

**Props**: `title`, `description`, `icon`, `action`

---

### Breadcrumbs
Navigation breadcrumb trail.

```typescript
import { Breadcrumbs } from '@/components/Breadcrumbs'

<Breadcrumbs
  items={[
    { label: 'Home', href: '/' },
    { label: 'Targets', href: '/targets' },
    { label: 'John Doe', current: true }
  ]}
/>
```

**Props**: `items`

---

### Tabs
Tabbed interface for grouped content.

```typescript
import { Tabs } from '@/components/ui/tabs'

<Tabs defaultValue="overview">
  <Tabs.List>
    <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
    <Tabs.Trigger value="details">Details</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="overview">Overview content</Tabs.Content>
  <Tabs.Content value="details">Details content</Tabs.Content>
</Tabs>
```

**Props**: `defaultValue`, `children`

---

## 📊 Data Display Components

### DataTable
Sortable, filterable table component.

```typescript
import { DataTable } from '@/components/DataTable'

<DataTable
  columns={[
    { header: 'Name', accessor: 'name' },
    { header: 'Status', accessor: 'status' }
  ]}
  data={tableData}
  sortable={true}
  filterable={true}
  pagination={true}
/>
```

**Props**: `columns`, `data`, `sortable`, `filterable`, `pagination`, `onRowClick`

---

### StatCard
Summary statistic card.

```typescript
import { StatCard } from '@/components/StatCard'

<StatCard
  title="Total Targets"
  value="1,234"
  change="+12%"
  trend="up"
  icon="Users"
/>
```

**Props**: `title`, `value`, `change`, `trend`, `icon`

---

## 🎓 Documentation Components

### CodeBlock
Syntax-highlighted code display.

```typescript
import { CodeBlock } from '@/components/CodeBlock'

<CodeBlock
  code="const x = 1"
  language="typescript"
  showLineNumbers={true}
/>
```

**Props**: `code`, `language`, `showLineNumbers`, `theme`

---

### InfoBox
Information callout boxes.

```typescript
import { InfoBox } from '@/components/InfoBox'

<InfoBox type="info">
  This is an informational message
</InfoBox>

<InfoBox type="warning">
  This is a warning
</InfoBox>
```

**Props**: `type` ('info', 'warning', 'error', 'success'), `children`, `title`

---

## 🎨 Styling & Theming

### Theme Colors
```typescript
// tailwind.config.ts
colors: {
  primary: '#3b82f6',      // Blue
  secondary: '#6b7280',    // Gray
  success: '#10b981',      // Green
  warning: '#f59e0b',      // Amber
  danger: '#ef4444',       // Red
  info: '#06b6d4'          // Cyan
}
```

### Dark Mode
All components support dark mode through Tailwind CSS.

```typescript
// Global dark mode
<html className="dark">
```

---

## 📝 Component Creation Guidelines

### File Structure
```
components/
├── MyComponent.tsx         # Component code
├── MyComponent.test.tsx    # Tests
└── MyComponent.module.css  # Scoped styles (optional)
```

### Template
```typescript
import { ReactNode } from 'react'

interface MyComponentProps {
  title: string
  children: ReactNode
  variant?: 'default' | 'outline'
  disabled?: boolean
}

export function MyComponent({
  title,
  children,
  variant = 'default',
  disabled = false
}: MyComponentProps) {
  return (
    <div className={`component component--${variant}`}>
      <h2>{title}</h2>
      {children}
    </div>
  )
}
```

### Best Practices
- ✅ Use TypeScript for type safety
- ✅ Provide JSDoc comments
- ✅ Keep components focused (single responsibility)
- ✅ Use Tailwind classes for styling
- ✅ Test components thoroughly
- ✅ Document props and usage

---

## 🔗 Component Hierarchy Reference

```
App (Root Layout)
├── Providers
│   ├── QueryClientProvider
│   ├── Supabase Provider
│   └── Theme Provider
├── Header
├── Sidebar
├── Main Content
│   ├── Breadcrumbs
│   ├── Page Component
│   │   ├── FeatureComponents
│   │   │   ├── TargetList
│   │   │   │   └── TargetCard (UI Component)
│   │   │   ├── AlertCards
│   │   │   └── DataTable (UI Component)
│   │   └── UI Components
│   │       ├── Button
│   │       ├── Card
│   │       └── Modal
│   └── Footer
└── Toast Notifications
```

---

## 📚 Resources

- **shadcn/ui**: https://ui.shadcn.com
- **Radix UI**: https://radix-ui.com
- **Tailwind CSS**: https://tailwindcss.com
- **React Documentation**: https://react.dev
