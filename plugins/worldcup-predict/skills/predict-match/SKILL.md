---
name: predict-match
description: Use when the user asks to predict a World Cup match or fixture, forecast a scoreline or winner, find value bets, analyze betting markets (handicap, over/under, correct score, half-time/full-time), or runs /predict-match. Pulls live fixtures, form, player and tactical data, and bookmaker odds from the web, then outputs a multi-dimensional analysis plus a betting board with expected-value calls.
allowed-tools: WebSearch, WebFetch
---

# World Cup Match Prediction

**Type**: Live-data sports forecast
**Goal**: For each requested fixture, produce a defensible, multi-dimensional read — winner, likely scorelines, confidence — backed by current data, and a betting board across markets that flags positive expected-value calls.

## Preflight (resolve before any analysis)

Determine **which match(es)** to predict from `$ARGUMENTS`:

- Two team names (e.g. `Brazil vs Argentina`) → that single fixture.
- A date or `today` / `tomorrow` → every World Cup fixture on that date (in **GMT+8**).
- A team name only → that team's next scheduled World Cup fixture.
- **Empty** → ask the user which fixture or date they want. Do not guess.

State the resolved target in one line before proceeding (e.g. "Predicting: Brazil vs Argentina, 2026-07-02 03:00 GMT+8").

## Flow

1. **Gather live data** with WebSearch / WebFetch. Cite the source for every figure; if a point can't be found, mark it `unknown` and lower confidence — never invent it. Collect:

   **Hard signals (weight these most)**
   - **Fixture facts** — kickoff (convert to **GMT+8**), stage (group/knockout), venue, host city. For knockouts note there is **no draw** (extra time / penalties decide).
   - **Form & quality** — last 5–6 competitive results per side, goals for/against trend, and xG / shot quality where available (beats raw W-L).
   - **Player availability & form** — injuries, suspensions, key returns, **and yellow-card suspension jeopardy** into the next round. Fetch a dedicated match-preview or predicted-line-up page; a generic team-form search misses current team news. Note the form/fitness of decisive individuals and the **goalkeeper**. **A "doubtful / hamstring / late fitness test" star is NOT a confirmed absence** — treat it as a probability (knockout games pull borderline stars back, often off the bench), don't model them as fully out; team news firms up near kickoff, so mark it an unknown to re-check.
   - **Tactical style matchup** — formations, pressing vs build-up, width vs narrow defense, **set-piece** strength, **penalty-shootout record** (knockouts). Style clashes carry more signal than ranking gaps.
   - **Head-to-head** — recent meetings and overall balance.

   **Context (modifiers, not drivers — EXCEPT the scenario flags below, which can be primary drivers)**
   - **Mentality** — must-win/qualification scenario, manager security, title pressure, motivation asymmetry. Only state what a source supports.
   - **Scenario flags (these MAY override raw team quality — see the rule below).** Actively check for and flag. **First discount each side's form by opponent quality** — goals/results piled up against a weak or winless side are inflated and are NOT evidence of real attacking strength (a 5-1 over a minnow ≠ a hot attack). Then check for:
     - **爆冷傾向 / upset-prone** — driven by **motivation / rotation**, NOT by an underdog's recent scoring: a favourite who is a **dead rubber** (already qualified/seeded, match means nothing) and **likely to rotate**; **extreme motivation asymmetry** (must-win underdog vs nothing-to-play-for favourite); a **giant-killer / bogey** history. The market is slow to price favourite apathy + rotation — that is where underdog longshots become genuinely +EV. A merely "in-form" underdog is **not** an upset flag (the market already rates them).
     - **強隊大勝傾向 / favourite-blowout** — a strong favourite on **genuine** form (not minnow-inflated) vs a weak/winless/low-quality side, especially with no motivation drag. Shift the scoreline distribution toward **2+ goal margins** and Over; do NOT cap the favourite at a 1-goal win. The model must not be structurally blind to routs.
     - **低比分傾向 / low-scoring (goals market)** — two low-xG sides, a bus-parking minnow, or strong defences. Tilts the **goals market**: Under / no-BTTS / favourite team-total under. **A blowout can also be "low total" via dominance — low total ≠ tight contest**, so this flag alone does NOT lift the draw.
     - **和局/勢均力敵傾向 / tight (1X2 market)** — only when the two sides are **genuinely close** (favourite implied prob < ~60%) AND both are cagey / content with a point. Lifts the **draw** and "favourite fails to cover a handicap". **Do NOT emit this for a heavy mismatch** — opener nerves and caginess compress an *even* game, not a lopsided one.
   - **Conditions** — heat/altitude, kickoff time, and **travel + rest-day** asymmetry (2026 spans the US/Canada/Mexico with long hops); home-nation advantage (hosts: USA / Canada / Mexico).
   - **Referee** — cards/penalty tendency (feeds the cards/penalty markets).
   - **Pundit consensus** — what credible previews predict; use as a sanity check, not as your answer.

   **Soft color (mention only — do NOT weight into probabilities)**
   - **National footballing identity / "character"** — one line of flavor at most. Low predictive value and stereotype-prone; never let it move a number.

   **Market data**
   - **Odds** across markets: 1X2, **Asian handicap**, over/under (and Asian total), **both-teams-to-score (BTTS)**, **correct score**, to-qualify / extra-time, plus half-time-full-time and goalscorer where the user wants them. A match-preview article rarely lists the full board — fetch a dedicated sportsbook / odds page that publishes handicap and totals, not just the moneyline. If a line genuinely isn't published in any source you reach, mark it `unknown`; never infer or back-fill an odds figure to fill the table. Note the source, the timestamp (GMT+8), and **line movement** + public-vs-sharp money if reported (sharp money against heavy public backing is a contrarian flag).
   - **Taiwan Sports Lottery (台灣運彩)**: the odds page (`sportslottery.com.tw/sportsbook/world-cup`) is a JS-rendered SPA — **WebFetch and WebSearch cannot read it** (they return an empty shell / only futures 冠軍賠率). Two ways to get per-match lines:
     1. **If Playwright (or another real-browser) MCP is available** → scrape it (this whole recipe runs well in a **background agent**; never click 投注 / login):
        a. Navigate to the listing `https://www.sportslottery.com.tw/sportsbook/world-cup`, wait ~3s for the SPA to render.
        b. Each match card carries an **「其它玩法」anchor** whose `href` is `/sportsbook/daily-coupons/event/{eventId}.1` and whose card text names the teams as **`客隊 @ 主隊` (away @ home)**. Read all `<a>` via `browser_evaluate`, map each 其它玩法 href to its card's team names, and pick the row matching your fixture by name. **Do not hardcode or guess the eventId** — it differs per match; always resolve it from the listing.
        c. Navigate to that event href → the full board renders (不讓分 / 讓分 / 大小 / BTTS / 半全場 / 波膽). Read `document.body.innerText` and parse.
        d. **Correct-score (波膽) orientation is ambiguous and easy to flip** — the score columns are not reliably home:away. Sanity-check against the moneyline: the shortest 波膽 prices must sit on the **favourite's** winning scores. If they don't, your orientation is reversed — fix it before quoting any scoreline, or you will recommend the exact opposite bet.
     2. **Otherwise** → ask the user to paste the match's lines (不讓分 / 讓分 / 大小球 / 波膽 / 半全場).
     運彩 odds are already decimal, so EV math applies directly — **but its overround is heavy (~17% on 大小, ~27% on 不讓分 vs ~5% at sharp books), so genuine +EV is rare; a bet that is +EV at an international book is often ~0 or negative at 運彩.** Always state the 運彩 overround and don't manufacture value. See the 運彩 localization rule below for settlement differences.

2. **Build the call.** Weight: form/quality + tactical matchup + availability > context modifiers > soft color (zero weight). **Exception — scenario flags outrank raw quality**: when a dead-rubber/rotation, extreme-motivation-asymmetry, or bus-vs-favourite pattern is present, let it move the probability *materially* (e.g. cut a rotating dead-rubber favourite's win prob well below the market's, lift a desperate motivated underdog's) — do not leave it as a zero-weight footnote. The adjustment is a strong tilt, not an automatic flip (a rotated elite side still has quality). Reconcile against the market: a large gap from the odds is a prompt to re-check your inputs, not automatic edge — but a market that hasn't priced favourite apathy is exactly where the edge lives.
   - **Headline the distribution, not the bare argmax-favourite.** The headline winner should reflect what the probabilities actually say: when the favourite has **no positive-EV edge** and **draw + underdog combined ≳ 45%** (or a tight/和局 flag is active), report the headline as **"勢均力敵 / 和局機率高（X 微幅領先）"**, not a confident pick of the favourite. Naming the favourite just because it is the single highest cell, while your own split leans toward a draw, is the most common way the call reads wrong even when the model was right. Also surface **"贏≠掌控"**: a short-priced favourite vs an elite-defence / transition side can win yet trail and be decided late — cap headline confidence and say so.

3. **Estimate probabilities and a correct-score distribution.** Give your win/draw/loss split and a top-3 most-likely scorelines, then derive the secondary markets (handicap, O/U, BTTS) from that same distribution so they stay internally consistent. State **how confident you are in each estimate** (your eyeballed probability carries an error band, often ±3–5pp) — a market where your read rests on hard, narrow evidence is more trustworthy than a multi-path outcome with many ways to be wrong.

4. **Compute expected value** for each market line you call:
   - Implied probability = `1 / decimal_odds`.
   - EV per 1 unit staked = `(your_probability × decimal_odds) − 1`.
   - **The edge must beat your own error bar.** A self-estimated probability is uncertain; if the EV (~edge) is smaller than the ±error on your estimate, it is noise, not value. So **only EV ≳ 0.08 on a confidently-held estimate counts as a true BET**; +0.02 to +0.07 is `lean` (skip or entertainment), not a recommendation.
   - **The gate is EV, not probability.** A low-probability, high-odds line (a correct score, an upset, a scorecast — typically 5.0+ decimal) is a legitimate value bet if its EV clears the bar; do not skip it just for being a longshot. BUT at high odds EV is hypersensitive to estimate error — a few pp off your probability swings EV hard — so longshots need a **fatter cushion: EV ≳ ~0.15**, are **small-stake / 試水 by default** (high variance), and come with a caveat that **correct-score / scorecast markets carry heavy bookmaker overround**, so apparent value there is often illusory. Treat these as a separate speculative lane from the safer 1X2 / handicap / totals picks.
   - When two lines both clear the bar, **rank by EV**; prefer a lower-EV line over a higher-EV one only with an explicit stated reason (tighter estimate confidence, lower variance, less correlation risk) — never on gut. Probability alone is not the criterion; a higher win% with no edge over the odds is not a bet, and a longshot with a real edge is.

5. **Output** the report below — exactly three blocks per fixture, in order: **1 資料描述 → 2 資料分析 → 3 推薦下注**. Keep facts in block 1, interpretation in block 2, and actionable bets in block 3; do not mix them.

## Output format

```
## <Home> vs <Away>
<stage> · <kickoff GMT+8> · <venue, city>

> **🏆 預測：<winner 勝 / 和局機率高·X 微幅領先 / 勢均力敵> · 最可能比分 <h>–<a> · 信心 <Low|Medium|High>（<n>%）**
> _(if the favourite has no EV edge and draw+underdog ≳45%, headline the draw/tightness — do NOT name the favourite just for being the top cell)_

### 1. 資料描述（the facts — every line cited; unknown stays `unknown`）
- Fixture: kickoff (GMT+8), stage, venue; conditions (heat/altitude), rest/travel asymmetry
- Form: each side's last 4–6 results (+ goals for/against, xG if found)
- Availability: injuries, suspensions, key returns, goalkeeper, yellow-card jeopardy
- Head-to-head: recent meetings / overall balance
- Referee: cards/penalty tendency (or `unknown`)
- Market odds (raw): published lines per market, with source + timestamp (GMT+8)

### 2. 資料分析（the read）
- Tactical matchup: how the styles clash; set pieces; who controls what
- Mentality & context: must-win, pressure, rest/travel, home edge
- **Scenario flags**: `爆冷傾向` / `強隊大勝傾向` / `低比分傾向` / `和局傾向` / none — with the structural reason, and how much it moved your probability (state pre/post numbers if it materially shifted). Keep `低比分傾向` (goals market) distinct from `和局傾向` (1X2); a rout can be low-total without being tight.
- Pundit consensus: what credible previews lean toward
- **My estimate**: win/draw/loss split + top-3 most-likely scorelines, each with a confidence tag (how tight the error band is, and why)
- Upset / dark-horse: the realistic path the underdog wins + rough %
- Color: one line of national-identity flavor — not weighted

### 3. 推薦下注（recommendations）

**🎯 建議：<one plain-language line — the single bet to place, OR "本場無明確 value，建議跳過（純娛樂可小玩 X）">**

Then list the bets you actually recommend — **0 to 2 only, ranked by EV**, each as a plain line. Never recommend more than two; if nothing clears the bar, recommend none and say so.
1. **<market — pick @ odds>** · 注碼 <主注 / 半注 / 試水> · EV +x.xx · <one-clause why>
2. <second only if it also clears the bar; else omit>

(若無任何注達標，寫「無 — EV 全為負或邊際（在估計誤差內），跳過」，不要硬湊。)
**Marginal edges (EV < ~0.08 on an eyeballed probability) are NOT recommendations** — they go to `lean`, not the list above. If you ever list a lower-EV bet above a higher-EV one, you must state the concrete reason (estimate confidence / variance), never a hunch.
A **speculative longshot** (high-odds line, EV ≳ ~0.15) may be listed as one of the picks but must be tagged `投機/試水` with a small stake and a one-clause note that high odds magnify estimate error — it never displaces a safer BET as the top pick.

<details: full market board for reference>

| Market | Pick | Odds | Implied | My est. | EV/unit | Confidence | Verdict |
|--------|------|------|---------|---------|---------|------------|---------|
| 1X2 (match result) | <pick> | x.xx | xx% | xx% | +/-x.xx | <L/M/H> | BET / lean / avoid |
| Asian handicap | <line> | x.xx | xx% | xx% | +/-x.xx | <L/M/H> | — |
| Over/Under <line> | <O/U> | x.xx | xx% | xx% | +/-x.xx | <L/M/H> | — |
| BTTS | <Y/N> | x.xx | xx% | xx% | +/-x.xx | <L/M/H> | — |
| Correct score (top 3) | <s1 / s2 / s3> | — | — | xx/xx/xx% | — | <L/M/H> | most likely first |
| To qualify / ET-pen | <pick> | x.xx | xx% | xx% | +/-x.xx | <L/M/H> | knockout only |
| HT-FT | <pick> | x.xx | — | — | — | Weak | entertainment |
| Anytime scorer | <player> | x.xx | — | — | — | Weak | entertainment |

Verdict column = **BET** only on a real edge (EV ≳ 0.08 on a confidently-held estimate); **lean** for thin/marginal edge (EV +0.02 to +0.07, i.e. inside the error bar); **avoid** otherwise. Only **BET** rows may appear in the recommendation list above, and they appear there ranked by EV.
Staking & unknowns: flat stake sized to bankroll, never chase; <what would change the call — confirmed XI, weather, line movement near kickoff>.
```

## Rules

- **Never fabricate data.** Every result, injury, referee note, and odds figure must come from a fetched source. Missing → write `unknown` and lower confidence.
- **Soft factors stay soft.** National "character" and other narrative factors are color only; they must never move a probability. Mentality/conditions are modifiers, not primary drivers — **except the scenario flags below.**
- **Scenario flags can outrank quality, then defer to EV.** A dead-rubber/rotation, extreme-motivation-asymmetry, or bus-vs-favourite pattern MAY move the probability materially (the one place context beats raw form) — because the market underprices favourite apathy. But the adjusted probability still goes through the same EV gate: a scenario-driven underdog longshot is a bet only if it clears the longshot EV bar. The scenario corrects the number; **EV remains the judge**. A single upset/draw that hits does not prove a passed-on bet was wrong (good process, variance outcome), and one that you flagged but was -EV is still not a regret.
- **A flag improves the prediction always, but is a BET only when the market hasn't already priced it.** Distinguish two cases: (a) the scenario is *obvious* (an ultra-defensive minnow → Under; a giant facing a minnow → favourite) — the market sees it too and the line is already shaded, so it sharpens your call but offers little/no betting value; (b) the scenario is *underpriced* (dead-rubber apathy + rotation, late motivation shifts — markets are slow here) — this is where the edge lives. Before staking a scenario-driven bet, ask "has the price already moved to reflect this?" If yes, it's a `lean` at best, not a BET, however confident the prediction.
- **Claim the tilt, not the freak.** From a stalemate/upset flag, recommend the *direction* (Under / handicap / draw / the underdog side) — never claim to predict the exact freak scoreline or a keeper masterclass. Precise correct-score and one-off heroics are tail variance; keep them in the small-stake longshot lane with humility.
- **Discount form by opponent quality.** Goals/results compiled against weak or winless sides are inflated; do not read a minnow-padded scoreline as real attacking strength, and never bet an underdog up on it. This single misread is what turns a sound favourite into a losing upset pick.
- **Low total ≠ tight game; don't over-emit 僵局.** Separate the goals-market read (`低比分傾向` → Under/no-BTTS, can co-exist with a rout) from the 1X2 read (`和局傾向` → lift the draw). Only emit the tight/draw read when the sides are genuinely close (favourite implied < ~60%). Opener-caginess/host-nerves dampers apply to *even* games, not heavy mismatches — a mismatch is one-sided-low-scoring, not tight.
- **Headline from the distribution.** When the favourite has no +EV edge and draw+underdog ≳45% (or a 和局 flag is active), the headline reports the draw/tightness, not the bare top-cell favourite. Also flag 贏≠掌控: a short-priced favourite vs an elite-defence/transition side can win while trailing and be decided late — cap headline confidence.
- **Track-record honesty — in-sample vs out-of-sample.** Accuracy measured on matches you used to derive or tune these rules (or on games already played when you scored them) is *in-sample* and optimistically biased — never quote it as the skill's hit rate. Only a call locked *before* kickoff counts as out-of-sample validation. Whenever you report any accuracy, label which it is and flag the overfitting risk; a clean-looking backtest on the games the rules were built from proves consistency, not predictive power.
- **Cite sources**; prefer recent, reputable previews and a mainstream odds aggregator. Note that odds and team news move — re-check near kickoff.
- **Keep markets internally consistent.** Derive handicap / O/U / BTTS / correct-score from one probability model; don't hand-wave each in isolation.
- **Tag low-reliability markets.** HT-FT, anytime/first scorer, and any Bet Builder / same-game parlay are **Weak / entertainment** — compound legs multiply error; never present them as equal-confidence to 1X2.
- **All times in GMT+8 (Asia/Taipei)** with the timezone shown. Convert any UTC kickoff before printing.
- **Calibrate confidence honestly.** Define it: High ≈ aligned signals + clear favorite; Medium ≈ lean with real counter-risk; Low ≈ coin-flip / volatile. A knockout tie that can go to penalties is rarely High.
- **Taiwan Sports Lottery (台灣運彩) localization.** When the user is betting via 運彩 (Taiwanese context, or they paste 運彩 odds):
  - **Terminology map**: 不讓分 = 1X2 / moneyline (主勝 / 和 / 客勝), 讓分 = handicap, 大小球 = over/under, 波膽 = correct score, 半全場 = HT-FT, 晉級 = to-qualify, 獨贏/冠軍 = outright.
  - **90-minute settlement (critical):** 運彩 basic markets (不讓分, 讓分, 大小球, 波膽, 半全場) settle on **regulation 90 minutes + stoppage only — extra time and penalties do NOT count.** Only 晉級 / 冠軍-type markets use the final result. Consequence: in a knockout, the **和 (draw) outcome of 不讓分 is a real, bettable result** (the tie is decided in ET/PK, but the 90-min bet still settles as a draw) — do not call the draw "impossible" for 運彩 markets; reserve the "no draw, goes to ET/PK" framing for the 晉級 market only.
  - Source the 運彩 lines by Playwright scrape (preferred, if available) or user paste; keep all other discipline (EV gate, error bar, longshot lane) identical. **Flag the heavy 運彩 overround every time** — under that margin, "no value, skip" is the honest default and a bet that wins at a sharp book frequently loses its edge here.
- Report in the user's language (Traditional Chinese by default). Write **country / national-team names in Chinese**, with the English name in parentheses **only at the title header** (e.g. `墨西哥 (Mexico) vs 厄瓜多 (Ecuador)`); use the Chinese name alone everywhere else. Keep player names, competition terms, and metric labels in their common form.
