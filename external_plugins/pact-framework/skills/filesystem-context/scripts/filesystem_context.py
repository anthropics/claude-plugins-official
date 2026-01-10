"""
Filesystem Context Manager

Demonstrates the core patterns for filesystem-based context engineering:
1. Scratch pad for tool output offloading
2. Plan persistence for long-horizon tasks
3. Dynamic context discovery with file references

Usage:
    python filesystem_context.py

This script demonstrates concepts without external dependencies.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# =============================================================================
# Pattern 1: Scratch Pad Manager
# =============================================================================

class ScratchPadManager:
    """
    Manages temporary file storage for offloading large tool outputs.
    
    Instead of keeping 10k tokens of search results in context,
    write them to a file and return a reference. The agent can
    then grep or read specific sections as needed.
    """
    
    def __init__(self, base_path: str = "scratch", token_threshold: int = 2000):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.token_threshold = token_threshold
    
    def estimate_tokens(self, content: str) -> int:
        """Rough token estimate: ~4 characters per token."""
        return len(content) // 4
    
    def should_offload(self, content: str) -> bool:
        """Determine if content exceeds threshold for offloading."""
        return self.estimate_tokens(content) > self.token_threshold
    
    def offload(self, content: str, source: str) -> Dict[str, Any]:
        """
        Write content to file, return compact reference.
        
        The reference includes:
        - File path for later retrieval
        - Summary of first few lines
        - Token estimate for the full content
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{source}_{timestamp}.txt"
        file_path = self.base_path / filename
        
        file_path.write_text(content)
        
        # Extract summary from first meaningful lines
        lines = content.strip().split('\n')[:5]
        summary = '\n'.join(lines)
        if len(summary) > 300:
            summary = summary[:300] + "..."
        
        return {
            "path": str(file_path),
            "source": source,
            "tokens_saved": self.estimate_tokens(content),
            "summary": summary
        }
    
    def format_reference(self, ref: Dict[str, Any]) -> str:
        """Format reference for inclusion in context."""
        return (
            f"[Output from {ref['source']} saved to {ref['path']}. "
            f"~{ref['tokens_saved']} tokens. "
            f"Summary: {ref['summary'][:200]}]"
        )


# =============================================================================
# Pattern 2: Plan Persistence
# =============================================================================

@dataclass
class PlanStep:
    """Individual step in an agent plan."""
    id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, blocked
    notes: Optional[str] = None


@dataclass
class AgentPlan:
    """
    Persistent plan that survives context window limitations.
    
    Write the plan to disk so the agent can re-read it at any point,
    even after summarization or context window refresh.
    """
    objective: str
    steps: List[PlanStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "objective": self.objective,
            "created_at": self.created_at,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "status": s.status,
                    "notes": s.notes
                }
                for s in self.steps
            ]
        }
    
    def save(self, path: str = "scratch/current_plan.json"):
        """Persist plan to filesystem."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"Plan saved to {path}")
    
    @classmethod
    def load(cls, path: str = "scratch/current_plan.json") -> "AgentPlan":
        """Load plan from filesystem."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        plan = cls(objective=data["objective"])
        plan.created_at = data.get("created_at", "")
        
        for step_data in data.get("steps", []):
            plan.steps.append(PlanStep(
                id=step_data["id"],
                description=step_data["description"],
                status=step_data["status"],
                notes=step_data.get("notes")
            ))
        return plan
    
    def current_step(self) -> Optional[PlanStep]:
        """Get the current (first non-completed) step."""
        for step in self.steps:
            if step.status not in ["completed", "cancelled"]:
                return step
        return None
    
    def complete_step(self, step_id: int, notes: str = None):
        """Mark a step as completed."""
        for step in self.steps:
            if step.id == step_id:
                step.status = "completed"
                if notes:
                    step.notes = notes
                return
        raise ValueError(f"Step {step_id} not found")
    
    def progress_summary(self) -> str:
        """Generate summary for context injection."""
        completed = sum(1 for s in self.steps if s.status == "completed")
        total = len(self.steps)
        current = self.current_step()
        
        summary = f"Objective: {self.objective}\n"
        summary += f"Progress: {completed}/{total} steps completed\n"
        if current:
            summary += f"Current step: [{current.id}] {current.description}"
        else:
            summary += "All steps completed."
        
        return summary


# =============================================================================
# Pattern 3: Tool Output Handler
# =============================================================================

class ToolOutputHandler:
    """
    Handles tool outputs with automatic offloading decision.
    
    Small outputs stay in context. Large outputs get written to files
    with a compact reference returned instead.
    """
    
    def __init__(self, scratch_pad: ScratchPadManager = None):
        self.scratch_pad = scratch_pad or ScratchPadManager()
    
    def process_output(self, tool_name: str, output: str) -> str:
        """
        Process tool output, offloading if too large.
        
        Returns either:
        - The original output (if small enough)
        - A file reference with summary (if too large)
        """
        if self.scratch_pad.should_offload(output):
            ref = self.scratch_pad.offload(output, source=tool_name)
            return self.scratch_pad.format_reference(ref)
        return output


# =============================================================================
# Demonstration
# =============================================================================

def demo_scratch_pad():
    """Demonstrate scratch pad pattern."""
    print("=" * 60)
    print("DEMO: Scratch Pad for Tool Output Offloading")
    print("=" * 60)
    
    scratch = ScratchPadManager(base_path="demo_scratch", token_threshold=100)
    
    # Small output stays in context
    small_output = "API returned: {'status': 'ok', 'data': [1, 2, 3]}"
    print(f"\nSmall output ({scratch.estimate_tokens(small_output)} tokens):")
    print(f"  Should offload: {scratch.should_offload(small_output)}")
    
    # Large output gets offloaded
    large_output = """
Search Results for "context engineering":

1. Context Engineering: The Art of Curating LLM Context
   URL: https://example.com/article1
   Snippet: Context engineering is the discipline of managing what information 
   enters the language model's context window. Unlike prompt engineering which
   focuses on instruction crafting, context engineering addresses the holistic
   curation of all information...
   
2. Building Production Agents with Effective Context Management
   URL: https://example.com/article2
   Snippet: Production agent systems require sophisticated context management
   strategies. This includes compression, caching, and strategic partitioning
   of work across sub-agents with isolated contexts...
   
3. The Lost-in-Middle Problem and How to Avoid It
   URL: https://example.com/article3
   Snippet: Research shows that language models exhibit U-shaped attention
   patterns, with information in the middle of long contexts receiving less
   attention than content at the beginning or end...

... (imagine 50 more results) ...
"""
    
    print(f"\nLarge output ({scratch.estimate_tokens(large_output)} tokens):")
    print(f"  Should offload: {scratch.should_offload(large_output)}")
    
    if scratch.should_offload(large_output):
        ref = scratch.offload(large_output, source="web_search")
        print(f"\nOffloaded to: {ref['path']}")
        print(f"Tokens saved: {ref['tokens_saved']}")
        print(f"\nReference for context:\n{scratch.format_reference(ref)}")


def demo_plan_persistence():
    """Demonstrate plan persistence pattern."""
    print("\n" + "=" * 60)
    print("DEMO: Plan Persistence for Long-Horizon Tasks")
    print("=" * 60)
    
    # Create a plan
    plan = AgentPlan(objective="Refactor authentication module")
    plan.steps = [
        PlanStep(id=1, description="Audit current auth endpoints"),
        PlanStep(id=2, description="Design new token validation flow"),
        PlanStep(id=3, description="Implement changes"),
        PlanStep(id=4, description="Write tests"),
        PlanStep(id=5, description="Deploy and monitor"),
    ]
    
    print("\nInitial plan:")
    print(plan.progress_summary())
    
    # Save to filesystem
    plan.save("demo_scratch/current_plan.json")
    
    # Simulate completing first step
    plan.complete_step(1, notes="Found 12 endpoints, 3 need updates")
    plan.steps[1].status = "in_progress"
    
    print("\nAfter completing step 1:")
    print(plan.progress_summary())
    
    # Save updated plan
    plan.save("demo_scratch/current_plan.json")
    
    # Simulate loading from file (as if in new context)
    print("\n--- Simulating context refresh ---")
    loaded_plan = AgentPlan.load("demo_scratch/current_plan.json")
    print("\nPlan loaded from file:")
    print(loaded_plan.progress_summary())


def demo_tool_handler():
    """Demonstrate integrated tool output handling."""
    print("\n" + "=" * 60)
    print("DEMO: Integrated Tool Output Handler")
    print("=" * 60)
    
    handler = ToolOutputHandler(
        scratch_pad=ScratchPadManager(base_path="demo_scratch", token_threshold=50)
    )
    
    outputs = [
        ("calculator", "42"),
        ("file_read", "Error: File not found"),
        ("database_query", """
            Results (250 rows):
            | id | name | email | created_at | status |
            |----|------|-------|------------|--------|
            | 1  | John | j@e.c | 2024-01-01 | active |
            | 2  | Jane | j@e.c | 2024-01-02 | active |
            ... (248 more rows) ...
        """),
    ]
    
    for tool_name, output in outputs:
        processed = handler.process_output(tool_name, output)
        print(f"\n{tool_name}:")
        print(f"  Original length: {len(output)} chars")
        print(f"  Processed: {processed[:100]}...")


def cleanup_demo():
    """Clean up demo files."""
    import shutil
    demo_path = Path("demo_scratch")
    if demo_path.exists():
        shutil.rmtree(demo_path)
        print("\nDemo files cleaned up.")


if __name__ == "__main__":
    demo_scratch_pad()
    demo_plan_persistence()
    demo_tool_handler()
    
    print("\n" + "=" * 60)
    print("Cleanup demo files? (y/n): ", end="")
    # Auto-cleanup for non-interactive runs
    cleanup_demo()

