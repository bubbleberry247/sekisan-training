# sekisan-training

建築積算士 一次試験の過去問演習を行う GAS Web アプリです。平成25年度から令和7年度までの 650 問を `QuestionBank` に投入し、分野別ミニテストと年度別模試を提供します。

## 概要
- 技術構成: Google Apps Script Web アプリ + Google Sheets DB + `src/index.html`
- 公開URL: https://script.google.com/macros/s/AKfycbyA0E4NEXVo3FmbwvkNej3r4msmdy4W5mHgIbLEqvGIzChYRjn4HWT9TOUvE6E32uQirg/exec
- 主要分野: `Ⅰ建築一般` / `Ⅱ数量積算`
- 学習プラン: `TestPlan14` シートを使った 17 回の週次演習セット（2026年7月1日〜10月24日）
- 標準設定: 週次演習 20〜25問、分野別ミニテスト 10問、年度別模試 50問、模試制限時間 180分

## 主要ファイル
- [src/README.md](src/README.md): GAS ソースの役割一覧
- [data/README.md](data/README.md): インポート用 CSV の配置場所
- [src/db.gs](src/db.gs): `HEADERS` と DB 初期化
- [src/sekisanConfig.gs](src/sekisanConfig.gs): アプリ名、年度、画像パス変換

## セットアップ
1. `npm install`
2. `npx clasp login`
3. `npx clasp create --title "sekisan-training" --type standalone` または `.clasp.json` に対象 Script ID を設定
4. `npx clasp push`
5. Apps Script エディタまたは `clasp run` で `setup_()` を実行

## データ投入
- 完成版 CSV は `data/sekisan_all_final.csv`
- 検証レポートは `data/sekisan_all_final_report.json`
- Admin 画面の Dry-run -> Import で `QuestionBank` に投入
- 画像付き問題は、CSV投入後に `?action=linkGitHub` で `imageUrl` を GitHub raw URL 化
- 2026-06-17: 650問投入、GitHub画像リンク更新、公開デプロイ @17 で診断済み
- 2026-06-17: 建築2次・土木2次のスマホUIに合わせ、未ログイン画面、ボタン寸法、カード余白、スクロールトップボタンを調整済み
- 2026-06-17: 管理者/上長ダッシュボードを `UserAccess.managerEmail` と `showInDashboard` ベースに更新し、建築・土木と同じ管理対象者表示に調整
- 2026-06-18: 2026年度一次試験日（2026-10-25）に向け、7月1日開始の週次演習17回へ更新。年度別模試はQuestionBankに存在する年度数と問題数から自動表示
- 2026-06-19: 公開デプロイ @35 に更新。UserAccess/Users 26名同期、ダッシュボード24名表示、管理画面26名表示、第1回ミニテスト25問ロード、スマホ表示をPlaywrightで確認済み。`pageErrors: []`

## 補足
- `localStorage` の接頭辞は `sekisanTraining_`
- Script manifest のタイムゾーンは `Asia/Tokyo`
- `QuestionBank` の正本ヘッダは `src/db.gs` の `HEADERS[SHEETS.QuestionBank]`
