#!/usr/bin/env python3
"""
Reset SQLite database for testing purposes.

Clears the processing history without modifying database schema.
Creates automatic backup before any modifications.

Usage:
    python reset_database.py          # Interactive mode
    python reset_database.py --yes    # Automated mode (still creates backup, validates)
"""

import sys
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

# Ensure we're in the project root
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

from config import config
from logger import logger


class DatabaseReset:
    """Handle database reset for testing."""

    def __init__(self):
        """Initialize database reset handler."""
        self.db_path = config.DB_PATH
        self.backup_dir = self.db_path.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_path = None
        self.initial_count = 0
        self.final_count = 0

    def get_record_count(self) -> int:
        """Get current record count in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM processed_items")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Error querying database: {e}")
            return -1

    def get_schema_info(self) -> dict:
        """Get database schema information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get tables
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = [row[0] for row in cursor.fetchall()]

                # Get columns for processed_items table
                cursor.execute("PRAGMA table_info(processed_items)")
                columns = [
                    {"name": row[1], "type": row[2]} for row in cursor.fetchall()
                ]

                # Get indices
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='processed_items'"
                )
                indices = [row[0] for row in cursor.fetchall()]

                return {
                    "tables": tables,
                    "columns": columns,
                    "indices": indices,
                }
        except sqlite3.Error as e:
            logger.error(f"Error reading schema: {e}")
            return None

    def create_backup(self) -> bool:
        """Create backup of current database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"processed_items_{timestamp}.db"
            self.backup_path = self.backup_dir / backup_name

            shutil.copy2(self.db_path, self.backup_path)
            print(f"   Backup created: {self.backup_path}")
            return True
        except Exception as e:
            print(f"   [ERROR] Failed to create backup: {e}")
            return False

    def verify_backup(self) -> bool:
        """Verify backup file was created successfully."""
        try:
            if not self.backup_path or not self.backup_path.exists():
                print(f"   [ERROR] Backup file does not exist: {self.backup_path}")
                return False

            # Verify it's a valid SQLite database
            with sqlite3.connect(self.backup_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM processed_items")
                backup_count = cursor.fetchone()[0]

            print(f"   Backup verified: {backup_count} records")
            return True
        except sqlite3.Error as e:
            print(f"   [ERROR] Backup verification failed: {e}")
            return False

    def reset_database(self) -> bool:
        """Clear all records from processed_items table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM processed_items")
                conn.commit()

            self.final_count = self.get_record_count()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error resetting database: {e}")
            print(f"   [ERROR] Failed to reset database: {e}")
            return False

    def verify_schema_unchanged(self, original_schema: dict) -> bool:
        """Verify database schema is unchanged after reset."""
        try:
            new_schema = self.get_schema_info()

            if new_schema is None:
                print("   [ERROR] Could not read schema after reset")
                return False

            # Check tables
            if set(original_schema["tables"]) != set(new_schema["tables"]):
                print("   [ERROR] Table count changed")
                return False

            # Check columns
            if len(original_schema["columns"]) != len(new_schema["columns"]):
                print("   [ERROR] Column count changed")
                return False

            # Check column names and types
            orig_cols = {c["name"]: c["type"] for c in original_schema["columns"]}
            new_cols = {c["name"]: c["type"] for c in new_schema["columns"]}
            if orig_cols != new_cols:
                print("   [ERROR] Column structure changed")
                return False

            # Verify indices (they should be preserved)
            if set(original_schema["indices"]) != set(new_schema["indices"]):
                print("   [WARNING] Index count changed (may be auto-recreated)")

            print("   Schema verification: OK")
            return True
        except Exception as e:
            print(f"   [ERROR] Schema verification failed: {e}")
            return False

    def run_interactive(self) -> bool:
        """Run reset in interactive mode with confirmations."""
        print("\n" + "=" * 80)
        print("RESET DATABASE - TESTING MODE")
        print("=" * 80)

        # Check database exists
        if not self.db_path.exists():
            print(f"\n[ERROR] Database not found: {self.db_path}")
            return False

        print(f"\nDatabase path:")
        print(f"  {self.db_path}")

        # Get initial state
        self.initial_count = self.get_record_count()
        print(f"\nCurrent records: {self.initial_count}")

        # Show warning if DRY_RUN is false
        if not config.DRY_RUN:
            print("\n⚠️  WARNING:")
            print("DRY_RUN is currently set to FALSE")
            print("")
            print("This reset is primarily for testing.")
            print("Ensure this is NOT your production database.")
            response = input("\nContinue? [y/N]: ").strip().lower()
            if response != "y":
                print("[CANCELLED] No changes made.")
                return False

        # Confirm reset
        print("\nThis action will:")
        print("  1. Create a backup of the database")
        print("  2. Delete all processing records")
        print("  3. Keep the database schema unchanged")
        print("")
        response = input("Continue with reset? [y/N]: ").strip().lower()
        if response != "y":
            print("[CANCELLED] No changes made.")
            return False

        # Get original schema
        print("\n1. Capturing schema...")
        original_schema = self.get_schema_info()
        if not original_schema:
            print("   [ERROR] Could not read schema")
            return False
        print("   Schema captured: OK")

        # Create backup
        print("\n2. Creating backup...")
        if not self.create_backup():
            return False

        # Verify backup
        print("\n3. Verifying backup...")
        if not self.verify_backup():
            return False

        # Reset database
        print("\n4. Resetting database...")
        if not self.reset_database():
            print("   [ERROR] Reset failed. Backup preserved at:")
            print(f"   {self.backup_path}")
            return False
        print("   Reset completed: OK")

        # Verify schema unchanged
        print("\n5. Verifying schema...")
        if not self.verify_schema_unchanged(original_schema):
            print("\n   [ERROR] Schema verification failed!")
            print(f"   Backup preserved at: {self.backup_path}")
            return False

        return True

    def run_automated(self) -> bool:
        """Run reset in automated mode (still validates everything)."""
        # Same checks but without interactive prompts
        if not self.db_path.exists():
            print(f"[ERROR] Database not found: {self.db_path}")
            return False

        self.initial_count = self.get_record_count()

        # Get original schema
        original_schema = self.get_schema_info()
        if not original_schema:
            print("[ERROR] Could not read schema")
            return False

        # Create backup
        if not self.create_backup():
            return False

        # Verify backup
        if not self.verify_backup():
            return False

        # Reset database
        if not self.reset_database():
            print(f"[ERROR] Reset failed. Backup at: {self.backup_path}")
            return False

        # Verify schema unchanged
        if not self.verify_schema_unchanged(original_schema):
            print(f"[ERROR] Schema verification failed! Backup at: {self.backup_path}")
            return False

        return True

    def show_summary(self, success: bool) -> None:
        """Show operation summary."""
        print("\n" + "=" * 80)
        if success:
            print("✅ RESET COMPLETED SUCCESSFULLY")
        else:
            print("❌ RESET FAILED")
        print("=" * 80)

        print(f"\nDatabase:")
        print(f"  Path: {self.db_path}")

        print(f"\nRecords:")
        print(f"  Before: {self.initial_count}")
        print(f"  After:  {self.final_count}")
        print(f"  Deleted: {self.initial_count - self.final_count}")

        if self.backup_path and self.backup_path.exists():
            print(f"\nBackup:")
            print(f"  Location: {self.backup_path}")
            print(f"  Size: {self.backup_path.stat().st_size} bytes")

        if success:
            print(f"\nSchema: ✅ Unchanged")
            print(f"\nYou can now run:")
            print(f"  python main.py")
            print(f"to process items from scratch.")

        print("=" * 80 + "\n")


def main():
    """Main entry point."""
    automated = "--yes" in sys.argv

    reset = DatabaseReset()

    if automated:
        success = reset.run_automated()
    else:
        success = reset.run_interactive()

    reset.show_summary(success)
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[CANCELLED] Operation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
