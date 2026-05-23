#!/usr/bin/env python3
"""
ARKHE OS — Cybersecurity Foundations CLI
Arquiteto: ORCID 0009-0005-2697-4668
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from .curriculum import CURRICULUM, get_topic, get_pillar_topics
from .quiz_engine import QuizEngine
from .lab_auditor import LabAuditor
from .nmap_bridge import NmapBridge

console = Console()

@click.group()
def cybersec():
    """ARKHE Cybersecurity Foundations — 12 pillars, 48 topics."""
    pass

@cybersec.command()
@click.argument("topic_id", required=False)
@click.option("--pillar", "-p", help="Filter by pillar (P1-P12)")
def learn(topic_id, pillar):
    """Browse the cybersecurity curriculum."""
    if topic_id:
        topic = get_topic(topic_id)
        if topic:
            panel = Panel.fit(
                f"[bold]{topic['name']}[/bold]\n\n{topic['content']}",
                title=f"613.{topic['id']}", border_style="green"
            )
            console.print(panel)
            if topic.get("prerequisites"):
                console.print("[yellow]Prerequisites:[/yellow]")
                for prereq in topic["prerequisites"]:
                    console.print(f"  • {prereq}")
            if topic.get("tools"):
                console.print("[yellow]Tools:[/yellow]")
                for tool in topic["tools"]:
                    console.print(f"  • {tool}")
        else:
            console.print(f"[red]Topic '{topic_id}' not found.[/red]")
        return

    # List all topics or filter by pillar
    table = Table(title="ARKHE Cybersecurity Curriculum")
    table.add_column("ID", style="cyan")
    table.add_column("Topic", style="green")
    table.add_column("Pillar", style="yellow")
    table.add_column("Tools", style="dim")

    for p_id, p_data in CURRICULUM.items():
        if pillar and p_id != pillar:
            continue
        for topic in p_data["topics"]:
            table.add_row(
                topic["id"],
                topic["name"],
                p_data["name"],
                ", ".join(topic.get("tools", []))[:60]
            )

    console.print(table)

@cybersec.command()
@click.argument("topic")
@click.option("--count", "-n", default=5, help="Number of questions")
def quiz(topic, count):
    """Take a quiz on a cybersecurity topic."""
    engine = QuizEngine()
    questions = engine.generate_quiz(topic, count)
    score = 0
    total = len(questions)

    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold]Q{i}[/bold]: {q['question']}")
        for opt_id, opt_text in q["options"].items():
            console.print(f"  {opt_id}) {opt_text}")
        answer = click.prompt("Your answer", type=str).upper()
        if answer == q["correct"]:
            console.print("[green]✓ Correct![/green]")
            score += 1
        else:
            console.print(f"[red]✗ Incorrect. Correct: {q['correct']}[/red]")
        if q.get("explanation"):
            console.print(f"[dim]{q['explanation']}[/dim]")

    percentage = (score / total) * 100
    color = "green" if percentage >= 80 else "yellow" if percentage >= 60 else "red"
    console.print(f"\n[bold {color}]Score: {score}/{total} ({percentage:.1f}%)[/bold {color}]")

@cybersec.command()
@click.argument("target", required=False)
@click.option("--port", "-p", default="1-1000", help="Port range")
@click.option("--scan-type", "-s", type=click.Choice(["tcp", "udp", "syn", "os"]), default="tcp")
def scan(target, port, scan_type):
    """Perform network reconnaissance scan (educational use only)."""
    if not target:
        target = click.prompt("Target IP or hostname")

    console.print(f"[yellow]Starting {scan_type} scan on {target}:{port}...[/yellow]")
    console.print("[red]⚠ Educational use only — scan only your own lab environment![/red]")

    nmap = NmapBridge()
    results = nmap.scan(target, port, scan_type)

    if results.get("error"):
        console.print(f"[red]Scan error: {results['error']}[/red]")
        return

    table = Table(title=f"Scan Results — {target}")
    table.add_column("Port", style="cyan")
    table.add_column("State", style="green")
    table.add_column("Service", style="yellow")
    table.add_column("Version", style="dim")

    for port_data in results.get("ports", []):
        table.add_row(
            str(port_data["port"]),
            port_data["state"],
            port_data.get("service", ""),
            port_data.get("version", "")
        )

    console.print(table)

@cybersec.command()
@click.option("--url", "-u", help="Target URL to test")
@click.option("--test", "-t", type=click.Choice(["xss", "sqli", "upload", "all"]), default="all")
def test_web(url, test):
    """Test a web application for common vulnerabilities (educational use only)."""
    if not url:
        url = click.prompt("Target URL (e.g., http://localhost:8080)")

    console.print(f"[yellow]Testing {url} for {test} vulnerabilities...[/yellow]")
    console.print("[red]⚠ Educational use only — test only your own lab applications![/red]")

    # Use Nuclei templates for educational testing
    from .nuclei_runner import run_educational_templates
    results = run_educational_templates(url, test)

    for finding in results:
        severity_color = "red" if finding["severity"] in ["critical", "high"] else "yellow"
        console.print(f"[{severity_color}]●[/{severity_color}] {finding['name']} ({finding['severity']})")
        if finding.get("remediation"):
            console.print(f"  [dim]Fix: {finding['remediation']}[/dim]")

@cybersec.command()
def lab_check():
    """Audit your lab environment for security and isolation."""
    auditor = LabAuditor()
    results = auditor.audit()

    console.print("[bold]Lab Environment Audit[/bold]")
    for check, passed in results.items():
        icon = "✓" if passed else "✗"
        color = "green" if passed else "red"
        console.print(f"  [{color}]{icon} {check}[/{color}]")

def register(cli: click.Group):
    cli.add_command(cybersec)