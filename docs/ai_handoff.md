# AI Handoff (sekisan-training)

最終更新: `2026-06-19`

目的: 建築積算士 一次試験向けの `sekisan-training` を、`GAS + Spreadsheet + HtmlService` の独立 Web アプリとして運用再開できる状態にそろえる。

## 主要情報
- リポジトリ: `C:\ProgramData\Generative AI\Github\sekisan-training`
- GAS Script ID: `1_REQ7n8e4xJkX1E3nqseFvwivdTErh2JpaJ9Rhp06dxshravzgoFOqub`
- 最新公開 deployment ID: `AKfycbyA0E4NEXVo3FmbwvkNej3r4msmdy4W5mHgIbLEqvGIzChYRjn4HWT9TOUvE6E32uQirg`
- 公開 exec URL: `https://script.google.com/macros/s/AKfycbyA0E4NEXVo3FmbwvkNej3r4msmdy4W5mHgIbLEqvGIzChYRjn4HWT9TOUvE6E32uQirg/exec`
- localStorage prefix: `sekisanTraining_`
- アプリ名: `建築積算士 一次試験 過去問演習`

## この時点で完了していること
- `sekisan-training` は別アプリとして Script ID を分離済み
- manifest / README / `CLAUDE.md` / 各種 GAS ソースは sekisan 用に切替済み
- 完成版データを repo に配置済み:
  - `data/sekisan_all_final.csv`
  - `data/sekisan_all_final_report.json`
- 画像 108 枚を `images/sekisan/` に配置済み
- ホーム画面のデザイン方針は `MUJI` に決定
- `src/index.html` は MUJI 方向で再調整済み
- ローカル確認用に `google.script.run` 非依存の fallback を追加済み
- デザイン比較・参照用の静的ページを追加済み:
  - `docs/design-comparison.html`
  - `docs/japanese-design-skill-catalog.html`

## 完了状況（2026-06-17）
- 既存公開デプロイを @17 に更新
- `data/sekisan_all_final.csv` 650問を `QuestionBank` に投入済み
- `?action=linkGitHub` で `imageUrl` を GitHub raw URL に更新済み
- 診断結果: `totalQB=650`, `published=650`, `valid=650`, 年度別 H25-R7 各50問、分野別 Ⅰ/Ⅱ 各325問
- 2026年度一次試験日（2026-10-25）に向け、`PROGRAM_START_DATE=2026-07-01`、`EXAM_DATE=2026-10-25`、週次演習 `TestPlan14` は17回構成へ更新
- 年度別模試は固定配列ではなく、`QuestionBank` に存在する年度別問題数から `mockYears` を返して表示
- 建築2次・土木2次の `src/index.html` を再確認し、積算のスマホUIを合わせ込み済み:
  - `html{font-size:min(5.8vw,16px)}` / `main max-width:360px`
  - ログインボタン `font-size:15.2px`, `min-height:46px`, `border-radius:10px`
  - 未ログイン時はヒーローを隠し、ログインカードだけ表示
  - スマホのミニテストカードは1列、PCは3列
  - スクロールトップボタンは 44px 固定、初期非表示
- 管理者/上長ダッシュボードを実装済み:
  - `UserAccess` 列は `email, role, managerEmail, active, updatedAt, displayName, showInDashboard`
  - `admin` は `showInDashboard=true` の有効ユーザー全体を表示
  - `manager` は `managerEmail` が自分のメールと一致する有効ユーザーだけを表示
  - 管理画面から `active` と `showInDashboard` を保存可能
  - `?action=diagDashboard&key=sekisan2026` で個人情報を返さず管理者/上長集計の件数診断が可能
  - 初期管理者が未作成の場合は `?action=bootstrapAdmin&key=sekisan2026` でデプロイ実行ユーザーを admin として復旧可能
- Playwright で `390x844` と `1365x900` の表示を確認済み:
  - `output/playwright/sekisan-mobile-after-admin-parity.png`
  - `output/playwright/sekisan-desktop-after-admin-parity.png`
  - `output/playwright/sekisan-oauth-start-after-admin-parity.png`
  - `output/playwright/sekisan-google-oauth-result-after-admin-parity.png`
- ログインボタンは `?oauthStart=1` へ遷移し、中間ページの `Googleアカウントに進む` まで反応確認済み
- OAuth設定は @35 時点で本番運用用に設定済み。古いOAuthエラーメモは解消済みで、最新の確認は下の「完了状況（2026-06-19）」を正とする。

## 再開手順
1. `C:\ProgramData\Generative AI\Github\sekisan-training` で `npm install`
2. `npx clasp push`
3. Apps Script エディタで `setup()` を実行
4. Script Properties に `DB_SPREADSHEET_ID` が保存されたことを確認
5. Admin 画面または `importCsvText` で `data/sekisan_all_final.csv` を投入
6. `?action=linkGitHub` を実行して `imageUrl` を GitHub raw URL 化
7. 必要なら再 deploy

## デザインまわり
- ユーザー選択: `muji`
- 狙い:
  - 紙っぽい白 / きなり基調
  - 赤は `MUJI Red` を最小限に使用
  - フラットな境界線ベース
  - 強い影、派手なグラデーション、大きい角丸は使わない
- 主な変更点:
  - ヘッダ / ヒーロー / ホームカード群を MUJI トーンへ再調整
  - serif 寄りから、素朴な sans-serif 中心へ寄せ直し
  - ローカルプレビュー時は `ローカルプレビュー中: Apps Script 連携なし` を表示

## ローカル確認方法
- アプリ画面:
  - `C:\ProgramData\Generative AI\Github\sekisan-training\src` で `python -m http.server 8765`
  - `http://127.0.0.1:8765/index.html`
- 参考ページ:
  - repo root で `python -m http.server 8766`
  - `http://127.0.0.1:8766/docs/design-comparison.html`
  - `http://127.0.0.1:8766/docs/japanese-design-skill-catalog.html`

## 重要ファイル
- `src/db.gs`: DB 初期化、`setup()` / `setupForce()`
- `src/api.gs`: API と Drive 画像リンク
- `src/Code.gs`: `doGet`、診断アクション
- `src/sekisanConfig.gs`: アプリ設定、年度・画像名変換
- `src/index.html`: MUJI デザイン調整とローカルプレビュー fallback
- `data/sekisan_all_final.csv`: 本番投入用の完成版 CSV
- `data/sekisan_all_final_report.json`: 検証レポート

## 次にやるとよいこと
- 必要なら MUJI トーンを模試画面 / 結果画面にも追加で広げる

## 完了状況（2026-06-19）
- 既存公開デプロイを @35 に更新済み。本番 URL は変更なし。
  - deployment ID: `AKfycbyA0E4NEXVo3FmbwvkNej3r4msmdy4W5mHgIbLEqvGIzChYRjn4HWT9TOUvE6E32uQirg`
  - rollback: 同じ deployment ID を @34 に戻す
- `UserAccess` の既存26名を `Users` シートにも同期済み。
  - `UserAccess`: 26行
  - `Users`: 26行
  - ダッシュボード表示: 利用者24名
  - 非表示の内訳: ログイン中の管理者本人1名はチーム表示から除外、開発者管理者1名は `showInDashboard=false`
- `syncSchedule` 実行済み。
  - `PROGRAM_START_DATE=2026-07-01`
  - `EXAM_DATE=2026-10-25`
  - 週次ミニテストは17回構成
- GAS Date のUTC/JSTずれを修正。
  - ホーム試験日: `2026年10月25日`
  - 第1回: `7月1日〜7月7日`
  - 第17回: `10月21日〜10月24日`
- 問題データ診断:
  - `QuestionBank`: 650問
  - `published`: 650問
  - 年度別: H25〜H30 / R1〜R7 各50問
  - 分野別: `sekisan_I=325`, `sekisan_II=325`
  - 必須項目欠損: 0件
- Playwrightで本番URLを実ブラウザ確認済み。
  - ログイン画面表示
  - Googleログイン開始ページ表示
  - 管理者ホーム表示
  - ダッシュボード表示
  - 管理画面ユーザー一覧26行表示
  - 第1回ミニテスト開始、25問ロード
  - スマホ幅390px表示
  - page error: 0
- 検証成果物:
  - `output/playwright/verify-sekisan-prod-2026-06-19T01-35-10-223Z.json`
  - `output/playwright/sekisan-v35-login.png`
  - `output/playwright/sekisan-v35-oauth-start.png`
  - `output/playwright/sekisan-v35-admin-home.png`
  - `output/playwright/sekisan-v35-dashboard.png`
  - `output/playwright/sekisan-v35-admin-users.png`
  - `output/playwright/sekisan-v35-test-started.png`
  - `output/playwright/sekisan-v35-mobile-home.png`

## 横展開メモ
- 建築2次・土木2次・宅建士へ適用する時は、今回の積算士と同じ順で確認する。
  1. 既存ユーザー同期
  2. 試験日・開始日・週次テスト数の同期
  3. 年度別模試/問題データ数の診断
  4. JST日付表示のブラウザ確認
  5. 管理画面ユーザー一覧とダッシュボード表示の確認
  6. テスト開始まで実クリック確認
