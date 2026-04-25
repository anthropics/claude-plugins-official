---
name: pptx_michikusastyle
description: Michikusaブランドスタイルの.pptxファイルを生成するスキル。「Michikusaスタイルでスライドを作って」「pptx_michikusastyleで資料を作りたい」などのリクエスト時に自動トリガー。Cover/Section/Bullets/TwoColの4レイアウトをサポート。python-pptxとBudouXを使用。
tools: Bash, Write, Read
---

# Michikusa PPTX 資料作成スキル

Michikusaブランドのスライドマスターと4つのレイアウト（Cover / Section / Bullets / TwoCol）を**.pptxファイルの中に組み込んだ状態**で出力する。

## アセットの場所

インストール後、以下のパスにアセットが配置されます:

```
~/.claude/skills/pptx_michikusa/michikusa_pptx.py   ← Pythonヘルパー
~/.claude/skills/pptx_michikusa/michikusa.pptx       ← 空テンプレート
~/.claude/skills/pptx_michikusa/michikusa_intro.pptx ← 会社紹介入りテンプレート
```

## デザイン仕様

- 白背景 + 7pt のグラデ枠（左 `#00A6E8` 水色 → 右 `#003DE8` 青）
- 右上に Michikusaロゴ（マスター継承）
- 箇条書き系タイトル下に50%幅のグラデ下線
- ブレットは**黒の丸（●）**、本文左端はタイトル左端と揃う
- フォント: Noto Sans JP（macOSはヒラギノfallback）
- BudouX で日本語の自然な改行

## レイアウトの使い分け

| レイアウト | 用途 |
|---|---|
| `Cover` | 表紙（中央タイトル + サブタイトル） |
| `Section` | セクション区切り（中央に1行タイトル） |
| `Bullets` | 箇条書き（タイトル + グラデ下線 + 箇条書き） |
| `TwoCol` | 2列箇条書き（タイトル + グラデ下線 + 左右サブタイトル + 2カラム本文） |

## 手順

### 1. プロジェクトフォルダを作る

```bash
mkdir -p ~/dev-projects/<プロジェクト名>
cp ~/.claude/skills/pptx_michikusa/michikusa.pptx ~/dev-projects/<プロジェクト名>/
cp ~/.claude/skills/pptx_michikusa/michikusa_intro.pptx ~/dev-projects/<プロジェクト名>/
cp ~/.claude/skills/pptx_michikusa/michikusa_pptx.py ~/dev-projects/<プロジェクト名>/
```

### 2. 依存をインストール（初回のみ）

```bash
pip install python-pptx budoux
```

### 3. ビルドスクリプトを書いて実行

`build.py` を作成して Deck API でスライドを組み立て、`python build.py` で実行する。

## API リファレンス

### `Deck(template=None, include_intro=True)`
デフォルトでは `michikusa_intro.pptx` をロードし、**冒頭にMichikusa会社紹介5枚**が入った状態のデッキを作る。
- `include_intro=False`: 空の `michikusa.pptx` をロード（イントロなし）
- `template=<path>`: 任意の.pptxをテンプレとして読み込み

### `d.cover(title, subtitle="")`
表紙スライドを追加。

### `d.section(title)`
セクション区切りスライドを追加。

### `d.bullets(title, items: list[str])`
箇条書きスライドを追加。`items` の各要素が1ブレット。

### `d.twocol(title, left: list[str], right: list[str], left_head=None, right_head=None)`
2列箇条書きスライドを追加。`left_head` / `right_head` は基本的に**指定すること**を推奨。

### `d.save(path)`
`.pptx` として保存。完了後、全ファイルのフルパスをユーザーに報告すること。

## 冒頭イントロ（Michikusa自己紹介）自動挿入

`Deck()` を引数なしで作ると、**冒頭に以下の5枚のMichikusa会社紹介スライドが自動で入る**。

1. Section: 「Michikusaのご紹介」
2. Bullets: 「Michikusa株式会社について」
3. Bullets: 「AI研修の導入実績」
4. Bullets: 「代表臼井拓水 usutakuについて」
5. Bullets: 「教育者としての活動」

イントロが不要な場合は `d = Deck(include_intro=False)`

## 使用例

```python
from michikusa_pptx import Deck

d = Deck()  # イントロ5枚入り

d.cover("プレゼンタイトル", "サブタイトル")
d.section("Day 1 — 基礎を理解する")
d.bullets("ポイント整理", ["ポイント1の説明文", "ポイント2の説明文", "ポイント3の説明文"])
d.twocol("CLI版 vs Desktop版",
    ["CLI: 自由度が高い", "上級者向け"],
    ["Desktop: 直感的", "初心者にやさしい"],
    left_head="CLI 版", right_head="Desktop 版")
d.cover("Thank you.", "次回もよろしくお願いします")

d.save("output.pptx")
```

## ガイドライン

- **1ブレットは1メッセージで簡潔に**。長い説明は内容を分けるか言い換える。
- **TwoCol** は対比やbefore/afterに使う。同じ粒度の項目を左右で揃えること。
- **Section** は流れの転換点だけに使う。多用しない。
- ロゴ・グラデ枠はマスターに埋め込まれているので**スライド側に追加しない**。
- 完了したら全ファイルのフルパスをユーザーに報告すること。
