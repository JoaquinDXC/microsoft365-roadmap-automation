#!/usr/bin/env python3
"""Test to verify the main workflow can run in DRY_RUN mode with new config."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_workflow():
    """Test that workflow runs with new DRY_RUN configuration."""
    print("\n" + "=" * 70)
    print("WORKFLOW DRY_RUN TEST")
    print("=" * 70)

    from config import config
    from main_workflow_new import run_automation

    print(f"\nConfiguration:")
    print(f"  DRY_RUN: {config.DRY_RUN}")
    print(f"  EMAIL_MODE: {config.EMAIL_MODE}")
    print(f"  LOG_LEVEL: {config.LOG_LEVEL}")

    print(f"\nStarting workflow...")

    try:
        exit_code = await run_automation()

        if exit_code == 0:
            print(f"\n✅ Workflow completed successfully (exit code: {exit_code})")
            return True
        else:
            print(f"\n❌ Workflow failed (exit code: {exit_code})")
            return False
    except Exception as e:
        print(f"\n❌ Workflow raised exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MAIN WORKFLOW TEST - DRY_RUN MODE")
    print("=" * 70)

    result = asyncio.run(test_workflow())

    print("\n" + "=" * 70)
    if result:
        print("✅ WORKFLOW TEST PASSED")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ WORKFLOW TEST FAILED")
        print("=" * 70)
        sys.exit(1)
