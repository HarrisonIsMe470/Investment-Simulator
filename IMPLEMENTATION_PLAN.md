# Investment Simulator: implementation plan and gap analysis

## Product goal

Create a replayable 365-day strategy game in which the player allocates $10,000 across markets, receives imperfect information, gets two financial operations per day, and wins by maximizing final net assets. The core simulation must be deterministic when seeded, financially consistent, persistent, and independent from the Pygame presentation layer.

## Existing program compared with the target

| Area | Existing state found | Replacement / target state |
|---|---|---|
| Daily loop | 365-day counter and two-trade limit | Config-driven year and action limit, explicit end-game result |
| Trading integrity | UI/CLI could provide any execution price | Engine always executes the live market quote |
| Products | Stocks, crypto, bonds, ETFs and forex were tradeable; deposits/options were labels only | All eight requested categories have tradeable representatives |
| Primary market | IPO-themed emails only | Phase 2: time-limited IPO allocations which later list publicly |
| Market | Global random generator; event price impact was hidden | Seeded local generator, daily changes, interest products, event alerts |
| Email | Random generic messages disconnected from simulation | Live events produce matching alerts; reports/ads/scams remain clearly typed |
| Persistence | Transactions saved, but positions and operation count were not; load recreated cash without holdings | Portfolio and player progress are atomically synchronized and restored |
| Configuration | Runtime expected nested JSON but shipped JSON was flat | One nested, validated source for game/UI/feature rules |
| GUI | Attractive skeleton, but Buy/Sell always targeted AAPL | Market rows select the asset used by trade dialogs |
| Tests | Mostly printed demonstrations | Assertions cover quote integrity, persistence and product coverage |

## Architecture

1. **Domain layer**: market, portfolio, instruments, orders, events, emails.
2. **Application layer**: `Game` owns the day/action lifecycle and is the only trading gateway.
3. **Persistence layer**: SQLite stores players, positions, transactions, prices and emails; portable save files should use versioned JSON rather than pickle.
4. **Presentation layer**: Pygame and CLI consume snapshots and submit commands without duplicating financial rules.

## Delivery roadmap

### Phase 1 — playable, correct core (implemented in this revision)

- Enforce market quotes and reject unknown symbols.
- Persist and restore portfolio positions and daily operation usage.
- Add savings, fixed deposit and simplified option instruments.
- Make simulation seeding isolated and reproducible.
- Show daily percentage movements, asset selection and event-linked news.
- Consolidate configuration and add behavioral regression tests.

### Phase 2 — strategic depth

- Add IPO subscription windows, allocations, listing dates and first-day volatility.
- Model fixed-deposit lock periods and early-withdrawal penalties.
- Give options strike, expiry, premium and settlement mechanics.
- Add spreads/fees, dividends/coupons and explicit forex base/quote exposure.
- Make advertisements actionable; scams should require player judgment and have consequences rather than carrying warning labels.

### Phase 3 — complete game experience

- Add inbox/detail, market-category, history-chart and end-game screens.
- Add save selection and versioned JSON autosaves.
- Add difficulty presets, tutorial, scoring, achievements and seeded scenarios.
- Replace system-font styling with licensed pixel assets, accessible colors, audio controls and responsive layout.

## Acceptance criteria

- No action can bypass the two-operation limit or choose its own price.
- Saving/reloading preserves cash, positions, day, operations, market and inbox.
- Every product category has distinct risk/return or contract behavior.
- News that claims a market move corresponds to the simulated move.
- A seeded run is reproducible and automated tests do not modify the shipped database.
- The player can finish a full year and see final net assets and performance.
