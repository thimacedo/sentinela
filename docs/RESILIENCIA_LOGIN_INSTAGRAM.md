# Resiliência de Login e Autenticação no Instagram — Sentinela

## 🔍 Diagnóstico do Problema do DOM Dinâmico
O Instagram utiliza mecanismos de obfuscamento no front-end para evitar interações não solicitadas no DOM. Isso acarreta duas características principais:
1. **Classes CSS Ofuscadas e Dinâmicas**: Classes como `x1i10hfl`, `xggy1nq`, etc., mudam a cada build ou carregamento.
2. **Atributo `name` Dinâmico / Alternativo**: Em várias páginas de login e perfis, o input clássico de usuário com `name="username"` foi alterado ou coexiste com `name="email"`. Os IDs dos elementos, como `_R_32d9lplcldcpbn6b5ipamH1_`, também são gerados aleatoriamente em tempo de execução.

Qualquer automação de login que dependa exclusivamente dessas classes ou de seletores baseados em IDs estáticos falhará de forma intermitente ou sistemática.

---

## 🛠 Abordagem Resiliente do Sentinela
Para garantir alta disponibilidade das contas de coleta sem interrupções por mudanças no DOM, o script de renovação de cookies ([export_playwright_cookies.py](file:///c:/Projetos/sentinela/scripts/export_playwright_cookies.py)) foi desenhado com as seguintes defesas de resiliência:

### 1. Seletores Estáveis baseados em Semântica e Acessibilidade (ARIA)
Em vez de depender de classes de estilo ou IDs gerados dinamicamente, utilizamos seletores abrangentes e prioritários por atributos funcionais e rótulos de acessibilidade:
*   **Identificação do Usuário**:
    ```python
    input_selector = (
        'input[name="username"], input[name="email"], '
        'input[aria-label*="usuario"], input[aria-label*="usuário"], '
        'input[aria-label*="user"], input[aria-label*="Phone"], '
        'input[aria-label*="telefone"]'
    )
    ```
    Isso captura o campo seja qual for a variante regional ou o rótulo (`aria-label`) associado pelo Instagram.
*   **Identificação da Senha**:
    ```python
    password_selector = 'input[name="password"], input[type="password"], input[aria-label*="senha"], input[aria-label*="password"]'
    ```

### 2. Simulação de Digitação Humana (Detecção de Injeção Rápida)
O Instagram detecta quando strings extensas são preenchidas instantaneamente no formulário (efeito do método `page.fill()`), o que desabilita o botão de submissão `Entrar` por validação interna de segurança de eventos no browser.
*   **Ação**: O script utiliza digitação sequencial de caracteres (`page.type()`) com um atraso físico real configurado para simulação humana:
    ```python
    await page.type(input_selector, user, delay=150)
    await page.type(password_selector, password, delay=150)
    ```

### 3. Adaptação para Login em Múltiplas Etapas (WebAuthn / Passkey Checkpoint)
Em logins modernos do Instagram ou sob contextos de segurança elevados, a tela de login inicial pode exibir apenas o input de usuário/email. O campo de senha é apresentado em um formulário secundário somente após a confirmação.
*   **Ação**: O script verifica a visibilidade imediata do seletor de senha. Se não for detectável, envia a tecla `Enter` no input de usuário e suspende a execução por um atraso visual de transição para permitir o carregamento da próxima etapa:
    ```python
    if not password_element or not await password_element.is_visible():
        print("[*] Layout de login em duas etapas detectado. Avançando...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(4) # Aguarda transição visual
    ```

### 4. Gestão e Rotação Multipessoal no `.env`
O script de exportação lê de forma dinâmica e sequencial as contas disponíveis no `.env` (`IG_USER` / `IG_PASS`, `IG_USER_1` / `IG_PASS_1`, até 10 slots) e executa o login individualizado.
*   Se a chave de cookies (`INSTAGRAM_COOKIE_FULL`) ou a sessão legado (`INSTAGRAM_SESSIONID_N`) for informada e funcional, o script realiza um login expresso adicionando o cookie direto no contexto do Playwright.
*   Se a sessão inicial falhar ou estiver ausente, ele inicia o fluxo completo por formulário e atualiza automaticamente os slots correspondentes no arquivo `.env` (ex.: `INSTAGRAM_SESSIONID_2`), garantindo isolamento total entre os contextos das contas e evitando contaminações de cookies.

---

## 📸 Diagnóstico Visual de Erros
Se uma conta cair em verificação de checkpoint de segurança (SMS/E-mail/Captcha) impossível de contornar de forma headless pura:
*   O Playwright captura um screenshot do estado da página e o armazena em `scratch/login_error.png` para análise imediata, continuando a execução do ciclo para as contas restantes sem interromper o fluxo global do Watchdog.
