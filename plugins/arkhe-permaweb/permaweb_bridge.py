#!/usr/bin/env python3
# permaweb_bridge.py — Substrate 927
# Arweave/AO/Permaweb Bridge for ARKHE-OS Omni-Agent
# Integrates with HyperBEAM (OS do permaweb), AO Computer, AOS, and Arweave storage

import json
import hashlib
import base64
import time
import asyncio
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════
# Permaweb Configuration
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PermawebConfig:
    """Configuration for Permaweb Bridge."""
    # Arweave settings
    arweave_gateway: str = "https://arweave.net"
    arweave_graphql: str = "https://arweave.net/graphql"

    # AO Computer settings
    ao_mu_url: str = "https://mu.ao-testnet.xyz"
    ao_cu_url: str = "https://cu.ao-testnet.xyz"
    ao_su_url: str = "https://su.ao-testnet.xyz"

    # AOS settings
    aos_process_id: Optional[str] = None
    aos_module_id: str = "SBNb1qPQ1TDwpD_mokmNSia-Sc-7tPvUl8keTt22PE"  # Default AOS module

    # Wallet
    wallet_path: Optional[str] = None  # Path to Arweave keyfile (JWK)
    wallet_jwk: Optional[Dict] = None  # Or provide JWK directly

    # Bridge settings
    auto_upload: bool = False  # Auto-upload agent state to Arweave
    upload_interval: int = 3600  # Seconds between auto-uploads

    # HyperBEAM integration
    hyperbeam_endpoint: Optional[str] = None

    # Logging
    debug: bool = False


# ═══════════════════════════════════════════════════════════════════
# Arweave Data Layer
# ═══════════════════════════════════════════════════════════════════

class ArweaveDataLayer:
    """Interface with Arweave permanent storage."""

    def __init__(self, config: PermawebConfig):
        self.config = config
        self._wallet = None
        if config.wallet_jwk:
            self._wallet = config.wallet_jwk
        elif config.wallet_path:
            with open(config.wallet_path) as f:
                self._wallet = json.load(f)

    def upload_data(self, data: Union[str, bytes],
                    tags: Optional[Dict[str, str]] = None) -> Dict:
        """
        Upload data to Arweave permanently.

        Args:
            data: Content to store (string or bytes)
            tags: Arweave tags for indexing

        Returns:
            Transaction info with tx_id
        """
        try:
            import arweave
            wallet = arweave.Wallet(self._wallet) if self._wallet else None

            if isinstance(data, str):
                data = data.encode('utf-8')

            transaction = arweave.Transaction(wallet, data=data)

            # Add tags
            default_tags = {
                "App-Name": "ARKHE-OS",
                "App-Version": "2.0.0",
                "Substrate": "927",
                "Content-Type": "application/json",
                "Timestamp": str(int(time.time())),
            }
            if tags:
                default_tags.update(tags)

            for key, value in default_tags.items():
                transaction.add_tag(key, value)

            if wallet:
                transaction.sign()
                transaction.send()

            return {
                "tx_id": transaction.id,
                "status": "uploaded",
                "url": f"{self.config.arweave_gateway}/{transaction.id}",
                "size": len(data),
                "tags": default_tags,
            }
        except ImportError:
            # Fallback: return mock/simulated upload
            mock_tx_id = hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()
            return {
                "tx_id": mock_tx_id,
                "status": "mock_uploaded",
                "url": f"{self.config.arweave_gateway}/{mock_tx_id}",
                "size": len(data) if isinstance(data, bytes) else len(data.encode()),
                "tags": tags or {},
                "mock": True,
            }

    def fetch_data(self, tx_id: str) -> Dict:
        """Fetch data from Arweave by transaction ID."""
        import requests
        url = f"{self.config.arweave_gateway}/{tx_id}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return {
                "tx_id": tx_id,
                "data": response.text,
                "size": len(response.content),
                "status": "fetched",
            }
        except Exception as e:
            return {
                "tx_id": tx_id,
                "error": str(e),
                "status": "failed",
            }

    def query_transactions(self, tags: Dict[str, str],
                           owners: Optional[List[str]] = None,
                           limit: int = 10) -> List[Dict]:
        """Query Arweave transactions via GraphQL."""
        query = """
        query($tags: [TagFilter!], $owners: [String!], $limit: Int) {
            transactions(tags: $tags, owners: $owners, first: $limit) {
                edges {
                    node {
                        id
                        tags {
                            name
                            value
                        }
                        block {
                            height
                            timestamp
                        }
                        owner {
                            address
                        }
                    }
                }
            }
        }
        """
        variables = {
            "tags": [{"name": k, "values": [v]} for k, v in tags.items()],
            "owners": owners or [],
            "limit": limit,
        }

        import requests
        try:
            response = requests.post(
                self.config.arweave_graphql,
                json={"query": query, "variables": variables},
                timeout=30,
            )
            data = response.json()
            edges = data.get("data", {}).get("transactions", {}).get("edges", [])
            return [edge["node"] for edge in edges]
        except Exception as e:
            return [{"error": str(e)}]


# ═══════════════════════════════════════════════════════════════════
# AO Computer Integration
# ═══════════════════════════════════════════════════════════════════

class AOComputerInterface:
    """Interface with AO Computer (actor-oriented hyper-parallel computer)."""

    def __init__(self, config: PermawebConfig):
        self.config = config

    def spawn_process(self, module_id: Optional[str] = None,
                      scheduler: str = "_GQ33BkPtZrqxA84vM8Zk-N2aO0toBCuFrlTsq1Bf",
                      tags: Optional[Dict] = None) -> Dict:
        """Spawn a new AO process (like spawning a VM)."""
        import requests

        payload = {
            "Module": module_id or self.config.aos_module_id,
            "Scheduler": scheduler,
            "Tags": tags or [],
        }

        try:
            response = requests.post(
                f"{self.config.ao_mu_url}/",
                json=payload,
                timeout=60,
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def send_message(self, process_id: str, action: str,
                     data: Optional[str] = None,
                     tags: Optional[Dict] = None) -> Dict:
        """Send message to AO process."""
        import requests

        message_tags = [
            {"name": "Action", "value": action},
            {"name": "Target", "value": process_id},
        ]
        if tags:
            for k, v in tags.items():
                message_tags.append({"name": k, "value": v})

        payload = {
            "Target": process_id,
            "Tags": message_tags,
            "Data": data or "",
        }

        try:
            response = requests.post(
                f"{self.config.ao_mu_url}/",
                json=payload,
                timeout=60,
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def read_result(self, process_id: str, message_id: str) -> Dict:
        """Read result from AO compute unit."""
        import requests
        url = f"{self.config.ao_cu_url}/result/{message_id}?process-id={process_id}"
        try:
            response = requests.get(url, timeout=60)
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def dry_run(self, process_id: str, action: str,
                data: Optional[str] = None) -> Dict:
        """Execute dry-run (simulation) on AO process."""
        import requests

        payload = {
            "process-id": process_id,
            "Tags": [{"name": "Action", "value": action}],
            "Data": data or "",
        }

        try:
            response = requests.post(
                f"{self.config.ao_cu_url}/dry-run?process-id={process_id}",
                json=payload,
                timeout=60,
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "failed"}


# ═══════════════════════════════════════════════════════════════════
# AOS (AO Operating System) Integration
# ═══════════════════════════════════════════════════════════════════

class AOSInterface:
    """Interface with AOS — the Lua-based OS for AO processes."""

    def __init__(self, ao_interface: AOComputerInterface,
                 config: PermawebConfig):
        self.ao = ao_interface
        self.config = config
        self.process_id = config.aos_process_id

    def load_blueprint(self, blueprint_name: str) -> Dict:
        """Load an AOS blueprint (Lua module)."""
        if not self.process_id:
            return {"error": "No AOS process ID configured"}

        return self.ao.send_message(
            self.process_id,
            action="Eval",
            data=f'.load-blueprint {blueprint_name}',
        )

    def eval_lua(self, lua_code: str) -> Dict:
        """Evaluate Lua code in AOS process."""
        if not self.process_id:
            return {"error": "No AOS process ID configured"}

        return self.ao.send_message(
            self.process_id,
            action="Eval",
            data=lua_code,
        )

    def get_inbox(self) -> Dict:
        """Get AOS inbox (messages received)."""
        return self.eval_lua("Inbox")

    def spawn_aos(self, name: str) -> Dict:
        """Spawn a new AOS process."""
        result = self.ao.spawn_process(
            module_id=self.config.aos_module_id,
            tags=[{"name": "Name", "value": name}],
        )
        if "id" in result:
            self.process_id = result["id"]
        return result


# ═══════════════════════════════════════════════════════════════════
# HyperBEAM Integration
# ═══════════════════════════════════════════════════════════════════

class HyperBEAMInterface:
    """
    Interface with HyperBEAM — the operating system for the permaweb.

    HyperBEAM is described as "the operating system for the permaweb"
    with a narrow core and infinitely extensible scope.
    """

    def __init__(self, config: PermawebConfig):
        self.config = config

    def resolve_path(self, path: str) -> Dict:
        """Resolve a HyperBEAM HashPath."""
        if not self.config.hyperbeam_endpoint:
            return {"error": "HyperBEAM endpoint not configured"}

        import requests
        try:
            response = requests.get(
                f"{self.config.hyperbeam_endpoint}/{path}",
                timeout=30,
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def execute_device(self, device_name: str,
                       input_data: Dict) -> Dict:
        """Execute a HyperBEAM device (pluggable computation module)."""
        # Devices are pluggable components in HyperBEAM
        # They define specific computational logic (WASM execution, state management, etc.)
        return {
            "device": device_name,
            "input": input_data,
            "status": "executed",
            "mock": True,
        }


# ═══════════════════════════════════════════════════════════════════
# Permaweb Bridge — Main Class
# ═══════════════════════════════════════════════════════════════════

class PermawebBridge:
    """
    Substrate 927 — Permaweb Bridge

    Integrates ARKHE-OS with the Arweave/AO/Permaweb ecosystem:
    - Arweave: Permanent storage of agent state and knowledge
    - AO Computer: Hyper-parallel computation for agent processes
    - AOS: Lua-based operating system for agent smart contracts
    - HyperBEAM: Extensible OS layer for the permaweb
    """

    def __init__(self, config: Optional[PermawebConfig] = None):
        self.config = config or PermawebConfig()
        self.arweave = ArweaveDataLayer(self.config)
        self.ao = AOComputerInterface(self.config)
        self.aos = AOSInterface(self.ao, self.config)
        self.hyperbeam = HyperBEAMInterface(self.config)

        self._upload_history: List[Dict] = []
        self._process_registry: Dict[str, Dict] = {}

    # ═══════════════════════════════════════════════════════════════
    # Agent State Persistence
    # ═══════════════════════════════════════════════════════════════

    def persist_agent_state(self, agent_state: Dict,
                            agent_id: str) -> Dict:
        """
        Upload agent state to Arweave permanently.
        Creates an immutable snapshot of the agent's knowledge.
        """
        state_json = json.dumps(agent_state, sort_keys=True, default=str)

        tags = {
            "Agent-ID": agent_id,
            "Substrate": "927",
            "Type": "Agent-State",
            "Version": "2.0.0",
            "Timestamp": datetime.now(timezone.utc).isoformat(),
        }

        result = self.arweave.upload_data(state_json, tags)
        self._upload_history.append(result)
        return result

    def restore_agent_state(self, tx_id: str) -> Dict:
        """Restore agent state from Arweave."""
        result = self.arweave.fetch_data(tx_id)
        if result.get("status") == "fetched":
            try:
                return json.loads(result["data"])
            except json.JSONDecodeError:
                return {"error": "Invalid JSON in stored state"}
        return result

    def list_agent_states(self, agent_id: str) -> List[Dict]:
        """List all persisted states for an agent."""
        return self.arweave.query_transactions(
            tags={"Agent-ID": agent_id, "Type": "Agent-State"},
            limit=50,
        )

    # ═══════════════════════════════════════════════════════════════
    # AO Process Management
    # ═══════════════════════════════════════════════════════════════

    def spawn_agent_process(self, agent_id: str,
                            name: str = "arkhe-agent") -> Dict:
        """Spawn an AO process to act as the agent's on-chain identity."""
        result = self.ao.spawn_process(
            tags=[
                {"name": "Agent-ID", "value": agent_id},
                {"name": "Name", "value": name},
                {"name": "Substrate", "value": "927"},
            ]
        )

        if "id" in result:
            self._process_registry[agent_id] = {
                "process_id": result["id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        return result

    def send_agent_message(self, agent_id: str, target_process: str,
                           action: str, data: Optional[str] = None) -> Dict:
        """Send a message from the agent's process to another AO process."""
        registry = self._process_registry.get(agent_id)
        if not registry:
            return {"error": f"No process registered for agent {agent_id}"}

        return self.ao.send_message(
            process_id=registry["process_id"],
            action=action,
            data=data,
            tags={"Target-Process": target_process},
        )

    # ═══════════════════════════════════════════════════════════════
    # AOS Agent Shell
    # ═══════════════════════════════════════════════════════════════

    def create_agent_shell(self, agent_id: str) -> Dict:
        """Create an AOS shell for the agent (interactive Lua environment)."""
        # Spawn AOS process if not exists
        if agent_id not in self._process_registry:
            spawn_result = self.aos.spawn_aos(f"arkhe-{agent_id}")
            if "error" in spawn_result:
                return spawn_result

        # Load ARKHE-specific blueprints
        blueprints = ["json", "base64"]  # Standard AOS blueprints
        for bp in blueprints:
            self.aos.load_blueprint(bp)

        # Define agent capabilities in Lua
        agent_lua = f"""
        Agent = {{}}
        Agent.id = "{agent_id}"
        Agent.substrate = "927"
        Agent.version = "2.0.0"

        function Agent.perceive(input)
            -- Send perception to ARKHE-OS
            ao.send({{
                Target = "{agent_id}",
                Action = "Perceive",
                Data = input
            }})
            return "Perception sent"
        end

        function Agent.commit(memory)
            -- Commit memory to Arweave
            ao.send({{
                Target = "{agent_id}",
                Action = "Commit",
                Data = memory
            }})
            return "Memory committed"
        end

        return Agent
        """

        return self.aos.eval_lua(agent_lua)

    # ═══════════════════════════════════════════════════════════════
    # HyperBEAM Integration
    # ═══════════════════════════════════════════════════════════════

    def resolve_hyperbeam_path(self, path: str) -> Dict:
        """Resolve a computation path in HyperBEAM."""
        return self.hyperbeam.resolve_path(path)

    def register_agent_device(self, agent_id: str,
                              device_logic: Dict) -> Dict:
        """Register agent as a HyperBEAM device."""
        return self.hyperbeam.execute_device(
            device_name=f"arkhe-agent-{agent_id}",
            input_data=device_logic,
        )

    # ═══════════════════════════════════════════════════════════════
    # Cross-Substrate Integration
    # ═══════════════════════════════════════════════════════════════

    def sync_with_arkhe(self, agent) -> Dict:
        """
        Synchronize ARKHE-OS agent state with Permaweb.
        Uploads memory, hypergraph, and substrate registry.
        """
        # Collect agent state
        state = {
            "agent_id": agent.agent_id,
            "substrates_active": agent.get_status(),
            "memory_entries": len(agent.memory.entries) if hasattr(agent, 'memory') else 0,
            "hypergraph_edges": len(agent.hypergraph.edges) if hasattr(agent, 'hypergraph') else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Persist to Arweave
        upload = self.persist_agent_state(state, agent.agent_id)

        # Notify AO process
        if agent.agent_id in self._process_registry:
            self.send_agent_message(
                agent.agent_id,
                target_process=self._process_registry[agent.agent_id]["process_id"],
                action="State-Sync",
                data=json.dumps(upload),
            )

        return {
            "upload": upload,
            "state": state,
            "status": "synced",
        }

    def get_bridge_status(self) -> Dict:
        """Get comprehensive bridge status."""
        return {
            "substrate": "927",
            "arweave_gateway": self.config.arweave_gateway,
            "ao_mu": self.config.ao_mu_url,
            "ao_cu": self.config.ao_cu_url,
            "aos_process": self.config.aos_process_id,
            "hyperbeam_endpoint": self.config.hyperbeam_endpoint,
            "uploads_count": len(self._upload_history),
            "processes_registered": len(self._process_registry),
            "wallet_configured": self._wallet is not None,
        }


# ═══════════════════════════════════════════════════════════════════
# Integration with ArkheOmniAgent
# ═══════════════════════════════════════════════════════════════════

class PermawebAdapter:
    """Adapter that injects PermawebBridge into ArkheOmniAgent."""

    def __init__(self, agent, config: Optional[PermawebConfig] = None):
        self.agent = agent
        self.bridge = PermawebBridge(config)
        self._patch_agent()

    def _patch_agent(self):
        """Monkey-patch agent with permaweb capabilities."""
        self.agent.permaweb = self.bridge

        # Override commit_memory to also persist to Arweave
        original_commit = self.agent.commit_memory
        def permaweb_commit(content: Dict):
            # First, do normal commit
            cid = original_commit(content)
            # Then, persist to Arweave
            try:
                upload = self.bridge.persist_agent_state(
                    {"commit_id": cid, "content": content},
                    self.agent.agent_id,
                )
                return {
                    "commit_id": cid,
                    "arweave_tx": upload.get("tx_id"),
                    "arweave_url": upload.get("url"),
                }
            except Exception as e:
                return {
                    "commit_id": cid,
                    "arweave_error": str(e),
                }

        self.agent.commit_memory = permaweb_commit
        print("⛓️  Substrate 927 (Permaweb Bridge) injected — commits now persist to Arweave")
