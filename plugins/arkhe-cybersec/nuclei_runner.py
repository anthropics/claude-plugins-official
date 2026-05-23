#!/usr/bin/env python3
"""Nuclei runner stub for testing web vulnerabilities."""

def run_educational_templates(url, test_type):
    return [
        {
            "name": f"Dummy {test_type} finding",
            "severity": "low",
            "remediation": "This is a dummy remediation for educational purposes."
        }
    ]
