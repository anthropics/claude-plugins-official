---
name: Release
about: リリース用ISSUEテンプレート
title: 'Release v'
labels: 'release'
assignees: ''
---

# Release vX.X.X

## リリース概要
<!-- このリリースの主な内容を日本語で記載 -->

## 変更内容

### 新機能
-

### 改善
-

### バグ修正
-

### 破壊的変更
-

## リリースチェックリスト

### Phase 1: 準備

- [ ] GitHubでこのISSUEを作成
- [ ] develop Branching: Run the following command on the production server
- [ ] バージョン番号を確定（`vX.X.X`）
- [ ] CHANGELOG.mdを更新

### Phase 2: テスト

- [ ] すべてのテストが合格
- [ ] ビルドが成功
- [ ] ドキュメントが最新

### Phase 3: リリース実行

- [ ] developブランチで最終調整完了
- [ ] PR作成: `develop` → `main`
  - **タイトル**: `release: vX.X.X`（英語）
  - **本文**: このISSUEの内容をコピー（日本語）
- [ ] **マージコミット**でマージ（Squash禁止）
- [ ] タグ付け: `git tag vX.X.X`
- [ ] タグをプッシュ: `git push origin vX.X.X`

### Phase 4: リリース後

- [ ] GitHubでリリースノート作成
- [ ] mainブランチのデプロイ確認（該当する場合）
- [ ] このISSUEをクローズ

---

## 🚨 重要な注意事項

### Git Workflow遵守

- ✅ **develop → main への直接PR**（リリース時のみ許可）
- ❌ **main → develop への逆流は絶対禁止**
- ✅ **マージコミット使用**（Squash禁止）

### 言語ルール

- ✅ PRタイトル: 英語（例: `release: v1.0.1`）
- ✅ PR本文: 日本語（このISSUEの内容）

---

**関連ドキュメント**: CLAUDE.md の「リリースフロー」セクションを参照
