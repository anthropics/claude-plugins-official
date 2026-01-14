# Integration Patterns

## Integrating Pseudo-Code with Feature-Dev

### Pattern 1: Requirement Structuring
**When**: At start of Discovery phase
**Application**:
```
Original: "Add user authentication with social login"
Structured: implement_authentication(
  type="oauth",
  providers=["google", "github"],
  session_management="jwt",
  security_level="standard"
)
```

### Pattern 2: Task Decomposition
**When**: During Exploration phase
**Application**:
```
Original: "Build dashboard with real-time updates"
Decomposed:
- create_dashboard_layout(framework="react", responsive=true)
- implement_websocket_connection(protocol="socket.io")
- design_data_flow(pattern="redux", realtime=true)
- add_ui_components(charts=["line", "bar"], widgets=[...])
```

### Pattern 3: Implementation Sequencing
**When**: During Implementation phase
**Application**:
```
Step 1: setup_database_schema(tables=[...])
Step 2: create_api_endpoints(routes=[...])
Step 3: implement_business_logic(services=[...])
Step 4: build_ui_components(pages=[...])
Step 5: integrate_components(flow="...")
```

### Pattern 4: Review Criteria
**When**: During Review phase
**Application**:
```
validate_implementation(
  functional_requirements=[...],
  performance_metrics={latency: "<200ms", throughput: ">1000rps"},
  security_checks=["auth", "input_validation", "sql_injection"],
  code_quality={coverage: ">80%", complexity: "<10"}
)
```

## Cross-Phase Patterns

### State Tracking
Track decisions and progress across phases:
```
track_decision(
  phase="exploration",
  decision="use_graphql_over_rest",
  rationale="...",
  implications=[...]
)
```

### Dependency Management
Identify and manage cross-phase dependencies:
```
manage_dependency(
  from_phase="discovery",
  to_phase="implementation",
  type="api_contract",
  status="defined"
)
