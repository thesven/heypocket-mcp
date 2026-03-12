from __future__ import annotations

import os
import subprocess
import sys


def test_cli_help_stdio() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [sys.executable, "-m", "heypocket_mcp", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0
    assert "stdio" in result.stdout
    assert "http" in result.stdout

