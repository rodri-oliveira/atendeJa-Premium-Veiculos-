# UX Guidelines — AtendeJá Frontend

Estas diretrizes consolidam padrões de acessibilidade, semântica e testabilidade adotados no front (Vite/React/TS/Tailwind).

## Acessibilidade (A11y)

- Labels e inputs
  - Use `label` com `htmlFor` e `input` com `id` correspondente.
  - Exemplo: `Rua`, `Número`, `Bairro`, `Cidade`, `Estado`, `CEP` em `src/components/OrderDrawer.tsx`.
- Botões e nomes acessíveis
  - Forneça nomes claros em pt-BR e evite termos em inglês na UI.
  - Quando necessário, complemente com `aria-label` para estabilizar queries e leitores de tela.
- Feedback de erro por campo
  - Mensagens curtas e objetivas (pt-BR), preferencialmente próximas ao campo.
  - Indicar erro visualmente (ex.: borda vermelha) + texto.

## Semântica e idioma

- Interface 100% pt-BR.
- Títulos e rótulos devem comunicar a ação de forma clara (ex.: “Salvar endereço”, “Atualizar agora”).

## Testabilidade (RTL/Vitest)

- Queries recomendadas
  - Prefira `findByRole`/`getByRole` e `findByLabelText`/`getByLabelText`.
  - Use `data-testid` apenas quando necessário para sincronização (ex.: `data-testid="addr-section"`).
- Sincronização de render
  - Aguarde elementos-chave da tela antes de interagir (ex.: `Resumo` no Drawer, `addr-section` quando status = `draft`).
- Mocks de API
  - Use `url.includes()` para tolerar querystrings e bases distintas.
  - Testes devem cobrir todos os endpoints utilizados no fluxo do componente.

## Padrões de chamadas HTTP (frontend)

- GETs padronizadas
  - Utilize `timedFetch(url, { method: 'GET', cache: 'no-store' }, op)`.
  - Benefícios: previsibilidade de mocks, sem cache em dev/teste.
- Observabilidade leve
  - `timedFetch` loga latência e status (info/warn/error) sem dependência de vendor.

## Drawer (OrderDrawer)

- Resiliência de carregamento
  - Carregar primeiro `getOrder()`; demais (`events`, `relation`, `reorders`) paralelos via `Promise.allSettled`.
  - Falhas em endpoints auxiliares não devem bloquear o render da UI.
- Validações de endereço
  - CEP com máscara `00000-000` ao digitar 8 dígitos.
  - UF com 2 letras e uppercase.
  - Mensagens objetivas por campo.

## Boas práticas gerais

- Evite depender de escala visual (zoom/scale); prefira densidade controlada e layouts responsivos.
- Ajustes persistentes de UI (ex.: modo compacto) via `localStorage` com chaves nomeadas (`atendeja.ui.*`).
- Manter textos, estados e labels em pt-BR, alinhados às regras de negócio e ao `config.json`.
