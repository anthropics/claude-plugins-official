---
name: pptx-michikusa
description: Claude Code にインストールされているスキル一覧をスキャンし、PPTX形式のスキル図として出力する。ユーザーが /PPTX_Michikusa または /pptx-michikusa と入力したとき、あるいはスキル図・スキル一覧のPPTX作成を依頼したときに使用する。
version: 1.0.0
---

# PPTX Michikusa — Claude Code スキル図ジェネレーター

## 手順

1. `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/` 以下を再帰的にスキャンし、すべての `SKILL.md` を収集する

2. 各 SKILL.md から以下を抽出する:
   - `name`: スキル名
   - `description`: 説明（最初の1文）
   - プラグイン名（ディレクトリ名から）
   - ユーザー呼び出し可否（`user-invocable: false` でなければ呼び出し可能）

3. `anthropic-skills:pptx` スキルを使って PPTX を生成する:
   - **スライド1 (タイトル):** "Claude Code スキル図 — Michikusa" + 生成日
   - **スライド2 (サマリー):** プラグイン別スキル数の一覧表
   - **スライド3以降 (プラグイン別):** 各プラグインのスキル一覧（名前・説明・呼び出しコマンド）

4. 出力先: `~/Desktop/claude-skill-diagram-YYYYMMDD.pptx`（YYYYMMDD は実行日）

5. 完了メッセージとファイルパスをユーザーに伝える
