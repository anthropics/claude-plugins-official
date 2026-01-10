# Debugging Skill

> Reusable workflow extracted from dario-debugger expertise.

## Purpose
Systematically investigate and resolve bugs through scientific methodology, root cause analysis, and evidence-based diagnosis across all technology stacks.

## When to Use
- Production incidents and outages
- Intermittent or hard-to-reproduce bugs
- Performance degradation investigation
- Memory leaks and resource exhaustion
- Concurrency issues (race conditions, deadlocks)
- Crash analysis and stack trace interpretation
- Test failures and CI/CD pipeline issues

## Workflow Steps

1. **Reproduce**
   - Confirm issue can be consistently reproduced
   - Document exact reproduction steps
   - Identify required environment/conditions
   - Create minimal reproduction case

2. **Isolate**
   - Narrow down problem space (component, input, timing)
   - Use binary search to eliminate possibilities
   - Identify affected versions (git bisect)
   - Determine scope of impact

3. **Gather Evidence**
   - Collect logs from all relevant systems
   - Capture stack traces and error messages
   - Record metrics and performance data
   - Preserve system state before changes
   - Use distributed tracing for microservices

4. **Hypothesize**
   - Form testable hypotheses about root cause
   - List potential causes ranked by probability
   - Consider symptoms vs actual cause
   - Apply 5 Whys technique

5. **Test Hypotheses**
   - Design experiments to prove/disprove each hypothesis
   - Use debuggers and profilers to validate
   - Check logs for evidence supporting/refuting
   - Eliminate possibilities systematically

6. **Identify Root Cause**
   - Determine fundamental issue (not just symptom)
   - Verify with >95% confidence
   - Document evidence trail
   - Distinguish correlation from causation

7. **Fix & Verify**
   - Implement targeted fix for root cause
   - Verify fix resolves issue
   - Test for regressions
   - Measure impact of fix

8. **Prevent Recurrence**
   - Add regression tests
   - Implement monitoring/alerting
   - Document findings for team
   - Update runbooks if applicable

## Inputs Required
- **Bug description**: Expected vs actual behavior
- **Environment**: OS, versions, configurations, recent changes
- **Reproduction**: Steps to reproduce (if known)
- **Evidence**: Logs, error messages, screenshots, metrics
- **Scope**: When did it start? How many affected?

## Outputs Produced
- **Root Cause Report**: Detailed analysis with evidence
- **Reproduction Steps**: Minimal, reliable reproduction case
- **Fix Recommendations**: Prioritized solutions with trade-offs
- **Prevention Strategy**: How to prevent similar issues
- **Regression Tests**: Tests to verify fix and prevent recurrence

## Bug Classification

### Priority Levels
- **🔴 P0 - Critical**: System down, data loss, security breach - immediate response
- **🟠 P1 - High**: Major feature broken, significant user impact
- **🟡 P2 - Medium**: Feature degraded, workaround exists
- **🟢 P3 - Low**: Minor issue, cosmetic, edge case

## Debugging Techniques

### Scientific Method
1. Observe the problem
2. Form hypothesis about cause
3. Design experiment to test hypothesis
4. Execute test and collect data
5. Analyze results
6. Refine hypothesis or conclude

### Binary Search Debugging
- Divide problem space in half repeatedly
- Test midpoint to eliminate half of possibilities
- Efficient for narrowing down cause

### 5 Whys Technique
```
Problem: API endpoint returns 500 error
Why? Database connection failed
Why? Connection pool exhausted
Why? Connections not being released
Why? Missing finally block in error path
Why? Error handling added without proper resource cleanup
Root Cause: Incomplete error handling refactor
```

### Time-Travel Debugging
- Use tools like rr, UndoDB for execution replay
- Step backwards through execution
- Examine state at any point in time

## Example Usage

```
Input: Production API returning 500 errors intermittently

Workflow Execution:
1. Reproduce: 500 errors occur under load (>100 req/sec)
2. Isolate: Only affects /api/users endpoint, started after v2.3 deploy
3. Evidence: Connection pool at max, slow query log shows 30s timeouts
4. Hypothesis: Query performance degraded with new schema
5. Test: EXPLAIN ANALYZE shows missing index after migration
6. Root Cause: Migration script failed to create user_email_idx index
7. Fix: CREATE INDEX user_email_idx; query time drops to 50ms
8. Prevent: Add index existence check to health endpoint

Output:
ROOT CAUSE: Missing database index after incomplete migration
EVIDENCE: Query plan shows seq scan, migration log shows index creation failed
FIX: Manual index creation, update migration with IF NOT EXISTS
PREVENTION: Added database index monitoring, migration dry-run validation
CONFIDENCE: 99%
```

## Debugging Tools by Platform

### Language-Specific
- **Python**: pdb, ipdb, py-spy, memory_profiler
- **JavaScript/Node**: Chrome DevTools, node --inspect, ndb
- **C/C++/Objective-C**: LLDB, Instruments, AddressSanitizer, Valgrind
- **Java/Kotlin**: JDB, VisualVM, async-profiler
- **Go**: Delve, pprof, race detector

### System-Level
- **Linux**: strace, ltrace, perf, eBPF/bpftrace
- **macOS**: dtrace, Instruments, sample, spindump
- **Network**: Wireshark, tcpdump, mtr, curl -v
- **Container**: docker logs, kubectl logs, container-diff

### Observability
- **Logging**: ELK Stack, Splunk, Datadog
- **Tracing**: Jaeger, Zipkin, OpenTelemetry
- **Metrics**: Prometheus, Grafana, New Relic
- **APM**: Datadog APM, New Relic, Dynatrace

## Log Analysis Patterns

### Error Pattern Recognition
- Stack trace analysis and grouping
- Error rate anomaly detection
- Correlation of errors across services
- Timeline reconstruction

### Distributed Tracing
- Follow request ID across microservices
- Identify latency contributors
- Find error propagation paths
- Visualize service dependencies

## Related Agents
- **dario-debugger** - Full agent with reasoning and tool expertise
- **rex-code-reviewer** - Identifies bug-prone patterns
- **otto-performance-optimizer** - Performance-related debugging
- **thor-quality-assurance-guardian** - Test gap identification
- **luca-security-expert** - Security vulnerability investigation

## ISE Engineering Fundamentals Alignment
- Build applications test-ready with comprehensive logging
- Use correlation IDs for distributed tracing
- Include contextual metadata in all logs
- Log to external systems for analysis
- Blameless post-mortems for systemic improvements
- Code without tests is incomplete - add regression tests
