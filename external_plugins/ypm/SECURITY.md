# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in YPM, please report it by:

1. **Email**: Send details to the maintainer (contact info in README.md)
2. **GitHub Security Advisory**: Use [GitHub's private vulnerability reporting](https://github.com/signalcompose/YPM/security/advisories/new)

**Please do not report security vulnerabilities through public GitHub issues.**

We will respond within 48 hours and provide a timeline for addressing the issue.

---

## Security Considerations

### 1. Prompt Injection Risks

YPM reads documentation files (CLAUDE.md, README.md, docs/) from monitored projects. This creates a potential attack vector:

**Risk**: Malicious actors could include harmful instructions in project documentation to manipulate YPM's behavior.

**Mitigation**:
- YPM has strict read-only principles for monitored projects
- Only YPM's own files (PROJECT_STATUS.md, config.yml) can be modified
- See [CLAUDE.md](CLAUDE.md) for detailed prompt injection protection guidelines

**Best Practices**:
- ✅ Only monitor projects from trusted sources
- ✅ Review documentation before adding third-party projects to monitoring
- ✅ Use `config.yml` exclude patterns for untrusted projects
- ❌ Do not blindly monitor cloned repositories from unknown sources

### 2. Git History and Sensitive Information

**Important**: YPM's repository was cleaned of all previous Git history to remove potentially sensitive information (config.yml, PROJECT_STATUS.md).

**For Users**:
- Never commit `config.yml` or `PROJECT_STATUS.md` to public repositories
- These files are Git-ignored by default
- Review `.gitignore` before making your fork public

### 3. Protected Files

The following files contain user-specific or potentially sensitive information and are excluded from Git:

- `config.yml` - Contains directory paths
- `PROJECT_STATUS.md` - May contain project details
- `HANDOFF.md` - Internal handoff documentation

---

## Contribution Security

### Pull Request Guidelines

To protect against malicious contributions:

1. **Code Review Requirements**
   - All PRs require review from a maintainer
   - No direct pushes to `main` branch
   - Automated checks must pass before merge

2. **Suspicious Patterns to Watch For**
   - Modifications to `.claude/settings.json` that expand file access
   - Changes to CLAUDE.md that weaken security restrictions
   - Addition of scripts that read/write outside project scope
   - Network requests to external URLs
   - File operations on parent directories (`../`)

3. **Documentation Changes**
   - Be cautious of documentation that includes instructions to Claude Code
   - Verify that CLAUDE.md changes don't compromise read-only principles
   - Ensure new instructions don't expand YPM's scope beyond monitoring

### Automated Security Checks

We recommend the following GitHub Actions (to be implemented):

- [ ] CodeQL analysis for Python code
- [ ] Dependency vulnerability scanning
- [ ] Branch protection rules for `main`
- [ ] Required status checks before merge
- [ ] Review requirement from code owners

---

## Repository Settings (Maintainer Checklist)

### Branch Protection Rules

Configure the following for the `main` branch:

- ✅ Require pull request reviews before merging (at least 1)
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Do not allow bypassing the above settings
- ✅ Restrict who can push to matching branches (maintainers only)

### Security Features

Enable the following GitHub repository settings:

- ✅ Private vulnerability reporting
- ✅ Dependency graph
- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Code scanning (CodeQL)

### Access Control

- Limit write access to trusted maintainers only
- Use branch protection to prevent force pushes
- Enable 2FA for all collaborators

---

## Security Updates

This project follows semantic versioning. Security patches will be released as:

- **Patch version** (x.x.X) - Security fixes for the current version
- **Minor version** (x.X.x) - Security improvements with backward compatibility
- **Major version** (X.x.x) - Security-related breaking changes

---

## Known Limitations

1. **Claude Code Trust Model**: YPM relies on Claude Code correctly interpreting instructions in CLAUDE.md. While safeguards are in place, determined attackers with control over monitored project documentation could attempt prompt injection.

2. **File System Access**: YPM has read access to monitored directories. Ensure you trust all projects in your monitoring scope.

3. **No Sandboxing**: YPM runs with the same permissions as the user. There is no isolated sandbox environment.

---

## Security Best Practices for Users

### 1. Carefully Choose Monitored Projects

Only add projects to `config.yml` that you:
- Own personally
- Trust completely (e.g., from verified organizations)
- Have manually reviewed the documentation

### 2. Regular Audits

Periodically review:
- `config.yml` monitoring targets
- Recent changes to monitored projects' CLAUDE.md files
- YPM's own codebase updates

### 3. Limit Scope

Use specific patterns in `config.yml` rather than wildcards when possible:

```yaml
# Less secure (monitors everything)
patterns:
  - "*"

# More secure (explicit projects only)
patterns:
  - "my-app"
  - "my-library"
  - "specific-project"
```

### 4. Use Separate Monitoring Instances

For untrusted or experimental projects:
- Create a separate YPM instance
- Use a dedicated config.yml
- Run in an isolated directory

---

## Contact

For security concerns, please contact:

- **GitHub**: [@dropcontrol](https://github.com/dropcontrol)
- **Website**: [hiroshiyamato.com](https://hiroshiyamato.com/)

---

**Last Updated**: 2025-10-16
