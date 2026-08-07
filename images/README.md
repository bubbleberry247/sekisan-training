# images/ — 問題画像

QuestionBank の `imageUrl` で参照する問題画像を格納するフォルダです。

[← リポジトリルートへ](../README.md)

## sekisan 画像
- 配置先: `images/sekisan/`
- ファイル名: `sekisan_<年度>_<問題番号>.png`
- 例: `sekisan_H25_043.png`
- 試験当時原版から監査済みの表を再生成するときは、`python tools/build_sekisan_context_images.py --pdf-root <原版PDFフォルダ>` を実行する

## 画像登録方法
1. `images/sekisan/` の画像を Git で追跡し、GitHub `main` へ公開
2. `python tools/preflight_sekisan_release.py` を実行し、ローカル・Git追跡・GitHub公開の3条件を確認
3. GAS エディタで `preflightGitHubImages_()` を実行し、`missing` が空であることを確認
4. `linkGitHubImages_()` を実行して `QuestionBank.imageUrl` を GitHub raw の絶対URLへ更新

`linkGitHubImages_()` は、必要な画像が1件でもGitHubに存在しない場合、QuestionBankを書き換えずに中止します。

## 補足
- 完成版 CSV では、画像付き問題に `images/sekisan/...` のプレースホルダが入っている
- `src/sekisanConfig.gs` の変換ヘルパーで `qId` と画像ファイル名を相互変換できる
- 画像URLの本番反映前に、CSVの画像行数・ローカル画像数・GitHub公開画像数が114件で一致することを必須とする
