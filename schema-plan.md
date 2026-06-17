# Implementação de Schema Markup (SEO)

## Goal
Aumentar a visibilidade orgânica do Sentinela Democrática no Google adicionando `JSON-LD` schemas recomendados pela documentação, otimizando o Next.js App Router para SEO técnico.

## Tasks
- [x] Task 1: Criar o componente base `JsonLd` em `frontend/components/JsonLd.tsx` → Verify: Arquivo existe e aceita tipagem `data: any`.
- [x] Task 2: Injetar schemas `WebSite` e `Organization` no `frontend/app/layout.tsx` (Root) → Verify: O `<script type="application/ld+json">` aparece no código-fonte em todas as rotas da aplicação.
- [x] Task 3: Injetar schema `SoftwareApplication` e `BreadcrumbList` na página de Preços (`frontend/app/planos/page.tsx`) → Verify: As propriedades de oferta (Preço = 0 ou CIs) estão configuradas para Rich Results.
- [x] Task 4: Injetar schema `WebPage` (About) e `BreadcrumbList` na página de Metodologia (`frontend/app/metodologia/page.tsx`) → Verify: Renderiza com breadcrumbs apontando para a raiz.

## Done When
- [x] Componente `JsonLd` criado e injetado em pelo menos 3 arquivos (Layout, Planos, Metodologia).
- [x] Nenhum erro de build do TypeScript (TS) nos arquivos alterados.