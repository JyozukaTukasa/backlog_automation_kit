# Backlog Automation Kit

このキットは、**AI でタスクを整理し、Backlog に安全に反映するための入口**です。

## 最初に見るもの

1. [使い方の流れ](./usage_flows.md)
2. [運用ガイド](./backlog_automation_guide.md)

## `.env` の書き方

`.env.sample` をコピーして `.env` を作ります。

```env
BACKLOG_SPACE_ID=your-space
BACKLOG_API_KEY=your-api-key
BACKLOG_PROJECT_KEY=YOURPROJECT
```

入れる値:
- `BACKLOG_SPACE_ID`
  - Backlog の URL にあるスペース ID です
  - 例: `https://example.backlog.com` なら `example`
- `BACKLOG_API_KEY`
  - Backlog の API 設定画面で発行する API キーです
- `BACKLOG_PROJECT_KEY`
  - 対象プロジェクトのキーです
  - 例: `AITEST`

どこで確認するか:
- スペース ID
  - Backlog の URL、または招待メールで確認
- API キー
  - Backlog の `Personal Settings` -> `API` で発行
- プロジェクトキー
  - 対象プロジェクトで使っているキーを確認
  - 1つの確認方法として、Backlog Git URL の `/[Project key]/[Repository].git` に含まれます

参考:
- Backlog API Settings: https://support.backlog.com/hc/en-us/articles/115015420567-API-Settings
- スペースIDとは？: https://support-ja.backlog.com/hc/ja/articles/360036151593-%E3%82%B9%E3%83%9A%E3%83%BC%E3%82%B9ID%E3%81%A8%E3%81%AF
- Authentication & Authorization: https://developer.nulab.com/docs/backlog/auth/
- Git summary: https://support.backlog.com/hc/en-us/articles/115015468828-Git-summary

## まず伝えること

- 新規案件は、要件から `task_plan.md` を作る
- 既存案件は、更新対象に `Issue Key` を入れる
- いきなり Backlog に反映せず、先に事前確認をする
- 開発後は、先に review 草案を作ってから反映する

## ざっくりした流れ

1. AI に `task_plan.md` を作らせる
2. 事前確認をする
3. Backlog に反映する
4. 開発後に review 草案を作る
5. PM が確認してから反映する

## レクチャーする時の順番

1. `usage_flows.md` で全体の流れを見せる
2. 新規案件と既存案件の違いを説明する
3. `task_plan_template.md` を見せる
4. 必要な時だけ `backlog_automation_guide.md` を見る

## 補足

- markdown の雛形: [task_plan_template.md](./task_plan_template.md)
- 詳細ルール: [backlog_automation_guide.md](./backlog_automation_guide.md)
