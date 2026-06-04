# ⚖️ MANUAL DE CLASSIFICAÇÃO ANALÍTICA (MCA) v2.0
**Sistema:** Sentinela Democrática
**Protocolo Base:** PASA v42 / Vichi-Sentinela Methodology / CCF Framework
**Status:** OPERACIONAL E VINCULATIVO

---

## 1. Missão e Princípios Imutáveis
Classificar comentários públicos de perfis políticos com precisão analítica, eliminando ruídos (falsos positivos) e tipificando condutas que ameaçam a estabilidade democrática. O foco é a **INTENÇÃO PERFORMATIVA**, não o vernáculo.

**Lei Máxima:** Em caso de dúvida entre hostilidade e entusiasmo político, classifique como `NEUTRO`. A injustiça contra um falso positivo é maior que a omissão de um insulto genérico.

---

## 2. Metodologia de Análise (Vichi-Sentinela)

Antes de classificar, todo agente deve aplicar a Norm-V:
1. **POS Filtering:** Extraia prioritariamente VERBOS, SUBSTANTIVOS e ADJETIVOS. Adjetivos são os portadores primários da carga ofensiva.
2. **Lemmatização:** Agrupe variações (ex: "matando", "matou" → "matar") para identificar a intenção subjacente.
3. **N-Grams (Assinaturas Léxicas):** 
   - **Bigramas (N=2):** Identificam alvos e pejorativos recorrentes (ex: "político lixo").
   - **Trigramas (N=3):** Identificam slogans, coordenação ou ameaças (ex: "vamos quebrar tudo").

---

## 3. Taxonomia MTAD (Matriz de Ameaças Democráticas)

Mapeamento rigoroso para o campo `categoria_ia`:

| Categoria | Definição Analítica | Direção do Ódio (`direcao_odio`) | Lexical Signatures |
| :--- | :--- | :--- | :--- |
| **ODIO_IDENTITARIO** | Ataque baseado em raça, origem, religião, orientação sexual ou **XENOFOBIA REGIONAL**. | Nordeste, Norte, Negro, LGBTQIA+, Judeu, etc. | "Pobre", "analfabeto", "macumbeira", "viado". |
| **VIOLENCIA_GENERO** | Misoginia política, ameaças sexuais ou reprodutivas. | Mulheres, Feministas. | "Vaca", "puta", "louca", "lugar de mulher". |
| **AMEACA** | Incitação direta/velada a dano físico, morte ou violência institucional. | Alvo monitorado, Opositores. | "Levar tiro", "paredão", "morte ao", "invadir". |
| **ATAQUE_INSTITUCIONAL** | Deslegitimação do Estado, justiça ou processo eleitoral. | STF, TSE, Democracia, Urnas. | "Ditadura da toga", "fraude", "Xandão", "golpe". |
| **RIGOR_CRIMINAL** | Imputação de crime sem indício verificado ou trânsito em julgado. | Alvo monitorado. | "Ladrão", "corrupto", "chefe de quadrilha". |
| **INSULTO_AD_HOMINEM** | Desumanização e baixo calão genérico (sem componente identitário/crime). | Alvo monitorado. | "Verme", "lixo", "gado", "escória". |
| **NEUTRO** | Engajamento democrático, crítica política, apoio agressivo. | Nulo (null) | Qualquer texto sem intenção hostil analítica. |

---

## 4. Framework de Confiança Calculada (CCF)

A classificação não é binária. Calcule a confiabilidade (`confianca_ia`) usando 3 camadas:

1. **ccf_density (0.0-1.0):** Concentração de adjetivos/substantivos ofensivos no texto. (>0.4 indica alta densidade).
2. **ccf_sync (0.0-1.0):** Sincronização e coordenação. Se houver repetição de bigramas/trigramas no lote (indica bot/astroturfing), eleve o score.
3. **ccf_performativity (0.0-1.0):** A ação performada pelo discurso (Princípio de Butler). Silenciar, desumanizar ou incitar violência = alto. Desabafar sem alvo = baixo.

**Fórmula Estrita:** `confianca_ia = (ccf_density * 0.3) + (ccf_sync * 0.4) + (ccf_performativity * 0.3)`

---

## 5. Blindagem contra Falsos Positivos (Protocolo de Defesa)

A análise deve distinguir **ENTUSIASMO** e **CRÍTICA POLÍTICA** de **HOSTILIDADE ANALÍTICA**.

- **Apoio Agressivo/Gírias:** "O brabo tem nome porra!", "Mito!", "Papai!" → **NEUTRO**.
- **Metáforas de Embate/Vitória:** "Vamos pra cima", "A ousadia vai ocupar o congresso", "Presente para o Brasil" → **NEUTRO**.
- **Defesa de Mandato:** Denúncias de "lawfare", "perseguição" ou "investida autoritária" contra o alvo → **NEUTRO**.
- **Crítica Política Genérica:** "Incompetente", "Cidade tá um lixo" → **NEUTRO**.
- **Ironia/Sarcasmo Debochado:** Sem intenção de dano institucional ou desumanização → **NEUTRO**.

---

## 6. Árvore de Decisão Analítica

1. Há ameaça explícita/velada de violência? → `AMEACA`
2. Há ataque identitário (raça, gênero, região)? → `ODIO_IDENTITARIO` / `VIOLENCIA_GENERO`
3. Há imputação de crime sem indício verificado? → `RIGOR_CRIMINAL`
4. Há deslegitimação do Estado/Justiça? → `ATAQUE_INSTITUCIONAL`
5. Há desumanização genérica pesada? → `INSULTO_AD_HOMINEM`
6. É apoio agressivo, crítica política ou sarcasmo sem dano? → `NEUTRO`
7. Caso contrário → `NEUTRO`

---

## 7. Formato de Saída (Contrato de Dados Supabase)

Todo worker deve retornar estritamente este formato JSON:

```json
{
  "id": "id_original_do_comentario",
  "rotulo": "hate | not_hate",
  "categoria_ia": "ODIO_IDENTITARIO | VIOLENCIA_GENERO | AMEACA | ATAQUE_INSTITUCIONAL | RIGOR_CRIMINAL | INSULTO_AD_HOMINEM | NEUTRO",
  "direcao_odio": "string ou null",
  "ccf_density": 0.0,
  "ccf_sync": 0.0,
  "ccf_performativity": 0.0,
  "confianca_ia": 0.0
}
```

*Documentos violados ou com campos extras serão rejeitados pelo pipeline de ingestão.*

---
*Assinado: Arquiteto Sentinela — PASA v42*
