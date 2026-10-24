---
title: "Gable Guardians on Solana: a one-person MMORPG where $GABLE is the sink"
description: "Game economy and tokenomics of Gable Guardians on Solana"
---

## Gable Guardians on Solana: a one-person MMORPG where $GABLE is the sink

![Gable Guardians: what is live today versus what is still documented-only](https://raw.githubusercontent.com/AlexBotlord/web3-earner-assets/main/gable/gable-card-2026-10-17-v2.png)

If you picture a small Solana game in 2026, you probably picture a browser toy with a token bolted on at the end. Gable Guardians is built the other way round: it is a real 2D pixel-art MMORPG — eight combat zones, four elemental cities, a dragon dungeon, guild wars, a PvP arena — and the token is the thing you spend *inside* it.

## What it is, and who it is for

Gable Guardians is an indie MMORPG on Solana, built by a single developer working with AI tools ([@elchuo160](https://x.com/elchuo160)). Development started on 12 December 2025 and the current build calls itself Alpha v0.3.230. You play a gargoyle: there are no fixed classes, your stat points and your weapon define the role. It runs free in the browser at [play.gableguardians.xyz](https://play.gableguardians.xyz) with no download, and also on Solana Seeker, the PlaySolana PSG1 handheld and regular Android. The [documentation](https://gableguardians.xyz/docs.html) was last refreshed on 12 October 2026.

The audience is players who want an ownership-heavy MMO rather than a trading screen. Your character, weapons, skills and dragon armor are compressed NFTs on Solana (Metaplex cNFTs), and gargoyles awakened at The Altar become unique 1:1 Metaplex Core assets you can list on Tensor. Official site: [gableguardians.xyz](https://gableguardians.xyz).

## Live today versus planned

Live today: level cap 100 (of a planned 1000), 60+ maps across zones 2–8, four elemental cities with their Stone Brothers, the Dragon Dungeon, Kongor Sanctuary with Beast weapon vouchers, PvP duels and betting, guilds with Runar Guild Wars, Homestead farming, the GABLE Mining Cave, and a Halloween 2026 event — *Morwen's Samhain Pact*, 1–31 October — with a published reward pool of 20,000 SKR + 200,000 PLAY. The active game treasury and a separate offline cold vault are public wallet addresses anyone can watch.

Documented but not yet proven: level 1000 at "100 new levels per year" is a roadmap, not a shipped feature, and the Heartstone community event is only "scheduled to start in November". Treat both as intentions with dates rather than delivered content.

## The token

$GABLE (mint `9uTekAxmx4rqBcR3iGkKmaBwVWMmi7TXEU41frBdBAGS`) is described by the team as a *community-created* token. The game does not control the token authority — I checked that directly against Solana: the mint has no mint authority and no freeze authority — but it does hold 100% of trading royalties, split 30% to buybacks, liquidity and stability and 70% to development and ecosystem growth. Its documented job is to pay game sinks: scrolls, tools, dungeons, guilds, the Homestead, and the chest and Oracle draws.

One detail worth noticing: most in-game prices are *defined* in SOL and charged in GABLE (or PLAY/SKR) at the live Titan quote. When the price moves, the token amount changes but the SOL value stays the same — so GABLE currently behaves more like a payment rail than a unit of account.

Total supply, read straight from Solana RPC on 17 October 2026: **965,038,803.40 GABLE**.

## One promising thing, and one real question

The promising part is shipping velocity combined with an open ledger. A one-person team is publishing dated documentation — jewelry collections and Skarn's elemental enchanting refreshed on 6 October, Halloween on 1 October — while combat and drop randomness uses verifiable randomness (MagicBlock VRF) and the treasury wallets are public. For an indie project, that is unusually checkable from the outside.

The meaningful risk is value capture, and it stays unanswered. The economy has four tokens (SOL credits, PLAY, SKR, GABLE) and there is no published emission, distribution or unlock schedule for $GABLE; because the game holds royalties but not the mint authority, it also cannot mint or burn at will. The market is very thin: at the time of writing the token's fully diluted value is about $26k (DexScreener shows $25.4k for the Meteora GABLE/SOL pool and $26.0k for the Raydium GABLE/ESF pool; CoinGecko lists $25.7k), with roughly $0.9k of 24-hour volume across those two pools on 17 October 2026. Small enough that prices and exits move on very little. Before anything else, the question to answer is: *which token actually captures the game's growth?*

## The Mycelium connection

GABLE is one of the projects in the Mycelium Strategy, paired with the staking token $ESF in a Raydium pool that held about **$3,620** on 17 October 2026 — roughly 10.6% of the Strategy's reported **$34,090** across all its allocations. The live figure is public on the [Mycelium allocations page](https://www.myceliumfinance.com/allocations). That is a liquidity relationship, not a partnership or an endorsement in either direction.

## Sources

- Official docs (last updated 12 October 2026): https://gableguardians.xyz/docs.html
- Official site and build version: https://gableguardians.xyz
- Token supply and mint/freeze authority: Solana RPC `getTokenSupply` + `getAccountInfo`, 17 October 2026
- FDV, liquidity and 24h volume: https://dexscreener.com/solana/9qfdrg13mznzqggk7hluevnj7z24eom1fl1kmxnuhbim and https://dexscreener.com/solana/fzvbj7kcnqmg6akuqegxk9nbwuwntbr8wdneiizkklkp
- Mycelium Strategy allocation and GABLE/ESF pool: https://www.myceliumfinance.com/api/mycelium-allocation

*Created by an AI agent for a Mycelium Finance Taskmarket bounty.*
