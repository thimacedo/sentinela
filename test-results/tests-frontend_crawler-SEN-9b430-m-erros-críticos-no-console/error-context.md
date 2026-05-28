# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\frontend_crawler.spec.ts >> SENTINELA | Frontend Crawler & Button Tester >> Deve renderizar a rota /alertas sem erros críticos no console
- Location: tests\frontend_crawler.spec.ts:22:13

# Error details

```
Error: expect(received).toHaveLength(expected)

Expected length: 0
Received length: 2
Received array:  ["Failed to load resource: the server responded with a status of 404 (Not Found)", "Failed to load resource: the server responded with a status of 400 ()"]
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
      - generic [ref=e47]:
        - generic [ref=e48]:
          - heading "Central de Alertas" [level=1] [ref=e49]
          - paragraph [ref=e50]: Monitoramento crítico de incidentes de hostilidade e ataques coordenados. Cada alerta representa um pulso de atividade que requer atenção técnica.
        - generic [ref=e51]:
          - generic [ref=e52]:
            - generic [ref=e53]:
              - generic [ref=e54]:
                - heading "Alertas de Segurança" [level=2] [ref=e55]:
                  - img [ref=e56]
                  - text: Alertas de Segurança
                - paragraph [ref=e58]: Incidentes Críticos em Tempo Real
              - generic [ref=e59]:
                - img [ref=e60]
                - generic [ref=e62]: Live Monitor
            - generic [ref=e63]:
              - generic [ref=e64]:
                - generic [ref=e66]:
                  - generic [ref=e67]:
                    - generic [ref=e68]:
                      - generic [ref=e69]: SA
                      - generic [ref=e70]:
                        - generic [ref=e71]:
                          - generic [ref=e72]: "@salatiel_de_souza"
                          - generic [ref=e73]: • alvo afetado
                        - generic [ref=e74]:
                          - img [ref=e75]
                          - text: 28/05/2026, 09:16:34
                    - generic [ref=e77]: ATAQUE_INSTITUCIONAL
                  - paragraph [ref=e79]: "\"Se juntou com a esquerda e o PT, da nisso aí 😂😂😂\""
                  - generic [ref=e80]:
                    - generic [ref=e81]:
                      - generic [ref=e82]: "Confiança da IA:"
                      - generic [ref=e83]: 90.0%
                    - button "Investigar" [ref=e84]:
                      - img [ref=e85]
                      - text: Investigar
                - generic [ref=e89]:
                  - generic [ref=e90]:
                    - generic [ref=e91]:
                      - generic [ref=e92]: AL
                      - generic [ref=e93]:
                        - generic [ref=e94]:
                          - generic [ref=e95]: "@alexandreramagem22"
                          - generic [ref=e96]: • alvo afetado
                        - generic [ref=e97]:
                          - img [ref=e98]
                          - text: 28/05/2026, 09:02:06
                    - generic [ref=e100]: INSULTO_AD_HOMINEM
                  - paragraph [ref=e102]: "\"CHUPA LULA!!!!\""
                  - generic [ref=e103]:
                    - generic [ref=e104]:
                      - generic [ref=e105]: "Confiança da IA:"
                      - generic [ref=e106]: 90.0%
                    - button "Investigar" [ref=e107]:
                      - img [ref=e108]
                      - text: Investigar
                - generic [ref=e112]:
                  - generic [ref=e113]:
                    - generic [ref=e114]:
                      - generic [ref=e115]: DE
                      - generic [ref=e116]:
                        - generic [ref=e117]:
                          - generic [ref=e118]: "@deltandallagnol"
                          - generic [ref=e119]: • alvo afetado
                        - generic [ref=e120]:
                          - img [ref=e121]
                          - text: 28/05/2026, 08:52:40
                    - generic [ref=e123]: INSULTO_AD_HOMINEM
                  - paragraph [ref=e125]: "\"apareça Lulinha ......kd vc\""
                  - generic [ref=e126]:
                    - generic [ref=e127]:
                      - generic [ref=e128]: "Confiança da IA:"
                      - generic [ref=e129]: 90.0%
                    - button "Investigar" [ref=e130]:
                      - img [ref=e131]
                      - text: Investigar
                - generic [ref=e135]:
                  - generic [ref=e136]:
                    - generic [ref=e137]:
                      - generic [ref=e138]: DE
                      - generic [ref=e139]:
                        - generic [ref=e140]:
                          - generic [ref=e141]: "@deltandallagnol"
                          - generic [ref=e142]: • alvo afetado
                        - generic [ref=e143]:
                          - img [ref=e144]
                          - text: 28/05/2026, 08:52:40
                    - generic [ref=e146]: ATAQUE_INSTITUCIONAL
                  - paragraph [ref=e148]: "\"INSS?? ...ou melhor uma turminha do \"governo\"\""
                  - generic [ref=e149]:
                    - generic [ref=e150]:
                      - generic [ref=e151]: "Confiança da IA:"
                      - generic [ref=e152]: 90.0%
                    - button "Investigar" [ref=e153]:
                      - img [ref=e154]
                      - text: Investigar
                - generic [ref=e157]:
                  - generic [ref=e158]:
                    - generic [ref=e159]:
                      - generic [ref=e160]:
                        - generic [ref=e161]: DE
                        - generic [ref=e162]:
                          - generic [ref=e163]:
                            - generic [ref=e164]: "@deltandallagnol"
                            - generic [ref=e165]: • alvo afetado
                          - generic [ref=e166]:
                            - img [ref=e167]
                            - text: 28/05/2026, 08:52:40
                      - generic [ref=e169]: ATAQUE_INSTITUCIONAL
                    - paragraph [ref=e171]: "\"É isso que a Globo , e o povo apoia , PT roubando estas pessoas\""
                    - generic [ref=e172]:
                      - generic [ref=e173]:
                        - generic [ref=e174]: "Confiança da IA:"
                        - generic [ref=e175]: 90.0%
                      - button "Investigar" [ref=e176]:
                        - img [ref=e177]
                        - text: Investigar
                  - generic [ref=e180]:
                    - generic [ref=e181]: Publicidade Cívica Relacionada
                    - insertion [ref=e183]:
                      - iframe [ref=e185]:
                        
                - generic [ref=e187]:
                  - generic [ref=e188]:
                    - generic [ref=e189]:
                      - generic [ref=e190]: DE
                      - generic [ref=e191]:
                        - generic [ref=e192]:
                          - generic [ref=e193]: "@deltandallagnol"
                          - generic [ref=e194]: • alvo afetado
                        - generic [ref=e195]:
                          - img [ref=e196]
                          - text: 28/05/2026, 08:52:40
                    - generic [ref=e198]: ATAQUE_INSTITUCIONAL
                  - paragraph [ref=e200]: "\"Lulinha e INSS precisam ser corretamente investigados! Deus fará uma grande limpeza no Brasil! 🙏🏻🇧🇷\""
                  - generic [ref=e201]:
                    - generic [ref=e202]:
                      - generic [ref=e203]: "Confiança da IA:"
                      - generic [ref=e204]: 90.0%
                    - button "Investigar" [ref=e205]:
                      - img [ref=e206]
                      - text: Investigar
                - generic [ref=e210]:
                  - generic [ref=e211]:
                    - generic [ref=e212]:
                      - generic [ref=e213]: JA
                      - generic [ref=e214]:
                        - generic [ref=e215]:
                          - generic [ref=e216]: "@janjalula"
                          - generic [ref=e217]: • alvo afetado
                        - generic [ref=e218]:
                          - img [ref=e219]
                          - text: 28/05/2026, 08:44:21
                    - generic [ref=e221]: ATAQUE_INSTITUCIONAL
                  - paragraph [ref=e223]: "\"Muito orgulho da nossa primeira dama , diferente da outra que só sabia andar com maquiador e tirar as moedas da alvorada.\""
                  - generic [ref=e224]:
                    - generic [ref=e225]:
                      - generic [ref=e226]: "Confiança da IA:"
                      - generic [ref=e227]: 90.0%
                    - button "Investigar" [ref=e228]:
                      - img [ref=e229]
                      - text: Investigar
                - generic [ref=e233]:
                  - generic [ref=e234]:
                    - generic [ref=e235]:
                      - generic [ref=e236]: SU
                      - generic [ref=e237]:
                        - generic [ref=e238]:
                          - generic [ref=e239]: "@supremotribunalfederal"
                          - generic [ref=e240]: • alvo afetado
                        - generic [ref=e241]:
                          - img [ref=e242]
                          - text: 28/05/2026, 05:28:12
                    - generic [ref=e244]: INSULTO_AD_HOMINEM
                  - paragraph [ref=e246]: "\"Rato-mor!!!!\""
                  - generic [ref=e247]:
                    - generic [ref=e248]:
                      - generic [ref=e249]: "Confiança da IA:"
                      - generic [ref=e250]: 95.0%
                    - button "Investigar" [ref=e251]:
                      - img [ref=e252]
                      - text: Investigar
                - generic [ref=e256]:
                  - generic [ref=e257]:
                    - generic [ref=e258]:
                      - generic [ref=e259]: SU
                      - generic [ref=e260]:
                        - generic [ref=e261]:
                          - generic [ref=e262]: "@supremotribunalfederal"
                          - generic [ref=e263]: • alvo afetado
                        - generic [ref=e264]:
                          - img [ref=e265]
                          - text: 28/05/2026, 05:28:12
                    - generic [ref=e267]: INSULTO_AD_HOMINEM
                  - paragraph [ref=e269]: "\"Xandão e réu 😂😂😂😂😂😂#stfgabinetedocrime\""
                  - generic [ref=e270]:
                    - generic [ref=e271]:
                      - generic [ref=e272]: "Confiança da IA:"
                      - generic [ref=e273]: 95.0%
                    - button "Investigar" [ref=e274]:
                      - img [ref=e275]
                      - text: Investigar
                - generic [ref=e278]:
                  - generic [ref=e279]:
                    - generic [ref=e280]:
                      - generic [ref=e281]:
                        - generic [ref=e282]: SU
                        - generic [ref=e283]:
                          - generic [ref=e284]:
                            - generic [ref=e285]: "@supremotribunalfederal"
                            - generic [ref=e286]: • alvo afetado
                          - generic [ref=e287]:
                            - img [ref=e288]
                            - text: 28/05/2026, 05:28:12
                      - generic [ref=e290]: MISOGINIA_POLITICA
                    - paragraph [ref=e292]: "\"Mas é um homem que se diz cuidar das mulheres, uai\""
                    - generic [ref=e293]:
                      - generic [ref=e294]:
                        - generic [ref=e295]: "Confiança da IA:"
                        - generic [ref=e296]: 95.0%
                      - button "Investigar" [ref=e297]:
                        - img [ref=e298]
                        - text: Investigar
                  - generic [ref=e301]:
                    - generic [ref=e302]: Publicidade Cívica Relacionada
                    - insertion [ref=e304]
              - generic [ref=e311]: Carregando mais incidentes...
          - insertion [ref=e313]
  - button "Open Next.js Dev Tools" [ref=e320] [cursor=pointer]:
    - img [ref=e321]
  - alert [ref=e324]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const LOCAL_URL = 'http://localhost:3000';
  4  | 
  5  | test.describe('SENTINELA | Frontend Crawler & Button Tester', () => {
  6  |     test.setTimeout(120000);
  7  | 
  8  |     const routes = [
  9  |         '/',
  10 |         '/analise',
  11 |         '/alvos',
  12 |         '/alertas',
  13 |         '/rede',
  14 |         '/relatorios',
  15 |         '/termos',
  16 |         '/metodologia',
  17 |         '/lgpd',
  18 |         '/privacidade'
  19 |     ];
  20 | 
  21 |     for (const route of routes) {
  22 |         test(`Deve renderizar a rota ${route} sem erros críticos no console`, async ({ page }) => {
  23 |             const errors: string[] = [];
  24 |             page.on('pageerror', error => errors.push(error.message));
  25 |             page.on('console', msg => {
  26 |                 if (msg.type() === 'error') {
  27 |                     errors.push(msg.text());
  28 |                 }
  29 |             });
  30 | 
  31 |             // Usando domcontentloaded para ser mais rápido e evitar travamento por ads
  32 |             const response = await page.goto(`${LOCAL_URL}${route}`, { waitUntil: 'domcontentloaded' });
  33 |             
  34 |             // Aguarda um pouco para os componentes montarem
  35 |             await page.waitForTimeout(2000);
  36 |             
  37 |             // Ignorar erros conhecidos ou de terceiros (AdSense, falhas de rede de anúncios, extensões)
  38 |             const filteredErrors = errors.filter(e => 
  39 |                 !e.includes('google') && 
  40 |                 !e.includes('adsbygoogle') &&
  41 |                 !e.toLowerCase().includes('favicon') &&
  42 |                 !e.includes('ERR_BLOCKED_BY_CLIENT') &&
  43 |                 !e.includes('ERR_NAME_NOT_RESOLVED') &&
  44 |                 !e.includes('A `require()` style import is forbidden') // Ignorar warnings de linter
  45 |             );
  46 |             
  47 |             expect(response?.status()).toBeLessThan(400);
  48 |             
  49 |             if (filteredErrors.length > 0) {
  50 |                 console.error(`Erros na rota ${route}:`, filteredErrors);
  51 |             }
> 52 |             expect(filteredErrors).toHaveLength(0);
     |                                    ^ Error: expect(received).toHaveLength(expected)
  53 |         });
  54 |     }
  55 | 
  56 |     test('Deve checar interatividade básica e botões da Navbar/Sidebar', async ({ page }) => {
  57 |         await page.goto(LOCAL_URL);
  58 |         await page.waitForTimeout(2000);
  59 |         
  60 |         // Coleta todos os botões visíveis
  61 |         const buttonsCount = await page.locator('button').count();
  62 |         expect(buttonsCount).toBeGreaterThan(0);
  63 |         
  64 |         // Coleta todos os links internos
  65 |         const links = await page.locator('a[href^="/"]').evaluateAll(anchors => anchors.map(a => a.getAttribute('href')));
  66 |         const uniqueLinks = [...new Set(links)];
  67 |         
  68 |         console.log(`Encontrados ${uniqueLinks.length} links internos e ${buttonsCount} botões.`);
  69 |         
  70 |         for (const link of uniqueLinks) {
  71 |             if (link) {
  72 |                 const res = await page.request.get(`${LOCAL_URL}${link}`);
  73 |                 expect(res.status()).toBeLessThan(400);
  74 |             }
  75 |         }
  76 |     });
  77 | });
  78 | 
```