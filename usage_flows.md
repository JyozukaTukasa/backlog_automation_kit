# Backlog Automation Kit 使い方

このファイルは、**何をどの順番でやるか** だけを簡単にまとめたものです。

## 全体の流れ

| 手順 | 何をするか | レビューする人 | 反映先 |
|---|---|---|---|
| 1 | AI にタスク整理をさせる | PM | `task_plan.md` |
| 2 | Backlog 反映前の事前確認をする | PM | 確認だけ |
| 3 | Backlog に反映する | PM | Backlog |
| 4 | 開発後に review 草案を作る | PM | `review_manifest.json` |
| 5 | 承認後にコメント・ステータス反映 | PM | Backlog |

## 使い始める前の置き方

1. 既存プロジェクトの中に `tools/` を作る
2. `backlog_automation_kit` を `tools/backlog_automation_kit/` に置く
3. `.env.sample` をコピーして `.env` を作る
4. `tools/backlog_automation_kit/` を AI に渡して使い方を聞くか、そのまま `usage_flows.md` を見る

## 新規案件の流れ

1. 要件や議事録をもとに、AI に `task_plan.md` を作らせる  
   この時は Git を見なくてよい  
2. PM が `task_plan.md` を確認する  
3. Backlog に反映する前の事前確認を実行して、作成予定の課題を確認する  
4. 問題なければ Backlog に反映する  
5. 開発後は review 草案を作り、PM が確認してから反映する

レビューを入れるタイミング:
- `task_plan.md` を作った後
- 事前確認の後
- review 草案を作った後

## 既存案件の流れ

1. 追加要件や修正要件だけを AI に整理させる  
   必要な時だけ Git や既存コードを見る  
2. PM が「新規追加か、既存更新か」を確認する  
3. 既存課題を更新する場合は、`task_plan.md` の対象タスクに `Issue Key` を入れる  
4. Backlog に反映する前の事前確認を実行して、更新対象と新規作成対象を確認する  
   既存案件では `--require-issue-key-for-updates` を付ける  
5. 問題なければ Backlog に反映する  
6. 開発後は review 草案を作り、PM が確認してから反映する

レビューを入れるタイミング:
- 追加タスク案を作った後
- 事前確認の後
- review 草案を作った後

## AI への基本指示

### 要件に何を書くか

- 何を作るか
- 何のためにやるか
- いつまでに必要か
- 誰が使うか
- 既存案件なら、どの課題や機能に対する追加か
- 分かっている担当者や優先度があればそれも書く

### 要件の書き方例

```text
目的:
新人研修の準備タスクを Backlog で管理できるようにしたい

やること:
- 研修カリキュラムを整理する
- 日ごとの資料作成タスクを洗い出す
- 演習環境の準備タスクを洗い出す

期限:
2026-03-31 まで

対象:
研修担当者、講師

補足:
- 既存の第一研修タスクに続く内容
- 優先度は高め
```

### 1. タスク整理

```text
backlog_automation_kit を使ってください。
この要件をもとに task_plan.md を作ってください。
親タスクと子タスクに分けて、担当者、優先度、開始日、期限日、目的、成果物、完了条件を入れてください。
Backlog にはまだ反映しないでください。
```

### 2. Backlog 反映前の事前確認

```text
backlog_automation_kit を使ってください。
task_plan.md を確認して、Backlog 同期の事前確認を実行してください。
Backlog にはまだ反映しないでください。
```

### 3. Backlog 反映

```text
backlog_automation_kit を使ってください。
事前確認の結果を確認したうえで、task_plan.md を Backlog に反映してください。
```

### 4. 開発後の確認

```text
backlog_automation_kit を使ってください。
対象リポジトリの Git diff とテスト結果をもとに、review_manifest.json と review_summary.md を作ってください。
Backlog にはまだ反映しないでください。
```

### 5. 承認後の反映

```text
backlog_automation_kit を使ってください。
approved=true のものだけを対象に、review_manifest.json の内容を Backlog に反映してください。
コメントとステータスを更新してください。
```

## 迷った時のルール

1. いきなり Backlog に反映しない  
2. 先に事前確認をする  
3. 開発後はいきなり更新せず、先に review 草案を作る  
4. PM が確認してから反映する
5. 既存課題を更新する時は `Issue Key` を入れる
6. 新規案件では不要な Git 調査をしない
7. 既存案件では `--require-issue-key-for-updates` を付ける
