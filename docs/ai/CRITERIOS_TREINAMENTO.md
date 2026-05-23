# 📜 Diretrizes de Treinamento e Classificação PASA v16.4

Este documento define os critérios para a classificação de discurso de ódio e hostilidade política do sistema Sentinela Democrática.

## 1. Matriz de Hostilidade (Categorias)

- **ODIO_IDENTITARIO**: Ataques baseados em raça, religião, orientação sexual, misoginia ou **XENOFOBIA/REGIONALISMO** (ex: ridicularização de sotaques, uso de identidades regionais como adjetivo pejorativo ou estereótipos de "preguiça").
- **VIOLENCIA_GENERO**: Ofensas focadas na condição feminina (ex: "vaca", "puta", "louca").
- **AMEACA**: Incitação a dano físico ou morte (ex: "tem que levar tiro", "paredão").
- **INSULTO_AD_HOMINEM**: Desumanização e baixo calão (ex: "verme", "rato", "lixo").
- **ATAQUE_INSTITUCIONAL**: Deslegitimação de órgãos de Estado (ex: "ditadura da toga", "fraude", "comprado").
- **RIGOR_CRIMINAL**: Imputação de crime sem prova ou trânsito em julgado (ex: "ladrão", "traficante", "corrupto").

## 2. Scanner de Ironia e Sarcasmo
A análise deve identificar dissonância semântica:
- *"Inglês de baiano com preguiça"* (Uso de regionalismo para insulto) → **ODIO_IDENTITARIO**.
- *"Grande democrata esse aí"* (em contexto de crítica a decisões judiciais) → **ATAQUE_INSTITUCIONAL**.
- *"Parabéns pelo roubo"* → **RIGOR_CRIMINAL**.

## 3. Dicionário de Alta Hostilidade
- **Ofensas**: lixo, escória, verme, rato, jumento, gado, mortadela.
- **Institucional**: ditadura, golpe, fraude, urnas, Alexandre, Xandão, careca.
- **Ideológico**: comunista, fascista, nazista, extrema-direita, esquerda caviar.

## 5. Blindagem contra Falsos Positivos (Protocolo de Defesa)

A análise deve distinguir **ENTUSIASMO** e **CRÍTICA POLÍTICA** de **HOSTILIDADE FORENSE**.

- **ENTUSIASMO / APOIO**: Frases como *"Fulano no Congresso será um presente"*, *"A ousadia vai ocupar o congresso"* ou *"Vamos pra cima"* são expressões de engajamento democrático e devem ser classificadas como **NEUTRO**.
- **DEFESA DE MANDATO**: Denúncias de "perseguição", "lawfare" ou "investida autoritária" feitas por apoiadores em defesa do alvo monitorado são **OPINIÕES POLÍTICAS**, não ataques institucionais ao Estado. Classificar como **NEUTRO**.
- **METÁFORAS DE EMBATE**: Termos como *"inimigos do povo"*, *"servir de lição"* ou *"mobilizar nas ruas"* dentro de um contexto de campanha ou manifestação legítima **NÃO** configuram AMEAÇA.
- **APOIO AGRESSIVO / GÍRIAS**: O uso de palavrões (ex: "porra", "caralho") ou gírias (ex: "o brabo", "mito", "papai") em frases de exaltação ao alvo monitorado deve ser classificado como **NEUTRO**. O foco é a **INTENÇÃO** e não o vernáculo.

## 6. Exemplos de Exclusão (Não é Ódio)
- *"O brabo tem nome porra!"* (Apoio agressivo/Gíria) -> **NEUTRO**.
- *"@alvo na Câmara vai ser um presente"* (Elogio/Esperança) -> **NEUTRO**.
- *"A ousadia vai ocupar o congresso!"* (Metáfora de vitória eleitoral) -> **NEUTRO**.
- *"Querem inviabilizar um mandato sério!"* (Defesa política) -> **NEUTRO**.
- *"Mobilizar nas ruas no 1º de maio"* (Direito de reunião) -> **NEUTRO**.
