# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\final_audit.spec.ts >> AdSense and UI Refinement Final Verification
- Location: tests\final_audit.spec.ts:5:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.hover: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('div.group').filter({ hasText: 'Perfis em Destaque' })

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
        - button "CANDIDATOS" [ref=e19]:
          - img [ref=e20]
          - generic [ref=e25]: CANDIDATOS
        - button "ALERTAS" [ref=e26]:
          - img [ref=e27]
          - generic [ref=e29]: ALERTAS
        - button "TENDÊNCIAS" [ref=e30]:
          - img [ref=e31]
          - generic [ref=e34]: TENDÊNCIAS
        - button "RELATÓRIOS" [ref=e35]:
          - img [ref=e36]
          - generic [ref=e39]: RELATÓRIOS
      - generic [ref=e40]:
        - generic [ref=e43]: Monitor Ativo
        - generic [ref=e44]: OBSERVATÓRIO CÍVICO
    - main [ref=e45]:
      - main [ref=e48]:
        - generic [ref=e49]:
          - generic [ref=e50]:
            - generic [ref=e51]:
              - generic [ref=e52]: 📊
              - generic [ref=e53]:
                - paragraph [ref=e54]: Observatório de Discurso Cívico
                - heading "Tendências no Discurso Político Brasileiro" [level=1] [ref=e55]
            - paragraph [ref=e56]: Acompanhe em tempo real os padrões de discurso de ódio e violência em redes sociais de candidatos e políticos monitorados. Transparência que alimenta a democracia.
          - generic [ref=e57]:
            - generic [ref=e58]:
              - generic [ref=e59]:
                - img [ref=e60]
                - generic [ref=e62]: Alertas Acumulados
              - generic [ref=e63]: "656"
              - paragraph [ref=e64]: Casos com ódio identificados
            - generic [ref=e65]:
              - generic [ref=e66]:
                - img [ref=e67]
                - generic [ref=e72]: Monitorados
              - generic [ref=e73]: "363"
              - paragraph [ref=e74]: Candidatos sob observação
            - generic [ref=e75]:
              - generic [ref=e76]:
                - img [ref=e77]
                - generic [ref=e80]: Posts Processados
              - generic [ref=e81]: 18.9k
              - paragraph [ref=e82]: Total coletados
          - generic [ref=e84]:
            - generic [ref=e85]: ⚡
            - generic [ref=e86]:
              - heading "Análise de Resiliência Democrática" [level=3] [ref=e87]
              - paragraph [ref=e88]: O sistema detectou um índice de resiliência de 96.5% no discurso das redes sociais brasileiras nas últimas 24h.
              - generic [ref=e89]:
                - button "Ver Detalhes" [ref=e90]
                - button "Compartilhar" [ref=e91]
        - generic [ref=e92]:
          - generic [ref=e93]:
            - heading "Atividade de Hostilidade (24h)" [level=2] [ref=e94]: Atividade de Hostilidade (24h)
            - generic [ref=e96]: Monitoramento Live Ativo
          - application [ref=e100]:
            - generic [ref=e110]:
              - generic [ref=e112]: 13h
              - generic [ref=e114]: 14h
              - generic [ref=e116]: 17h
              - generic [ref=e118]: 18h
              - generic [ref=e120]: 20h
              - generic [ref=e122]: 21h
              - generic [ref=e124]: 22h
              - generic [ref=e126]: 23h
              - generic [ref=e128]: 00h
              - generic [ref=e130]: 01h
              - generic [ref=e132]: 02h
              - generic [ref=e134]: 03h
              - generic [ref=e136]: 04h
              - generic [ref=e138]: 05h
              - generic [ref=e140]: 06h
              - generic [ref=e142]: 07h
              - generic [ref=e144]: 08h
              - generic [ref=e146]: 10h
              - generic [ref=e148]: 12h
              - generic [ref=e150]: 13h
              - generic [ref=e152]: 14h
              - generic [ref=e154]: 16h
              - generic [ref=e156]: 17h
        - generic [ref=e157]:
          - generic [ref=e158]:
            - heading "📰 Destaques Recentes" [level=2] [ref=e159]
            - button "Ver tudo →" [ref=e160]
          - generic [ref=e161]:
            - article [ref=e162] [cursor=pointer]:
              - generic [ref=e163]:
                - generic [ref=e164]:
                  - generic [ref=e165]: FE
                  - generic [ref=e166]:
                    - paragraph [ref=e167]: fernandoholiday
                    - paragraph [ref=e168]: 26/05/2026, 14:10:57
                - generic [ref=e169]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e170]
              - paragraph [ref=e171]: Irmão a lei tá aí. Simples é só processar vai ficar pondo a culpa nos outros até quando? Entra com um processo e tchau b...
              - generic [ref=e173]: INSULTO_AD_HOMINEM
              - generic [ref=e174]:
                - generic [ref=e175]: 1 caso(s) identificado(s)
                - button "Analisar Perícia →" [ref=e176]
            - article [ref=e177] [cursor=pointer]:
              - generic [ref=e178]:
                - generic [ref=e179]:
                  - generic [ref=e180]: FE
                  - generic [ref=e181]:
                    - paragraph [ref=e182]: fernandoholiday
                    - paragraph [ref=e183]: 26/05/2026, 14:10:57
                - generic [ref=e184]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e185]
              - paragraph [ref=e186]: Muié pode tudo, não vai acontecer nada. Agora se fosse um homem cristão de ultra direita já tinha sido preso ali mesmo....
              - generic [ref=e188]: MISOGINIA_POLITICA
              - generic [ref=e189]:
                - generic [ref=e190]: 1 caso(s) identificado(s)
                - button "Analisar Perícia →" [ref=e191]
            - article [ref=e192] [cursor=pointer]:
              - generic [ref=e193]:
                - generic [ref=e194]:
                  - generic [ref=e195]: FE
                  - generic [ref=e196]:
                    - paragraph [ref=e197]: fernandoholiday
                    - paragraph [ref=e198]: 26/05/2026, 14:10:57
                - generic [ref=e199]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e200]
              - paragraph [ref=e201]: Nunca foi pelo bem. Sempre por ideologia. Já passou da hora de Despertar....
              - generic [ref=e203]: INSULTO_AD_HOMINEM
              - generic [ref=e204]:
                - generic [ref=e205]: 1 caso(s) identificado(s)
                - button "Analisar Perícia →" [ref=e206]
            - article [ref=e207] [cursor=pointer]:
              - generic [ref=e208]:
                - generic [ref=e209]:
                  - generic [ref=e210]: FE
                  - generic [ref=e211]:
                    - paragraph [ref=e212]: fernandoholiday
                    - paragraph [ref=e213]: 26/05/2026, 14:10:57
                - generic [ref=e214]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e215]
              - paragraph [ref=e216]: Imaginem se fosse o Monark falando algo assim, sairia preso na mesma hora!...
              - generic [ref=e218]: ATAQUE_INSTITUCIONAL
              - generic [ref=e219]:
                - generic [ref=e220]: 1 caso(s) identificado(s)
                - button "Analisar Perícia →" [ref=e221]
            - article [ref=e222] [cursor=pointer]:
              - generic [ref=e223]:
                - generic [ref=e224]:
                  - generic [ref=e225]: FE
                  - generic [ref=e226]:
                    - paragraph [ref=e227]: fernandoholiday
                    - paragraph [ref=e228]: 26/05/2026, 14:10:57
                - generic [ref=e229]: Médio
              - heading "Discurso de ódio detectado" [level=3] [ref=e230]
              - paragraph [ref=e231]: Eu fiquei muito incomodada com esse assédio, que baixaria. Tem sim que ser processada...
              - generic [ref=e233]: INSULTO_AD_HOMINEM
              - generic [ref=e234]:
                - generic [ref=e235]: 1 caso(s) identificado(s)
                - button "Analisar Perícia →" [ref=e236]
        - generic [ref=e237]:
          - heading "🔬 Análises e Insights" [level=2] [ref=e238]
          - generic [ref=e239]:
            - generic [ref=e241]:
              - img [ref=e243]
              - generic [ref=e246]:
                - generic [ref=e247]:
                  - heading "Padrão de Discurso" [level=3] [ref=e248]
                  - generic [ref=e249]: TENDÊNCIA
                - paragraph [ref=e250]: Análise volumétrica da hostilidade detectada nos alvos ativos.
                - generic [ref=e251]:
                  - paragraph [ref=e252]: 📊 Saúde do Discurso
                  - paragraph [ref=e253]: 96.5%
                - paragraph [ref=e255]:
                  - strong [ref=e256]: "💡 Insight:"
                  - text: A tendência indica estabilidade com picos isolados de hostilidade ad hominem.
                - generic [ref=e257]:
                  - generic [ref=e258]:
                    - generic [ref=e259]: "CONFIANÇA:"
                    - generic [ref=e260]: 94%
                  - generic [ref=e261]:
                    - generic [ref=e262]: "FONTES:"
                    - generic [ref=e263]: 18932 posts
                - button "Explorar dados completos →" [ref=e264]
            - generic [ref=e266]:
              - img [ref=e268]
              - generic [ref=e270]:
                - generic [ref=e271]:
                  - heading "Comportamento Coordenado" [level=3] [ref=e272]
                  - generic [ref=e273]: PADRÃO
                - paragraph [ref=e274]: Detecção de mensagens idênticas ou altamente similares em massa.
                - paragraph [ref=e276]:
                  - strong [ref=e277]: "💡 Insight:"
                  - text: Monitoramento Solenya v71.0 ativo. Buscando padrões de automação.
                - generic [ref=e278]:
                  - generic [ref=e279]:
                    - generic [ref=e280]: "CONFIANÇA:"
                    - generic [ref=e281]: 88%
                  - generic [ref=e282]:
                    - generic [ref=e283]: "FONTES:"
                    - generic [ref=e284]: 18932 posts
                - button "Explorar dados completos →" [ref=e285]
        - generic [ref=e286]:
          - generic [ref=e287]:
            - heading "📅 Linha do Tempo" [level=2] [ref=e288]
            - generic [ref=e289]:
              - button "24h" [ref=e290]
              - button "7d" [ref=e291]
              - button "30d" [ref=e292]
          - paragraph [ref=e293]: Cronograma de eventos e picos de atividade (Últimas 24 Horas)
          - generic [ref=e294]:
            - generic [ref=e300]:
              - generic [ref=e301]:
                - generic [ref=e302]:
                  - paragraph [ref=e303]: 14:10
                  - heading "MISOGINIA_POLITICA" [level=4] [ref=e304]
                - generic [ref=e306]: 1 posts
              - paragraph [ref=e307]: Muié pode tudo, não vai acontecer nada. Agora se fosse um homem cristão de ultra direita já tinha si...
              - generic [ref=e308]:
                - generic [ref=e309]:
                  - text: "Candidato:"
                  - strong [ref=e310]: "@fernandoholiday"
                - generic [ref=e311]:
                  - text: "Engajamento:"
                  - strong [ref=e312]: 46%
            - generic [ref=e318]:
              - generic [ref=e319]:
                - generic [ref=e320]:
                  - paragraph [ref=e321]: 14:10
                  - heading "INSULTO_AD_HOMINEM" [level=4] [ref=e322]
                - generic [ref=e324]: 1 posts
              - paragraph [ref=e325]: Nunca foi pelo bem. Sempre por ideologia. Já passou da hora de Despertar....
              - generic [ref=e326]:
                - generic [ref=e327]:
                  - text: "Candidato:"
                  - strong [ref=e328]: "@fernandoholiday"
                - generic [ref=e329]:
                  - text: "Engajamento:"
                  - strong [ref=e330]: 52%
            - generic [ref=e336]:
              - generic [ref=e337]:
                - generic [ref=e338]:
                  - paragraph [ref=e339]: 14:10
                  - heading "INSULTO_AD_HOMINEM" [level=4] [ref=e340]
                - generic [ref=e342]: 1 posts
              - paragraph [ref=e343]: Irmão a lei tá aí. Simples é só processar vai ficar pondo a culpa nos outros até quando? Entra com u...
              - generic [ref=e344]:
                - generic [ref=e345]:
                  - text: "Candidato:"
                  - strong [ref=e346]: "@fernandoholiday"
                - generic [ref=e347]:
                  - text: "Engajamento:"
                  - strong [ref=e348]: 56%
            - generic [ref=e354]:
              - generic [ref=e355]:
                - generic [ref=e356]:
                  - paragraph [ref=e357]: 14:10
                  - heading "ATAQUE_INSTITUCIONAL" [level=4] [ref=e358]
                - generic [ref=e360]: 1 posts
              - paragraph [ref=e361]: Se fosse ao contrário já estariam pedindo 14 anos de prisão 🙄...
              - generic [ref=e362]:
                - generic [ref=e363]:
                  - text: "Candidato:"
                  - strong [ref=e364]: "@fernandoholiday"
                - generic [ref=e365]:
                  - text: "Engajamento:"
                  - strong [ref=e366]: 98%
            - generic [ref=e371]:
              - generic [ref=e372]:
                - generic [ref=e373]:
                  - paragraph [ref=e374]: 14:10
                  - heading "ATAQUE_INSTITUCIONAL" [level=4] [ref=e375]
                - generic [ref=e377]: 1 posts
              - paragraph [ref=e378]: Imaginem se fosse o Monark falando algo assim, sairia preso na mesma hora!...
              - generic [ref=e379]:
                - generic [ref=e380]:
                  - text: "Candidato:"
                  - strong [ref=e381]: "@fernandoholiday"
                - generic [ref=e382]:
                  - text: "Engajamento:"
                  - strong [ref=e383]: 23%
        - generic [ref=e384]:
          - generic [ref=e385]:
            - heading "👤 Perfis em Destaque" [level=2] [ref=e386]
            - paragraph [ref=e387]: Use as setas para explorar →
          - generic [ref=e389]:
            - button "Candidato Anterior" [ref=e390]:
              - img [ref=e391]
            - button "Próximo Candidato" [ref=e393]:
              - img [ref=e394]
            - generic [ref=e405]:
              - generic [ref=e407]: JA
              - generic [ref=e408]:
                - generic [ref=e409]:
                  - heading "@janainacpaschoal" [level=3] [ref=e410]
                  - generic [ref=e411]: Ativo
                - generic [ref=e413]:
                  - paragraph [ref=e414]: N/A | Não especificado
                  - paragraph [ref=e415]: "Monitorado desde: 26/05/2026"
              - generic [ref=e417]:
                - paragraph [ref=e418]: Score Risco
                - paragraph [ref=e419]: "0"
            - generic [ref=e420]:
              - generic [ref=e421]:
                - paragraph [ref=e422]: Comentários
                - generic [ref=e423]:
                  - paragraph [ref=e424]: "56"
                  - generic [ref=e425]:
                    - img [ref=e426]
                    - generic [ref=e429]: 15%
              - generic [ref=e430]:
                - paragraph [ref=e431]: Nível de Risco
                - generic [ref=e432]:
                  - paragraph [ref=e433]: "0"
                  - generic [ref=e434]:
                    - img [ref=e435]
                    - generic [ref=e438]: 8%
              - generic [ref=e439]:
                - paragraph [ref=e440]: Categorias
                - paragraph [ref=e442]: "5"
            - generic [ref=e443]:
              - heading "Alertas de Segurança" [level=4] [ref=e444]:
                - img [ref=e445]
                - text: Alertas de Segurança
              - generic [ref=e448]:
                - generic [ref=e449]: Nível CONTROLADO
                - generic [ref=e450]: Atualizado agora
        - generic [ref=e451]:
          - generic [ref=e452]:
            - img [ref=e453]
            - heading "📖 Sobre Este Observatório" [level=3] [ref=e455]
          - generic [ref=e456]:
            - generic [ref=e457]:
              - generic [ref=e458]:
                - paragraph [ref=e459]:
                  - text: O
                  - strong [ref=e460]: Sentinela
                  - text: monitora padrões de discurso em redes sociais para promover transparência e alimentar o debate democrático brasileiro.
                - paragraph [ref=e461]: Nossa plataforma identifica tendências de ódio, hostilidade e desinformação, fornecendo dados técnicos para a sociedade civil e órgãos de controle.
              - generic [ref=e462]:
                - heading "O Que Fazemos" [level=4] [ref=e463]:
                  - img [ref=e464]
                  - text: O Que Fazemos
                - list [ref=e467]:
                  - listitem [ref=e468]:
                    - generic [ref=e469]: ✓
                    - text: Coleta autônoma de posts públicos em redes sociais
                  - listitem [ref=e470]:
                    - generic [ref=e471]: ✓
                    - text: Identificação de padrões de discurso de ódio e violência
                  - listitem [ref=e472]:
                    - generic [ref=e473]: ✓
                    - text: Relatórios forenses com classificação semântica MCA v2.2
                  - listitem [ref=e474]:
                    - generic [ref=e475]: ✓
                    - text: Alertas em tempo real sobre picos anormais de hostilidade
            - generic [ref=e476]:
              - generic [ref=e477]:
                - heading "Limitações Importantes" [level=4] [ref=e478]:
                  - img [ref=e479]
                  - text: Limitações Importantes
                - list [ref=e481]:
                  - listitem [ref=e482]:
                    - generic [ref=e483]: ⚠️
                    - text: Não substitui análise humana — ferramenta de pesquisa
                  - listitem [ref=e484]:
                    - generic [ref=e485]: ⚠️
                    - text: Baseado em posts públicos — não detecta contas privadas
                  - listitem [ref=e486]:
                    - generic [ref=e487]: ⚠️
                    - text: Classificação por IA — sujeita a falsos positivos
                  - listitem [ref=e488]:
                    - generic [ref=e489]: ⚠️
                    - text: Não visa julgamento político, apenas transparência de dados
              - generic [ref=e490]:
                - heading "Metodologia Técnica" [level=4] [ref=e491]:
                  - img [ref=e492]
                  - text: Metodologia Técnica
                - generic [ref=e495]:
                  - paragraph [ref=e496]:
                    - strong [ref=e497]: "Coleta:"
                    - text: Motores Playwright v2 / Zyte
                  - paragraph [ref=e498]:
                    - strong [ref=e499]: "Processamento:"
                    - text: Análise semântica Híbrida (Mistral/Ollama)
                  - paragraph [ref=e500]:
                    - strong [ref=e501]: "Protocolo:"
                    - text: PASA v70.4 — Critérios Forenses
                  - paragraph [ref=e502]:
                    - strong [ref=e503]: "Frequência:"
                    - text: Ciclos de 24h com Autopilot L3
          - generic [ref=e504]:
            - paragraph [ref=e505]: 📚 Explore nossa documentação técnica para entender os algoritmos.
            - generic [ref=e506]:
              - button "Documentação" [ref=e507]
              - button "Publicações" [ref=e508]
        - generic [ref=e511]:
          - generic [ref=e512]: 💎
          - heading "Inteligência Ilimitada" [level=3] [ref=e513]
          - paragraph [ref=e514]: Dossiês completos, análise de grafos de influência e relatórios em tempo real com validade técnica.
          - generic [ref=e515]:
            - button "Ver Planos de Acesso" [ref=e516]
            - paragraph [ref=e517]: Apoie o observatório a partir de R$ 99/mês
        - generic [ref=e518]:
          - generic [ref=e519]:
            - generic [ref=e520]: S
            - paragraph [ref=e521]: SentinelaDemocrática
          - paragraph [ref=e522]: Tecnologia de vigilância cívica para a transparência do processo democrático brasileiro.
          - generic [ref=e523]:
            - button "Termos" [ref=e524]
            - button "Metodologia" [ref=e525]
            - button "LGPD" [ref=e526]
            - button "Privacidade" [ref=e527]
            - button "GitHub" [ref=e528]
  - alert [ref=e529]
  - generic [ref=e530]: 18h
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const PRODUCTION_URL = 'https://asentinela.vercel.app';
  4  | 
  5  | test('AdSense and UI Refinement Final Verification', async ({ page }) => {
  6  |   await page.goto(PRODUCTION_URL);
  7  | 
  8  |   // 1. Verify Raw Script tag in HEAD
  9  |   const scriptSource = await page.innerHTML('head');
  10 |   expect(scriptSource).toContain('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1827611269042960');
  11 | 
  12 |   // 2. Verify H1 title content and single-line classes
  13 |   const h1 = page.getByRole('heading', { name: 'Tendências no Discurso Político Brasileiro' });
  14 |   await expect(h1).toBeVisible();
  15 |   
  16 |   // 3. Verify Carousel controls visibility on hover
> 17 |   await page.locator('div.group').filter({ hasText: 'Perfis em Destaque' }).hover();
     |                                                                             ^ Error: locator.hover: Test timeout of 30000ms exceeded.
  18 |   await expect(page.getByLabel('Próximo Candidato')).toBeVisible();
  19 | 
  20 |   // 4. Verify Internal Page formatting (Candidatos)
  21 |   await page.goto(`${PRODUCTION_URL}/alvos`);
  22 |   await expect(page.getByRole('heading', { name: 'Central de Candidatos' })).toBeVisible();
  23 |   await expect(page.getByText('Radar de Severidade e Atividade')).toBeVisible();
  24 | 
  25 |   console.log('✅ Final Operational Check Passed: AdSense script is RAW, H1 is fixed, and internal pages are Editorial.');
  26 | });
  27 | 
```