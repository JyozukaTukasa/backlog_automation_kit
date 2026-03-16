# Backlog Automation Guide

## 運用イメージ
この仕組みは、**PM が AI で md にタスクを整理し、その md を Backlog に同期する**運用を前提にしています。  
開発担当者は Backlog の Web で実績や進捗を入力し、PM 側が必要に応じて自動化コマンドを使います。

基本の流れは以下です。

1. プロジェクト内で AI を使って、md 形式でタスクを洗い出す
2. md に親タスク、子タスク、開始日、期限日、担当者、優先度、目的、成果物、完了条件を書く
   既存課題を更新する場合は `Issue Key` も書く
3. Skill または CLI で md の事前確認をする
4. 問題なければ明示的に Backlog へ反映する
5. 実際の開発は担当者が Backlog Web 上で進捗管理する
6. PM が `draft-progress-review` でレビュー草案を作る
7. PM が内容を確認し、承認したものだけコメント・ステータス反映する

## 何をどこに書くか

### md に書くもの
- 親タスク
- 子タスク
- Issue Key
- 開始日
- 期限日
- 担当者
- 優先度
- 目的
- 成果物
- 完了条件

### Backlog に同期するもの
- 親子関係
- 開始日
- 期限日
- 担当者
- 優先度
- 詳細
  - 目的
  - 成果物
  - 完了条件

### 開発後に証拠ベースで反映するもの
- ステータス
  - まだ着手していない: `未対応`
  - 開発途中または証拠不足: `処理中`
  - 実装・修正は終わっていて PM 未確認: `処理済み`
  - PM 確認済み: `完了`
- コメント
  - 何を実装したか
  - 何を修正したか
  - どのリポジトリか
  - どのブランチか
  - どの PR / URL か

## PM と開発担当者の役割
- PM
  - md の内容を確認する
  - `sync-md` の事前確認結果を確認する
  - `draft-progress-review` を実行する
  - review manifest を確認し、承認可否を決める
  - 必要に応じて `apply-reviewed-manifest --apply` を実行する
- 開発担当者
  - Backlog Web で進捗や実績を入力する
  - PM にレビュー用の実装情報を共有する
  - このキットで直接 Backlog を更新する前提にはしない

## 最低限の設定
`.env` に以下を置く。

```env
BACKLOG_SPACE_ID=your-space
BACKLOG_API_KEY=your-api-key
BACKLOG_PROJECT_KEY=YOURPROJECT
```

## md テンプレート
まず雛形を出す。

```bash
python3 backlog_toolkit_cli.py dump-md-template task_plan.md
```

### md の書式
```md
# Backlog Task Plan

## Parent: 第一研修の要件定義を固める
- Issue Key:
- Assignee: 定塚 司
- Priority: high
- Start Date: 2026-03-16
- Due Date: 2026-03-19
- Purpose: 第一研修の前提、到達目標、判断基準を確定する。
- Deliverables:
  - 要件定義書
  - 判断基準表
- Done Conditions:
  - 要件定義書が確定している
  - 関係者合意が取れている

### Child: 1-1 議事録から前提情報を抜き出す
- Issue Key:
- Assignee: 定塚 司
- Priority: high
- Start Date: 2026-03-16
- Due Date: 2026-03-16
- Purpose: 議事録から研修の目的、対象者、期間、期待レベルを抽出する。
- Deliverables:
  - 前提整理メモ
- Done Conditions:
  - 目的、対象者、期間、期待レベルが整理されている
```

## Backlog へ同期

### md をそのまま同期
最初は必ず事前確認をする。

```bash
python3 backlog_toolkit_cli.py sync-md task_plan.md
```

### 実際に新規作成する
```bash
python3 backlog_toolkit_cli.py sync-md task_plan.md --apply
```

### 既存課題を更新する
既存課題更新は別許可にする。

```bash
python3 backlog_toolkit_cli.py sync-md task_plan.md --apply --allow-update-existing
```

既存案件で更新を含む場合は、`Issue Key` を書いたうえで次を使う。

```bash
python3 backlog_toolkit_cli.py sync-md task_plan.md --apply --allow-update-existing --require-issue-key-for-updates
```

### 中間JSONに変換して確認したい場合
```bash
python3 backlog_toolkit_cli.py convert-md task_plan.md task_plan.json
python3 backlog_toolkit_cli.py sync-json task_plan.json
```

## 安全運用ルール
- `sync-md` / `sync-json` はデフォルトで事前確認になる
- `--apply` がない限り Backlog を変更しない
- `--allow-update-existing` がない限り既存課題は更新しない
- `--require-issue-key-for-updates` を付けると、Issue Key がない更新は止める
- このキットには削除機能を入れない
- 既存課題更新の前に、必ず事前確認の結果を確認する
- 進捗比較は review 付き manifest ベースで、証拠がないものは更新しない
- 通常運用では `compare-progress` を直接使わず、`draft-progress-review` と `apply-reviewed-manifest` を使う

## 子タスクだけ追加
親タスク配下へ追加する場合は以下。  
このコマンドは事前確認なしで即時に課題を作成するため、PM が内容確認済みの時だけ使う。

```bash
python3 backlog_toolkit_cli.py add-child-task \
  --parent-key AITEST-83 \
  --summary "[第一研修WBS] 1-11 追加確認を行う" \
  --assignee "定塚 司" \
  --purpose "追加機能の観点整理を行う" \
  --deliverables "確認メモ" \
  --done-conditions "確認メモがレビュー可能" \
  --start-date 2026-03-31 \
  --due-date 2026-03-31 \
  --priority medium
```

## PM向けの確認コマンド

### 今日やるべきタスク
```bash
python3 backlog_toolkit_cli.py report-today --date 2026-03-16
```

### 誰が遅れているか
```bash
python3 backlog_toolkit_cli.py report-delayed --date 2026-03-16
```

## ソースコード比較
通常運用では、**レビュー草案を作ってから承認済みのものだけ反映する**。

### おすすめ運用
manifest を直接手書きせず、まず Git diff とテスト結果からレビュー草案を作る。
コマンド確認では、`|` や `;` などのシェル演算子は使わない。

```bash
python3 backlog_toolkit_cli.py draft-progress-review \
  --parent-key AITEST-83 \
  --repo-root /path/to/repo \
  --test-cmd "pytest -q" \
  --output review_manifest.json \
  --markdown-summary review_summary.md
```

この結果を PM が確認し、`approved`、`paths_exist`、`implemented`、`fixed`、`pm_confirmed` を埋める。

その後、承認済みのものだけを反映する。

```bash
python3 backlog_toolkit_cli.py apply-reviewed-manifest \
  --manifest review_manifest.json \
  --repo-root /path/to/repo \
  --write-comments \
  --apply-status \
  --apply
```

### 上級者向け: 既存 manifest を直接使う場合
`compare-progress` は既存 manifest を直接評価したい場合だけ使う。

```bash
python3 backlog_toolkit_cli.py compare-progress \
  --manifest compare_manifest.json \
  --repo-root /path/to/repo \
  --write-comments \
  --apply-status
```

### manifest に書けるもの
- `issue_key`
- `approved`
- `paths_exist`
- `candidate_paths`
- `grep`
- `commands`
- `repo_name`
- `branch`
- `pr_url`
- `implemented`
- `fixed`
- `pm_confirmed`

### manifest 例
```json
{
  "checks": [
    {
      "issue_key": "AITEST-123",
      "approved": true,
      "paths_exist": ["src/app.py"],
      "candidate_paths": ["src/app.py", "tests/test_app.py"],
      "grep": [
        {"path": "src/app.py", "pattern": "def main("}
      ],
      "commands": [
        {"cmd": "python3 -m py_compile src/app.py", "workdir": "."}
      ],
      "pass_status_id": 3,
      "fail_status_id": 2,
      "repo_name": "sample-repo",
      "branch": "feature/task-123",
      "pr_url": "https://github.com/example/sample-repo/pull/10",
      "implemented": [
        "main関数を追加した",
        "起動エラーを解消した"
      ],
      "fixed": [
        "未使用importを削除した"
      ],
      "pm_confirmed": false,
      "comment_header": "証拠ベース確認結果"
    }
  ]
}
```

### ステータス反映ルール
- 証拠が不足、または失敗: `処理中`
- 証拠が揃っているが PM 未確認: `処理済み`
- 証拠が揃っていて `pm_confirmed=true`: `完了`

## ハルシネーション防止ルール
- md 同期は、md に書かれている情報だけを Backlog に反映する
- ソースコード比較は、manifest に書いた証拠だけで判定する
- レビュー草案は自動生成してよいが、`approved=true` を人が付けるまで反映しない
- コメントには確認済みの事実だけを書く
- 「たぶん終わっている」「見た感じ良さそう」は反映しない
- 同名課題が複数ある場合は同期を止める
- 担当者本人の作業進捗入力は Backlog Web を正とする
