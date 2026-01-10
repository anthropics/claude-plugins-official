# Filesystem Context Implementation Patterns

This reference provides detailed implementation patterns for filesystem-based context engineering.

## Pattern Catalog

### 1. Scratch Pad Manager

A centralized manager for handling large tool outputs and intermediate results.

```python
import os
import json
from datetime import datetime
from pathlib import Path

class ScratchPadManager:
    """Manages temporary file storage for agent context offloading."""
    
    def __init__(self, base_path: str = "scratch", token_threshold: int = 2000):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.token_threshold = token_threshold
        self.manifest = {}
    
    def should_offload(self, content: str) -> bool:
        """Determine if content exceeds threshold for offloading."""
        # Rough token estimate: 1 token ≈ 4 characters
        estimated_tokens = len(content) // 4
        return estimated_tokens > self.token_threshold
    
    def offload(self, content: str, source: str, summary: str = None) -> dict:
        """Write content to file, return reference."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}.txt"
        file_path = self.base_path / filename
        
        file_path.write_text(content)
        
        reference = {
            "type": "file_reference",
            "path": str(file_path),
            "source": source,
            "timestamp": timestamp,
            "size_chars": len(content),
            "summary": summary or self._extract_summary(content)
        }
        
        self.manifest[filename] = reference
        return reference
    
    def _extract_summary(self, content: str, max_chars: int = 500) -> str:
        """Extract first meaningful content as summary."""
        lines = content.strip().split('\n')
        summary_lines = []
        char_count = 0
        
        for line in lines:
            if char_count + len(line) > max_chars:
                break
            summary_lines.append(line)
            char_count += len(line)
        
        return '\n'.join(summary_lines)
    
    def cleanup(self, max_age_hours: int = 24):
        """Remove scratch files older than threshold."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for file_path in self.base_path.glob("*.txt"):
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                if file_path.name in self.manifest:
                    del self.manifest[file_path.name]
```

### 2. Plan Persistence

Structured plan storage with progress tracking.

```python
import yaml
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional

class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class PlanStep:
    id: int
    description: str
    status: StepStatus = StepStatus.PENDING
    notes: Optional[str] = None

@dataclass
class AgentPlan:
    objective: str
    steps: List[PlanStep] = field(default_factory=list)
    status: str = "in_progress"
    
    def save(self, path: str = "scratch/current_plan.yaml"):
        """Persist plan to filesystem."""
        data = {
            "objective": self.objective,
            "status": self.status,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "status": s.status.value,
                    "notes": s.notes
                }
                for s in self.steps
            ]
        }
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    @classmethod
    def load(cls, path: str = "scratch/current_plan.yaml") -> "AgentPlan":
        """Load plan from filesystem."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        plan = cls(objective=data["objective"], status=data.get("status", "in_progress"))
        for step_data in data.get("steps", []):
            plan.steps.append(PlanStep(
                id=step_data["id"],
                description=step_data["description"],
                status=StepStatus(step_data["status"]),
                notes=step_data.get("notes")
            ))
        return plan
    
    def current_step(self) -> Optional[PlanStep]:
        """Get the first non-completed step."""
        for step in self.steps:
            if step.status != StepStatus.COMPLETED:
                return step
        return None
    
    def complete_step(self, step_id: int, notes: str = None):
        """Mark step as completed."""
        for step in self.steps:
            if step.id == step_id:
                step.status = StepStatus.COMPLETED
                if notes:
                    step.notes = notes
                break
```

### 3. Sub-Agent Workspace

File-based communication between agents.

```python
from pathlib import Path
from datetime import datetime
import json

class AgentWorkspace:
    """Manages file-based workspace for an agent."""
    
    def __init__(self, agent_id: str, base_path: str = "workspace/agents"):
        self.agent_id = agent_id
        self.path = Path(base_path) / agent_id
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Standard files
        self.findings_file = self.path / "findings.md"
        self.status_file = self.path / "status.json"
        self.log_file = self.path / "activity.log"
    
    def write_finding(self, content: str, append: bool = True):
        """Write or append a finding."""
        mode = 'a' if append else 'w'
        with open(self.findings_file, mode) as f:
            if append:
                f.write(f"\n---\n## {datetime.now().isoformat()}\n\n")
            f.write(content)
    
    def update_status(self, status: str, progress: float = None, details: dict = None):
        """Update agent status for coordinator visibility."""
        status_data = {
            "agent_id": self.agent_id,
            "status": status,
            "updated_at": datetime.now().isoformat(),
            "progress": progress,
            "details": details or {}
        }
        self.status_file.write_text(json.dumps(status_data, indent=2))
    
    def log(self, message: str):
        """Append to activity log."""
        with open(self.log_file, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    
    def read_peer_findings(self, peer_id: str) -> str:
        """Read findings from another agent's workspace."""
        peer_path = self.path.parent / peer_id / "findings.md"
        if peer_path.exists():
            return peer_path.read_text()
        return ""


class CoordinatorWorkspace:
    """Coordinator that reads from sub-agent workspaces."""
    
    def __init__(self, base_path: str = "workspace/agents"):
        self.base_path = Path(base_path)
    
    def get_all_statuses(self) -> dict:
        """Collect status from all sub-agents."""
        statuses = {}
        for agent_dir in self.base_path.iterdir():
            if agent_dir.is_dir():
                status_file = agent_dir / "status.json"
                if status_file.exists():
                    statuses[agent_dir.name] = json.loads(status_file.read_text())
        return statuses
    
    def aggregate_findings(self) -> str:
        """Combine all agent findings into synthesis."""
        findings = []
        for agent_dir in self.base_path.iterdir():
            if agent_dir.is_dir():
                findings_file = agent_dir / "findings.md"
                if findings_file.exists():
                    findings.append(f"# {agent_dir.name}\n\n{findings_file.read_text()}")
        return "\n\n".join(findings)
```

### 4. Dynamic Skill Loader

Load skill content on demand.

```python
from pathlib import Path
from typing import List, Optional
import yaml

@dataclass
class SkillMetadata:
    name: str
    description: str
    path: str
    triggers: List[str] = field(default_factory=list)

class SkillLoader:
    """Manages dynamic loading of agent skills."""
    
    def __init__(self, skills_path: str = "skills"):
        self.skills_path = Path(skills_path)
        self.skill_index = self._build_index()
    
    def _build_index(self) -> dict:
        """Build index of available skills from SKILL.md frontmatter."""
        index = {}
        for skill_dir in self.skills_path.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    metadata = self._parse_frontmatter(skill_file)
                    if metadata:
                        index[metadata.name] = metadata
        return index
    
    def _parse_frontmatter(self, path: Path) -> Optional[SkillMetadata]:
        """Extract YAML frontmatter from skill file."""
        content = path.read_text()
        if content.startswith('---'):
            end = content.find('---', 3)
            if end > 0:
                frontmatter = yaml.safe_load(content[3:end])
                return SkillMetadata(
                    name=frontmatter.get('name', path.parent.name),
                    description=frontmatter.get('description', ''),
                    path=str(path),
                    triggers=frontmatter.get('triggers', [])
                )
        return None
    
    def get_static_context(self) -> str:
        """Generate minimal static context listing available skills."""
        lines = ["Available skills (load with read_file when relevant):"]
        for name, meta in self.skill_index.items():
            lines.append(f"- {name}: {meta.description[:100]}")
        return "\n".join(lines)
    
    def load_skill(self, name: str) -> str:
        """Load full skill content."""
        if name in self.skill_index:
            return Path(self.skill_index[name].path).read_text()
        raise ValueError(f"Unknown skill: {name}")
    
    def find_relevant_skills(self, query: str) -> List[str]:
        """Find skills that might be relevant to a query."""
        query_lower = query.lower()
        relevant = []
        for name, meta in self.skill_index.items():
            if any(trigger in query_lower for trigger in meta.triggers):
                relevant.append(name)
            elif name.replace('-', ' ') in query_lower:
                relevant.append(name)
        return relevant
```

### 5. Terminal Output Persistence

Capture and persist terminal sessions.

```python
import subprocess
from pathlib import Path
from datetime import datetime
import re

class TerminalCapture:
    """Captures and persists terminal output for agent access."""
    
    def __init__(self, terminals_path: str = "terminals"):
        self.terminals_path = Path(terminals_path)
        self.terminals_path.mkdir(parents=True, exist_ok=True)
        self.session_counter = 0
    
    def run_command(self, command: str, capture: bool = True) -> dict:
        """Run command and optionally capture output to file."""
        self.session_counter += 1
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        
        output = {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        }
        
        if capture:
            output["file"] = self._persist_output(output)
        
        return output
    
    def _persist_output(self, output: dict) -> str:
        """Write output to terminal file."""
        filename = f"{self.session_counter}.txt"
        file_path = self.terminals_path / filename
        
        content = f"""---
command: {output['command']}
exit_code: {output['exit_code']}
timestamp: {output['timestamp']}
---

=== STDOUT ===
{output['stdout']}

=== STDERR ===
{output['stderr']}
"""
        file_path.write_text(content)
        return str(file_path)
    
    def grep_terminals(self, pattern: str, context_lines: int = 3) -> List[dict]:
        """Search all terminal outputs for pattern."""
        matches = []
        regex = re.compile(pattern, re.IGNORECASE)
        
        for term_file in self.terminals_path.glob("*.txt"):
            content = term_file.read_text()
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if regex.search(line):
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    matches.append({
                        "file": str(term_file),
                        "line_number": i + 1,
                        "context": '\n'.join(lines[start:end])
                    })
        
        return matches
```

### 6. Self-Modification Guard

Safe pattern for agent self-learning.

```python
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any

class PreferenceStore:
    """Guarded storage for agent-learned preferences."""
    
    MAX_ENTRIES = 100
    MAX_VALUE_LENGTH = 1000
    
    def __init__(self, path: str = "agent/preferences.yaml"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.preferences = self._load()
    
    def _load(self) -> dict:
        """Load preferences from file."""
        if self.path.exists():
            return yaml.safe_load(self.path.read_text()) or {}
        return {}
    
    def _save(self):
        """Persist preferences to file."""
        self.path.write_text(yaml.dump(self.preferences, default_flow_style=False))
    
    def remember(self, key: str, value: Any, source: str = "user"):
        """Store a preference with validation."""
        # Validate key
        if not key or len(key) > 100:
            raise ValueError("Invalid key length")
        
        # Validate value
        value_str = str(value)
        if len(value_str) > self.MAX_VALUE_LENGTH:
            raise ValueError(f"Value exceeds max length of {self.MAX_VALUE_LENGTH}")
        
        # Check entry limit
        if len(self.preferences) >= self.MAX_ENTRIES and key not in self.preferences:
            raise ValueError(f"Max entries ({self.MAX_ENTRIES}) reached")
        
        # Store with metadata
        self.preferences[key] = {
            "value": value,
            "source": source,
            "updated_at": datetime.now().isoformat()
        }
        self._save()
    
    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a preference."""
        entry = self.preferences.get(key)
        if entry:
            return entry["value"]
        return default
    
    def list_all(self) -> dict:
        """Get all preferences for context injection."""
        return {k: v["value"] for k, v in self.preferences.items()}
    
    def forget(self, key: str):
        """Remove a preference."""
        if key in self.preferences:
            del self.preferences[key]
            self._save()
```

## Integration Example

Combining patterns in an agent harness:

```python
class FilesystemContextAgent:
    """Agent with filesystem-based context management."""
    
    def __init__(self):
        self.scratch = ScratchPadManager()
        self.skills = SkillLoader()
        self.preferences = PreferenceStore()
        self.workspace = AgentWorkspace("main_agent")
    
    def handle_tool_output(self, tool_name: str, output: str) -> str:
        """Process tool output, offloading if necessary."""
        if self.scratch.should_offload(output):
            ref = self.scratch.offload(output, source=tool_name)
            return f"[{tool_name} output saved to {ref['path']}. Summary: {ref['summary'][:200]}]"
        return output
    
    def get_system_prompt(self) -> str:
        """Build system prompt with dynamic skill references."""
        base_prompt = "You are a helpful assistant."
        skill_context = self.skills.get_static_context()
        user_prefs = self.preferences.list_all()
        
        pref_section = ""
        if user_prefs:
            pref_section = "\n\nUser preferences:\n" + "\n".join(
                f"- {k}: {v}" for k, v in user_prefs.items()
            )
        
        return f"{base_prompt}\n\n{skill_context}{pref_section}"
```

## File Organization Best Practices

```
project/
├── scratch/                    # Ephemeral working files
│   ├── tool_outputs/          # Large tool results
│   │   └── search_20260107.txt
│   └── plans/                 # Active task plans
│       └── current_plan.yaml
├── workspace/                  # Agent workspaces
│   └── agents/
│       ├── research_agent/
│       │   ├── findings.md
│       │   └── status.json
│       └── code_agent/
│           ├── findings.md
│           └── status.json
├── agent/                      # Agent configuration
│   ├── preferences.yaml       # Learned preferences
│   └── patterns.md           # Discovered patterns
├── skills/                     # Loadable skills
│   └── {skill-name}/
│       └── SKILL.md
├── terminals/                  # Terminal output
│   ├── 1.txt
│   └── 2.txt
└── history/                    # Chat history archives
    └── session_001.txt
```

## Token Accounting Metrics

Track these metrics to validate filesystem patterns:

1. **Static context ratio**: tokens in static context / total tokens
2. **Dynamic load rate**: how often skills/files are loaded per task
3. **Offload savings**: tokens saved by writing to files vs keeping in context
4. **Retrieval precision**: percentage of loaded content actually used

Target benchmarks:
- Static context ratio < 20%
- Offload savings > 50% for tool-heavy workflows
- Retrieval precision > 70% (loaded content is relevant)

