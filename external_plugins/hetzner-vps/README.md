# Hetzner VPS Plugin

Provision secure, Claude Code-ready Hetzner VPS instances with auto-firewall, fail2ban, and SSH hardening.

## Features

- **One-command provisioning**: `/provision my-server`
- **Security hardened**: UFW firewall, fail2ban, SSH key-only auth
- **Cost-effective**: ~$5/month for a capable dev server
- **Claude Code pre-installed**: Ready to use immediately

## Commands

| Command | Description |
|---------|-------------|
| `/provision <name> [type] [location]` | Create a secure VPS |
| `/status [name]` | Check server status |
| `/destroy <name>` | Delete a server |
| `/cost-estimate [type]` | See pricing before you spend |

## Requirements

- [hcloud CLI](https://github.com/hetznercloud/cli) installed and configured
- Hetzner Cloud API token
- SSH key pair

## Installation

```
/plugin install hetzner-vps@claude-plugin-directory
```

Or install directly from the repository:

```
/plugin marketplace add The-Resonance/claude-code-hetzner-vps
```

## Documentation

Full documentation available at [github.com/The-Resonance/claude-code-hetzner-vps](https://github.com/The-Resonance/claude-code-hetzner-vps)

## License

MIT - A free tool by [Pete Sena](https://linkedin.com/in/petersena) at [The Resonance Labs](https://labs.theresonance.studio)
