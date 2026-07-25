# SDD Fusion Assessment — 公司框架 vs eli-marketplace/sdd

> **狀態：提案 A、B 皆已實作。** A（Walking Skeleton）採 3.2 路線 1（併進 `test-driven-development`）；B（`/research` 入口）已新增 `plugins/sdd/skills/research/SKILL.md`。以下內容保留為決策紀錄，行文中的「動手前先拍板」「未定案前不要改檔案」等指示均已完成，不再是待辦。
>
> **實作時的偏離（有意）**：§6 step 4 建議「動到 spine 的部分先走 `/propose` 產正式 spec 再實作、吃自家狗糧」—— 本次為**直接實作**，未產 spec。理由：事後補的 spec 沒有 catch-mismatch 價值，只是裝飾。

> **目的**：評估公司內部 AI 開發框架（Claude Code / Cursor toolkit）有哪些優點是本 repo 的 `sdd` 尚未具備，並判斷哪些值得融合進來。
> **交辦對象**：接手執行融合的工程師。
> **結論先講**：真正值得融的硬缺口只有一個（**Walking Skeleton / Integration-First**），外加半個可選項（**純 research 入口**）。其餘皆已被覆蓋或屬包裝差異，融了會違反本 repo 自訂的 fusing checklist（見 `plugins/sdd/CLAUDE.md` → *Fusing an External Skill*）。
> **評判框架**：全程以本 repo `plugins/sdd/CLAUDE.md` 的 spine/periphery 與 fusing checklist 為準，而非另立標準。
> **動手前必先拍板的一題**（見 3.2）：Walking Skeleton 是**併進 `test-driven-development`**，還是**開新 skill**？這決定要不要碰 frozen upstream skill，也決定本提案究竟是 periphery 還是真的動 spine。**未定案前不要開始改檔案。**

---

## 1. 背景：兩套框架速覽

### 1.1 公司那套（來源：`~/Project/cursor`）
- **形態**：單一 template repo + `install.sh` / `install.ps1` 把 `agents/` `skills/` `commands/` `rules/AGENTS.md` 複製進目標專案（Cursor 或 Claude）。
- **編排**：`rules/AGENTS.md` 是人類可讀的 orchestration guide（哪個情境用哪個 agent、順序、可否並行）。
- **方法論核心**：`spec-driven-development` skill —— Research → Business Spec（user story + Given/When/Then）→ 強制 plan file（`docs/plans/YYYY-MM-DD-*.md`）→ 複雜度評估 → E2E Path 或 Simplified TDD Path → **Integration-First（Phase 4）** → ATDD（Phase 5）→ Verify。
- **已知弱點**（供對照，非本文重點）：硬綁單一 stack、靠 agent description `MUST/PROACTIVELY` 期望自動觸發、`install.sh` 破壞性覆蓋、無 CI 驗證（存在 skill 內部路徑斷鏈 bug）。

### 1.2 本 repo 的 sdd
- **形態**：Claude Code plugin marketplace，core `sdd` + 7 個 `sdd-<lang>` pack，靠 `dependencies: ["sdd"]` 注入。
- **哲學**：thin fixed orchestration **spine** + fat lazily-loaded knowledge **periphery**。
- **工作流**：`/setup → /propose → /validate → /apply → /complete`（Full），`/quick`（fileless）。
- **實作 pipeline（`/apply`）**：Phase 1 single-writer 序列化（拓撲序、in-place squash、零 merge）→ Phase 2 並行唯讀 review + 序列化 fix + fresh reviewer 防錨定 → Phase 3 doc。
- **實作策略**：**Contract-First**（design.md 定 API contract/shared types）+ 垂直分層 group（backend group → frontend group）+ 各 agent 各層 TDD。
- **保護機制**：NEEDS/CONFLICT/BLOCKED signaling、check-structure.sh、validate、SOURCES.yaml、verification-before-completion。

---

## 2. 客觀評估：公司那套有、sdd 沒有的東西

已用 grep 驗證 sdd 現況，逐項分級。

| 公司那套的能力 | sdd 現況（已驗證） | 判定 | 是否融合 |
|---|---|---|---|
| **Integration-First / Walking Skeleton**（先 hardcode 打通端到端，再逐層換真實作） | grep 無此概念；sdd 只有 contract-first 垂直分層 | **真缺口（硬）** | ✅ **值得融** |
| **純 research / 理解模式入口**（read-only 產 findings、不寫 spec 不改 code） | 有 exhaustive scan 引擎（`propose` Step 5）但無獨立入口 | **半個缺口** | ⚠️ **可選**（看 handoff 需求） |
| `product-manager` agent / user story（As a / I want / So that） | 有 WHEN/THEN acceptance criteria + scope contract 覆蓋需求釐清 | 弱覆蓋 | ❌ 不值得（換皮，違反反鍍金原則） |
| `refactor` 專門 agent（dead code 清理） | `review-engineer` 已抓 dead/unused code（`agents/review-engineer.md:55,84`） | 已覆蓋 | ❌ 不需要 |
| `/debug-issue` `/optimize-performance` `/refactor-code` 動詞 command | 已有 `systematic-debugging`、`performance` skill，能力齊備 | 包裝差異 | ❌ 不是能力缺口（至多補 UX 糖） |
| `agent-browser` E2E | `qa-engineer` + `playwright` skill | 已覆蓋 | ❌ 不需要 |
| plan file 當人類可讀計畫 | proposal.md + design.md 更完整 | sdd 更強 | ❌ 不需要 |

---

## 3. 融合提案 A（主要）：Walking Skeleton 作為可選實作策略

### 3.1 為什麼是真缺口
sdd 的 contract-first 靠 design.md 的**紙上契約**保證層與層對得上；整合風險要到 frontend group 真的接 backend、甚至 Phase 2 QA E2E 才會暴露。Walking Skeleton 是**正交的水平切法**：先橫切一條最薄的端到端骨架（各層用 hardcode 資料）跑通，把整合風險在第一步打掉，再逐層填真實作。

**適用情境（高整合不確定性）**：新的外部系統整合、沒有先例的跨層資料流、SSR / IPC / 跨 process 邊界、契約本身還沒被驗證過的新功能。
**不適用**：純單層改動、有明確先例可循的 CRUD、refactor / 格式遷移類。

### 3.2 這不是「輕微動 spine」——先解決與 TDD skill 的正面衝突（阻擋項）

按 `plugins/sdd/CLAUDE.md` fusing checklist 第 1 條，它**不是純 periphery**：會改到 `propose` 的 grouping principle 與 `apply` 的 choreography。這是 checklist 說的「load-bearing for choreography 才准碰 spine」的正當案例，但成本比表面高，有兩個硬衝突必須先處理：

**(a) 名詞與立場，跟 `test-driven-development` 撞正面。**
- `plugins/sdd/skills/test-driven-development/SKILL.md:180` 的段落標題就是 **`## Anti-Pattern: Horizontal Slicing`**。
- 同檔 `:199` 已經在用同一個概念詞：*"The first cycle is your **tracer bullet** — it proves the path works end-to-end before you widen coverage."*
- 這支 skill 被所有 engineer agent **eager-load**。若另開一支叫「先橫切端到端骨架」的 skill，agent 會在同一個 context 同時吃到「horizontal 是 anti-pattern」與「請先 horizontal 打通」。

  按 fusing checklist 第 4 條（trigger 重疊 → merge 進既有 skill，不造 rival），**預設解是併進 TDD 那支的 tracer-bullet 段落**，而不是新開 skill。若堅持獨立 skill，兩邊都必須寫明消歧義：TDD 罵的是 *test 批次化 vs impl 批次化*，Walking Skeleton 講的是 *跨層整合探針*——兩者正交，不是同一軸。

**(b) 「骨架 group 不做 TDD」需要一條具名例外，而例外的家是 frozen upstream。**
- TDD 是 Team Standard（`plugins/sdd/CLAUDE.md:158`，新碼 100% coverage），`agents/review-engineer.md:57` 會查 coverage，TDD skill 自己寫著 *"Thinking 'skip TDD just this once'? Stop. That's rationalization."*
- 只在 `tasks.md` group 標題寫「本 group 不做 TDD」，dispatched agent 會被自己 eager-load 的 skill 打臉，Phase 2 review 也會把它當 finding。
- 正確做法是在 TDD skill 現成的 `Exceptions (ask the user)` 清單（throwaway prototypes / generated code / config files 那格）加一條具名例外。
- **但** `skills/SOURCES.yaml:274-277` 顯示 `test-driven-development` 是 `repo: https://github.com/obra/superpowers` + `frozen: true`——`frozen` 只代表「非 `--all` 時不 sync」，跑一次 `update-skills.sh --all` body 改動就被覆蓋（repo 根 `CLAUDE.md` 規則 4）。

  → 這是本提案真正的成本所在。三條路，接手前挑一條：
  1. **併進 TDD skill**（最符合 checklist），代價：改 frozen upstream body，需同時把 `SOURCES.yaml` 該項改為 `repo: original` 並註明 inspired-by，接受未來不再從 upstream 同步。
  2. **新開 `walking-skeleton` skill**（`repo: original`），例外規則寫在新 skill 內，並在 dispatch prompt 明確覆寫 TDD 的 Iron Law；代價：兩支 skill 語意需人工維持一致，且 TDD body 未改，agent 仍可能自我矛盾。
  3. **不給例外**：骨架 group 照樣寫 test（只是 test 打在端到端這層），完全不碰 TDD skill。代價：骨架階段變重，削弱「快速打通整合」的原意，但 spine 零改動、風險最低。

**不變量不可破**：無論選哪條，single-writer / in-place squash / NEEDS-CONFLICT-BLOCKED signaling / Phase 順序都不准改。

### 3.2b Phase 2 明確零改動（別手癢）

`agents/orchestrator.md:194` 起的 Phase 2 是在**所有** Phase 1 group commit 完才 dispatch，reviewer 看到的是 harden 之後的最終 diff，不會誤 review 骨架中間態。**因此 `orchestrator.md` 的 Phase 2 段落與 reviewer prompt 規則一律不動。**

### 3.3 具體要動的檔案與改法

> **Step 編號務必看清**：`/propose` 的 Step 6 是 orchestrator 自己做的 clarify + Scope Contract；architect 是 **Step 7c** 才 dispatch 並產出 `design.md`；`tasks.md` 是 **Step 7e** 由 orchestrator 依 design.md 生成。所以「選策略」的判斷寫在 **7c 的 architect dispatch prompt**（＋`agents/architect.md`），7e 只是**消費** design.md 已定案的策略。不要把判斷塞進 Step 6。

1. **`plugins/sdd/skills/propose/SKILL.md`（Step 7c dispatch prompt + Step 7e grouping principle）**
   - **Step 7c**：在 architect 的 dispatch prompt 新增一段，要求它評估本次 change 的**整合不確定性**（用 3.1 的適用情境清單），並把選定策略寫入 design.md 的 Decisions。
   - **Step 7e**：讀 design.md 的策略決定。若為高不確定性：`tasks.md` 分組改為
     `## 1. 端到端骨架（hardcode 打通）` →（`<!-- depends: 1 -->`）`## 2..N 逐層 harden`。
   - 骨架 group **不做 TDD**（它是整合探針，不是產品碼）；harden group 才回到 Red → Green → Refactor。
   - 骨架 group 內的 hardcode 必須標記（如統一註解 `// SKELETON: replace in harden phase`），供後續 group 與 verification 定位。

2. **`plugins/sdd/agents/architect.md`**
   - 新增一節「Implementation strategy selection」：在 design.md 產出「Contract-First（預設）」或「Walking Skeleton（高整合不確定性）」的判定與理由，寫入 design.md 的 Decisions。

3. **`plugins/sdd/agents/orchestrator.md`（Phase 1）**
   - 明確：骨架 group 是 Phase 1 的第一個 group，仍走 single-writer + squash，不破壞既有 pipeline。
   - harden group 依 `depends` 序在骨架 group 之後執行，讀骨架 group 已 commit 的碼。

4. **SKELETON 殘留卡關 —— 改 `skills/complete/SKILL.md`，不要改 `verification-before-completion`**

   ⚠️ **原稿把這條指向 `skills/verification-before-completion/SKILL.md`，那是錯的：**
   - `skills/SOURCES.yaml:278-281` 顯示它是 `repo: https://github.com/obra/superpowers` + `frozen: true`——upstream mirror，改 body 違反 repo 根 `CLAUDE.md` 規則 4，且 `update-skills.sh --all` 會覆蓋。
   - 功能上也不對：那支是通用的「宣稱完成前要有證據」原則，不知道 `/complete` 存在，塞 sdd 專屬 grep 進去是污染。

   正確落點（兩處都要）：
   - **`plugins/sdd/skills/complete/SKILL.md`（`repo: original`，可改）Step 2**：目前 `/complete` **完全沒有 verification**，只數 `- [ ]` / `- [x]` checkbox。在 Step 2 的 checkbox 檢查旁加一條 grep gate：全 repo（多 repo 模式：每個被觸及的 child repo）搜 `SKELETON:`，有殘留就阻擋完成並列出位置。
   - **`plugins/sdd/skills/validate/SKILL.md`**：新增一條 design.md / tasks.md 規則——當 design.md 策略為 Walking Skeleton 時，骨架 group 預告的每個 hardcode 點都必須有對應的 harden task 覆蓋（避免只有清除檢查、卻沒人負責清）。

5. **方法論細節的家：依 3.2 的三選一決定，不要預設開新 skill**
   - 若選 3.2 路線 1（併入）：細節寫進 `skills/test-driven-development/SKILL.md` 的 tracer-bullet 段落，並把 `SOURCES.yaml` 該項改成 `repo: original` + inspired-by 註解。
   - 若選路線 2（新 skill `plugins/sdd/skills/walking-skeleton/SKILL.md`）：註冊進 `SOURCES.yaml` 為 `repo: original`（附 inspired-by 公司 spec-driven Phase 4 註解），並在該 skill 與 TDD skill 兩邊各寫一句消歧義。
   - 若選路線 3（不給 TDD 例外）：不需要新 skill，方法論寫在 `agents/architect.md` 的策略選擇一節即可。
   - **無論哪條，description 必須以 "Use when..." 起頭**：`scripts/check-cso.sh:29` 的 `DANGEROUS_PATTERNS` 直接擋 description 開頭的 `Run|Execute|Perform|Create|Build|Generate|Scaffold|Deploy|Configure|Write|Produce|Detect|Analyze|Scan`，寫成 `Scan the codebase...` 之類會直接紅燈。改完跑 `check-cso.sh` 驗觸發條件精確、不與 `test-driven-development` 重疊。

### 3.4 驗收標準（Acceptance Criteria）
- **AC1**：對一個高整合不確定性的 change 跑 `/propose`，架構師在 design.md 明確選用 Walking Skeleton 並附理由，`tasks.md` 產出「骨架 group + harden groups」且依賴標註正確。
- **AC2**：對一個低不確定性的 change 跑 `/propose`，仍維持預設 Contract-First 垂直分層——**不得**無差別套用骨架模式（避免 ceremony 鍍金）。
- **AC3**：`/apply` 執行骨架 group 時走 single-writer + squash，harden group 讀到骨架 group 已 commit 的碼；pipeline 無 merge、無 worktree。
- **AC4**：harden 未清除 `SKELETON:` 標記時，**`/complete` Step 2** 阻擋完成並回報每個殘留位置（多 repo 模式逐 repo 檢查）。此檢查實作於 `skills/complete/SKILL.md`，**不得**寫入 `verification-before-completion`。
- **AC5**：`scripts/check-structure.sh` 與 `scripts/check-cso.sh` 全綠；若新增 skill，已註冊於 `SOURCES.yaml`。
- **AC6**：spine 既有不變量未被破壞（single-writer、in-place squash、NEEDS/CONFLICT/BLOCKED signaling 行為不變）；`orchestrator.md` 的 Phase 2 段落與 reviewer prompt 規則零改動（3.2b）。
- **AC7**：design.md 選 Walking Skeleton 時，骨架 group 預告的**每個** hardcode 點都有對應 harden task 覆蓋，`/validate` 能抓出遺漏（不是只有事後的清除檢查）。
- **AC8**：TDD 例外（若採 3.2 路線 1 或 2）有具名出處，且**跑過 `scripts/update-skills.sh --all` 之後例外與 SKELETON gate 仍然存在**（證明沒有改到會被 sync 覆蓋的 frozen body，或已正確改為 `repo: original`）。

---

## 4. 融合提案 B（可選）：純 Research 入口

### 4.1 缺口性質
能力已有（`propose` Step 5 exhaustive scan），缺的是「只理解、產可存檔文件、不進實作流」的獨立入口。價值只在**需要產出給別人看的理解文件**；自用時對話探索即可。**非必要，看 handoff 需求決定。**

### 4.2 改法
- 新增 read-only command `plugins/sdd/skills/research/SKILL.md`（`/research <area>`）。
- 復用 Step 5 的 scan 邏輯，輸出一份 research findings（affected files、現有 pattern、依賴、風險），**不寫 spec、不改 code、不 commit code**。
- 定位為 `/review` 的 read-only sibling，不動 spine。
- **trigger 必須與 `/review` 明確區隔**（fusing checklist 第 4 條）：`/review` 是「對既有 code 下 review 判斷」，`/research` 是「產出理解文件、不下判斷」。description 起頭寫 `Use when...`；**不要**寫成 `Scan ...` / `Analyze ...`——`scripts/check-cso.sh:29` 會直接擋掉這些開頭動詞。

### 4.3 驗收標準
- **AC1**：`/research <area>` 產出結構化 findings 文件，全程 read-only（無 code 變更、無 code commit）。
- **AC2**：不觸發 `/propose` 的 artifact 生成，不建立 `feature-spec/changes/`。
- **AC3**：`check-structure.sh` 與 `check-cso.sh` 皆通過，且 description 與 `/review` 的觸發條件不重疊。

---

## 5. 明確不做（及理由）
- **user story / product-manager 視角**：sdd 的 WHEN/THEN + scope contract 已覆蓋需求釐清；加 As-a/I-want 是換皮，違反 fusing checklist「trigger 重疊就 merge，不造 rival」。
- **refactor / dead-code 專門 agent**：`review-engineer` 已涵蓋。
- **動詞型 command（debug / optimize / refactor）**：能力已存在於既有 skill，屬可發現性（UX）議題，非架構缺口；若要補，僅加薄 command 指向既有 skill，不新增能力。
- **agent-browser、plan file**：已被 `qa-engineer`/`playwright` 與 `proposal.md`/`design.md` 覆蓋或超越。

---

## 6. 建議執行順序
1. **先拍板 3.2 的三選一**（併入 TDD / 新 skill / 不給例外）。這是阻擋項——它決定要不要碰 frozen upstream、要不要新增 skill、AC8 怎麼驗。**未定案前不要改任何檔案。**
2. 再做 **提案 A（Walking Skeleton）**——唯一的硬缺口，價值最高。動手前先跑一次 `scripts/check-structure.sh` 建立 baseline（本次會動 skill / agent / 可能動 SOURCES.yaml，屬於根 `CLAUDE.md` 要求跑它的情境）。
3. 評估是否有 handoff 文件需求，再決定 **提案 B（Research 入口）**。
4. 提案 A 與 B 皆須通過 `check-structure.sh` + `check-cso.sh` + `/review-prompt`（動到流程邏輯的部分再加 `/review-workflow`）；動到 spine 的部分（A）建議走 `/propose` 自身流程產生正式 spec 後再實作，吃自家狗糧。
