# Documentação de Padronização Linguística Analítica (PASA v16.3)
**Projeto: Sentinela Democrática**
**Versão:** 16.3.0 - Analytical Intelligence
**Data:** 28 de Abril de 2026

## 1. Visão Geral
Este documento estabelece as diretrizes léxico-semânticas e os protocolos periciais para todos os Workers e Agentes de IA do sistema Sentinela. O objetivo é garantir a precisão na detecção de discurso de ódio, violência política e ataques coordenados, utilizando os princípios da **Linguística Analítica** e a **Matriz Taxonômica de Ameaças Democráticas (MTAD)**.

## 2. Matriz Taxonômica de Ameaças (Padrão de Classificação)

Todo indício coletado deve ser classificado dentro de um dos seguintes eixos, seguindo o padrão JSON de saída:

| Categoria | Marcadores Semânticos (Keywords) | Nível de Risco |
| :--- | :--- | :--- |
| **XENOFOBIA_REGIONAL** | pobre, analfabeto, ingrato, burro, miserável, 'não sabe votar' | CRÍTICO |
| **RACISMO_RELIGIOSO** | macumba, vodu, magia negra, demônio, 'guerra espiritual', intolerância | ALTO |
| **VIOLÊNCIA_GÊNERO** | vagabunda, piranha, termos sexuais, doxxing, redpill, misoginia | CRÍTICO |
| **MILICIA_DIGITAL** | 'ditadura do STF', 'Xandão', fraude nas urnas, intervenção, URLs falsas | ALTO |
| **RACISMO_ESTRUTURAL** | macaco, termos depreciativos raciais, segregação, injúria racial | CRÍTICO |
| **MISOGINIA_POLITICA** | ataques estéticos a candidatas, questionamento de competência por gênero | MÉDIO |
| **NEUTRO** | discordância política civilizada, crítica administrativa, debate de ideias | BAIXO |

## 3. Protocolos de Análise (Guia para Agentes)

### 3.1. Princípio da Performatividade (Judith Butler)
O Agente não deve analisar apenas a 'descrição' do sentimento, mas a 'ação' do discurso. O insulto proferido em massa visa ferir, isolar e paralisar a existência política da vítima. Se o discurso busca anular a cidadania do alvo, é **Discurso de Ódio**.

### 3.2. Análise Diacrônica (Calendário do Ódio)
A sensibilidade do Agente deve aumentar conforme a proximidade do pleito eleitoral:
- **Fase de Aquecimento (Julho/Agosto):** Foco em termos de classe.
- **Fase Crítica (Setembro/Outubro):** Foco em termos de desumanização cognitiva ('burro', 'analfabeto').

### 3.3. Detecção de Coordenação (Astroturfing)
Um ataque é considerado **Coordenado** quando:
1. Mais de 5 perfis usam o mesmo cluster lexical em um intervalo de 60 segundos.
2. Há repetição de termos específicos (n-gramas) raros em contextos orgânicos.
3. Perfis recém-criados ou com comportamento de bot disparam o mesmo veredito pericial.

## 4. Estrutura de Saída Esperada (JSON)
Todos os Workers de inteligência (Ollama, Gemini, Groq) DEVEM retornar este formato:

`json
{
  "is_hate": true,
  "categoria": "XENOFOBIA_REGIONAL",
  "risco": "CRITICO",
  "indicio_lexical": ["analfabeto", "burro", "povo do NE"],
  "analise_pericial": "O autor utiliza insultos cognitivos para desumanizar o eleitorado regional, caracterizando xenofobia eleitoral performativa.",
  "pasa_version": "16.3.0"
}
`

## 5. Referências Teóricas Integradas
- **Linguística Analítica Digital**: Técnicas de extração de termos e frequências (N-Gramas).
- **Análise de Discurso (PASA)**: Protocolo de Análise Semântico-Arquitetural.
- **Operaçaõ Bulwark (2026)**: Parâmetros de repressão cibernética e desmantelamento de milícias digitais.
- **Estudo NLP UFSCar/UFCG**: Mapeamento do ódio anti-nordestino em ciclos eleitorais.

---
*Documento de uso restrito do Ecossistema Sentinela Democrática.*

## 6. Critérios Enriquecidos via Pesquisa Automatizada
_Última atualização: 04/06/2026_

### Regras Linguísticas Adicionais:
- Considerar contexto cultural e social para evitar falsos positivos em ofensas raciais e religiosas
- Analisar a intenção por trás das palavras para diferenciar insultos ad hominem de críticas construtivas
- Considerar contexto cultural e histórico para evitar falsos positivos em 'VIOLENCIA_GENERO'
- Desconsiderar expressões de opinião política como 'ATAQUE_INSTITUCIONAL'
- Considerar contexto cultural e histórico para entender o uso de linguagem ofensiva
- Analisar relações de poder e dinâmicas entre produtores, receptores e percebedores de linguagem ofensiva
- Considerar contexto cultural e histórico para entender preconceitos raciais e religiosos
- Verificar se ofensas a mulheres são específicas de gênero ou generalizadas
- Considerar contexto para evitar falsos positivos em 'AMEACA'
- Usar recursos de NLP para identificar ironia em 'INSULTO_AD_HOMINEM'
- Considerar contexto para diferenciar entre ironia e hostilidade
- Analisar a intenção por trás das palavras
- Considerar contexto para diferenciar entre humor e hostilidade
- Usar recursos de NLP para identificar ironia e sarcasmo
- Considerar ataques a instituições democráticas como ATAQUE_INSTITUCIONAL

### Regras de Mitigação de Falsos Positivos:
- Evitar marcação de expressões comuns em comunidades específicas como ofensivas sem contexto
- Considerar o tom e a intenção por trás das palavras para evitar marcação de expressões inofensivas como ameaças
- Evitar marcar como 'AMEACA' expressões comuns como 'vamos esmagá-los' em contexto esportivo
- Não marcar como 'DANO_A_IMAGEM' críticas construtivas
- Evitar classificar linguagem reappropriada como ofensiva em contextos específicos da comunidade marginalizada
- Não classificar linguagem que visa desafiar estruturas sociais existentes como ofensiva
- Evitar marcar como 'DANO_A_IMAGEM' quando a acusação for feita por uma fonte confiável
- Não marcar como 'INSULTO_AD_HOMINEM' se a crítica for construtiva
- Evitar classificar expressões de opinião política como ameaças
- Não considerar insultos leves como ataques à honra
- Evitar marcar como 'VIOLENCIA_GENERO' quando a mulher é mencionada como exemplo genérico
- Não marcar como 'ATAQUE_INSTITUCIONAL' quando a crítica é construtiva
- Evitar classificar expressões de opinião fortes como hostilidade
- Considerar o tom de voz e emoção por trás das palavras
- Considerar a intenção comunicativa para diferenciar entre insultos e expressões coloquiais

### Marcadores Léxico-Semânticos Adicionais:
- **ODIO_IDENTITARIO**: racista, xenofobia, homofobia, transfobia, racismo, racial slur, homophobic slur, xenophobic term, regionalismo, islamofobia, raça, religião, orientação sexual, religiophobia, antissemitismo, racial slurs, religious slurs, homophobic slurs
- **VIOLENCIA_GENERO**: machista, sexista, misoginia, machismo, sexismo, abuso, misogynistic slur, sexist term, violência de gênero, mulheres, patriarcado, feminicidio, misogynistic term, sexist slur, feminicídio, misogynistic terms, sexist slurs, misoandria
- **AMEACA**: morte, violência, ameaça, matar, atacar, destruir, threat, violence, kill, ataque, ameaça de morte, assassinato, harm, incitação à violência, ataque físico, incitar violência, terrorismo, incitar à violência, incitar
- **INSULTO_AD_HOMINEM**: idiota, imbecil, estúpido, incompetente, insult, attack, offensive slur, insulto, ofensa, calúnia, covarde, mentiroso, honra, competência, aparência, traidor, ofender, difamar, fraco, fraude
- **ATAQUE_INSTITUCIONAL**: corrupto, incompetente, deslegitimar, corrupção, institutional attack, electoral system attack, deslegitimação, crime, sistema, sistema político, governo, órgãos de Estado, sistema eleitoral, crítica construtiva, government, institutions, democratic infrastructure, press, law system, science
- **DANO_A_IMAGEM**: crime, corrupção, desvios de conduta, theorize crime, impute grave misconduct, corruption, crimes, desvios de conduta grave, imputação de desvios de conduta, fake news, misinformation, discredit, desvios, imputar, desvio de conduta, scandal, acusações falsas, teorias da conspiração, imputação de crimes, escândalo

