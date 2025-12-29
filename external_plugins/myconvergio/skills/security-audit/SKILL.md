# Security Audit Skill

> Reusable workflow extracted from luca-security-expert expertise.

## Purpose
Conduct comprehensive security assessments to identify vulnerabilities, assess risks, and provide remediation strategies aligned with OWASP, zero-trust principles, and compliance requirements.

## When to Use
- Pre-release security validation
- Post-incident security review
- Compliance audit preparation (SOC2, ISO27001, GDPR)
- Third-party vendor security assessment
- Penetration testing planning
- Security architecture review
- Incident response and forensics
- Security posture assessment

## Workflow Steps

1. **Scope Definition**
   - Identify assets in scope (applications, infrastructure, data)
   - Define assessment boundaries
   - Establish testing authorization and rules of engagement
   - Identify compliance requirements (GDPR, HIPAA, PCI-DSS)
   - Set testing timeline and constraints

2. **Information Gathering**
   - Map attack surface (endpoints, services, dependencies)
   - Inventory assets and technologies
   - Review architecture and data flow diagrams
   - Collect existing security documentation
   - Identify critical business functions

3. **Threat Modeling**
   - Apply STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
   - Identify threat actors and motivations
   - Map potential attack vectors
   - Prioritize threats by likelihood and impact
   - Create attack scenarios

4. **Vulnerability Assessment**
   - OWASP Top 10 verification
   - Authentication/authorization testing
   - Input validation and injection testing
   - Session management review
   - Cryptography assessment
   - API security testing
   - Infrastructure configuration review
   - Dependency vulnerability scanning

5. **Risk Analysis**
   - Calculate risk scores (Likelihood × Impact)
   - Classify vulnerabilities by severity
   - Assess business impact of each vulnerability
   - Identify compensating controls
   - Prioritize remediation efforts

6. **Penetration Testing** (if authorized)
   - Manual security testing
   - Automated scanning (Burp Suite, OWASP ZAP)
   - Exploitation attempts (in controlled manner)
   - Privilege escalation testing
   - Lateral movement simulation

7. **Remediation Planning**
   - Create prioritized remediation roadmap
   - Provide specific fix recommendations
   - Suggest compensating controls for deferred fixes
   - Estimate effort and timeline
   - Define validation criteria

8. **Reporting & Validation**
   - Document findings with evidence
   - Create executive summary for leadership
   - Provide technical details for developers
   - Re-test after remediation
   - Update security baseline

## Inputs Required
- **Scope**: Systems, applications, infrastructure to assess
- **Authorization**: Written permission for security testing
- **Access**: Test credentials, environment access
- **Documentation**: Architecture diagrams, tech stack, existing security docs
- **Compliance**: Regulatory requirements (GDPR, HIPAA, PCI-DSS, etc.)
- **Constraints**: Testing windows, off-limits areas

## Outputs Produced
- **Security Assessment Report**: Comprehensive findings with evidence
- **Risk Register**: Vulnerabilities ranked by severity and impact
- **Remediation Roadmap**: Prioritized fixes with timelines
- **Executive Summary**: High-level risk overview for leadership
- **Technical Details**: Exploitation steps and fix guidance for developers
- **Compliance Gap Analysis**: Gaps vs required standards

## OWASP Top 10 Checklist

### A01:2021 - Broken Access Control
- [ ] Authentication required for all sensitive operations
- [ ] Authorization checks on server-side (not just client)
- [ ] Principle of least privilege enforced
- [ ] No direct object references without validation
- [ ] CORS configured properly

### A02:2021 - Cryptographic Failures
- [ ] Sensitive data encrypted at rest
- [ ] TLS/HTTPS enforced for data in transit
- [ ] Strong cryptographic algorithms (AES-256, RSA-2048+)
- [ ] Secrets not hardcoded in source code
- [ ] Proper key management and rotation

### A03:2021 - Injection
- [ ] All inputs validated and sanitized
- [ ] Parameterized queries used (no string concatenation)
- [ ] ORM used correctly (no raw SQL injection)
- [ ] Command injection prevention
- [ ] NoSQL injection prevention

### A04:2021 - Insecure Design
- [ ] Threat modeling conducted
- [ ] Security requirements defined
- [ ] Secure design patterns applied
- [ ] Security by design, not as afterthought

### A05:2021 - Security Misconfiguration
- [ ] Default credentials changed
- [ ] Error messages don't leak sensitive info
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] Unnecessary features/services disabled
- [ ] Software up to date with security patches

### A06:2021 - Vulnerable and Outdated Components
- [ ] Dependency inventory maintained (SBOM)
- [ ] Automated vulnerability scanning
- [ ] Regular updates applied
- [ ] No known CVEs in dependencies

### A07:2021 - Identification and Authentication Failures
- [ ] Multi-factor authentication available
- [ ] Password complexity requirements enforced
- [ ] Rate limiting on login attempts
- [ ] Session management secure (timeout, regeneration)
- [ ] Credential stuffing prevention

### A08:2021 - Software and Data Integrity Failures
- [ ] Code signing implemented
- [ ] CI/CD pipeline secured
- [ ] Dependency integrity verified (checksums)
- [ ] Auto-update mechanism secured

### A09:2021 - Security Logging and Monitoring Failures
- [ ] Security events logged (login, access control)
- [ ] Logs protected from tampering
- [ ] Real-time alerting for anomalies
- [ ] Log retention policy defined
- [ ] SIEM integration

### A10:2021 - Server-Side Request Forgery (SSRF)
- [ ] URL validation and allowlisting
- [ ] Network segmentation
- [ ] Disable unused URL schemas
- [ ] Response validation

## Risk Rating Matrix

| Severity | Likelihood | Impact | Action Required |
|----------|-----------|--------|-----------------|
| **Critical** | High + High | Data breach, system compromise | Fix within 24 hours |
| **High** | High + Medium or Medium + High | Significant security risk | Fix within 7 days |
| **Medium** | Medium + Medium or Low + High | Moderate security concern | Fix within 30 days |
| **Low** | Low + Low or Low + Medium | Minor security issue | Fix in next release |

### Risk Calculation
- **Likelihood**: How probable is exploitation? (Low, Medium, High)
- **Impact**: What damage if exploited? (Low, Medium, High, Critical)
- **Risk Score**: Likelihood × Impact = Priority

## Example Usage

```
Input: Pre-release security audit for financial application

Workflow Execution:
1. Scope: Web app + API + Database, PCI-DSS compliance required
2. Information: React frontend, Node.js API, PostgreSQL, AWS hosting
3. Threat Model: STRIDE analysis identifies data exposure and injection risks
4. Vulnerabilities Found:
   - 🔴 CRITICAL: SQL injection in payment endpoint
   - 🔴 CRITICAL: JWT tokens never expire
   - 🟠 HIGH: Weak password policy (6 chars, no complexity)
   - 🟡 MEDIUM: Missing rate limiting on API
   - 🟢 LOW: Security headers not optimized
5. Risk Analysis: SQL injection = HIGH likelihood + CRITICAL impact = P0
6. Remediation:
   - P0: Parameterized queries, token expiration (24h immediate)
   - P1: Password policy update, rate limiting (7 days)
   - P2: Security headers (next sprint)
7. Report: Executive summary + technical details + remediation roadmap
8. Validation: Re-test after fixes applied

Output:
BLOCKED for release - 2 critical vulnerabilities must be fixed first
Remediation roadmap provided with 24h timeline for critical fixes
```

## Security Testing Tools

### Vulnerability Scanning
- **OWASP ZAP**: Web application scanner
- **Burp Suite**: Penetration testing toolkit
- **Nmap**: Network scanning
- **Nikto**: Web server scanner

### Code Analysis
- **SonarQube**: Static code analysis
- **Snyk**: Dependency vulnerability scanning
- **Semgrep**: Pattern-based code scanning
- **GitHub Advanced Security**: CodeQL scanning

### Infrastructure
- **Trivy**: Container/IaC scanning
- **Checkov**: Infrastructure as Code scanner
- **AWS Security Hub**: Cloud security posture
- **Prowler**: AWS security assessment

### Authentication Testing
- **Hydra**: Brute force testing
- **John the Ripper**: Password cracking
- **Hashcat**: Hash cracking

## Zero-Trust Security Principles

1. **Verify Explicitly**: Always authenticate and authorize
2. **Least Privilege Access**: Minimal permissions required
3. **Assume Breach**: Design for compromise, limit blast radius
4. **Microsegmentation**: Isolate workloads and networks
5. **Continuous Monitoring**: Real-time threat detection

## Compliance Frameworks

### GDPR (Data Privacy)
- Data protection by design and by default
- Right to erasure (delete user data)
- Data breach notification (72 hours)
- Privacy impact assessments

### SOC2 (Security Controls)
- Security, availability, processing integrity
- Confidentiality, privacy
- Annual audits required

### ISO27001 (Information Security)
- 114 security controls across 14 domains
- Risk management framework
- Continuous improvement cycle

### PCI-DSS (Payment Card)
- Build and maintain secure network
- Protect cardholder data
- Vulnerability management program
- Regular monitoring and testing

## Related Agents
- **luca-security-expert** - Full agent with reasoning and threat analysis
- **rex-code-reviewer** - Code-level security review
- **baccio-tech-architect** - Security architecture validation
- **marco-devops-engineer** - Infrastructure security
- **elena-legal-compliance-expert** - Regulatory compliance guidance

## ISE Engineering Fundamentals Alignment
- Threat modeling (STRIDE/DREAD) for all features
- Static and dynamic security testing in CI/CD
- Shift-left security: checks early in pipeline
- Dependency scanning automated
- Container security: image scanning, runtime protection
- Secret management: vault-based, no secrets in code
- Security code review checklist for every PR
