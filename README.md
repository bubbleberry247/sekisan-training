# sekisan-training

建築積算士 一次試験の過去問演習を行う GAS Web アプリです。平成25年度から令和7年度までの 650 問を `QuestionBank` に投入し、分野別ミニテストと年度別模試を提供します。

## 概要
- 技術構成: Google Apps Script Web アプリ + Google Sheets DB + `src/index.html`
- 主要分野: `Ⅰ建築一般` / `Ⅱ数量積算`
- 学習プラン: `TestPlan14` シートを使った 12 回の演習セット
- 標準設定: ミニテスト 20 問、模試 50 問、模試制限時間 120 分

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
- 画像付き問題は、CSV投入後に Drive フォルダへ画像をアップロードし、`apiAdminLinkAllDriveImages` で `imageUrl` を実URL化

## 補足
- `localStorage` の接頭辞は `sekisanTraining_`
- Script manifest のタイムゾーンは `Asia/Tokyo`
- `QuestionBank` の正本ヘッダは `src/db.gs` の `HEADERS[SHEETS.QuestionBank]`
