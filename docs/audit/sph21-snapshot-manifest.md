# SPH-21 CSV検証・JSONマニフェスト v1

参照: [PR #3517](https://github.com/etsu33/jinja_app/pull/3517)、
[SQL v1.1](sql/sph21_permission_snapshot.sql)、
[psql runner](sql/sph21_permission_snapshot_run.psql)。既存SQL・取得範囲は変更しない。

## 実行方法

Python 3.11以上・標準ライブラリのみ。DB接続・SQL実行・環境変数の読み取りは行わない。
以下は既に非公開領域に保存されたCSVに対するオフライン操作であり、本番取得の許可ではない。

```sh
python3 scripts/audit/sph21_snapshot_manifest.py /private/path/snapshot.csv \
  --output /private/path/snapshot.manifest.json
python3 scripts/audit/sph21_snapshot_manifest.py /private/path/snapshot.csv \
  --verify /private/path/snapshot.manifest.json
```

`--output` と `--verify` はどちらか一つが必須。
成功時は終了コード0、検証失敗・ファイル不在・I/O失敗・JSON不正は1、引数不正は2。
CSVは読み取りのみ。出力は排他的な新規作成とし、既存ファイル、シンボリックリンク、CSV自身への出力を拒否する。
構造検証の失敗時は出力を作らない。書き込み中のI/O障害時は不完全なJSONが残り得るため、
信頼する前に終了コードを確認する。既存マニフェストを削除・更新して再検証する運用はしない。
エラーにはCSVのセル値やファイルパスを出さない。

## 入力契約

- runnerの複数セクションCSV（psql CSV形式、UTF-8、任意の先頭BOM）。LF・CRLFと引用符内のカンマ・引用符・改行を扱う。
- SQL v1.1の正確なヘッダーをS0〜S9の順序で各1回必要とする。データ行の列数と先頭の `snapshot_query` ラベルを検証する。
- 空の結果でもヘッダーは必須。S0・S8はそれぞれ1行、その他は0行以上を許容する。
- 空行、NUL、不正UTF-8、閉じない引用符、ヘッダーの欠落・重複・順序違い、余分な列やログ・行数フッターを拒否する。
- S0は `transaction_isolation=repeatable read`、`transaction_read_only=on`、`guard=ok` が必須。
- `snapshot_started_at` は実在する日付・時刻とタイムゾーンを必須とする。
  ISO形式の `YYYY-MM-DD HH:MM:SS[.ffffff]+HH[:MM]`（T区切り、Z、+HHMMも可）を許容する。
  取得日時としてS0の値をそのまま記録し、検証時の時計とは比較しない。
- S0の正の整数 `server_version_num` とPostgreSQL形式の `snapshot` も検証する。
- 権限列の意味・ロールの実在性・SQL実行の事実は検証しない。

## マニフェスト

```json
{
  "manifest_version": 1,
  "snapshot_query_set": "sph21_permission_snapshot/v1.1",
  "sha256": "<64桁の小文字16進数>",
  "size_bytes": 1234,
  "snapshot_started_at": "2026-11-24 10:00:00+09",
  "sections": [
    {"id": "S0", "row_count": 1},
    {"id": "S1", "row_count": 0}
  ]
}
```

上記の `sections` は説明用抜粋。実際にはS0〜S9の10要素を記録する。
SHA-256とサイズは、一度読み取った同一バイト列の全体から計算する。
BOM、引用符、改行、末尾改行を含み、デコード後の再エンコードや正規化はしない。
ファイル名・絶対パス・ACL・ロール一覧・取得結果のセル値はJSONに含めない。

## 完全性と信頼境界

初回生成では構造上の欠損・破損を検出する。構造を保つ任意の改変や、末尾セクション内の
完全なデータ行の削除は、比較元なしには判別できない。
取得直後に生成して信頼できる場所へ保存したマニフェストを `--verify` に渡すことで、
以降の1バイトの変更・切り詰め・追加もSHA-256とサイズの照合により失敗とする。
検証は構造の再検証とマニフェスト全フィールドの一致を要求する。

これは署名や取得元の認証ではない。CSVとマニフェストの両方を書き換えられる場合の改変は検出できない。
S0のガードもCSV内の記録であり、実際にREAD ONLYで取得したことの独立した証明ではない。
原本とマニフェストはGitHubへ保存せず、アクセス制限のある非公開領域で管理する。
入力はメモリに全体を読み込むため、大容量CSVではメモリ容量に注意する。
読み取り中に別プロセスがCSVを書き換えない、取得完了済みの原本を入力する。

## 自動テスト

ダミーCSVはテストコード内で生成・保持し、本番CSV・ユーザーデータ・権限結果は使用しない。
テストは既存の `backend/tests` に置き、DBなしでも以下で実行できる。

```sh
python3 -m unittest discover -s backend/tests -p test_sph21_snapshot_manifest.py -v
```

正常系は空セクション・BOM・LF/CRLF・末尾改行なし・Unicode・引用符内改行・JSON生成と照合。
異常系は全10セクションそれぞれの欠落・重複、順序違い、ラベル・列数・文字コード・引用符の破損、
S0条件・日時不正、ファイル不在、JSON不正、内容・改行変更・切り詰め、出力先の衝突を検証する。
