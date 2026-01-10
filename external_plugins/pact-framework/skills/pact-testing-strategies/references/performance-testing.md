# Performance Testing Guide

Comprehensive guide to performance testing including load testing, stress testing,
benchmark patterns, and performance metrics collection.

---

## Performance Testing Types

| Type | Purpose | When to Use |
|------|---------|-------------|
| **Load Testing** | Verify performance under expected load | Before release |
| **Stress Testing** | Find breaking points | Capacity planning |
| **Endurance Testing** | Check for memory leaks, degradation | Long-running services |
| **Spike Testing** | Verify handling of sudden load increases | Flash sale scenarios |
| **Benchmark Testing** | Compare performance between versions | After optimizations |

---

## Load Testing with k6

### Basic Load Test

```javascript
// tests/load/api-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '3m', target: 50 },   // Stay at 50 users
    { duration: '1m', target: 100 },  // Ramp up to 100 users
    { duration: '3m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
    errors: ['rate<0.01'],
  },
};

export default function () {
  // Test the API
  const response = http.get('http://api.example.com/products');

  // Check response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has products': (r) => JSON.parse(r.body).products.length > 0,
  });

  errorRate.add(!success);

  sleep(1); // 1 second between requests per user
}
```

### Realistic User Scenario

```javascript
// tests/load/user-journey.js
import http from 'k6/http';
import { check, group, sleep } from 'k6';

const BASE_URL = 'http://api.example.com';

export const options = {
  vus: 50,
  duration: '10m',
  thresholds: {
    'http_req_duration{name:login}': ['p(95)<1000'],
    'http_req_duration{name:browse}': ['p(95)<500'],
    'http_req_duration{name:checkout}': ['p(95)<2000'],
  },
};

export default function () {
  let authToken;

  group('login', function () {
    const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
      email: `user${__VU}@example.com`,
      password: 'testpassword'
    }), {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'login' }
    });

    check(loginRes, {
      'login successful': (r) => r.status === 200,
    });

    authToken = JSON.parse(loginRes.body).token;
  });

  sleep(2);

  group('browse products', function () {
    const headers = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    };

    // Browse product list
    const listRes = http.get(`${BASE_URL}/products`, {
      headers,
      tags: { name: 'browse' }
    });

    check(listRes, {
      'product list loaded': (r) => r.status === 200,
    });

    // View product detail
    const products = JSON.parse(listRes.body).products;
    if (products.length > 0) {
      const productId = products[Math.floor(Math.random() * products.length)].id;
      http.get(`${BASE_URL}/products/${productId}`, {
        headers,
        tags: { name: 'browse' }
      });
    }
  });

  sleep(3);

  group('checkout', function () {
    const headers = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    };

    // Add to cart
    http.post(`${BASE_URL}/cart/items`, JSON.stringify({
      productId: 'prod_123',
      quantity: 1
    }), { headers, tags: { name: 'checkout' } });

    // Create order
    const orderRes = http.post(`${BASE_URL}/orders`, JSON.stringify({
      paymentMethod: 'card',
      shippingAddress: {
        street: '123 Test St',
        city: 'Test City',
        zip: '12345'
      }
    }), { headers, tags: { name: 'checkout' } });

    check(orderRes, {
      'order created': (r) => r.status === 201,
    });
  });

  sleep(5);
}
```

### Running k6 Tests

```bash
# Run load test
k6 run tests/load/api-load-test.js

# Run with custom VUs and duration
k6 run --vus 100 --duration 5m tests/load/api-load-test.js

# Output results to JSON
k6 run --out json=results.json tests/load/api-load-test.js

# Output to InfluxDB for Grafana dashboards
k6 run --out influxdb=http://localhost:8086/k6 tests/load/api-load-test.js
```

---

## Stress Testing

### Finding Breaking Points

```javascript
// tests/stress/breaking-point.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '2m', target: 400 },
    { duration: '2m', target: 600 },
    { duration: '2m', target: 800 },
    { duration: '2m', target: 1000 },
    { duration: '5m', target: 0 },  // Recovery
  ],
  thresholds: {
    http_req_failed: ['rate<0.1'],  // Allow higher error rate
  },
};

export default function () {
  const response = http.get('http://api.example.com/health');

  check(response, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(0.1);
}
```

### Spike Testing

```javascript
// tests/stress/spike-test.js
export const options = {
  stages: [
    { duration: '1m', target: 10 },    // Normal load
    { duration: '10s', target: 500 },  // Spike!
    { duration: '3m', target: 500 },   // Stay at spike
    { duration: '10s', target: 10 },   // Back to normal
    { duration: '2m', target: 10 },    // Recovery observation
    { duration: '10s', target: 0 },
  ],
};
```

---

## Benchmark Testing

### Code-Level Benchmarks

**JavaScript with benchmark.js:**
```javascript
const Benchmark = require('benchmark');

const suite = new Benchmark.Suite();

// Functions to benchmark
const implementations = {
  forLoop: (arr) => {
    const result = [];
    for (let i = 0; i < arr.length; i++) {
      result.push(arr[i] * 2);
    }
    return result;
  },

  map: (arr) => arr.map(x => x * 2),

  reduce: (arr) => arr.reduce((acc, x) => [...acc, x * 2], []),
};

const testData = Array.from({ length: 10000 }, (_, i) => i);

suite
  .add('for loop', () => implementations.forLoop(testData))
  .add('Array.map', () => implementations.map(testData))
  .add('Array.reduce', () => implementations.reduce(testData))
  .on('cycle', (event) => console.log(String(event.target)))
  .on('complete', function() {
    console.log('Fastest is ' + this.filter('fastest').map('name'));
  })
  .run();

// Output:
// for loop x 12,345 ops/sec
// Array.map x 11,234 ops/sec
// Array.reduce x 1,234 ops/sec
// Fastest is for loop
```

### Database Query Benchmarks

```javascript
// tests/benchmarks/query-performance.js
const { performance } = require('perf_hooks');

async function benchmarkQuery(name, queryFn, iterations = 100) {
  const times = [];

  // Warmup
  for (let i = 0; i < 10; i++) {
    await queryFn();
  }

  // Actual benchmark
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await queryFn();
    times.push(performance.now() - start);
  }

  const avg = times.reduce((a, b) => a + b) / times.length;
  const sorted = [...times].sort((a, b) => a - b);
  const p50 = sorted[Math.floor(times.length * 0.5)];
  const p95 = sorted[Math.floor(times.length * 0.95)];
  const p99 = sorted[Math.floor(times.length * 0.99)];

  console.log(`${name}:`);
  console.log(`  avg: ${avg.toFixed(2)}ms`);
  console.log(`  p50: ${p50.toFixed(2)}ms`);
  console.log(`  p95: ${p95.toFixed(2)}ms`);
  console.log(`  p99: ${p99.toFixed(2)}ms`);

  return { avg, p50, p95, p99 };
}

// Usage
await benchmarkQuery('User lookup by ID', async () => {
  await db.query('SELECT * FROM users WHERE id = $1', [testUserId]);
});

await benchmarkQuery('User lookup by email (indexed)', async () => {
  await db.query('SELECT * FROM users WHERE email = $1', [testEmail]);
});

await benchmarkQuery('Complex join query', async () => {
  await db.query(`
    SELECT u.*, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    GROUP BY u.id
    LIMIT 100
  `);
});
```

---

## Performance Metrics

### Key Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| **Throughput** | Requests per second | Application-specific |
| **Latency (p50)** | Median response time | < 100ms |
| **Latency (p95)** | 95th percentile | < 500ms |
| **Latency (p99)** | 99th percentile | < 1000ms |
| **Error Rate** | Failed requests / total | < 0.1% |
| **Apdex Score** | User satisfaction | > 0.9 |

### Collecting Metrics

**Express Middleware:**
```javascript
const client = require('prom-client');

// Create metrics
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5]
});

const httpRequestTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status_code']
});

// Middleware
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route?.path || req.path;

    httpRequestDuration.observe(
      { method: req.method, route, status_code: res.statusCode },
      duration
    );

    httpRequestTotal.inc({
      method: req.method,
      route,
      status_code: res.statusCode
    });
  });

  next();
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});
```

---

## Performance Test Results Analysis

### Result Interpretation

```
Metric                         Value
================================================================
http_req_duration...............: avg=245.12ms  p(95)=489.23ms
http_req_failed.................: 0.23%
http_reqs.......................: 15234 152.34/s
vus.............................: 100
vus_max.........................: 100

Thresholds:
================================================================
http_req_duration...............: avg<500ms   p(95)<1000ms  ✓ PASS
http_req_failed.................: rate<1%                   ✓ PASS
```

### Performance Report Template

```markdown
# Performance Test Report

## Summary
- **Test Date**: 2024-01-15
- **Environment**: Staging
- **Duration**: 10 minutes
- **Virtual Users**: 100 concurrent

## Results

### Response Times
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Average | 245ms | <500ms | PASS |
| P95 | 489ms | <1000ms | PASS |
| P99 | 856ms | <2000ms | PASS |

### Throughput
- Requests/sec: 152.34
- Total requests: 15,234
- Failed requests: 35 (0.23%)

### Resource Usage
- Peak CPU: 72%
- Peak Memory: 1.8GB
- Database connections: 45/50

## Bottlenecks Identified
1. Database query on `/api/orders/search` - 95th percentile at 1.2s
2. Image processing on `/api/uploads` - Memory spike during concurrent uploads

## Recommendations
1. Add index on `orders.created_at` column
2. Implement async image processing queue
3. Consider connection pool increase to 75

## Comparison to Previous Test
| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| P95 Latency | 612ms | 489ms | -20% |
| Throughput | 128/s | 152/s | +19% |
| Error Rate | 0.45% | 0.23% | -49% |
```

---

## Performance Testing Checklist

### Before Testing
- [ ] Test environment matches production
- [ ] Test data is realistic
- [ ] Baseline metrics established
- [ ] Monitoring in place
- [ ] Test scenarios documented

### During Testing
- [ ] Monitor server resources
- [ ] Watch for errors in logs
- [ ] Track database metrics
- [ ] Observe memory patterns

### After Testing
- [ ] Analyze results against thresholds
- [ ] Document bottlenecks
- [ ] Create optimization plan
- [ ] Compare with previous results
- [ ] Update performance baselines

---

## CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start application
        run: docker-compose up -d

      - name: Wait for app
        run: sleep 30

      - name: Run k6 load test
        uses: grafana/k6-action@v0.3.0
        with:
          filename: tests/load/api-load-test.js
          flags: --out json=results.json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: k6-results
          path: results.json

      - name: Check thresholds
        run: |
          if grep -q '"thresholds":.*"failed":true' results.json; then
            echo "Performance thresholds failed!"
            exit 1
          fi
```
