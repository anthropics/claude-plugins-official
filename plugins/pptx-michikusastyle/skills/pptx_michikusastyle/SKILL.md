---
name: pptx_michikusastyle
description: MichikusaブランドのPPTX資料を作成するスキル。「PPTX作って」「パワポ作って」「資料を作って（PPTX）」「プレゼン資料」などで発動。スライドマスター＋4レイアウト（Cover/Section/Bullets/TwoCol）が組み込まれた.pptxを生成する。Marp版が欲しい場合はmarpスキルを使う。
user-invocable: true
---

# Michikusa PPTX 資料作成スキル

Michikusaブランドのスライドマスターと4つのレイアウト（Cover / Section / Bullets / TwoCol）を**.pptxファイルの中に組み込んだ状態**で出力する。納品先がPowerPointを編集するときに「新しいスライド」から4レイアウトを選べる。

## デザイン仕様

- 白背景 + 7pt のグラデ枠（左 `#00A6E8` 水色 → 右 `#003DE8` 青）
- 右上に Michikusaロゴ（マスター継承）
- 箇条書き系タイトル下に50%幅のグラデ下線
- ブレットは**黒の丸（●）**、本文左端はタイトル左端と揃う
- フォント: Noto Sans JP（macOSはヒラギノfallback）
- BudouX で日本語の自然な改行
- カラーパレット:
  | 用途 | カラー |
  |---|---|
  | 背景（白） | `#FFFFFF` |
  | テキスト（黒） | `#221F1F` |
  | アクセント（青） | `#003DE8` |
  | サブアクセント（水色） | `#00A6E8` |
  | サブテキスト（グレー） | `#666666` |

## レイアウトの使い分け

| レイアウト | 用途 |
|---|---|
| `Cover` | 表紙（中央タイトル + サブタイトル） |
| `Section` | セクション区切り（中央に1行タイトル） |
| `Bullets` | 箇条書き（タイトル + グラデ下線 + 箇条書き） |
| `TwoCol` | 2列箇条書き（タイトル + グラデ下線 + 左右サブタイトル + 2カラム本文） |

### レイアウト内のプレースホルダー構成

- **Cover / Section**: タイトル (idx=0) + サブタイトル (idx=1)
- **Bullets**: タイトル (idx=0) + 本文 (idx=1)
  - タイトルは上部 (top=0.3") に寄り、下線はタイトル直下 (top=1.17")、本文は top=1.5" から開始
- **TwoCol**: タイトル (idx=0) + 左サブタイトル (idx=10) + 左本文 (idx=1) + 右サブタイトル (idx=11) + 右本文 (idx=2)
  - PowerPointで「新しいスライド」から挿入したとき、**5つのプレースホルダー枠**が表示される
  - サブタイトル枠は 28pt 太字・ブレットなし、本文枠は 19pt 黒丸ブレット
  - 左右のサブタイトルは top=1.75" / h=0.6"、本文は top=2.4" / h=4.3"（サブタイトルと本文は隣接して一体に見える）

## 冒頭イントロ（Michikusa自己紹介）自動挿入

`Deck()` を引数なしで作ると、**冒頭に以下の5枚のMichikusa会社紹介スライドが自動で入る**（`michikusa_intro.pptx` をベーステンプレとしてロード）。ユーザーが `d.cover()` / `d.bullets()` などで追加するスライドはこの5枚の **後ろに** 積まれる。

1. Section: 「Michikusaのご紹介」
2. Bullets: 「Michikusa株式会社について」
3. Bullets: 「AI研修の導入実績」
4. Bullets: 「代表臼井拓水 usutakuについて」
5. Bullets: 「教育者としての活動」

イントロが不要な場合（社内メモ・練習スライド等）は明示的に外す:

```python
d = Deck(include_intro=False)
```

## 同梱ファイル（スキルディレクトリ）

スキルのファイルは以下の場所にある:

```
~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pptx-michikusastyle/skills/pptx_michikusastyle/
├── michikusa.pptx          — 空テンプレート（include_intro=False 時に使用）
├── michikusa_intro.pptx    — 冒頭5枚の会社紹介スライド入りテンプレート（デフォルト）
└── michikusa_pptx.py       — スライド生成用の Python ヘルパー（Deck クラス）
```

## 手順

### 1. プロジェクトフォルダを作る

`~/dev-projects/<プロジェクト名>/` を作成し、以下をコピー:

```bash
SKILL_DIR="$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/pptx-michikusastyle/skills/pptx_michikusastyle"
mkdir -p ~/dev-projects/<プロジェクト名>
cp "$SKILL_DIR/michikusa.pptx" ~/dev-projects/<プロジェクト名>/
cp "$SKILL_DIR/michikusa_intro.pptx" ~/dev-projects/<プロジェクト名>/
cp "$SKILL_DIR/michikusa_pptx.py" ~/dev-projects/<プロジェクト名>/
```

### 2. 依存をインストール（初回のみ）

```bash
pip3 install python-pptx budoux --break-system-packages
```

### 3. ビルドスクリプトを書く

`build.py` を作成し、以下のように `Deck` を使ってスライドを組み立てる:

```python
from michikusa_pptx import Deck

d = Deck()  # michikusa_intro.pptx を自動ロード

# 表紙
d.cover("プレゼンタイトル", "サブタイトル")

# 目次（2列）
d.twocol("本日のアジェンダ",
    ["1. はじめに", "2. 本論", "3. 事例"],
    ["4. デモ", "5. まとめ"],
    left_head="前半", right_head="後半")

# セクション区切り
d.section("Day 1 — 基礎を理解する")

# 箇条書き
d.bullets("ポイント整理",
    ["ポイント1の説明文",
     "ポイント2の説明文",
     "ポイント3の説明文"])

# 2列の対比
d.twocol("CLI版 vs Desktop版",
    ["CLI: 自由度が高い", "上級者向け"],
    ["Desktop: 直感的", "初心者にやさしい"],
    left_head="CLI 版", right_head="Desktop 版")

# 終わり
d.cover("Thank you.", "次回もよろしくお願いします")

d.save("output.pptx")
```

### 4. 実行

```bash
cd ~/dev-projects/<プロジェクト名>
python3 build.py
```

### 5. （任意）PDF・プレビュー化

PowerPointで開いて確認、または:

```bash
# 重要: 既に同じファイルを開いていると古い内容のままPDFが出る。必ず一度閉じてから開き直す。
osascript -e 'tell application "Microsoft PowerPoint" to close every presentation saving no' 2>/dev/null
osascript -e 'tell application "Microsoft PowerPoint" to activate' \
          -e 'tell application "Microsoft PowerPoint" to open POSIX file "/path/to/output.pptx"'
sleep 5
osascript -e 'tell application "Microsoft PowerPoint" to save active presentation in (POSIX file "/path/to/output.pdf") as save as PDF'
```

## API リファレンス

### `Deck(template=None, include_intro=True)`
デフォルトでは `michikusa_intro.pptx` をロードし、**冒頭にMichikusa会社紹介5枚**が入った状態のデッキを作る。以降 `d.cover()` / `d.bullets()` などで追加するスライドはこの5枚の後ろに積まれる。
- `include_intro=False`: 空の `michikusa.pptx` をロード（イントロなし）
- `template=<path>`: 任意の.pptxをテンプレとして読み込み（全スライド削除）

### `d.cover(title, subtitle="")`
表紙スライドを追加。

### `d.section(title)`
セクション区切りスライドを追加。

### `d.bullets(title, items: list[str])`
箇条書きスライドを追加。`items` の各要素が1ブレット。

### `d.twocol(title, left: list[str], right: list[str], left_head=None, right_head=None)`
2列箇条書きスライドを追加。`left_head` / `right_head` を指定すると、**専用のサブタイトルプレースホルダー**(idx=10 左, idx=11 右) に入る（本文より大きく・タイトルより少し小さい・ブレットなし）。
TwoColスライドはそもそも「サブタイトル別の対比」だから、`left_head`/`right_head` は基本的に**指定すること**を推奨。サブタイトルのフォントサイズは `michikusa_pptx.TWOCOL_HEAD_PT`（デフォルト 28pt）で調整可能。

**PowerPointで手動編集する場合**: 「新しいスライド > TwoCol」を選ぶと5つのプレースホルダー（タイトル / 左サブタイトル / 左本文 / 右サブタイトル / 右本文）が表示される。それぞれクリックしてテキストを入れる。プログラム的に生成する場合（`d.twocol()`）は全部自動で埋まる。

### `d.save(path)`
`.pptx` として保存。

### 文字数の自動折り返し（max_chars）

各レイアウトのプレースホルダ幅とフォントサイズに合わせて、BudouX で文節境界に折り返す。デフォルト値は `michikusa_pptx.WRAP` で調整可能:

```python
import michikusa_pptx
michikusa_pptx.WRAP["bullets_body"] = 28  # もう少し短く折る
```

| キー | デフォルト | 用途 |
|---|---|---|
| `cover_title` | 12 | 表紙タイトル（60pt） |
| `cover_subtitle` | 24 | 表紙サブタイトル（22pt） |
| `section` | 16 | セクション区切り（46pt） |
| `bullets_title` | 22 | 箇条書きタイトル（36pt） |
| `bullets_body` | 28 | 箇条書き本文（22pt） |
| `twocol_title` | 22 | 2列タイトル（36pt） |
| `twocol_head` | 16 | 2列カラムサブタイトル（28pt） |
| `twocol_body` | 16 | 2列本文（19pt） |

### 改行方針 — 孤立行（寡婦）を出さないための3原則

**問題:** 日本語スライドで「プロンプトは気にしなくていい、大事なの／は／言語化力。」のように、1〜2文字だけの孤立行が生まれると極端に読みづらくなる。原因は3つあって、`michikusa_pptx.py` はそれぞれに対策を入れている:

1. **BudouX 文節境界で折り返す**（`jp_wrap`）
   - `budoux.load_default_japanese_parser()` で文節に分割し、`max_chars`（全角換算）を超えるたび行を確定する
   - これだけだと末尾文節が短いときに孤立行が残る

2. **`_char_width` を日本語組版準拠に**
   - CJK統合漢字・かな・全角英数に加えて、`→` `←` などの矢印（U+2190-U+21FF）、`—` `…` などの一般記号（U+2010-U+206F）、罫線・図形記号（U+25A0-U+25FF）、絵文字系（U+2600-U+27BF）も**全角扱い（1.0）**
   - 半角英数のみ 0.55
   - これで「→基本的には」などの幅を実際のレンダリングに合わせて正しく見積もれる

3. **寡婦回避（orphan merge）**
   - `jp_wrap` の末尾処理で、最後の行の幅が `ORPHAN_MIN_W`（デフォルト 3.0 = 全角3文字相当）以下なら、直前の行に吸収する
   - 「は」「も」「いい」などの1〜2文字単独行を自動で前行末にくっつける

4. **`WRAP` のデフォルトは保守的に**
   - プレースホルダ幅とフォントサイズから**実測で安全側**に設定済み
   - これを超えて緩い値を設定すると、`jp_wrap` では1行に収まってもPowerPointが自動折り返しで孤立行を生み出す
   - 調整するときは現行値より**下げる**方向で

**デバッグのコツ:** 実機で孤立行が出たら、`jp_wrap(text, max_chars)` の出力を `python3 -c "..."` で直接確認する。もしPythonの出力は正しいのにPowerPointでだけ孤立行が出るなら、その `max_chars` が緩すぎる（=PowerPoint側で自動折り返しが発生している）ので値を下げる。

生成済みの `.pptx` に対して検証したいときは、`Deck` が各 wrap 行を個別の paragraph として入れている想定で `python-pptx` から読み戻す:

```python
from pptx import Presentation
import michikusa_pptx as m
prs = Presentation("output.pptx")
for slide in prs.slides:
    for shape in slide.shapes:
        if not shape.has_text_frame: continue
        for para in shape.text_frame.paragraphs:
            t = para.text
            if not t: continue
            w = sum(m._char_width(c) for c in t)
            tag = "ORPHAN" if w <= m.ORPHAN_MIN_W else "ok"
            print(f"  ({w:.1f}) {tag}: {t}")
```

末尾行の幅が `ORPHAN_MIN_W`（デフォルト 3.0）以下なら孤立行。`jp_wrap` 単体の検証と、生成済み .pptx の検証を両方やると `max_chars` の緩さと寡婦回避の効き具合が切り分けられる。

## ガイドライン

- **1ブレットは1メッセージで簡潔に**。長い説明は2行折返しで読みづらくなるので、内容を分けるか言い換える。
- **TwoCol** は対比やbefore/afterに使う。同じ粒度の項目を左右で揃えること。
- **Section** は流れの転換点だけに使う。多用しない。
- **画像や図** を入れたい場合は `python-pptx` の `slide.shapes.add_picture()` を直接呼ぶ:
  ```python
  s = d.bullets("画像入りスライド", ["説明1", "説明2"])
  from pptx.util import Inches
  s.shapes.add_picture("path/to/img.png", Inches(7.5), Inches(2.5), height=Inches(3.5))
  ```
- 出力先は `~/dev-projects/<プロジェクト名>/<deck>.pptx` を推奨。

## 注意事項

- ロゴ・グラデ枠はマスターに埋め込まれているので**スライド側に追加しない**。
- 不要なレイアウト（Title Slide, Two Content など）は既に削除済み。再追加するとPowerPointの「新しいスライド」メニューが汚れる。
- `.potx` のままでは編集できないので、納品物は `.pptx` で保存する。
- 完了したら全ファイルのフルパスをユーザーに報告すること。
