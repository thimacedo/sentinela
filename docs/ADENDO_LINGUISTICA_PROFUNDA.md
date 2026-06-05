# Adendo de Linguística Analítica Profunda (PASA v16.3.1)
**Projeto:** Sentinela Democrática
**Integração:** Base Teórica 'linguistica-analitica' (Bakhtin, Empoli, Marcuschi)

## 1. Psicologia do Caos Algorítmico (Engenheiros do Caos)
A análise deve agora identificar o **Vetor de Engajamento por Fúria**. Comentários que utilizam "Polarização Afetiva" (ódio ao outro mais do que amor ao próprio candidato) devem ser sinalizados como **ESTRATÉGIA_CAOS**.

- **Indicador:** Uso de termos de desumanização extrema seguidos de chamamento à ação ou indignação artificial.
- **Teoria:** O ódio é o combustível mais barato para o engajamento digital.

## 2. Gêneros do Discurso de Ódio (Bakhtin)
O discurso de ódio deve ser tratado como um **Gênero Discursivo Estabilizado**. Ele possui:
- **Temas Estáveis:** Corrupção moral, ameaça externa, pureza de grupo.
- **Estilo:** Linguagem hiperbólica, imperativa e exclamativa.
- **Construção Composicional:** Ataque (Ad Hominem) -> Generalização -> Exclusão.

## 3. Matriz de Falácias Argumentativas (Othon Garcia)
Os Agentes de Inteligência devem identificar a estrutura lógica do ataque:
1. **Ad Hominem:** Atacar a pessoa para invalidar o argumento.
2. **Espantalho:** Distorcer a fala do alvo para atacá-la.
3. **Falsa Dicotomia:** "Ou você está com o povo (nós), ou está com os criminosos (eles)".

## 4. Atualização do JSON de Saída (Metadata Profundo)
A partir da v16.3.1, o campo analise_analitica deve incluir a identificação da falácia e do vetor de fúria:

```json
{
  "is_hate": true,
  "categoria": "VIOLÊNCIA_GÊNERO",
  "falacia_detectada": "AD_HOMINEM",
  "vetor_furia": "ALTO",
  "analise_analitica": "Ataque performativo utilizando falácia Ad Hominem para silenciamento político via deslegitimação de gênero.",
  "referencia_teorica": "Bakhtin/Empoli"
}
```

---
*Este adendo expande as capacidades de diagnóstico para além da superfície lexical.*
