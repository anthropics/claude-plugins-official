# Performance Optimization Skill

> Reusable workflow extracted from otto-performance-optimizer expertise.

## Purpose
Systematically identify and eliminate performance bottlenecks through data-driven profiling, algorithmic optimization, and infrastructure tuning to achieve scalability and efficiency goals.

## When to Use
- Performance degradation investigation
- Pre-release performance validation
- Scalability planning and capacity assessment
- High-load optimization
- Cost optimization through efficiency
- Database query optimization
- Frontend performance improvement (Core Web Vitals)
- Infrastructure right-sizing

## Workflow Steps

1. **Define Performance Goals**
   - Establish specific, measurable targets (e.g., P95 < 200ms)
   - Define throughput requirements (req/sec, ops/sec)
   - Set resource efficiency goals (CPU, memory, cost)
   - Identify user experience requirements (page load, TTI)
   - Document current baseline metrics

2. **Baseline Measurement**
   - Create reproducible benchmark suite
   - Measure current performance across key metrics
   - Identify representative workloads
   - Document environment configuration
   - Establish measurement methodology

3. **Profile & Analyze**
   - CPU profiling: Identify hot paths and expensive functions
   - Memory profiling: Find allocations, leaks, GC pressure
   - I/O profiling: Measure disk and network bottlenecks
   - Database profiling: Query analysis with EXPLAIN
   - Frontend profiling: Lighthouse, WebPageTest, DevTools

4. **Identify Bottlenecks**
   - Analyze profiling data for actual constraints
   - Distinguish symptoms from root causes
   - Quantify impact of each bottleneck
   - Prioritize by impact/effort ratio
   - Avoid premature optimization (profile first!)

5. **Prioritize Optimizations**
   - **Quick Wins**: High impact, low effort
   - **Strategic**: High impact, medium effort
   - **Incremental**: Medium impact, low effort
   - **Deferred**: Low impact or high complexity
   - Create optimization roadmap

6. **Implement & Measure**
   - Apply optimizations incrementally
   - Measure each change independently
   - Document before/after metrics
   - Verify no functional regressions
   - Track trade-offs (complexity, maintainability)

7. **Validate & Compare**
   - Compare against baseline and goals
   - Run load tests to verify at scale
   - Test edge cases and failure modes
   - Check resource utilization under load
   - Measure cost impact

8. **Monitor & Prevent Regression**
   - Set up performance monitoring
   - Create alerting for degradation
   - Add performance tests to CI/CD
   - Document optimization decisions
   - Regular performance review cadence

## Inputs Required
- **Performance targets**: Specific latency, throughput, resource goals
- **Current metrics**: Baseline performance measurements
- **Workload profile**: Traffic patterns, peak loads, data volumes
- **Constraints**: Budget, timeline, acceptable trade-offs
- **Environment**: Production specs, infrastructure configuration

## Outputs Produced
- **Profiling Report**: Flame graphs, hot spots, bottleneck analysis
- **Optimization Roadmap**: Prioritized improvements with expected impact
- **Before/After Benchmarks**: Quantified performance improvements
- **Capacity Plan**: Scalability analysis and resource projections
- **Monitoring Setup**: Metrics, dashboards, and alerting configuration
- **Cost Analysis**: Infrastructure cost savings from optimization

## Profiling Tools by Category

### CPU Profiling
- **Python**: cProfile, py-spy, line_profiler
- **JavaScript/Node**: Chrome DevTools, clinic.js, 0x, node --prof
- **C/C++/Objective-C**: Instruments, perf, Valgrind, Intel VTune
- **Java/Kotlin**: JProfiler, async-profiler, JFR, VisualVM
- **Go**: pprof, trace, benchstat

### Memory Profiling
- **Python**: memory_profiler, tracemalloc, objgraph
- **JavaScript/Node**: Chrome DevTools heap profiler, node --heap-prof
- **C/C++**: Valgrind, AddressSanitizer, LeakSanitizer
- **Java**: VisualVM, JProfiler, heap dumps
- **Go**: pprof heap profile

### Database Profiling
- **PostgreSQL**: EXPLAIN ANALYZE, pg_stat_statements
- **MySQL**: EXPLAIN, slow query log, pt-query-digest
- **MongoDB**: explain(), profiler, slow query log
- **Redis**: SLOWLOG, redis-cli --latency

### System Profiling
- **Linux**: perf, eBPF/bpftrace, sysstat, iotop
- **macOS**: Instruments, dtrace, fs_usage
- **Network**: Wireshark, tcpdump, netstat, ss

## Optimization Strategies Catalog

### Algorithmic Optimization
- **Complexity Reduction**: O(n²) → O(n log n) → O(n)
- **Data Structure Selection**: Array vs Hash vs Tree
- **Caching Results**: Memoization, computed properties
- **Lazy Evaluation**: Compute only when needed
- **Batch Processing**: N+1 → single batch operation

### Database Optimization
- **Query Optimization**: Rewrite inefficient queries
- **Index Strategy**: B-tree, hash, partial, covering indexes
- **Connection Pooling**: Optimal pool size (typically 2-10× CPU cores)
- **Query Batching**: Combine multiple queries
- **Denormalization**: Trade-off for read performance
- **Caching**: Redis/Memcached for hot data

### Frontend Optimization
- **Core Web Vitals**:
  - LCP (Largest Contentful Paint) < 2.5s
  - FID (First Input Delay) < 100ms
  - CLS (Cumulative Layout Shift) < 0.1
- **Bundle Optimization**: Code splitting, tree shaking, lazy loading
- **Asset Optimization**: Image compression, WebP, responsive images
- **Caching**: Service workers, Cache-Control headers
- **CDN**: Geographic distribution, edge caching

### Backend Optimization
- **API Response**: Reduce payload size, compression
- **Async Processing**: Queue long-running tasks
- **Connection Reuse**: HTTP keep-alive, connection pooling
- **Caching Layers**: Application cache, CDN, database cache
- **Concurrency**: Proper use of async/await, workers

### Infrastructure Optimization
- **Auto-Scaling**: Horizontal and vertical scaling policies
- **Right-Sizing**: Match resources to actual usage
- **Load Balancing**: Distribute traffic efficiently
- **Geographic Distribution**: Multi-region for global users
- **Resource Limits**: Prevent resource exhaustion

## Performance Metrics Checklist

### Latency Metrics
- [ ] P50 (median) latency measured
- [ ] P95 latency (95th percentile) tracked
- [ ] P99 latency (worst case) monitored
- [ ] Max latency identified

### Throughput Metrics
- [ ] Requests per second (RPS) capacity known
- [ ] Transactions per second (TPS) measured
- [ ] Concurrent users handled documented
- [ ] Peak load capacity established

### Resource Metrics
- [ ] CPU utilization tracked (target: <70% at peak)
- [ ] Memory usage monitored (avoid swapping)
- [ ] Disk I/O measured (IOPS, throughput)
- [ ] Network bandwidth utilization tracked

### User Experience Metrics
- [ ] Time to First Byte (TTFB) < 200ms
- [ ] First Contentful Paint (FCP) < 1.8s
- [ ] Time to Interactive (TTI) < 3.8s
- [ ] Total Page Load < 3s

## Example Usage

```
Input: API endpoint /api/users slow (P95: 3.2s), target: <200ms

Workflow Execution:
1. Goal: Reduce P95 latency to <200ms, increase throughput 5x
2. Baseline: Current P95 = 3.2s, 50 req/sec max
3. Profile:
   - Flame graph shows 80% time in database query
   - Query: SELECT * FROM users JOIN orders... (full table scan)
   - 5M users table, no index on email column
4. Bottleneck: Missing index causing seq scan, N+1 query pattern
5. Prioritize:
   - 🔴 Quick Win: Add index on users.email
   - 🔴 Quick Win: Fix N+1 with JOIN optimization
   - 🟡 Strategic: Add Redis cache for user profile
6. Implement:
   - CREATE INDEX idx_users_email ON users(email)
   - Rewrite query with proper JOIN
   - Add Redis cache (TTL: 5min)
7. Validate:
   - P95 latency: 3.2s → 45ms (98.6% improvement)
   - Throughput: 50 → 400 req/sec (8x improvement)
   - Database CPU: 85% → 12%
8. Monitor: Added Grafana dashboard, alert if P95 > 200ms

Output:
✅ Performance goal achieved: P95 = 45ms (target: <200ms)
✅ Throughput exceeded: 400 req/sec (target: 250 req/sec)
✅ Cost reduced: 6 → 2 database instances ($2,400/month savings)
```

## Optimization Anti-Patterns to Avoid

### Premature Optimization
- ❌ Optimizing without profiling data
- ✅ Profile first, identify actual bottleneck, then optimize

### Micro-Optimizations
- ❌ Focusing on saving nanoseconds while ignoring second-long delays
- ✅ Focus on bottlenecks with measurable user impact

### Benchmark Gaming
- ❌ Optimizing for artificial benchmarks not real workloads
- ✅ Use representative production-like workloads

### Complexity Creep
- ❌ Adding complexity for marginal 2% gains
- ✅ Balance performance with maintainability

### Ignoring Trade-offs
- ❌ Not considering memory usage, code complexity, maintainability
- ✅ Document trade-offs explicitly

## Performance Budget Template

```markdown
## Performance Budget: [Feature/Page Name]

### Targets
- P95 Latency: < [target]ms
- Throughput: > [target] req/sec
- Page Load: < [target]s
- Bundle Size: < [target]KB
- CPU Usage: < [target]%
- Memory Usage: < [target]MB

### Current Metrics
- P95 Latency: [current]ms
- Throughput: [current] req/sec
- Status: ✅ Within budget / ❌ Exceeds budget

### Action Required
[If budget exceeded, optimization plan]
```

## Related Agents
- **otto-performance-optimizer** - Full agent with profiling expertise
- **baccio-tech-architect** - Architecture-level performance design
- **dario-debugger** - Performance-related bug investigation
- **omri-data-scientist** - ML model inference optimization
- **marco-devops-engineer** - Infrastructure performance tuning

## ISE Engineering Fundamentals Alignment
- Leverage observability (metrics, tracing) for performance
- Load testing validates behavior under peak load
- Performance testing measures against baselines
- Stress testing finds breaking points
- Design for NFRs: performance SLAs defined upfront
- Parametrize configurations for easy tuning
- Log operation durations on critical paths
- Test under realistic load, not just happy-path
