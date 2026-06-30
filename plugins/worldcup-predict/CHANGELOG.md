# Changelog

## [1.0.1] - 2026-06-30

### Fixed
- Corrected a Taiwan Sports Lottery odds-reading error that could pick the wrong favourite and flip a recommendation to the opposite side; the favourite is now confirmed against the correct-score board and outside odds before any bet is named.

### Added
- Every match now ends with at least one scoreline prediction (the best odds-value pick, honestly tagged), plus a reference list of all full-match odds priced 2.0 or higher — so you can see the longshot candidates and why most don't qualify.

### Changed
- Win/draw/loss odds are now built off the market as a baseline and only move when there's a stated reason the market is wrong, and are shown as ranges — so calls are steadier between runs and don't claim precision the data can't support.
- Sharper team read: more weight on the current squad and star quality, playstyle and chance quality; less on years-old head-to-head and stats padded against weak opponents; a star everyone is hyping is treated as a reason to fade the price, not follow it.
- Clearer guidance on where value survives the heavy 運彩 margin (team totals and contrarian sides), plus a new warning that a low-scoring bet can still lose to a late stoppage-time goal in tight knockouts — favour a team-total or lower line there.

## [1.0.0] - 2026-06-30

### Added
- `/predict-match` — predict a World Cup fixture, a full day's slate, or a team's next match. Pulls live fixtures, form, player/tactical data, conditions, referee tendency, and pundit consensus from the web (every figure cited; missing data marked `unknown`).
- Three-block output (資料描述 → 資料分析 → 推薦下注) led by a winner / scoreline / confidence headline that reports from the probability distribution rather than naming the bare favourite.
- Betting board across markets — 1X2, Asian handicap, over/under, BTTS, correct score, to-qualify — with implied vs estimated probability and expected value; flags only clearly positive-EV calls, with a separate small-stake longshot lane. Half-time/full-time and goalscorer markets tagged Weak / entertainment.
- Scenario flags: 爆冷傾向 (dead-rubber/rotation/motivation asymmetry), 強隊大勝傾向 (favourite blowout), 低比分傾向 (goals market), and 和局傾向 (tight 1X2) — may move the probability, then defer to the EV gate.
- Taiwan Sports Lottery (台灣運彩) localization: terminology map, 90-minute settlement, heavy-overround warning, and a Playwright scrape recipe (resolve a match's event page from the listing by team name, read the full board, sanity-check 波膽 orientation against the favourite).
- Preflight verifies the fixture is real before analyzing — a non-existent or not-yet-scheduled matchup gets the true bracket situation, not a fabricated forecast.
- Discipline guardrails: EV must beat the estimate's error bar; bet only when the market hasn't already priced a scenario; discount form by opponent quality; claim the tilt, not the freak scoreline; grade only pre-locked calls and never quote in-sample accuracy as a hit rate.
- All times in GMT+8; country names in Chinese with English only in the title header.
