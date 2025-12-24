# YPM 詳細ガイド（日本語）

> **Note**: This document is deprecated. Please refer to [guide-en.md](./guide-en.md) as the primary documentation.
> YPM now supports language settings in `~/.ypm/config.yml`. Set `settings.language: ja` for Japanese output - Claude will translate dynamically.

> **注意**: このドキュメントは非推奨です。最新のドキュメントは [guide-en.md](./guide-en.md) を参照してください。
> YPMは `~/.ypm/config.yml` で言語設定をサポートしています。`settings.language: ja` を設定すると、Claude が日本語に翻訳して出力します。

---

> YPM (Your Project Manager) の完全な使い方ガイド

---

## 目次

- [概要](#概要)
- [特徴](#特徴)
- [前提条件](#前提条件)
- [インストール](#インストール)
- [セットアップ](#セットアップ)
- [使い方](#使い方)
- [カスタマイズ](#カスタマイズ)
- [よくある質問](#よくある質問)
- [今後の拡張予定](#今後の拡張予定)

---

## 概要

YPMは、ユーザーが指定したディレクトリ配下の複数プロジェクトの進行状況を自動的に収集・整理し、一覧表示するツールです。

**誰のためのツール？**
- 複数のプロジェクトを同時並行で進めているエンジニア・クリエイター
- 本業以外にもサイドプロジェクトを持つ人
- チームで複数プロジェクトを管理するマネージャー

### こんな課題を解決します

- ✅ プロジェクトが増えすぎて、どれが進行中かわからない
- ✅ 本業以外のプロジェクトの状況を覚えておくのが大変
- ✅ 次に何をすべきか確認するのに時間がかかる
- ✅ 進捗率や優先順位を把握しにくい

---

## 特徴

- **自動収集**: Git履歴とドキュメントから情報を自動収集
- **一元管理**: すべてのプロジェクトを1つのファイルで管理
- **Claude Code連携**: Claude Codeを使って簡単に更新
- **進捗可視化**: 各プロジェクトの進捗率を表示
- **次のタスク明示**: 各プロジェクトで次にやるべきことを表示
- **柔軟な設定**: `config.yml`で監視対象を自由にカスタマイズ

---

## 前提条件

- **Claude Code**: YPM実行に必要
  - [Claude Codeダウンロード](https://claude.ai/download)
- **Git**: プロジェクト情報の収集に使用
- **Python 3.8+**: プロジェクトスキャン用（プラグインに含まれています）

---

## インストール

YPMはClaude Codeプラグインとしてインストールされ、**どのディレクトリからでも**アクセスできます。

### ステップ1: プラグインをインストール

```bash
# Claude Code内で、まずマーケットプレースを追加:
/plugin marketplace add signalcompose/ypm

# 次にプラグインをインストール:
/plugin install ypm
```

### ステップ2: 初期設定

```bash
# セットアップウィザードを実行（どのディレクトリからでもOK）
/ypm:setup
```

セットアップウィザードが以下の情報を対話的に収集します：
1. 監視したいプロジェクトディレクトリのパス
2. プロジェクト検出パターン
3. アクティブ/休止中の分類基準日数

完了すると、`~/.ypm/config.yml`が自動生成されます。

### ステップ3: 初回スキャン

```bash
# プロジェクトをスキャン
/ypm:update
```

これで `~/.ypm/PROJECT_STATUS.md` が生成され、すべてのプロジェクト情報が収集されます。

### データの保存場所

YPMはすべてのユーザーデータを `~/.ypm/` に保存します：

```
~/.ypm/
  ├── config.yml           # 監視設定
  └── PROJECT_STATUS.md    # 生成されたプロジェクト状況
```

この分離により：
- プラグインの更新があなたの設定に影響しない
- バックアップが簡単（`~/.ypm/` をバックアップするだけ）
- すべてのプロジェクトで動作

---

## 使い方

### 1. プロジェクト状況の確認

```bash
# ステータスファイルを直接確認
cat ~/.ypm/PROJECT_STATUS.md

# またはコマンドを使用
/ypm:active
```

すべてのプロジェクトの状況が一覧で確認できます。

### 2. 状況の更新

```bash
# Claude Codeでどのディレクトリからでも実行可能
/ypm:update
```

自動的に以下が実行されます：
1. `~/.ypm/config.yml`で指定したディレクトリをスキャン
2. 各プロジェクトのGit情報を取得
3. ドキュメント（CLAUDE.md、README.md、docs/INDEX.md）を読み込み
4. `~/.ypm/PROJECT_STATUS.md`を更新

### 3. 次のタスク確認

```bash
/ypm:next
```

各プロジェクトの次のタスクを優先度順に表示します。

---

## 利用可能なコマンド

YPMは以下のコマンドを提供します。すべてのコマンドは `ypm:` プレフィックス付きです。

| コマンド | 説明 |
|---------|------|
| `/ypm:setup` | 初期設定ウィザード |
| `/ypm:start` | ウェルカムメッセージ表示 |
| `/ypm:help` | 詳細ヘルプ表示 |
| `/ypm:update` | プロジェクト状況更新 |
| `/ypm:next` | 次のタスク表示 |
| `/ypm:active` | アクティブプロジェクト表示 |
| `/ypm:open` | エディタでプロジェクトを開く |
| `/ypm:new` | 新規プロジェクトウィザード |
| `/ypm:setup-gitflow` | Git Flowワークフロー設定 |
| `/ypm:export-community` | コミュニティ版へエクスポート |
| `/ypm:trufflehog-scan` | TruffleHogセキュリティスキャン |

### プロジェクト管理コマンド

#### `/ypm:start`
ウェルカムメッセージとよく使うコマンド一覧を表示します。セッション開始時に便利です。

#### `/ypm:help`
全コマンドの詳細なヘルプを表示します。各コマンドの説明、YPMの原則、よくある使い方が確認できます。

#### `/ypm:update`
全プロジェクトをスキャンして `~/.ypm/PROJECT_STATUS.md` を更新します。

**実行内容**:
1. `~/.ypm/config.yml` で指定された監視対象ディレクトリをスキャン
2. 各プロジェクトのGit情報を取得（ブランチ、最終コミット、変更ファイル数）
3. 各プロジェクトの `CLAUDE.md`、`README.md`、`docs/INDEX.md` を読み込み
4. プロジェクトの進捗情報（Phase、実装進捗、テスト、ドキュメント）を収集
5. `~/.ypm/PROJECT_STATUS.md` を更新

**注意**: 他のプロジェクトのファイルは読み取り専用です（変更禁止）

#### `/ypm:next`
各プロジェクトの「次のタスク」を優先度順に表示します。

**表示内容**:
- プロジェクト名
- 現在のPhase
- 次のタスク
- 最終更新日

**優先順位**:
1. アクティブなプロジェクト（最近1週間以内に更新）
2. 実装進捗が高いプロジェクト
3. Phase順

#### `/ypm:active`
最近1週間以内に更新されたアクティブなプロジェクトのみを表示します。

**表示内容**:
- プロジェクト名、概要、ブランチ
- 最終更新日、Phase、実装進捗
- 次のタスク

更新日時の降順（新しい順）で表示されます。

#### `/ypm:open [プロジェクト名] [エディタ] [オプション]`
選択したエディタでプロジェクトを開きます。環境変数を自動的にクリアします。

**基本的な使い方**:
- `/ypm:open` - プロジェクト一覧を表示（ignore除外、worktreeは自動除外）
- `/ypm:open oshireq` - "oshireq"プロジェクトをデフォルトエディタで開く
- `/ypm:open oshireq cursor` - "oshireq"プロジェクトをCursorで開く

**対応エディタ**:
- `code` - VS Code
- `cursor` - Cursor
- `zed` - Zed
- `terminal` - Terminal.app

**エディタ設定**:
- `/ypm:open --editor` - 現在のデフォルトエディタを表示
- `/ypm:open --editor cursor` - デフォルトエディタをCursorに設定
- `/ypm:open --editor zed` - デフォルトエディタをZedに設定

**Ignore管理**:
- `/ypm:open all` - ignore設定済みを含む全プロジェクトを表示
- `/ypm:open ignore-list` - ignore設定済みプロジェクト一覧
- `/ypm:open add-ignore` - プロジェクトをignoreに追加
- `/ypm:open remove-ignore` - プロジェクトをignoreから削除

**機能**:
- **環境変数クリア**: エディタ起動前に`NODENV_VERSION`、`NODENV_DIR`、`RBENV_VERSION`、`PYENV_VERSION`を自動的にクリアし、各プロジェクトのバージョンファイル（`.node-version`等）が正しく読み込まれるようにします
- **Worktree自動除外**: Git worktreeディレクトリ（例: `MaxMCP-main`、`InstrVo-develop`）は選択肢から自動的に除外されます
- **柔軟なエディタ選択**: プロジェクトのニーズや個人の好みに応じてエディタを切り替え可能

**設定**:
デフォルトエディタは`~/.ypm/config.yml`で設定：
```yaml
editor:
  default: code  # 選択肢: code, cursor, zed, terminal
```

詳細な仕様は [ypm-open-spec.md](development/ypm-open-spec.md) を参照してください。

### 新規プロジェクト立ち上げコマンド

#### `/ypm:new`
新規プロジェクトの立ち上げを支援する対話型ウィザードを起動します。

8つのフェーズで段階的にプロジェクトをセットアップ：
1. **プロジェクト企画**: 要件定義、技術選定
2. **ディレクトリ作成**: ローカルディレクトリ作成とGit初期化
3. **ドキュメント整備**: DDD・TDD・DRY原則に基づく開発環境構築
4. **GitHub連携**: リモートリポジトリ作成と初期プッシュ
5. **Git Workflow設定**: ブランチ戦略とルール確立
6. **環境設定ファイル整備**: `.gitignore`、`.claude/settings.json`
7. **ドキュメント管理ルール確立**: 実装とドキュメントの同期維持
8. **最終確認**: 開発開始の準備完了

**セットアップ完了後**:
- 新しいプロジェクトディレクトリに移動
- そのプロジェクト専用のClaude Codeセッションで開発を開始
- YPMは次回の `/ypm:update` で自動的に監視対象に追加

詳細は [project-bootstrap-prompt.md](../project-bootstrap-prompt.md) を参照してください。

### Git Workflowコマンド

#### `/ypm:setup-gitflow`
現在のプロジェクトにGit Flowワークフローを設定します。ブランチ保護とセキュリティ設定を含みます。

**実行内容**:
- `main`（デフォルト）と`develop`ブランチを作成
- ブランチ保護を設定（main/developへの直プッシュ禁止）
- Squash/Rebaseマージを無効化（マージコミットのみ許可）
- プロジェクトタイプに応じたセキュリティ設定（CODEOWNERS、Secret Scanning）

**プロジェクトタイプ**:
1. **個人プロジェクト** - 最小限の設定、一人開発
2. **小規模OSS** - CODEOWNERS、ブランチ保護推奨
3. **大規模OSS** - 全セキュリティ設定を有効化

**使い方**:
```bash
/ypm:setup-gitflow
```

コマンドはプロジェクトタイプと開発スタイルについて対話的に質問し、適切な設定を構成します。

### セキュリティ＆エクスポートコマンド

#### `/ypm:export-community`
プライベートリポジトリをパブリックコミュニティ版にエクスポートします。
- 初回実行時は対話型セットアップ
- 2回目以降は自動エクスポート
- TruffleHogセキュリティスキャン統合

#### `/ypm:trufflehog-scan`
管理対象の全プロジェクトでTruffleHogセキュリティスキャンを実行します。
- TruffleHogのインストールが必要（`brew install trufflehog`）
- Git履歴全体をスキャンして秘密情報を検出

---

## プロジェクト立ち上げアシスタント

YPMには新規プロジェクトを立ち上げるための包括的なアシスタント機能があります。

### 使い方

2つの方法があります：

**方法1: カスタムコマンドを使用（推奨）**

Claude Code内で以下を実行：
```
/ypm:new
```

**方法2: プロンプトを手動で使用**

1. `project-bootstrap-prompt.md` の内容をコピー
2. Claude Codeに貼り付け
3. 対話形式で8つのフェーズを進める

### 特徴

- **要件定義からセットアップまで一貫サポート**
  - プロジェクト企画のヒアリング
  - 要件定義書・仕様書の作成
  - 適切なディレクトリ構造の構築

- **開発ベストプラクティスの導入**
  - DDD（ドメイン駆動設計）
  - TDD（テスト駆動開発）
  - DRY（Don't Repeat Yourself）原則

- **Git Workflowの設定**
  - Git Flow対応
  - Git Worktree対応（オプション）
  - ブランチ保護ルール

- **ドキュメント管理ルール**
  - 実装とドキュメントの同期維持
  - オンボーディング支援
  - PRテンプレートとチェックリスト

### 導入される開発原則

#### DDD（ドメイン駆動設計）
- レイヤー構造の定義（Domain, Application, Infrastructure, Presentation）
- ディレクトリ構成のガイドライン作成

#### TDD（テスト駆動開発）
- Red → Green → Refactor サイクルの遵守
- 実装前にテストを書く文化
- テストカバレッジの目標設定

#### DRY（Don't Repeat Yourself）
- コードの重複を避ける
- 共通ロジックの抽出
- 再利用可能なコンポーネント設計

### 生成されるドキュメント

プロジェクトセットアップ時に以下のドキュメントが作成されます：

- `README.md` - プロジェクト概要、セットアップ手順
- `docs/requirements.md` - 要件定義書
- `docs/specifications.md` - システム仕様書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/development-guide.md` - 開発ガイドライン
- `docs/onboarding.md` - 新メンバー向けオンボーディングガイド
- `.claude/settings.json` - Claude Code権限設定
- `.gitignore` - Git除外設定

---

## ファイル構成

### プラグインファイル（`/install`でインストール）

```
~/.claude/plugins/ypm/          # プラグインインストールディレクトリ
├── commands/                   # スラッシュコマンド
│   ├── start.md
│   ├── help.md
│   ├── setup.md
│   ├── update.md
│   ├── next.md
│   ├── active.md
│   ├── open.md
│   ├── new.md
│   ├── setup-gitflow.md
│   ├── export-community.md
│   └── trufflehog-scan.md
├── scripts/
│   └── scan_projects.py        # プロジェクトスキャンスクリプト
└── ...
```

### ユーザーデータ（`/ypm:setup`で作成）

```
~/.ypm/
├── config.yml                  # 監視設定
└── PROJECT_STATUS.md           # 生成されたプロジェクト状況
```

---

## プロジェクトのカテゴリ

### 🔥 アクティブプロジェクト
最近1週間以内に更新があったプロジェクト。現在進行中。

### 🎨 設計・計画段階
Phase 0やドキュメント策定中のプロジェクト。実装前。

### 🚧 開発中
実装が進行中だが、最近の更新が1週間以上前のプロジェクト。

### 💤 休止中
1ヶ月以上更新がないプロジェクト。一時停止中。

### 📦 Git非管理
Gitリポジトリでないディレクトリ。進捗追跡対象外。

---

## 進捗率の算出基準

YPMは以下の基準でプロジェクトの進捗率を推測します：

| 進捗 | フェーズ | 状態 |
|------|---------|------|
| 0-20% | Phase 0 | 設計・計画段階 |
| 20-30% | Phase 1 | 開発環境構築 |
| 30-60% | Phase 2-3 | 基本機能実装 |
| 60-80% | Phase 4-5 | テスト・改善 |
| 80-100% | Phase 6+ | 本番稼働・機能拡張 |

**注意**: あくまで推測値です。実態と異なる場合は手動で調整してください。

---

## カスタマイズ

`~/.ypm/config.yml` を編集してYPMの動作をカスタマイズできます。

### 監視対象の追加

`~/.ypm/config.yml`の`directories`に追加：

```yaml
monitor:
  directories:
    - ~/Projects
    - ~/Work      # 追加
    - ~/Documents/code  # 追加
```

### プロジェクト検出パターンの変更

異なるディレクトリ構造に対応する場合：

```yaml
monitor:
  patterns:
    - "proj_*/*"          # 2階層構造
    - "projects/*"        # 1階層構造
    - "my-apps/*/src"     # 3階層構造
```

### デフォルトエディタの変更

お好みのエディタを`~/.ypm/config.yml`で設定：

```yaml
editor:
  default: cursor    # codeからcursorに変更
  # 選択肢: code (VS Code), cursor (Cursor), zed (Zed), terminal (Terminal.app)
```

またはコマンドで設定：
```
/ypm:open --editor cursor
```

### 分類基準の変更

アクティブ/休止の判定日数を変更：

```yaml
classification:
  active_days: 14    # 2週間以内をアクティブに変更
  inactive_days: 60  # 2ヶ月以上を休止に変更
```

---

## 更新頻度

- **推奨**: 週に1回程度
- **最低**: 月に1回

定期的に更新することで、プロジェクトの状況を常に把握できます。

---

## よくある質問

### Q: 新しいプロジェクトを追加したい

**A**: `~/.ypm/config.yml`で指定したディレクトリ配下にプロジェクトを作成すれば、次回 `/ypm:update` 時に自動的に検出されます。

### Q: プロジェクトを除外したい

**A**: `~/.ypm/config.yml`の`exclude`に追加してください：

```yaml
monitor:
  exclude:
    - proj_YPM/YPM
    - old_projects/*   # 除外したいパターン
```

### Q: 進捗率が不正確

**A**: `~/.ypm/PROJECT_STATUS.md`を直接編集して調整してください。

### Q: 次のタスクが表示されない

**A**: 該当プロジェクトの`CLAUDE.md`や`docs/`に開発計画を記載してください。YPMはそれを読み取って表示します。

### Q: 別のマシンで使いたい

**A**: `/plugin marketplace add signalcompose/ypm` でマーケットプレースを追加し、`/plugin install ypm` でYPMをインストールしてから、`/ypm:setup` で環境を設定してください。`~/.ypm/config.yml` を新しいマシンにコピーすることもできます。

---

## 今後の拡張予定

YPMは現在**Phase 1完成状態**です。Claude Code駆動のアプローチが実運用で有効性を発揮しています。

将来的に検討可能な拡張：

- [ ] プロジェクト作成支援ツール
- [ ] ダッシュボードUI（Webベース）
- [ ] Slack通知連携
- [ ] 優先度の自動算出
- [ ] ガントチャート生成
- [ ] プロジェクト間の依存関係可視化

**Note**: 自動更新スクリプト（cron対応）については、AIによる文脈理解と柔軟なタスク抽出の方が優れているため、現時点では優先度を下げています。

---

## トラブルシューティング

### Q: プロジェクトが検出されない

**A**: 以下を確認：
1. Gitリポジトリか？（`.git/`ディレクトリがあるか）
2. `~/.ypm/config.yml` のパターンとディレクトリ構造が一致するか？
3. 除外対象に含まれていないか？

### Q: "config.yml not found" エラー

**A**: `/ypm:setup` を実行して `~/.ypm/config.yml` に初期設定ファイルを作成してください。

---

## 貢献方法

YPMへの貢献を歓迎します！

### バグ報告・機能要望

- [GitHub Issues](https://github.com/signalcompose/YPM/issues)でお知らせください

### プルリクエスト

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'feat: Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### 開発ガイドライン

詳細は `CONTRIBUTING.md`（作成予定）を参照してください。

---

## ライセンス

このプロジェクトは [MIT License](../LICENSE) のもとで公開されています。

---

## 作成者

**Hiroshi Yamato / dropcontrol**

- Website: [hiroshiyamato.com](https://hiroshiyamato.com/) | [yamato.dev](https://yamato.dev/)
- X: [@yamato](https://x.com/yamato)
- GitHub: [dropcontrol](https://github.com/dropcontrol)

Powered by Claude Code

---

## 関連ドキュメント

- **[README.md](../README.md)** - プロジェクト概要（英語）
- **[Detailed Guide (English)](guide-en.md)** - 英語詳細ガイド
- **[CLAUDE.md](../CLAUDE.md)** - Claude Code向け指示書
- **[docs/INDEX.md](INDEX.md)** - ドキュメント索引

---

**あなたのプロジェクトを、もっと管理しやすく。** 🚀
