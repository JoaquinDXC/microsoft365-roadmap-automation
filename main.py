#!/usr/bin/env python3
"""
Main entry point for M365 Roadmap Automation.
Orchestrates the entire workflow: RSS fetch → filter → AI processing → email send.
"""

import asyncio
import sys
import os
from pathlib import Path

# Ensure we're in the project root (for .env loading)
project_root = Path(__file__).parent
os.chdir(project_root)

# Add src to path
sys.path.insert(0, str(project_root / "src"))

from main_workflow_new import run_automation


async def main():
    exit_code = await run_automation()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
