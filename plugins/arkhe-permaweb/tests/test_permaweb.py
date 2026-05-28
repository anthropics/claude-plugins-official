import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from permaweb_bridge import PermawebBridge, PermawebConfig, PermawebAdapter

class MockAgent:
    def __init__(self):
        self.agent_id = "test-agent"
    def commit_memory(self, content):
        return "mock_cid"

def test_bridge_upload():
    config = PermawebConfig(wallet_jwk={"kty": "RSA"})
    bridge = PermawebBridge(config)
    res = bridge.arweave.upload_data("test data")
    assert res["status"] in ["mock_uploaded", "uploaded"]

def test_adapter():
    agent = MockAgent()
    adapter = PermawebAdapter(agent)
    assert hasattr(agent, "permaweb")
    res = agent.commit_memory({"test": "data"})
    assert res["commit_id"] == "mock_cid"
    assert "arweave_tx" in res or "arweave_error" in res
