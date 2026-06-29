# worldcup-predict

Predict World Cup matches from live data.

## Skills

### `/predict-match` — Match Prediction

Give it a fixture (`Brazil vs Argentina`), a date (`today`, `2026-07-02`), or a team, and it pulls current data off the web and returns a multi-dimensional read for each match:

- **Live data, always cited**: fixtures, form & xG, player availability and form, goalkeeper, tactical style matchup, set pieces, mentality/context, conditions and travel, referee tendency, and pundit consensus — nothing fabricated; missing data is marked `unknown`
- **The call**: predicted winner, top-3 most-likely scorelines, and an honestly-calibrated confidence level — plus a realistic dark-horse / upset scenario with a rough probability
- **Betting board across markets**: 1X2, Asian handicap, over/under, both-teams-to-score, correct score, to-qualify / extra-time — each with implied vs estimated probability and expected value, flagging only clearly positive-EV calls. Half-time/full-time and goalscorer markets are included but tagged **Weak / entertainment**
- **Discipline built in**: soft factors (national "character") are color only and never move a number; markets are derived from one consistent probability model; flat-staking and responsible-gambling guidance wherever odds appear
- Kickoff and all times shown in **GMT+8 (Asia/Taipei)**

Predictions are probabilistic and for entertainment only.
