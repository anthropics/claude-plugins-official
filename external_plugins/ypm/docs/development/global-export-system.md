# グローバルエクスポートシステム

## 概要

グローバルエクスポートシステムは、privateリポジトリからpublicコミュニティ版へのexport機能をグローバルシステムとして実装したものです。YPM、MaxMCP、その他任意のプロジェクトで使用可能です。

## システム構成

### 1. グローバルスクリプト

**ファイル**: `~/.claude/scripts/export-to-community.sh`

汎用的なprivate→public export機能を提供：
- 各プロジェクトの`.export-config.yml`を読み込み
- git-filter-repoでファイル除外＋コミットメッセージサニタイズ
- 自動PR作成
- TruffleHogセキュリティスキャン（自動）
- インタラクティブマージ（オプション）
- 自動クリーンアップ

### 2. グローバルコマンド

**ファイル**: `~/.claude/commands/ypm-export-community.md`

どのプロジェクトからも`/ypm:export-community`で実行可能なClaude Code slash command。

**特徴**:
- **多言語対応**: ユーザーのメッセージから言語を自動検出（日本語/英語）
- **AskUserQuestion使用**: 構造化された対話形式でセットアップ
- **Claude Code完結型**: ターミナル実行不要

### 3. 設定ファイル

各プロジェクトのルートに`.export-config.yml`を配置：

```yaml
export:
  private_repo: "/path/to/private"
  public_repo_url: "https://github.com/org/public.git"
  exclude_paths:
    - CLAUDE.md
    - docs/research/
  sanitize_patterns:
    - pattern: "sensitive"
      replace: "[redacted]"
```

## インストール手順

### Step 1: グローバルスクリプトのインストール

```bash
# YPMリポジトリからテンプレートをコピー
cp /path/to/YPM/templates/scripts/export-to-community.sh ~/.claude/scripts/
chmod +x ~/.claude/scripts/export-to-community.sh
```

### Step 2: グローバルコマンドのインストール

```bash
# YPMリポジトリからテンプレートをコピー
cp /path/to/YPM/templates/commands/ypm-export-community.md ~/.claude/commands/
```

**注意**: グローバルコマンドを認識させるには、Claude Codeの再起動が必要です。

### Step 3: 依存ツールのインストール

```bash
# yq (YAML parser)
brew install yq

# git-filter-repo (Git history rewriting)
brew install git-filter-repo

# TruffleHog (Security scanner)
brew install trufflehog
```

### Step 4: プロジェクトごとの設定（自動）

**YPM v1.3以降**では、`.export-config.yml`がない場合、スクリプトが自動的にインタラクティブセットアップを開始します。

**手動で作成する場合**（オプション）：

```bash
# サンプルからコピー
cp .export-config.yml.example .export-config.yml

# 自分の環境に合わせて編集
vim .export-config.yml
```

**重要**: `.export-config.yml`は個人のパスを含むため、`.gitignore`に追加してください。

## 使い方

### 初回実行（インタラクティブセットアップ）

**YPM v1.4以降**では、Claude Code完結型のインタラクティブセットアップに対応しています。

#### 推奨方法: Claude Codeで実行

```
/ypm:export-community
```

**Claude Codeが自動的に**:
1. `.export-config.yml`の存在をチェック
2. 存在しない場合 → **AskUserQuestionツール**で対話形式セットアップ
3. 存在する場合 → 即座にexport実行

**インタラクティブセットアップの流れ**（初回のみ）：

1. **Question 1: Repository Configuration**
   - Private repo path:
     - Current directory（現在のディレクトリ）
     - Custom path（Git worktree対応：main branchのパスを指定）
   - Public repo:
     - Create new（新規作成）
     - Use existing（既存URLを使用）

2. **Question 2: Files to Exclude**（複数選択可）
   - 推奨除外ファイル（デフォルト選択）：
     - `CLAUDE.md` (personal configuration)
     - `config.yml` (personal paths)
     - `PROJECT_STATUS.md` (personal project data)
     - `docs/research/` (internal research documents)
   - 追加除外ファイル（任意）

3. **Question 3: Commit Message Sanitization**
   - Skip（サニタイズなし）
   - Add keywords（機密キーワードを指定）

**セットアップ完了後**:
- Claude Codeが`.export-config.yml`を自動作成
- 内容を確認
- そのままexportに進む

#### 代替方法: ターミナルで実行

Bash対話形式を使いたい場合：

```bash
# プロジェクトのルートディレクトリで実行
~/.claude/scripts/export-to-community.sh
```

スクリプトが4ステップのウィザードを起動します（Bash `read -p`形式）

**自動生成される`.export-config.yml`の例**：

```yaml
# Export Configuration for ProjectName
# Generated: 2025-11-12

export:
  private_repo: "/Users/username/Src/proj_ProjectName/ProjectName-dev"
  public_repo_url: "https://github.com/organization/ProjectName.git"

  exclude_paths:
    - CLAUDE.md           # Personal configuration
    - config.yml          # Personal paths
    - PROJECT_STATUS.md   # Personal project data
    - docs/research/      # Internal research documents
    - .env                # Additional (user-specified)

  sanitize_patterns:
    - pattern: "project-alpha|project-beta"
      replace: "[redacted]"
```

**Public repoの自動作成**：

- オプション1を選択した場合、スクリプトが自動的に：
  - `gh repo create`でpublic repoを作成
  - exportブランチをmainに直接push
  - ブランチ保護設定を適用
  - デフォルトブランチをmainに設定
  - exportブランチを削除（クリーンアップ）

### 2回目以降の実行

`.export-config.yml`が既に存在する場合、インタラクティブセットアップはスキップされ、即座にexportが開始されます：

```bash
# プロジェクトのルートディレクトリで実行
~/.claude/scripts/export-to-community.sh

# または、Claude Codeで
/ypm:export-community
```

**実行フロー**：
1. `.export-config.yml`を読み込み
2. Public repoの存在を確認（存在しない場合は作成プロンプト）
3. ブランチ保護設定を確認・適用
4. Exportを自動実行

### ワークフロー

#### 初回Export（Public repository新規作成時）

```
1. プロジェクトをクローン
   ↓
2. 機密ファイルを除外（git-filter-repo）
   ↓
3. コミットメッセージをサニタイズ
   ↓
4. exportブランチを作成
   ↓
5. exportブランチをmainに直接push（force）
   ↓
6. ブランチ保護設定を適用
   ↓
7. デフォルトブランチをmainに設定
   ↓
8. exportブランチを削除（クリーンアップ）
   ↓
9. TruffleHogセキュリティスキャン（自動）
   ↓
10. 一時ディレクトリクリーンアップ
```

#### 2回目以降のExport（PR作成）

```
1. プロジェクトをクローン
   ↓
2. 機密ファイルを除外（git-filter-repo）
   ↓
3. コミットメッセージをサニタイズ
   ↓
4. featureブランチを作成してpush
   ↓
5. PR自動作成
   ↓
6. TruffleHogセキュリティスキャン（自動）
   ↓
7. インタラクティブマージプロンプト
   - "y"選択 → 自動マージ + クリーンアップ
   - "n"選択 → 手動マージの手順を表示
```

## 機能詳細

### Step 7: Security Verification

**TruffleHogセキュリティスキャン**を自動実行：
- Verified Secrets: 0
- Unverified Secrets: 0

**結果**:
- ✅ スキャンパス → インタラクティブマージへ進む
- ❌ スキャン失敗 → 手動マージが必要（プロンプト表示）

**TruffleHog未インストールの場合**:
- 警告メッセージを表示
- インストール手順を表示
- 手動マージの手順を表示

### Step 8: Interactive Merge

セキュリティスキャンが通過した場合のみ、以下のプロンプトが表示されます：

```
Merge PR now? (y/n):
```

**"y"を選択**:
1. 自動的にPRをマージ（`gh pr merge --merge --delete-branch`）
2. 一時ディレクトリを自動クリーンアップ
3. 完了サマリーを表示

**"n"を選択**:
1. 手動マージの手順を表示
2. 一時ディレクトリはそのまま残る（手動クリーンアップが必要）

### Step 9: Cleanup

自動マージを選択した場合のみ実行：
- 元のディレクトリに戻る
- `/tmp/ypm-public-export-XXXXXXXXXX`を削除
- 完了メッセージを表示

## トラブルシューティング

### Q: コマンドが表示されない

**A**: Claude Codeを再起動してください。グローバルコマンドの読み込みには再起動が必要です。

### Q: TruffleHogが見つからない

**A**: 以下でインストール：
```bash
brew install trufflehog
```

### Q: セキュリティスキャンで問題が検出された

**A**:
1. PRをマージせずに手動で確認
2. `/tmp/ypm-public-export-XXXXXXXXXX`で問題箇所を特定
3. `.export-config.yml`の`exclude_paths`や`sanitize_patterns`を修正
4. 再度exportを実行

### Q: マージ後にエラーが発生した

**A**:
- PRは既にマージされているため、手動でクリーンアップ：
  ```bash
  rm -rf /tmp/ypm-public-export-XXXXXXXXXX
  ```

### Q: gh pr createが間違ったリポジトリにPRを作成してしまう

**A**: upstream設定があるプロジェクト（private fork等）では、ghコマンドがupstreamをデフォルトリポジトリとして使用する場合があります。

**予防策**:

1. **ghコマンド実行前にリポジトリ一致を確認**:

```bash
# 現在のリポジトリ
CURRENT_REPO=$(git remote get-url origin | sed -E 's/.*github\.com[:/](.*)(\.git)?/\1/')

# ghのデフォルトリポジトリ
GH_DEFAULT_REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)

# 一致確認
if [ "$CURRENT_REPO" != "$GH_DEFAULT_REPO" ]; then
  echo "⚠️  警告: リポジトリ不一致"
  echo "  現在: $CURRENT_REPO"
  echo "  gh デフォルト: $GH_DEFAULT_REPO"
  echo "  -R $CURRENT_REPO を使用してください"
  exit 1
fi
```

2. **常に-Rフラグでリポジトリを明示的に指定**:

```bash
# 正しい方法
gh pr create -R signalcompose/YPM-yamato --base develop --head feature/xxx

# 間違った方法（upstreamに誤爆する可能性）
gh pr create --base develop --head feature/xxx
```

**注意**: export-to-community.shスクリプトは、意図的に異なるリポジトリ（private→public）を操作するため、スクリプト内で`--repo "$REPO_NAME"`を明示的に使用しています。

## セキュリティ考慮事項

1. **機密情報の除外**
   - CLAUDE.md（個人設定）
   - config.yml（個人パス）
   - docs/research/（内部ドキュメント）

2. **コミットメッセージのサニタイズ**
   - プロジェクト名 → `[project]`
   - 統計情報 → `[N]`
   - タイムスタンプ → `[time]`

3. **自動検証**
   - TruffleHogによる全履歴スキャン
   - 検証済みシークレット: 0を確認
   - 未検証シークレット: 0を確認

## 他プロジェクトでの使用例

### MaxMCP

```yaml
# MaxMCP/.export-config.yml
export:
  private_repo: "~/Projects/my-project-private"
  public_repo_url: "https://github.com/signalcompose/MaxMCP.git"
  exclude_paths:
    - CLAUDE.md
    - config.yml
    - docs/research/
  sanitize_patterns:
    - pattern: "internal-project-name"
      replace: "[project]"
```

### 任意のプロジェクト

1. `.export-config.yml`を作成
2. `/ypm:export-community`を実行
3. 完了

## 今後の改善案

- [ ] ドライランモード（実際のpushなしでテスト）
- [ ] 複数リポジトリの一括export
- [ ] export履歴の管理
- [ ] カスタムセキュリティスキャンルール

## 関連ドキュメント

- [Private-to-Public Strategy](../research/private-to-public-strategy.md)
- [Issue #4](https://github.com/signalcompose/YPM/issues/4) - Auto-merge機能追加
- [Issue #45](https://github.com/signalcompose/YPM/pull/45) - グローバルエクスポートシステム実装
