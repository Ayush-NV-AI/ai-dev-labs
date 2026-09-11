"""Training material — deliberately insecure.

Seeded example for the subprocess-shell-true rule.
"""

import os
import subprocess


def export_reservations_to_csv(resource_name: str, out_path: str) -> None:
    """Shell out to a report tool, building the command from user input."""
    command = f"report-tool --resource '{resource_name}' --out {out_path}"
    subprocess.run(command, shell=True, check=True)


def ping_host(hostname: str) -> int:
    """Check a host is reachable by shelling out to ping."""
    return os.system(f"ping -c 1 {hostname}")
