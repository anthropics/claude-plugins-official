# `/ypm:open` コマンド仕様書

**作成日**: 2025-10-21
**最終更新**: 2025-10-21
**ステータス**: Implemented
**対応Issue**: N/A

---

## 1. 概要

YPMで管理している複数プロジェクトの中から、指定したプロジェクトをVS Codeで開くスラッシュコマンド。

### 目的

- プロジェクト切り替えを高速化
- PROJECT_STATUS.mdから直接プロジェクトを開けるようにする
- CLI操作なしでYPM内で完結させる
- 記憶に頼らず、常に全プロジェクトを確認できる（番号選択方式）
- 休止中プロジェクトをignoreで非表示化し、必要時に表示できる

### 対象ユーザー

- YPMを使ってプロジェクトを管理している全ての開発者

---

## 2. 機能要件

### 2.1 サブコマンド構成

#### F1: 通常モード（引数なし）

**使用例**:
```
/ypm:open
```

**動作**:
1. PROJECT_STATUS.mdとconfig.ymlを読み込み
2. Git worktreeを除外
3. config.ymlの`ignore_in_open`に含まれるプロジェクトを除外
4. カテゴリ別（アクティブ/開発中/休止中）に番号付き一覧を表示
5. ユーザーが番号またはプロジェクト名（部分一致）で選択
6. `code <プロジェクトパス>` で新しいウィンドウで開く

#### F2: 全表示モード（`all`）

**使用例**:
```
/ypm:open all
```

**動作**:
- Git worktreeのみ除外
- **ignore_in_openは除外しない**（これが通常モードとの違い）
- その他は通常モードと同じ

#### F3: ignore一覧表示（`ignore-list`）

**使用例**:
```
/ypm:open ignore-list
```

**動作**:
- config.ymlの`monitor.ignore_in_open`リストを表示
- 追加・削除方法を案内

#### F4: ignore追加（`add-ignore`）

**使用例**:
```
/ypm:open add-ignore
```

**動作**:
1. 通常モードと同じプロジェクト一覧を表示
2. ユーザーが選択
3. config.ymlの`monitor.ignore_in_open`に追加
4. 次回から通常モードで非表示

#### F5: ignore削除（`remove-ignore`）

**使用例**:
```
/ypm:open remove-ignore
```

**動作**:
1. ignore_in_openリストを番号付きで表示
2. ユーザーが選択
3. config.ymlから削除
4. 次回から通常モードで表示

### 2.2 Git worktreeの自動除外

**理由**:
- worktreeプロジェクト（例: `MaxMCP-main`, `redmine-mcp-server-main`）は通常、main/developブランチの確認用
- 実際の開発は親プロジェクト（例: `MaxMCP`, `redmine-mcp-server`）で行う
- 選択肢を減らしてユーザビリティを向上

**除外対象**:
- `.git`が**ファイル**であるプロジェクト（worktree）
- `.git`が**ディレクトリ**であるプロジェクトは通常のリポジトリとして表示

**検出方法**:
- `scripts/scan_projects.py`の`is_worktree()`関数
- Python Pathlibの`.is_file()`で判定
- 100%正確で、命名規則に依存しない

### 2.3 エラーハンドリング

#### E1: プロジェクトが見つからない（番号・名前入力時）

**入力**:
```
999
```
または
```
NonExistentProject
```

**出力**:
```
❌ プロジェクト "NonExistentProject" が見つかりませんでした。

正確なプロジェクト名または番号を指定してください。
```

#### E2: 複数のプロジェクトがマッチ（部分一致）

**入力**:
```
Max
```

**出力**:
```
複数のプロジェクトがマッチしました：

1. MaxMCP
2. MaxMSP-MCP-Server-multipatch

番号を入力してください:
```

**動作**:
- 完全一致があればそれを優先
- なければ選択肢を表示
- ユーザーが番号で再選択

#### E3: VS Code CLIが利用できない

**検出方法**:
```bash
which code
```

**出力**:
```
❌ VS Code CLI (code) が見つかりません。

VS Code CLIをインストールしてください：
1. VS Codeを開く
2. Command Palette (Cmd+Shift+P)
3. "Shell Command: Install 'code' command in PATH" を実行
```

#### E4: PROJECT_STATUS.mdが存在しない

**出力**:
```
❌ PROJECT_STATUS.md が見つかりません。

先に /ypm:update を実行してプロジェクトをスキャンしてください。
```

---

## 3. 非機能要件

### 3.1 パフォーマンス

- PROJECT_STATUS.mdの読み込み: 1秒以内
- VS Codeの起動: システム依存（YPMの責任外）

### 3.2 ユーザビリティ

- エラーメッセージは分かりやすく、解決策を含める
- プロジェクト一覧は見やすくフォーマット

### 3.3 保守性

- PROJECT_STATUS.mdのフォーマットに依存（マークダウンパース）
- フォーマット変更時に影響を受ける可能性あり

---

## 4. 技術仕様

### 4.1 使用ツール

- **Bashツール**: `code <path>` コマンド実行、`which code`でCLI確認
- **Readツール**: PROJECT_STATUS.md、config.yml読み込み
- **Writeツール**: config.yml更新（ignore追加・削除時）
- **Bash出力**: ユーザー入力受付（番号またはプロジェクト名）

### 4.2 プロジェクト情報抽出ロジック

#### ステップ1: スキャン結果から取得

**`scripts/scan_projects.py`の実行結果**:
```json
{
  "projects": [
    {
      "name": "MaxMCP",
      "path": "~/Projects/my-project",
      "branch": "feature/35-maxmcp-server-implementation",
      "last_commit": "2 days ago|feat(server): implement MCP tools...",
      "changed_files": 0,
      "category": "active",
      "is_worktree": false,
      "docs": {...}
    }
  ],
  "summary": {...}
}
```

#### ステップ2: Git worktreeを除外

```python
# 疑似コード（実際はスキャンスクリプトで判定済み）
def is_worktree(project_path):
    git_path = Path(project_path) / ".git"
    return git_path.is_file()  # ファイル → worktree
```

#### ステップ3: ignore_in_openによる除外（通常モードのみ）

```python
# config.ymlから読み込み
ignore_list = config['monitor']['ignore_in_open']

# 除外
filtered_projects = [
    p for p in projects
    if not p['is_worktree'] and p['name'] not in ignore_list
]
```

#### ステップ4: プロジェクトパス解決

```python
# スキャン結果にパスが含まれているので、直接使用
project_path = selected_project['path']
```

### 4.3 VS Code起動コマンド

```bash
# 新しいウィンドウで開く（デフォルト）
code /path/to/project

# 将来的な拡張: 既存ウィンドウに追加
# code -a /path/to/project
```

---

## 5. 実装例

### 5.1 スラッシュコマンドファイル (.claude/commands/ypm:open.md)

実装済み。詳細は`.claude/commands/ypm:open.md`を参照。

**主な構成**:
- サブコマンド説明（引数なし/all/ignore-list/add-ignore/remove-ignore）
- 5つのモード別実行手順
- STEP単位での詳細フロー
- エラーハンドリング
- worktree除外ロジック
- config.yml保存手順

---

## 6. テスト仕様

### 6.1 正常系テスト

| テストケース | 入力 | 期待する動作 |
|------------|------|------------|
| TC1: 通常モード | `/ypm:open` → `1` | 番号選択でプロジェクトが開く |
| TC2: 名前検索（一意） | `/ypm:open` → `Slack` | 部分一致で Slack_MCPプロジェクトが開く |
| TC3: 全表示モード | `/ypm:open all` | ignore含む全プロジェクトが表示される |
| TC4: worktree除外 | `/ypm:open` | MaxMCP-main等が選択肢に含まれない |
| TC5: ignore一覧 | `/ypm:open ignore-list` | ignore_in_openリストが表示される |
| TC6: ignore追加 | `/ypm:open add-ignore` → `1` | config.ymlに追加される |
| TC7: ignore削除 | `/ypm:open remove-ignore` → `1` | config.ymlから削除される |

### 6.2 異常系テスト

| テストケース | 入力 | 期待する動作 |
|------------|------|------------|
| TC8: 存在しない番号 | `/ypm:open` → `999` | エラーメッセージ表示 |
| TC9: 存在しないプロジェクト | `/ypm:open` → `NoSuchProject` | エラーメッセージ表示 |
| TC10: 複数マッチ | `/ypm:open` → `Max` | 選択肢が表示され、再度番号入力 |
| TC11: VS Code CLIなし | `/ypm:open` (codeコマンドなし) | インストール手順を表示 |
| TC12: PROJECT_STATUS.md不在 | `/ypm:open` | `/ypm:update` 実行を促す |
| TC13: config.yml不在 | `/ypm:open` | エラーメッセージ表示 |

---

## 7. 実装上の注意事項

### 7.1 config.ymlの保存

**ignore追加・削除時**:
- Writeツールを使用してconfig.ymlを完全に書き換える
- YAML構造を保持する（コメント含む）
- 既存の設定を破壊しない

### 7.2 worktree判定の信頼性

**`.git`ファイル/ディレクトリ判定**:
- 100%正確で命名規則に依存しない
- `scripts/scan_projects.py`で判定済み
- PROJECT_STATUS.mdには反映されていないため、再スキャン推奨

### 7.3 ユーザー入力処理

**番号入力とプロジェクト名入力**:
- 番号: `1`, `2`, ...
- プロジェクト名: 大文字小文字を区別せず部分一致
- 完全一致を優先
- 複数マッチ時は選択肢を再表示

---

## 8. 将来の拡張案

### 8.1 オプション追加

- `-a`, `--add`: 既存ウィンドウに追加（`code -a`）
- `-r`, `--reuse`: 既存ウィンドウを再利用（`code -r`）

### 8.2 エディタ切り替え

- VS Code以外のエディタもサポート（環境変数で設定）
- 例: `EDITOR=cursor`, `EDITOR=subl`

### 8.3 統計情報

- よく開くプロジェクトを記録し、選択肢の順序を最適化

---

## 9. 関連ドキュメント

- **[CLAUDE.md](../../CLAUDE.md)** - YPMの主要機能
- **[PROJECT_STATUS.md](../../PROJECT_STATUS.md)** - プロジェクト状況一覧
- **[config.yml](../../config.yml)** - YPM設定ファイル
- **[scripts/scan_projects.py](../../scripts/scan_projects.py)** - プロジェクトスキャンスクリプト
- **[.claude/commands/ypm:open.md](../../.claude/commands/ypm:open.md)** - `/ypm:open`コマンド実装

---

## 10. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-10-21 | 1.0 | 初版作成（Draft） |
| 2025-10-21 | 2.0 | 最終実装に合わせて更新（Implemented） |

**主な変更点（v2.0）**:
- 引数システムの削除（常に番号選択方式）
- ignore機能の追加（5つのサブコマンド）
- worktree検出方法の変更（`.git`ファイル/ディレクトリ判定）
- スキャンスクリプトとの統合
- テスト仕様の更新

---

**この仕様書は、DDD原則に基づいて作成されました。実装前に必ずレビューしてください。**
