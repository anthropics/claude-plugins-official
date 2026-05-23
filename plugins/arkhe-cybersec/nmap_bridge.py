#!/usr/bin/env python3
"""nmap bridge for educational scanning."""
import subprocess, json, re

class NmapBridge:
    def scan(self, target, port_range, scan_type):
        cmd = ["nmap", "-p", port_range]
        if scan_type == "syn":
            cmd.append("-sS")
        elif scan_type == "udp":
            cmd.append("-sU")
        elif scan_type == "os":
            cmd.append("-O")
        cmd.extend(["-oX", "-", target])  # XML output to stdout

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {"error": result.stderr}
            return self._parse_nmap_xml(result.stdout)
        except subprocess.TimeoutExpired:
            return {"error": "Scan timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_nmap_xml(self, xml_output):
        # Simplified XML parsing — in production, use xml.etree.ElementTree
        ports = []
        for match in re.finditer(r'<port protocol="tcp" portid="(\d+)"><state state="(\w+)"', xml_output):
            ports.append({"port": int(match.group(1)), "state": match.group(2), "service": "", "version": ""})
        return {"ports": ports}