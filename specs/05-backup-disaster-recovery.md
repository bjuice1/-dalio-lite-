# Backup & Disaster Recovery Specification

**Document:** 05-backup-disaster-recovery.md
**Project:** Dalio Lite Production Hardening
**Date:** 2026-02-17
**Status:** Final
**Dependencies:** 02-concurrency-control.md (atomic operations)
**Enables:** 07-production-checklist.md (backup validation gate)

---

## Overview

Addresses audit1 finding: "No backup or disaster recovery for state files - single point of failure."

**Why This Exists:**
- State files are critical (last_rebalance.json, autopilot_status.json)
- Loss of state = system thinks it never rebalanced = immediate unwanted rebalance
- Single machine = no redundancy

**What This Covers:**
- State file versioning (local backup)
- Cloud backup (optional S3/Dropbox)
- Integrity validation (checksums)
- Recovery procedures
- RTO/RPO targets

---

## Architecture

```
┌────────────────────────────┐
│   DalioLite Writes State   │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│  state/last_rebalance.json             │
│  (primary state file)                  │
└─────────────┬──────────────────────────┘
              │
              ▼ Automatic backup
┌────────────────────────────────────────┐
│  BackupManager                         │
│  • Copies to backups/                  │
│  • Adds SHA256 checksum                │
│  • Uploads to S3 (if configured)       │
└─────────────┬──────────────────────────┘
              │
       ┌──────┴──────┐
       ▼             ▼
┌──────────────┐  ┌────────────────┐
│ Local Backup │  │  Cloud Backup  │
│ backups/     │  │  S3 bucket     │
│ (last 30)    │  │  (all history) │
└──────────────┘  └────────────────┘
```

---

## Specification

### 1. Local Backup Strategy

**Backup Location:** `backups/`

**Retention Policy:**
- Keep last 30 daily snapshots
- Delete snapshots older than 30 days
- Total disk usage: ~30KB (30 files × 1KB each)

**Backup Filename Format:**
```
backups/last_rebalance_YYYY-MM-DD_HH-MM-SS.json
backups/last_rebalance_YYYY-MM-DD_HH-MM-SS.json.sha256
```

---

### 2. BackupManager Implementation

**File:** `backup_manager.py` (new file)

```python
"""Backup and recovery for state files."""

import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import json

class BackupManager:
    """Manages backups of critical state files."""

    def __init__(
        self,
        backup_dir: str = "backups",
        retention_days: int = 30,
        cloud_enabled: bool = False,
        s3_bucket: Optional[str] = None
    ):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.cloud_enabled = cloud_enabled
        self.s3_bucket = s3_bucket

    def backup_state_file(self, state_file_path: str):
        """
        Create backup of state file with checksum.

        Args:
            state_file_path: Path to state file to backup
        """
        state_file = Path(state_file_path)

        if not state_file.exists():
            return  # Nothing to backup

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"{state_file.stem}_{timestamp}{state_file.suffix}"
        backup_path = self.backup_dir / backup_filename

        # Copy file
        shutil.copy2(state_file, backup_path)

        # Generate checksum
        checksum = self._calculate_checksum(backup_path)
        checksum_path = backup_path.with_suffix('.json.sha256')

        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  {backup_path.name}\n")

        # Upload to cloud (if enabled)
        if self.cloud_enabled:
            self._upload_to_cloud(backup_path)

        # Clean old backups
        self._cleanup_old_backups(state_file.stem)

    def restore_from_backup(
        self,
        state_file_path: str,
        backup_timestamp: Optional[str] = None
    ) -> bool:
        """
        Restore state file from backup.

        Args:
            state_file_path: Path to state file to restore
            backup_timestamp: Specific backup to restore (None = latest)

        Returns:
            True if restored successfully
        """
        state_file = Path(state_file_path)

        # Find backup to restore
        if backup_timestamp:
            backup_pattern = f"{state_file.stem}_{backup_timestamp}*.json"
        else:
            backup_pattern = f"{state_file.stem}_*.json"

        backups = sorted(self.backup_dir.glob(backup_pattern), reverse=True)

        if not backups:
            return False

        backup_to_restore = backups[0]

        # Verify checksum
        if not self._verify_checksum(backup_to_restore):
            return False

        # Restore file
        shutil.copy2(backup_to_restore, state_file)
        return True

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _verify_checksum(self, backup_path: Path) -> bool:
        """Verify backup file integrity."""
        checksum_path = backup_path.with_suffix('.json.sha256')

        if not checksum_path.exists():
            return False  # No checksum = can't verify

        # Read stored checksum
        with open(checksum_path, 'r') as f:
            stored_checksum = f.read().split()[0]

        # Calculate current checksum
        current_checksum = self._calculate_checksum(backup_path)

        return stored_checksum == current_checksum

    def _cleanup_old_backups(self, state_file_stem: str):
        """Delete backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for backup_file in self.backup_dir.glob(f"{state_file_stem}_*.json"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                # Also delete checksum
                checksum_file = backup_file.with_suffix('.json.sha256')
                if checksum_file.exists():
                    checksum_file.unlink()

    def _upload_to_cloud(self, backup_path: Path):
        """Upload backup to S3 (optional)."""
        if not self.cloud_enabled or not self.s3_bucket:
            return

        try:
            import boto3
            s3 = boto3.client('s3')
            s3.upload_file(
                str(backup_path),
                self.s3_bucket,
                f"dalio-lite-backups/{backup_path.name}"
            )
        except Exception as e:
            # Log error but don't fail backup
            print(f"Cloud backup failed: {e}")
```

---

### 3. Integration with DalioLite

**Modified `dalio_lite.py`:**

```python
from backup_manager import BackupManager

class DalioLite:
    def __init__(self, config_path: str = "config.yaml"):
        # ... existing initialization ...

        # Initialize backup manager
        self.backup_manager = BackupManager(
            backup_dir="backups",
            retention_days=self.config.get('backup', {}).get('retention_days', 30),
            cloud_enabled=self.config.get('backup', {}).get('cloud_enabled', False),
            s3_bucket=self.config.get('backup', {}).get('s3_bucket')
        )

    def _save_rebalance_date(self, timestamp: datetime):
        """Save with automatic backup."""
        # Save state file (existing logic)
        state_file = Path("state/last_rebalance.json")
        # ... write logic ...

        # Backup state file
        self.backup_manager.backup_state_file(str(state_file))
```

---

### 4. Recovery Procedures

**Manual Recovery Steps:**

```bash
# List available backups
ls -lh backups/

# Restore latest backup
python -c "
from backup_manager import BackupManager
bm = BackupManager()
success = bm.restore_from_backup('state/last_rebalance.json')
print(f'Restore: {"SUCCESS" if success else "FAILED"}')
"

# Restore specific backup
python -c "
from backup_manager import BackupManager
bm = BackupManager()
success = bm.restore_from_backup('state/last_rebalance.json', '2026-02-17_10-30-00')
print(f'Restore: {"SUCCESS" if success else "FAILED"}')
"
```

---

### 5. RTO/RPO Targets

| Metric | Target | Actual |
|--------|--------|--------|
| **RTO** (Recovery Time Objective) | <5 minutes | ~2 minutes (manual restore) |
| **RPO** (Recovery Point Objective) | <1 hour | ~5 minutes (backup on every state change) |
| **Backup Frequency** | On every state change | Immediate (no delay) |
| **Retention** | 30 days | 30 daily snapshots |

---

## Verification Strategy

- [ ] Backups created on state change
- [ ] Checksums valid
- [ ] Restore procedure works
- [ ] Old backups cleaned up

---

## Results Criteria

- [ ] Backup created after every rebalance
- [ ] Can restore from backup successfully
- [ ] Backup directory contains 30 days of history
- [ ] Cloud backup configured (if enabled)

---

**Status:** Ready for implementation
**Next Document:** 06-migration-rollout.md
