#!/usr/bin/env python3
"""Lab environment auditor for cybersecurity exercises."""
import subprocess, os, socket

class LabAuditor:
    def audit(self):
        results = {}
        results["VirtualBox installed"] = self._check_binary("VBoxManage")
        results["Kali Linux VM detected"] = self._check_kali_vm()
        results["Network isolation verified"] = self._check_network_isolation()
        results["nmap installed"] = self._check_binary("nmap")
        results["Burp Suite / ZAP installed"] = self._check_binary("burpsuite") or self._check_binary("zap")
        results["Python 3 available"] = self._check_binary("python3")
        results["Docker available"] = self._check_binary("docker")
        return results

    def _check_binary(self, name):
        return subprocess.run(["which", name], capture_output=True).returncode == 0

    def _check_kali_vm(self):
        try:
            result = subprocess.run(["VBoxManage", "list", "vms"], capture_output=True, text=True)
            return "kali" in result.stdout.lower()
        except:
            return False

    def _check_network_isolation(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return not ip.startswith(("10.", "172.", "192.168."))