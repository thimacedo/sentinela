# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\debug_prod.spec.ts >> debug production site
- Location: tests\debug_prod.spec.ts:5:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.innerText: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('#kpi-monitorados')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - heading "SENTINELAAI" [level=1] [ref=e5]
        - button "Recolher menu" [ref=e6]:
          - img [ref=e7]
      - navigation [ref=e9]:
        - button "INÍCIO" [ref=e10]:
          - img [ref=e11]
          - generic [ref=e14]: INÍCIO
        - button "ANÁLISE" [ref=e15]:
          - img [ref=e16]
          - generic [ref=e18]: ANÁLISE
        - button "ESTATÍSTICAS" [ref=e19]:
          - img [ref=e20]
          - generic [ref=e22]: ESTATÍSTICAS
        - button "CANDIDATOS" [ref=e23]:
          - img [ref=e24]
          - generic [ref=e29]: CANDIDATOS
        - button "ALERTAS" [ref=e30]:
          - img [ref=e31]
          - generic [ref=e33]: ALERTAS
        - button "REDE" [ref=e34]:
          - img [ref=e35]
          - generic [ref=e38]: REDE
        - button "RELATÓRIOS" [ref=e39]:
          - img [ref=e40]
          - generic [ref=e43]: RELATÓRIOS
      - generic [ref=e44]:
        - generic [ref=e45]:
          - generic [ref=e46]:
            - generic [ref=e47]: Aporte de Inteligência
            - generic [ref=e48]: ⚡ 0 CI
          - button "Restaurar Aporte" [ref=e51]
        - generic [ref=e54]: Monitor Ativo
        - generic [ref=e55]:
          - generic [ref=e56]:
            - generic [ref=e57]: Alertas (24h)
            - generic [ref=e58]: "3.646"
          - generic [ref=e59]:
            - generic [ref=e60]: Monitorados
            - generic [ref=e61]: "339"
          - generic [ref=e62]:
            - generic [ref=e63]: Amostragem
            - generic [ref=e64]: 64.1k
          - generic [ref=e66]:
            - generic [ref=e67]: Resiliência
            - generic [ref=e68]: 94.3%
        - generic [ref=e71]: OBSERVATÓRIO CÍVICO
    - main [ref=e72]:
      - main [ref=e75]:
        - generic [ref=e79]:
          - generic [ref=e80]:
            - img [ref=e81]
            - text: "Status: Monitoramento Ativo"
          - heading "Visão Tática Global" [level=1] [ref=e83]
          - paragraph [ref=e84]: Observatório de Discurso Cívico em tempo real. Padrões de comportamento anômalo e ações coordenadas detectadas via Protocolo PASA.
        - generic [ref=e85]:
          - generic [ref=e86]:
            - heading "📅 Linha do Tempo" [level=2] [ref=e87]: 📅 Linha do Tempo
            - generic [ref=e89]:
              - button "24h" [ref=e90] [cursor=pointer]
              - button "7d" [ref=e91] [cursor=pointer]
              - button "30d" [ref=e92] [cursor=pointer]
          - paragraph [ref=e93]: Histórico e picos de ocorrência em ordem cronológica (Últimas 24 Horas)
          - generic [ref=e94]:
            - generic [ref=e100]:
              - generic [ref=e101]:
                - generic [ref=e102]:
                  - paragraph [ref=e103]: 13:53
                  - heading "CAMPANHA_COORDENADA" [level=4] [ref=e104]
                - generic [ref=e106]: 1 posts
              - paragraph [ref=e107]: 167razoesrn...
              - generic [ref=e108]:
                - generic [ref=e109]:
                  - text: "Alvo:"
                  - strong [ref=e110]: "@allysonbezerra.rn"
                - generic [ref=e111]:
                  - text: "Risco Calculado:"
                  - strong [ref=e112]: 50%
            - generic [ref=e118]:
              - generic [ref=e119]:
                - generic [ref=e120]:
                  - paragraph [ref=e121]: 08:08
                  - heading "CAMPANHA_COORDENADA" [level=4] [ref=e122]
                - generic [ref=e124]: 1 posts
              - paragraph [ref=e125]: Parabéns!!!! Feliz aniversário amigo e irmão. Muitos anos de vida 🙌🙌....
              - generic [ref=e126]:
                - generic [ref=e127]:
                  - text: "Alvo:"
                  - strong [ref=e128]: "@carlosbrandaooficial"
                - generic [ref=e129]:
                  - text: "Risco Calculado:"
                  - strong [ref=e130]: 50%
            - generic [ref=e136]:
              - generic [ref=e137]:
                - generic [ref=e138]:
                  - paragraph [ref=e139]: 08:08
                  - heading "CAMPANHA_COORDENADA" [level=4] [ref=e140]
                - generic [ref=e142]: 1 posts
              - paragraph [ref=e143]: Parabéns !!!! Meu amigo tudo de bom pra vc. Felicidades...
              - generic [ref=e144]:
                - generic [ref=e145]:
                  - text: "Alvo:"
                  - strong [ref=e146]: "@carlosbrandaooficial"
                - generic [ref=e147]:
                  - text: "Risco Calculado:"
                  - strong [ref=e148]: 50%
            - generic [ref=e154]:
              - generic [ref=e155]:
                - generic [ref=e156]:
                  - paragraph [ref=e157]: 08:08
                  - heading "CAMPANHA_COORDENADA" [level=4] [ref=e158]
                - generic [ref=e160]: 1 posts
              - paragraph [ref=e161]: Parabéns 🎈👏🏼👏🏼👏🏼👏🏼 😍...
              - generic [ref=e162]:
                - generic [ref=e163]:
                  - text: "Alvo:"
                  - strong [ref=e164]: "@carlosbrandaooficial"
                - generic [ref=e165]:
                  - text: "Risco Calculado:"
                  - strong [ref=e166]: 50%
            - generic [ref=e171]:
              - generic [ref=e172]:
                - generic [ref=e173]:
                  - paragraph [ref=e174]: 08:08
                  - heading "CAMPANHA_COORDENADA" [level=4] [ref=e175]
                - generic [ref=e177]: 1 posts
              - paragraph [ref=e178]: Parabéns meu amigo Deus abençoe sua vida tudo de bom pra vc e sua família....
              - generic [ref=e179]:
                - generic [ref=e180]:
                  - text: "Alvo:"
                  - strong [ref=e181]: "@carlosbrandaooficial"
                - generic [ref=e182]:
                  - text: "Risco Calculado:"
                  - strong [ref=e183]: 50%
        - generic [ref=e185]:
          - generic [ref=e186]:
            - generic [ref=e188]:
              - generic [ref=e189]:
                - heading "Pulso de Hostilidade" [level=2] [ref=e190]:
                  - img [ref=e191]
                  - text: Pulso de Hostilidade
                - paragraph [ref=e193]: Análise Quantitativa / Último Período
              - generic [ref=e196]: Live Monitor
            - application [ref=e200]:
              - generic [ref=e210]:
                - generic [ref=e212]: 11h
                - generic [ref=e214]: 16h
          - generic [ref=e215]:
            - generic [ref=e216]:
              - heading "Espectro de Ameaça" [level=2] [ref=e217]:
                - img [ref=e218]
                - text: Espectro de Ameaça
              - paragraph [ref=e220]: Perfil Qualitativo / MCA v2.2
            - application [ref=e224]:
              - generic [ref=e244]:
                - generic [ref=e246]: AMEACA
                - generic [ref=e249]: INSULTO
                - generic [ref=e252]: ATAQUE
                - generic [ref=e254]: ODIO
                - generic [ref=e257]: GENERO
                - generic [ref=e260]: CRIME
            - generic [ref=e261]:
              - generic [ref=e262]:
                - generic [ref=e263]: 34.2%
                - generic [ref=e264]: Densidade de Ódio
              - generic [ref=e265]:
                - generic [ref=e266]: Ativo
                - generic [ref=e267]: Gatilho de Crise
          - generic [ref=e268]:
            - generic [ref=e269]:
              - heading "Termômetro Nacional" [level=2] [ref=e270]:
                - img [ref=e271]
                - text: Termômetro Nacional
              - paragraph [ref=e274]: Concentração de Hostilidade por Estado
            - generic [ref=e275]:
              - generic [ref=e277]:
                - generic [ref=e278]:
                  - generic [ref=e279]: MA
                  - generic [ref=e280]: alvos
                - generic [ref=e281]: "9"
              - generic [ref=e285]:
                - generic [ref=e286]:
                  - generic [ref=e287]: SP
                  - generic [ref=e288]: alvos
                - generic [ref=e289]: "2"
              - generic [ref=e293]:
                - generic [ref=e294]:
                  - generic [ref=e295]: RN
                  - generic [ref=e296]: alvos
                - generic [ref=e297]: "1"
            - generic [ref=e301]:
              - generic [ref=e302]:
                - img [ref=e303]
                - text: Radar Geográfico
              - paragraph [ref=e305]: Mapeamento em tempo real do epicentro dos ataques, permitindo mobilização jurídica e de RP direcionada por região.
        - generic [ref=e306]:
          - generic [ref=e307]:
            - heading "📰 Destaques Recentes" [level=2] [ref=e308]
            - link "Ver tudo →" [ref=e309] [cursor=pointer]:
              - /url: /alertas
          - generic [ref=e310]:
            - article [ref=e311] [cursor=pointer]:
              - generic [ref=e312]:
                - generic [ref=e313]:
                  - generic [ref=e314]: AL
                  - generic [ref=e315]:
                    - paragraph [ref=e316]: allysonbezerra.rn
                    - paragraph [ref=e317]: 04/07/2026, 13:53:28
                - generic [ref=e318]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e319]
              - paragraph [ref=e320]: 167razoesrn...
              - generic [ref=e322]: CAMPANHA_COORDENADA
              - generic [ref=e323]:
                - generic [ref=e324]: 1 Evento(s) Analisado(s)
                - link "Explorar Dados →" [ref=e325]:
                  - /url: /analise
                  - text: Explorar Dados
                  - generic [ref=e326]: →
            - article [ref=e327] [cursor=pointer]:
              - generic [ref=e328]:
                - generic [ref=e329]:
                  - generic [ref=e330]: CA
                  - generic [ref=e331]:
                    - paragraph [ref=e332]: carlosbrandaooficial
                    - paragraph [ref=e333]: 04/07/2026, 08:08:00
                - generic [ref=e334]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e335]
              - paragraph [ref=e336]: Felicidades meu amigo que o senhor sempre te proteja . Estamos com saudades de vc . Abraços de toda nossa família feliz ...
              - generic [ref=e338]: CAMPANHA_COORDENADA
              - generic [ref=e339]:
                - generic [ref=e340]: 1 Evento(s) Analisado(s)
                - link "Explorar Dados →" [ref=e341]:
                  - /url: /analise
                  - text: Explorar Dados
                  - generic [ref=e342]: →
            - article [ref=e343] [cursor=pointer]:
              - generic [ref=e344]:
                - generic [ref=e345]:
                  - generic [ref=e346]: CA
                  - generic [ref=e347]:
                    - paragraph [ref=e348]: carlosbrandaooficial
                    - paragraph [ref=e349]: 04/07/2026, 08:08:00
                - generic [ref=e350]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e351]
              - paragraph [ref=e352]: Parabéns meu irmão...
              - generic [ref=e354]: CAMPANHA_COORDENADA
              - generic [ref=e355]:
                - generic [ref=e356]: 1 Evento(s) Analisado(s)
                - link "Explorar Dados →" [ref=e357]:
                  - /url: /analise
                  - text: Explorar Dados
                  - generic [ref=e358]: →
            - article [ref=e359] [cursor=pointer]:
              - generic [ref=e360]:
                - generic [ref=e361]:
                  - generic [ref=e362]: CA
                  - generic [ref=e363]:
                    - paragraph [ref=e364]: carlosbrandaooficial
                    - paragraph [ref=e365]: 04/07/2026, 08:08:00
                - generic [ref=e366]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e367]
              - paragraph [ref=e368]: Parabéns meu amigo Deus abençoe sua vida tudo de bom pra vc e sua família....
              - generic [ref=e370]: CAMPANHA_COORDENADA
              - generic [ref=e371]:
                - generic [ref=e372]: 1 Evento(s) Analisado(s)
                - link "Explorar Dados →" [ref=e373]:
                  - /url: /analise
                  - text: Explorar Dados
                  - generic [ref=e374]: →
            - article [ref=e375] [cursor=pointer]:
              - generic [ref=e376]:
                - generic [ref=e377]:
                  - generic [ref=e378]: CA
                  - generic [ref=e379]:
                    - paragraph [ref=e380]: carlosbrandaooficial
                    - paragraph [ref=e381]: 04/07/2026, 08:08:00
                - generic [ref=e382]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e383]
              - paragraph [ref=e384]: Parabéns meu ami, felicidades!!...
              - generic [ref=e386]: CAMPANHA_COORDENADA
              - generic [ref=e387]:
                - generic [ref=e388]: 1 Evento(s) Analisado(s)
                - link "Explorar Dados →" [ref=e389]:
                  - /url: /analise
                  - text: Explorar Dados
                  - generic [ref=e390]: →
        - generic "Espaço Publicitário" [ref=e391]:
          - insertion [ref=e392]:
            - iframe [ref=e394]:
              
        - generic [ref=e395]:
          - generic [ref=e396]:
            - generic [ref=e397]: 🔬
            - heading "Análises e Insights" [level=2] [ref=e398]
          - generic [ref=e399]:
            - generic [ref=e402]:
              - img [ref=e404]
              - generic [ref=e407]:
                - generic [ref=e408]:
                  - heading "Padrão de Discurso" [level=3] [ref=e409]
                  - generic [ref=e410]: TENDÊNCIA
                - paragraph [ref=e411]: Análise volumétrica da hostilidade detectada nos alvos ativos.
                - generic [ref=e412]:
                  - paragraph [ref=e413]: Saúde do Discurso
                  - paragraph [ref=e414]: 94.3%
                - paragraph [ref=e416]:
                  - strong [ref=e417]: "Insight Analítico:"
                  - text: A tendência indica estabilidade com picos isolados de hostilidade ad hominem.
                - generic [ref=e418]:
                  - generic [ref=e419]:
                    - generic [ref=e420]: "CONFIANÇA:"
                    - generic [ref=e421]: 94%
                  - generic [ref=e422]:
                    - generic [ref=e423]: "FONTES:"
                    - generic [ref=e424]: 64066 posts
                - link "Explorar dados completos →" [ref=e425] [cursor=pointer]:
                  - /url: /analise
            - generic [ref=e428]:
              - img [ref=e430]
              - generic [ref=e432]:
                - generic [ref=e433]:
                  - heading "Comportamento Coordenado" [level=3] [ref=e434]
                  - generic [ref=e435]: PADRÃO
                - paragraph [ref=e436]: Detecção de mensagens idênticas ou altamente similares em massa.
                - paragraph [ref=e438]:
                  - strong [ref=e439]: "Insight Analítico:"
                  - text: Monitoramento Solenya v71.0 ativo. Buscando padrões de automação.
                - generic [ref=e440]:
                  - generic [ref=e441]:
                    - generic [ref=e442]: "CONFIANÇA:"
                    - generic [ref=e443]: 88%
                  - generic [ref=e444]:
                    - generic [ref=e445]: "FONTES:"
                    - generic [ref=e446]: 64066 posts
                - link "Explorar dados completos →" [ref=e447] [cursor=pointer]:
                  - /url: /analise
        - generic [ref=e448]:
          - generic [ref=e449]:
            - generic [ref=e450]:
              - generic [ref=e451]: 👤
              - heading "Perfis em Destaque" [level=2] [ref=e452]
            - paragraph [ref=e453]: Use as setas para explorar →
          - generic [ref=e455]:
            - button "Candidato Anterior" [ref=e456]:
              - img [ref=e457]
            - button "Próximo Candidato" [ref=e459]:
              - img [ref=e460]
            - generic [ref=e471]:
              - generic [ref=e473]: CI
              - generic [ref=e474]:
                - generic [ref=e475]:
                  - heading "@cirogomes" [level=3] [ref=e476]
                  - generic [ref=e477]: Ativo
                - generic [ref=e479]:
                  - paragraph [ref=e480]: PDT | Influenciador Político
                  - paragraph [ref=e481]: "Monitorado desde: N/A"
              - generic [ref=e483]:
                - paragraph [ref=e484]: Score Risco
                - paragraph [ref=e485]: "0"
            - generic [ref=e486]:
              - generic [ref=e487]:
                - generic [ref=e488]:
                  - img [ref=e489]
                  - paragraph [ref=e491]: Incidentes Detectados
                - generic [ref=e492]:
                  - paragraph [ref=e494]: "0"
                  - paragraph [ref=e495]: comentários hostis validados
              - generic [ref=e496]:
                - generic [ref=e497]:
                  - img [ref=e498]
                  - paragraph [ref=e500]: Nível de Ameaça
                - generic [ref=e501]:
                  - generic [ref=e502]:
                    - paragraph [ref=e503]: "0"
                    - generic [ref=e504]: /100
                  - paragraph [ref=e506]: índice de periculosidade
              - generic [ref=e507]:
                - generic [ref=e508]:
                  - img [ref=e509]
                  - paragraph [ref=e513]: Vetores de Ataque
                - generic [ref=e514]:
                  - paragraph [ref=e516]: "0"
                  - paragraph [ref=e517]: categorias de ódio distintas
            - generic [ref=e518]:
              - heading "Alertas de Segurança" [level=4] [ref=e519]:
                - img [ref=e520]
                - text: Alertas de Segurança
              - generic [ref=e523]:
                - generic [ref=e524]: Nível CONTROLADO
                - generic [ref=e525]: Atualizado agora
        - generic [ref=e526]:
          - generic [ref=e527]:
            - img [ref=e528]
            - heading "📖 Sobre Este Observatório" [level=3] [ref=e530]
          - generic [ref=e531]:
            - generic [ref=e532]:
              - generic [ref=e533]:
                - paragraph [ref=e534]:
                  - text: O
                  - strong [ref=e535]: Sentinela
                  - text: monitora padrões de discurso em redes sociais para promover transparência e alimentar o debate democrático brasileiro.
                - paragraph [ref=e536]: Nossa plataforma identifica tendências de ódio, hostilidade e desinformação, fornecendo dados técnicos para a sociedade civil e órgãos de controle.
              - generic [ref=e537]:
                - heading "O Que Fazemos" [level=4] [ref=e538]:
                  - img [ref=e539]
                  - text: O Que Fazemos
                - list [ref=e542]:
                  - listitem [ref=e543]:
                    - generic [ref=e544]: ✓
                    - text: Coleta autônoma de posts públicos em redes sociais
                  - listitem [ref=e545]:
                    - generic [ref=e546]: ✓
                    - text: Identificação de padrões de discurso de ódio e violência
                  - listitem [ref=e547]:
                    - generic [ref=e548]: ✓
                    - text: Relatórios analíticos com classificação semântica MCA v2.2
                  - listitem [ref=e549]:
                    - generic [ref=e550]: ✓
                    - text: Alertas em tempo real sobre picos anormais de hostilidade
            - generic [ref=e551]:
              - generic [ref=e552]:
                - heading "Limitações Importantes" [level=4] [ref=e553]:
                  - img [ref=e554]
                  - text: Limitações Importantes
                - list [ref=e556]:
                  - listitem [ref=e557]:
                    - generic [ref=e558]: ⚠️
                    - text: Não substitui análise humana — ferramenta de pesquisa
                  - listitem [ref=e559]:
                    - generic [ref=e560]: ⚠️
                    - text: Baseado em posts públicos — não detecta contas privadas
                  - listitem [ref=e561]:
                    - generic [ref=e562]: ⚠️
                    - text: Classificação por IA — sujeita a falsos positivos
                  - listitem [ref=e563]:
                    - generic [ref=e564]: ⚠️
                    - text: Não visa julgamento político, apenas transparência de dados
              - generic [ref=e565]:
                - heading "Metodologia Técnica" [level=4] [ref=e566]:
                  - img [ref=e567]
                  - text: Metodologia Técnica
                - generic [ref=e570]:
                  - paragraph [ref=e571]:
                    - strong [ref=e572]: "Coleta:"
                    - text: Motores Playwright v2 / Zyte
                  - paragraph [ref=e573]:
                    - strong [ref=e574]: "Processamento:"
                    - text: Análise semântica Híbrida (Mistral/Ollama)
                  - paragraph [ref=e575]:
                    - strong [ref=e576]: "Protocolo:"
                    - text: PASA v70.4 — Critérios de Análise
                  - paragraph [ref=e577]:
                    - strong [ref=e578]: "Frequência:"
                    - text: Ciclos de 24h com Autopilot L3
          - generic [ref=e579]:
            - paragraph [ref=e580]: 📚 Explore nossa documentação técnica para entender os algoritmos.
            - generic [ref=e581]:
              - link "Documentação" [ref=e582] [cursor=pointer]:
                - /url: /metodologia
              - link "Publicações" [ref=e583] [cursor=pointer]:
                - /url: /dossies
        - generic "Espaço Publicitário" [ref=e584]:
          - insertion [ref=e585]
        - generic [ref=e589]:
          - generic [ref=e590]: 💎
          - heading "Inteligência Ilimitada" [level=3] [ref=e591]
          - paragraph [ref=e592]: Dossiês completos, análise de grafos de influência e relatórios em tempo real com validade técnica.
          - generic [ref=e593]:
            - button "Adquirir Créditos de Inteligência" [ref=e594]
            - paragraph [ref=e595]: Opere na rede a partir de 1.000 CI
        - generic [ref=e596]:
          - generic [ref=e597]:
            - generic [ref=e598]: S
            - paragraph [ref=e599]: SentinelaDemocrática
          - paragraph [ref=e600]: Tecnologia de vigilância cívica para a transparência do processo democrático brasileiro.
          - generic [ref=e601]:
            - link "Termos" [ref=e602] [cursor=pointer]:
              - /url: /termos
            - link "Metodologia" [ref=e603] [cursor=pointer]:
              - /url: /metodologia
            - link "LGPD" [ref=e604] [cursor=pointer]:
              - /url: /lgpd
            - link "Privacidade" [ref=e605] [cursor=pointer]:
              - /url: /privacidade
            - link "GitHub" [ref=e606] [cursor=pointer]:
              - /url: https://github.com/THIAGO/sentinela
  - alert [ref=e607]
  - generic [ref=e608]: 23h
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const PRODUCTION_URL = 'https://asentinela.vercel.app';
  4  | 
  5  | test('debug production site', async ({ page }) => {
  6  |     page.on('console', msg => console.log(`BROWSER CONSOLE: ${msg.text()}`));
  7  |     page.on('requestfailed', request => console.log(`REQUEST FAILED: ${request.url()} - ${request.failure()?.errorText}`));
  8  |     page.on('response', response => {
  9  |         if (response.status() >= 400) {
  10 |             console.log(`RESPONSE ERROR: ${response.status()} ${response.url()}`);
  11 |         }
  12 |     });
  13 | 
  14 |     await page.goto(PRODUCTION_URL);
  15 |     await page.waitForLoadState('networkidle');
  16 | 
  17 |     const title = await page.title();
  18 |     console.log(`Page Title: ${title}`);
  19 | 
  20 |     const kpiMonitorados = page.locator('#kpi-monitorados');
> 21 |     const text = await kpiMonitorados.innerText();
     |                                       ^ Error: locator.innerText: Test timeout of 30000ms exceeded.
  22 |     console.log(`KPI Monitorados current text: ${text}`);
  23 | 
  24 |     // Screenshot for visual check
  25 |     await page.screenshot({ path: 'debug_production.png' });
  26 | });
  27 | 
```