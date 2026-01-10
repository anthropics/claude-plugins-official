# Architecture Design Skill

> Reusable workflow extracted from baccio-tech-architect expertise.

## Purpose
Design scalable, maintainable, and secure system architectures using proven patterns, with emphasis on Domain-Driven Design, Clean Architecture, and cloud-native principles.

## When to Use
- New system or feature architecture design
- Legacy system modernization planning
- Technology stack selection
- Scalability assessment and planning
- Microservices architecture design
- Cloud migration strategy
- Technical debt evaluation
- Architecture review and validation

## Workflow Steps

1. **Requirements Analysis**
   - Gather functional requirements
   - Define non-functional requirements (NFRs)
   - Identify constraints (budget, timeline, team skills)
   - Understand scale requirements (users, data, traffic)
   - Document compliance requirements

2. **Domain Modeling**
   - Apply Domain-Driven Design (DDD)
   - Identify bounded contexts
   - Define domain entities and aggregates
   - Map ubiquitous language
   - Establish context boundaries

3. **Architecture Pattern Selection**
   - Evaluate architecture styles (monolith, microservices, serverless)
   - Choose appropriate patterns (CQRS, Event Sourcing, Saga)
   - Apply Clean Architecture principles
   - Define layers and dependencies
   - Establish communication patterns

4. **Technology Stack Selection**
   - Evaluate technology options against requirements
   - Consider team expertise and learning curve
   - Assess vendor lock-in risks
   - Evaluate cost implications
   - Check compliance with organizational standards

5. **Scalability & Performance Design**
   - Design for horizontal and vertical scaling
   - Plan caching strategy (application, CDN, database)
   - Define load balancing approach
   - Design database sharding/partitioning if needed
   - Plan for geographic distribution

6. **Security Architecture**
   - Apply Zero-Trust principles
   - Design authentication/authorization
   - Plan data encryption (at rest, in transit)
   - Define security boundaries
   - Implement defense in depth

7. **Observability Design**
   - Design logging strategy (structured logging)
   - Plan metrics collection (Prometheus, CloudWatch)
   - Define distributed tracing approach
   - Create monitoring dashboards
   - Establish alerting thresholds

8. **Documentation & ADRs**
   - Create Architecture Decision Records (ADRs)
   - Document architecture diagrams (C4 model)
   - Define API contracts and versioning
   - Document deployment architecture
   - Create capacity planning guidelines

## Inputs Required
- **Business requirements**: What problem are we solving?
- **Non-functional requirements**: Performance, security, compliance needs
- **Scale expectations**: Current and projected users, data volume, traffic
- **Constraints**: Budget, timeline, team skills, existing systems
- **Compliance**: Regulatory requirements (GDPR, HIPAA, SOC2, etc.)

## Outputs Produced
- **Architecture Blueprint**: Comprehensive system design documentation
- **ADR (Architecture Decision Records)**: Documented design decisions with rationale
- **Technology Stack Recommendation**: Selected technologies with justification
- **Scalability Plan**: Scaling strategy with capacity planning
- **Security Architecture**: Security patterns and implementation guide
- **Deployment Diagrams**: Infrastructure and deployment architecture
- **Migration Roadmap**: Phased implementation or migration plan

## Architecture Patterns Catalog

### Architectural Styles
- **Monolithic Architecture**: Single deployable unit, simpler but less scalable
- **Microservices**: Independent services, complex but highly scalable
- **Serverless**: Event-driven, pay-per-use, highly elastic
- **Modular Monolith**: Compromise between monolith and microservices
- **Service-Oriented Architecture (SOA)**: Enterprise service bus pattern

### Design Patterns
- **Domain-Driven Design (DDD)**: Bounded contexts, aggregates, entities
- **Clean Architecture**: Dependency inversion, layers, boundaries
- **CQRS**: Command Query Responsibility Segregation
- **Event Sourcing**: Event log as source of truth
- **Saga Pattern**: Distributed transactions
- **API Gateway**: Single entry point for clients
- **Backend for Frontend (BFF)**: API per client type

### Communication Patterns
- **Synchronous**: REST, GraphQL, gRPC
- **Asynchronous**: Message queues, event streams (Kafka, RabbitMQ)
- **Pub/Sub**: Event-driven communication
- **Request-Reply**: RPC-style communication

## Trade-Off Analysis Template

```markdown
## Decision: [Technology/Pattern Choice]

### Context
[What problem are we solving? What are the constraints?]

### Options Considered
1. **Option A**: [Description]
   - Pros: [Benefits]
   - Cons: [Drawbacks]
   - Cost: [Time/Money/Complexity]

2. **Option B**: [Description]
   - Pros: [Benefits]
   - Cons: [Drawbacks]
   - Cost: [Time/Money/Complexity]

### Decision
[Chosen option with rationale]

### Consequences
- Positive: [Expected benefits]
- Negative: [Known drawbacks]
- Mitigation: [How we address drawbacks]
```

## Non-Functional Requirements Checklist

### Performance
- [ ] Response time SLA defined (e.g., P95 < 200ms)
- [ ] Throughput requirements specified
- [ ] Scalability targets identified
- [ ] Performance testing strategy defined

### Availability
- [ ] Uptime SLA defined (e.g., 99.9%)
- [ ] Redundancy strategy planned
- [ ] Failover mechanisms designed
- [ ] Disaster recovery plan created

### Security
- [ ] Authentication mechanism selected
- [ ] Authorization model defined
- [ ] Data encryption strategy planned
- [ ] Security boundaries identified
- [ ] Penetration testing planned

### Observability
- [ ] Logging strategy defined
- [ ] Metrics collection planned
- [ ] Distributed tracing implemented
- [ ] Dashboards designed
- [ ] Alerting configured

### Maintainability
- [ ] Code organization standards defined
- [ ] Testing strategy established
- [ ] Documentation requirements specified
- [ ] Deployment automation planned

## Example Usage

```
Input: Design architecture for e-commerce platform
Expected: 10K concurrent users, 99.9% uptime, PCI DSS compliant

Workflow Execution:
1. Requirements: User accounts, product catalog, shopping cart, checkout
2. Domain Model: User, Product, Cart, Order bounded contexts
3. Pattern: Microservices with API Gateway, Event-driven for orders
4. Tech Stack:
   - Backend: Node.js + TypeScript
   - Database: PostgreSQL (products/users), Redis (cart/sessions)
   - Message Bus: Kafka for order events
   - Cloud: AWS with ECS + RDS + ElastiCache
5. Scalability: Horizontal scaling via ECS, database read replicas, CDN
6. Security: OAuth2 + JWT, PCI-compliant payment gateway, encryption at rest
7. Observability: CloudWatch logs/metrics, X-Ray tracing, Grafana dashboards
8. Documentation: ADRs created, C4 diagrams, API documentation

Output: Comprehensive architecture blueprint with ADRs and diagrams
```

## Tech Stack Selection Criteria

### Evaluation Matrix
| Criterion | Weight | Option A | Option B | Option C |
|-----------|--------|----------|----------|----------|
| Team expertise | 20% | 8/10 | 5/10 | 6/10 |
| Scalability | 25% | 9/10 | 7/10 | 8/10 |
| Cost | 15% | 6/10 | 9/10 | 7/10 |
| Community support | 10% | 9/10 | 8/10 | 6/10 |
| Compliance fit | 15% | 8/10 | 7/10 | 9/10 |
| Vendor lock-in | 15% | 7/10 | 5/10 | 8/10 |
| **Total** | 100% | **7.9** | **6.9** | **7.5** |

## Related Agents
- **baccio-tech-architect** - Full agent with reasoning and decision-making
- **luca-security-expert** - Security architecture validation
- **dan-engineering-gm** - Engineering leadership alignment
- **marco-devops-engineer** - Infrastructure and deployment architecture
- **domik-mckinsey-strategic-decision-maker** - Strategic technology decisions

## ISE Engineering Fundamentals Alignment
- Document Architecture Decision Records (ADRs)
- Apply proven design patterns
- Conduct trade studies before major decisions
- Use technical spikes for high-risk unknowns
- Design for NFRs from day one (availability, scalability, security)
- Infrastructure as Code for all infrastructure
- GitOps workflows for deployments
