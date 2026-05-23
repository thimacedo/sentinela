# Manual Técnico de Padronização Linguística - Protocolo PASA v16.3
**Documento de Referência para Workers e Agentes de IA**
**Projeto:** Sentinela Democrática
**Status:** Oficial / Pericial

## 1. Introdução e Objetivo
Este manual define os critérios técnicos para a identificação, classificação e análise de evidências digitais no âmbito do monitoramento de ameaças democráticas. A padronização visa eliminar ambiguidades interpretativas entre diferentes modelos de IA (Ollama, Gemini, Groq) e garantir a validade jurídica dos vereditos.

## 2. Fundamentos Teóricos (Baseline)
O sistema opera sob três pilares científicos:
1. **Performatividade do Discurso (Judith Butler):** O foco não é o que o texto *diz*, mas o que o texto *faz*. O insulto é um ato que visa ferir e silenciar.
2. **Linguística Forense Digital:** Uso de frequências lexicais (n-gramas) para identificar autoria e coordenação de ataques (Astroturfing).
3. **Análise Diacrônica Eleitoral:** Reconhecimento de que o vocabulário de ódio sofre "endurecimento semântico" conforme a proximidade das urnas (Clusters: Pobre -> Analfabeto -> Burro).

## 3. Matriz Taxonômica de Ameaças Democráticas (MTAD)

### 3.1. XENOFOBIA_REGIONAL (Eixo Nordeste)
- **Definição:** Ataques direcionados à origem geográfica, cultura ou capacidade cognitiva de eleitores da região Nordeste.
- **Inclusão:** Termos como "comedor de abóbora", "analfabeto", "povo burro", "miserável", "ingrato".
- **Exclusão:** Críticas legítimas a políticas públicas regionais sem teor discriminatório.
- **Risco:** CRÍTICO.

### 3.2. RACISMO_RELIGIOSO (Eixo Narcopentecostalismo)
- **Definição:** Demonização de matrizes africanas e uso de termos religiosos para incitar ódio ou violência contra terreiros.
- **Inclusão:** "macumba", "vodu", "encosto", "chuta que é macumba", "guerra espiritual contra o mal".
- **Risco:** ALTO.

### 3.3. VIOLÊNCIA_GÊNERO / MISOGINIA_POLÍTICA
- **Definição:** Ataques que visam deslegitimar mulheres na política através de ofensas sexuais, estéticas ou doxxing familiar.
- **Inclusão:** Termos sexistas, "piranha", "vagabunda", ataques à aparência, "redpill".
- **Risco:** CRÍTICO.

### 3.4. MILÍCIA_DIGITAL / ATAQUE_INSTITUCIONAL
- **Definição:** Campanhas coordenadas para descredibilizar o sistema eleitoral ou membros das cortes superiores (STF/TSE).
- **Inclusão:** "Xandão", "ditadura da toga", "fraude nas urnas", "intervenção militar".
- **Risco:** ALTO.

### 3.5. RACISMO_ESTRUTURAL
- **Definição:** Uso de léxico degradante de cunho racial.
- **Inclusão:** "macaco", "senzala", "escravo", e variações codificadas.
- **Risco:** CRÍTICO.

## 4. Protocolo de Implementação em Workers

### 4.1. Prompt Engineering Padrão
Todos os prompts de IA devem conter a instrução:
> "Siga o Manual PASA v16.3. Identifique a evidência lexical. Avalie a performatividade. Retorne JSON estruturado."

### 4.2. Detecção de Coordenação
Os workers de análise devem sinalizar coordenação quando:
- **Repetição Imediata:** O mesmo cluster de xingamentos aparece em >3 perfis diferentes em menos de 5 minutos.
- **Sincronia Semântica:** Uso de termos idênticos (n-gramas de ordem 3) que não são gírias comuns.

## 5. Dicionário de Controle (N-Gramas Críticos)
- **Bigramas Críticos:** "povo burro", "voto comprado", "fazer macumba", "quebrar tudo".
- **Trigramas Críticos:** "nordestino não sabe", "fraude nas urnas", "morte ao candidato".

## 6. Governança de Dados
Os resultados devem ser persistidos no formato:
1. **SQLite (Local):** Texto bruto + ID externo + Metadata.
2. **Supabase (Cloud):** Veredito IA + Categoria + Nível de Risco + Analise Pericial (Texto).

---
*Aprovado por: IA Arquiteta Sentinela v16.3*
