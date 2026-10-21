# GitHub公開時の確認事項

## 公開範囲

公開対象は、PC内で起動するアプリのソースコード、テスト、文書、MITライセンス、
依存バージョンの記録、合成サンプルです。スマートフォン対応やオンラインデプロイは含めません。
GitHubへの初回公開は、公開先・Public設定・公開ファイル・ライセンスを提示し、
所有者の明示承認を得てから行います。

## 公開する内容

- ルート: `app.py`、`README.md`、`LICENSE`、`pyproject.toml`、`requirements-lock.txt`、`.gitignore`、`AGENTS.md`。
- `src/workout_maker/`のPythonソースと`tests/`のテスト。
- `docs/`のMarkdown文書。
- `examples/`の4つのJSONと2つのZWO。自作の合成データだけを含みます。
- `.streamlit/config.toml`。接続は`127.0.0.1`に限定し、利用統計送信を無効にします。

新しいファイルは内容を確認してから個別に追加してください。
`.gitignore`は誤追加の予防であり、ファイルの安全性を保証するものではありません。
強制追加や既に追跡したファイルには別の確認が必要です。

## 含めない内容

- `.venv/`、キャッシュ、ビルド生成物、`.tmp/`。
- `artifacts/`のスクリーンショットとローカルテスト記録。
- `user_data/`、`downloads/`、`backups/`、個人のワークアウトやFTP履歴。
- `.env`と`.env.*`、Streamlit secrets、認証情報、秘密鍵、ローカルDB、ログ。
- ユーザー名を含む絶対パス、連絡先、アカウント情報、外部サービスのロゴ・公式ワークアウト。

## 検証

1. READMEの手順、相対リンク、非公式関係の説明、MITライセンスの一致を確認する。
2. 固定依存とプロジェクトの依存条件を照合し、`pip check`を実行する。
3. 全テスト、Ruff検査、書式検査を実行する。
4. 公開候補の全ファイルで、秘密情報・個人情報・未確認ファイルの混入を点検する。
5. 公開するファイルの一覧とハッシュを承認対象として固定する。
6. 公開の直前に承認対象から変更がないことと、コミットの著者情報を確認する。

現時点の機能・検証結果は[検証記録](validation.md)、
外部サービスの確認範囲は[互換性記録](compatibility.md)を参照してください。
依存のバージョン記録はハッシュ付きロックではなく、未知の脆弱性がないことを保証しません。
ワークアウト名・説明にも個人情報が入り得るため、公開Issueに実データや認証情報を添付しないでください。

## 依存関係の未解決事項

確認日: 2026-10-21。固定した44パッケージについて、PyPI公式JSON APIで配布版の存在、
公開済み脆弱性情報、取り下げ情報を照合しました。照会した配布ファイルの取り下げは0件でした。
Pillow 12.3.0に8件の脆弱性情報があり、他の43パッケージには照会時の同API上で該当情報がありませんでした。
この照会は完全なセキュリティ監査ではなく、未知の問題やデータベースの未収録を含みません。

[Pillow 12.3.0のPyPI情報](https://pypi.org/pypi/pillow/12.3.0/json)に記載された修正版は13.0.0です。
[Pillow公式13.0.0リリースノート](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)にも修正内容があります。
一方、確認時の最新安定版[Streamlit 1.66.0の依存条件](https://pypi.org/pypi/streamlit/1.66.0/json)は
`pillow>=9.2.0,<13`です。13未満の最新安定版は12.3.0であり、互換条件内の修正は未解決です。

本アプリのソースにはPillowの直接呼び出しや画像・PDF入力がなく、JSONのみを受け付けます。
外部公開は実装せず、既定の接続はPC内に限定しています。これらは利用範囲の制限であり、
依存パッケージ全体について脆弱性が到達不能であることの証明ではありません。
ローカル実行用のソース公開を承認する場合も、この未解決事項を公開判断に含めてください。
依存条件が対応した時点で固定依存を更新し、全テストと依存監査を再実施します。

| PyPIに記載されたアドバイザリ | 修正版 |
| --- | --- |
| [GHSA-p4wg-p73j-c528](https://github.com/python-pillow/Pillow/security/advisories/GHSA-p4wg-p73j-c528) | 13.0.0 |
| [GHSA-65qm-jvmh-6pqg](https://github.com/python-pillow/Pillow/security/advisories/GHSA-65qm-jvmh-6pqg) | 13.0.0 |
| [GHSA-58r4-6rv3-gfh8](https://github.com/python-pillow/Pillow/security/advisories/GHSA-58r4-6rv3-gfh8) | 13.0.0 |
| [GHSA-pchr-8j38-3x4p](https://github.com/python-pillow/Pillow/security/advisories/GHSA-pchr-8j38-3x4p) | 13.0.0 |
| [GHSA-q45j-58j2-45rg](https://github.com/python-pillow/Pillow/security/advisories/GHSA-q45j-58j2-45rg) | 13.0.0 |
| [GHSA-462x-pgg6-55fp](https://github.com/python-pillow/Pillow/security/advisories/GHSA-462x-pgg6-55fp) | 13.0.0 |
| [GHSA-c6hw-5grf-ff96](https://github.com/python-pillow/Pillow/security/advisories/GHSA-c6hw-5grf-ff96) | 13.0.0 |
| [GHSA-vx6w-vv9f-6gvg](https://github.com/python-pillow/Pillow/security/advisories/GHSA-vx6w-vv9f-6gvg) | 13.0.0 |
