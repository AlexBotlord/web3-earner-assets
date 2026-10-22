# SaSame GEC: доказательства внешнего provider-path

- Сгенерировано: 2026-10-22T00:18:53.467Z
- Провайдер: web3-earner (внешний, не SaSame/Pancho)
- Demand: `demand:owner:54e758a3f5a7f427b96b456c7c1f078f`
- Participant: `participant:wallet:cf01a2dc00b33f9c14f330a76d71e84f`
- Payout wallet: `0x1659c37bc2f7bcc59EfA836d921585Dc87404aE2`
- Bid: `bid:5be0606804fd82619aba46c0b1564c80` на 5000000 microUSDC, state `SELECTED`
- Award: `award:377fc628f20f6c98335c86c43f2c25e2`, state `ACCEPTED`
- MCP protocol: `2025-06-18`

## Проверенный путь

1. Keyless Public MCP: initialize, tools/list, gec_open_demands.
2. Wallet auth: challenge 201, локальный personal_sign EIP-191, verify 200.
3. Browser OAuth consent для participant-client; получен доступ к User MCP.
4. User MCP: initialize, tools/list, gec_bid_submit; заявка принята.
5. Award: детерминированный выбор bootstrap, `gec_award_accept`.

## Трение

- OAuth consent на sasame.online/account/mcp/participant-connect требует браузерный JS; прямые POST к connector дают 405, а /authorize|/approve|/consent — 404.
- CIMD client_id redirects через live-sasame/authorize; без браузерной сессии authorization_code не получить.
- Публичный MCP не требует авторизации; User MCP требует Bearer, который выдаётся только после wallet-auth и OAuth consent.

## Секреты

Не включены: Authorization, cookies, OAuth code/token, подписи, приватные ключи, recovery material.

Полные redacted-транскрипты: `raw-public-mcp.json`, `raw-user-mcp.json`, `oauth-handoff.json`.
