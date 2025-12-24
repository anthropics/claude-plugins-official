#!/usr/bin/env python3
"""
YPM Onboarding Script

An interactive wizard script that collects necessary information from new users
when they first use YPM and automatically generates config.yml.

Specification: docs/development/onboarding-script-spec.md
"""

import os
import sys
from pathlib import Path
import subprocess
import yaml
from datetime import datetime

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ja': '日本語 (Japanese)'
}

def main():
    """Main entry point"""
    print_welcome()

    # Language selection (first step)
    language = ask_language()

    # Check for existing config.yml
    if config_exists():
        if not confirm_overwrite(language):
            msg = {
                'en': "\n❌ Setup cancelled.\nUsing existing config.yml.",
                'ja': "\n❌ セットアップを中止しました。\n既存のconfig.ymlを使用します。"
            }
            print(msg[language])
            sys.exit(0)

    # Collect information
    directory = ask_directory(language)
    pattern = ask_pattern(directory, language)
    active_days = ask_active_days(language)
    inactive_days = ask_inactive_days(active_days, language)

    # Generate config.yml
    generate_config(directory, pattern, active_days, inactive_days, language)

    # Generate PROJECT_STATUS.md (optional)
    if ask_generate_status(language):
        generate_project_status(directory, pattern, language)

    # Completion report
    print_completion_report(directory, pattern, active_days, inactive_days, language)

def print_welcome():
    """Welcome message (always in English first, then show language selection)"""
    print("\n" + "=" * 70)
    print("🚀 YPM (Your Project Manager) - Initial Setup Wizard")
    print("=" * 70)
    print("\nThis wizard will configure YPM to monitor your projects.")
    print("Just answer a few questions and config.yml will be auto-generated.\n")

def ask_language():
    """Ask for language preference"""
    print("-" * 70)
    print("🌐 Language Selection / 言語選択")
    print("-" * 70)
    print("\nSelect your preferred language for YPM output:")
    print("YPMの出力言語を選択してください:\n")

    for i, (code, name) in enumerate(SUPPORTED_LANGUAGES.items(), 1):
        print(f"  {i}. {name} ({code})")

    while True:
        choice = input("\nSelect [1]: ").strip()

        if not choice:
            choice = "1"

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(SUPPORTED_LANGUAGES):
                lang_code = list(SUPPORTED_LANGUAGES.keys())[idx]
                lang_name = SUPPORTED_LANGUAGES[lang_code]
                print(f"\n✅ Selected: {lang_name}")
                return lang_code
        except ValueError:
            pass

        print("❌ Error: Please select a valid number.")

def config_exists():
    """Check if config.yml exists"""
    config_path = Path("config.yml")
    return config_path.exists()

def confirm_overwrite(language):
    """Confirm overwrite"""
    msg = {
        'en': "\n⚠️  Warning: config.yml already exists.\n\nOverwrite? [y/N]: ",
        'ja': "\n⚠️  警告: config.ymlが既に存在します。\n\n上書きしますか？ [y/N]: "
    }
    response = input(msg[language]).strip().lower()
    return response in ['y', 'yes']

def ask_directory(language):
    """Ask for monitored directory"""
    msgs = {
        'en': {
            'header': "📁 STEP 1: Configure Monitored Directory",
            'prompt': "Enter the path to the project directory YPM should monitor.",
            'example': "Example: /Users/yourname/Projects, ~/workspace",
            'input': "Directory to monitor: ",
            'error_empty': "❌ Error: Please enter a path.",
            'error_not_exist': "❌ Error: Directory does not exist: ",
            'error_not_dir': "❌ Error: Path is not a directory: ",
            'error_no_read': "❌ Error: No read permission: ",
            'retry': "\nPlease try again.",
            'success': "\n✅ Directory confirmed: "
        },
        'ja': {
            'header': "📁 STEP 1: 監視対象ディレクトリの設定",
            'prompt': "YPMが監視するプロジェクトディレクトリのパスを入力してください。",
            'example': "例: /Users/yourname/Projects, ~/workspace",
            'input': "監視対象ディレクトリ: ",
            'error_empty': "❌ エラー: パスを入力してください。",
            'error_not_exist': "❌ エラー: ディレクトリが存在しません: ",
            'error_not_dir': "❌ エラー: パスがディレクトリではありません: ",
            'error_no_read': "❌ エラー: 読み取り権限がありません: ",
            'retry': "\nもう一度入力してください。",
            'success': "\n✅ ディレクトリを確認しました: "
        }
    }
    m = msgs[language]

    print("\n" + "-" * 70)
    print(m['header'])
    print("-" * 70)
    print(f"\n{m['prompt']}")
    print(f"{m['example']}\n")

    while True:
        path_input = input(m['input']).strip()

        if not path_input:
            print(m['error_empty'])
            continue

        # Expand ~
        path_expanded = Path(path_input).expanduser()

        # Check existence
        if not path_expanded.exists():
            print(f"{m['error_not_exist']}{path_expanded}")
            print(m['retry'])
            continue

        # Check if directory
        if not path_expanded.is_dir():
            print(f"{m['error_not_dir']}{path_expanded}")
            print(m['retry'])
            continue

        # Check read permission
        if not os.access(path_expanded, os.R_OK):
            print(f"{m['error_no_read']}{path_expanded}")
            print(m['retry'])
            continue

        print(f"{m['success']}{path_expanded}")
        return str(path_expanded)

def ask_pattern(directory, language):
    """Ask for project detection pattern"""
    msgs = {
        'en': {
            'header': "🔍 STEP 2: Configure Project Detection Pattern",
            'analyzing': "Analyzing directory structure...",
            'structure': "Directory structure: ",
            'scan_fail': "Failed to scan directory: ",
            'recommend': "\nRecommended project detection patterns:",
            'opt1': "  1. * (all projects directly under)",
            'opt2': "  2. work/* (under specific directory)",
            'opt3': "  3. proj_*/* (specific naming convention, 2 levels)",
            'opt4': "  4. Enter custom pattern",
            'select': "\nSelect [1]: ",
            'enter_dir': "Enter directory name (e.g., work): ",
            'enter_prefix': "Enter prefix (e.g., proj_): ",
            'enter_custom': "Enter custom pattern: ",
            'error_empty': "❌ Error: Please enter a value.",
            'error_select': "❌ Error: Please select 1-4."
        },
        'ja': {
            'header': "🔍 STEP 2: プロジェクト検出パターンの設定",
            'analyzing': "ディレクトリ構造を分析しています...",
            'structure': "ディレクトリ構造: ",
            'scan_fail': "ディレクトリのスキャンに失敗しました: ",
            'recommend': "\n推奨プロジェクト検出パターン:",
            'opt1': "  1. * (直下の全プロジェクト)",
            'opt2': "  2. work/* (特定のディレクトリ配下)",
            'opt3': "  3. proj_*/* (特定の命名規則、2階層)",
            'opt4': "  4. カスタムパターンを入力",
            'select': "\n選択してください [1]: ",
            'enter_dir': "ディレクトリ名を入力してください (例: work): ",
            'enter_prefix': "プレフィックスを入力してください (例: proj_): ",
            'enter_custom': "カスタムパターンを入力してください: ",
            'error_empty': "❌ エラー: 値を入力してください。",
            'error_select': "❌ エラー: 1-4の番号を選択してください。"
        }
    }
    m = msgs[language]

    print("\n" + "-" * 70)
    print(m['header'])
    print("-" * 70)
    print(f"\n{m['analyzing']}\n")

    # Display directory structure
    try:
        subdirs = [d.name for d in Path(directory).iterdir() if d.is_dir() and not d.name.startswith('.')]
        subdirs = sorted(subdirs[:10])  # First 10

        print(f"{m['structure']}{directory}/")
        for subdir in subdirs:
            print(f"  ├── {subdir}/")
            # Check 2nd level too
            subdir_path = Path(directory) / subdir
            try:
                sub_subdirs = [d.name for d in subdir_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
                for sub in sub_subdirs[:3]:
                    print(f"  │   ├── {sub}/")
            except (PermissionError, OSError):
                pass  # Skip subdirectories we cannot read

        if len(subdirs) > 10:
            print(f"  ... (+{len(list(Path(directory).iterdir())) - 10} more)")
    except Exception as e:
        print(f"{m['scan_fail']}{e}")

    print(m['recommend'])
    print(m['opt1'])
    print(m['opt2'])
    print(m['opt3'])
    print(m['opt4'])

    while True:
        choice = input(m['select']).strip()

        if not choice:
            choice = "1"

        if choice == "1":
            return "*"
        elif choice == "2":
            subdir = input(m['enter_dir']).strip()
            if subdir:
                return f"{subdir}/*"
            else:
                print(m['error_empty'])
        elif choice == "3":
            prefix = input(m['enter_prefix']).strip()
            if prefix:
                return f"{prefix}*/*"
            else:
                print(m['error_empty'])
        elif choice == "4":
            pattern = input(m['enter_custom']).strip()
            if pattern:
                return pattern
            else:
                print(m['error_empty'])
        else:
            print(m['error_select'])

def ask_active_days(language):
    """Ask for active days threshold"""
    msgs = {
        'en': {
            'header': "📅 STEP 3: Configure Classification Criteria",
            'prompt': "Set how many days since last update to consider a project \"active\".",
            'input': "\nActive project threshold (days) [7]: ",
            'error_positive': "❌ Error: Please enter a positive integer.",
            'error_max': "❌ Error: Please enter a value of 365 or less.",
            'error_invalid': "❌ Error: Invalid number: "
        },
        'ja': {
            'header': "📅 STEP 3: 分類基準の設定",
            'prompt': "何日以内に更新されたプロジェクトを「アクティブ」とするか設定します。",
            'input': "\nアクティブプロジェクトの基準日数 [7]: ",
            'error_positive': "❌ エラー: 正の整数を入力してください。",
            'error_max': "❌ エラー: 365日以下の値を入力してください。",
            'error_invalid': "❌ エラー: 無効な数値です: "
        }
    }
    m = msgs[language]

    print("\n" + "-" * 70)
    print(m['header'])
    print("-" * 70)
    print(f"\n{m['prompt']}")

    while True:
        response = input(m['input']).strip()

        if not response:
            return 7

        try:
            days = int(response)
            if days <= 0:
                print(m['error_positive'])
                continue
            if days > 365:
                print(m['error_max'])
                continue
            return days
        except ValueError:
            print(f"{m['error_invalid']}{response}")

def ask_inactive_days(active_days, language):
    """Ask for inactive days threshold"""
    msgs = {
        'en': {
            'prompt': "Set how many days without updates to consider a project \"dormant\".",
            'input': "\nDormant project threshold (days) [30]: ",
            'error_positive': "❌ Error: Please enter a positive integer.",
            'error_max': "❌ Error: Please enter a value of 365 or less.",
            'error_invalid': "❌ Error: Invalid number: ",
            'error_greater': "❌ Error: Please enter a value greater than active threshold ({} days)."
        },
        'ja': {
            'prompt': "何日以上更新されていないプロジェクトを「休止中」とするか設定します。",
            'input': "\n休止中プロジェクトの基準日数 [30]: ",
            'error_positive': "❌ エラー: 正の整数を入力してください。",
            'error_max': "❌ エラー: 365日以下の値を入力してください。",
            'error_invalid': "❌ エラー: 無効な数値です: ",
            'error_greater': "❌ エラー: アクティブ基準日数（{}日）より大きい値を入力してください。"
        }
    }
    m = msgs[language]

    print(f"\n{m['prompt']}")

    while True:
        response = input(m['input']).strip()

        if not response:
            days = 30
        else:
            try:
                days = int(response)
            except ValueError:
                print(f"{m['error_invalid']}{response}")
                continue

        if days <= 0:
            print(m['error_positive'])
            continue
        if days > 365:
            print(m['error_max'])
            continue
        if days <= active_days:
            print(m['error_greater'].format(active_days))
            continue

        return days

def generate_config(directory, pattern, active_days, inactive_days, language):
    """Generate config.yml"""
    msgs = {
        'en': {
            'header': "⚙️  Generating config.yml...",
            'success': "✅ config.yml generated."
        },
        'ja': {
            'header': "⚙️  config.ymlを生成しています...",
            'success': "✅ config.ymlを生成しました。"
        }
    }
    m = msgs[language]

    print("\n" + "-" * 70)
    print(m['header'])
    print("-" * 70)

    # Generate YAML with comments
    with open('config.yml', 'w', encoding='utf-8') as f:
        f.write(f"# YPM Configuration File\n")
        f.write(f"# Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        yaml.dump({
            'monitor': {
                'directories': [directory],
                'exclude': ['proj_YPM/YPM'],
                'patterns': [pattern]
            },
            'classification': {
                'active_days': active_days,
                'inactive_days': inactive_days
            },
            'progress': {
                'phase_0': '0-20',
                'phase_1': '20-30',
                'phase_2': '30-60',
                'phase_3': '60-80',
                'phase_4': '80-100'
            },
            'editor': {
                'default': 'code'
            },
            'settings': {
                'language': language,
                'include_non_git': False,
                'doc_priority': ['CLAUDE.md', 'README.md', 'docs/INDEX.md']
            }
        }, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(m['success'])

def ask_generate_status(language):
    """Ask whether to generate PROJECT_STATUS.md"""
    msgs = {
        'en': {
            'header': "📊 STEP 4: Generate Initial PROJECT_STATUS.md (Optional)",
            'prompt': "You can generate the initial PROJECT_STATUS.md now.",
            'note': "(You can also generate it later with Claude Code)",
            'git_warning': "\n⚠️  Warning: Git command not found.\nSkipping automatic PROJECT_STATUS.md generation.\nPlease generate it later with Claude Code.",
            'input': "\nGenerate initial PROJECT_STATUS.md? [Y/n]: "
        },
        'ja': {
            'header': "📊 STEP 4: 初回PROJECT_STATUS.mdの生成（オプション）",
            'prompt': "初回のPROJECT_STATUS.mdを今すぐ生成することもできます。",
            'note': "（Claude Codeで後ほど生成することも可能です）",
            'git_warning': "\n⚠️  警告: Gitコマンドが見つかりません。\nPROJECT_STATUS.mdの自動生成をスキップします。\nClaude Codeで後ほど生成してください。",
            'input': "\n初回のPROJECT_STATUS.mdを生成しますか？ [Y/n]: "
        }
    }
    m = msgs[language]

    print("\n" + "-" * 70)
    print(m['header'])
    print("-" * 70)
    print(f"\n{m['prompt']}")
    print(m['note'])

    # Check if Git is available
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(m['git_warning'])
        return False

    response = input(m['input']).strip().lower()
    return response != 'n'

def generate_project_status(directory, pattern, language):
    """Generate PROJECT_STATUS.md"""
    msgs = {
        'en': {
            'header': "📊 Generating PROJECT_STATUS.md...",
            'wait': "This may take a moment...",
            'success': "✅ PROJECT_STATUS.md (initial version) generated.",
            'note': "   For detailed information, update with Claude Code."
        },
        'ja': {
            'header': "📊 PROJECT_STATUS.mdを生成しています...",
            'wait': "この処理には時間がかかる場合があります...",
            'success': "✅ PROJECT_STATUS.md（初期版）を生成しました。",
            'note': "   詳細な情報はClaude Codeで更新してください。"
        }
    }
    m = msgs[language]

    print("\n" + "-" * 70)
    print(m['header'])
    print("-" * 70)
    print(f"\n{m['wait']}\n")

    # Generate simplified PROJECT_STATUS.md
    # (Full version delegated to Claude Code)
    with open('PROJECT_STATUS.md', 'w', encoding='utf-8') as f:
        f.write("# Project Status Overview\n\n")
        f.write(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("---\n\n")
        f.write("## Summary\n\n")
        f.write("Initial generation complete. Please use Claude Code to run \"update project status\".\n\n")

    print(m['success'])
    print(m['note'])

def print_completion_report(directory, pattern, active_days, inactive_days, language):
    """Display completion report"""
    msgs = {
        'en': {
            'header': "✅ Setup Complete!",
            'dir': "📁 Monitored Directory:",
            'pattern': "🔍 Detection Pattern:",
            'active': "📊 Active Threshold:",
            'days_within': "days",
            'dormant': "💤 Dormant Threshold:",
            'days_over': "days or more",
            'files': "Generated files:",
            'next_header': "🎉 Next Steps:",
            'next_prompt': "In Claude Code, run:",
            'next_command': '  "Update project status"',
            'next_note': "This will collect all project information."
        },
        'ja': {
            'header': "✅ セットアップが完了しました！",
            'dir': "📁 監視対象ディレクトリ:",
            'pattern': "🔍 検出パターン:",
            'active': "📊 アクティブ基準:",
            'days_within': "日以内",
            'dormant': "💤 休止中基準:",
            'days_over': "日以上",
            'files': "生成されたファイル:",
            'next_header': "🎉 次のステップ:",
            'next_prompt': "Claude Codeで以下のように指示してください：",
            'next_command': '  「プロジェクト状況を更新して」',
            'next_note': "これで、すべてのプロジェクト情報が収集されます。"
        }
    }
    m = msgs[language]

    print("\n" + "=" * 70)
    print(m['header'])
    print("=" * 70)
    print(f"\n{m['dir']} {directory}")
    print(f"{m['pattern']} {pattern}")
    print(f"{m['active']} {active_days} {m['days_within']}")
    print(f"{m['dormant']} {inactive_days} {m['days_over']}")
    print(f"\n{m['files']}")
    print("  - config.yml")
    if Path("PROJECT_STATUS.md").exists():
        print("  - PROJECT_STATUS.md")
    print("\n" + "-" * 70)
    print(m['next_header'])
    print("-" * 70)
    print(f"\n{m['next_prompt']}")
    print(m['next_command'])
    print(f"\n{m['next_note']}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
