"""Backup and recovery for state files."""

import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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

        logger.info(f"✓ State backup created: {backup_path.name}")

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
            logger.error(f"No backups found for {state_file_path}")
            return False

        backup_to_restore = backups[0]

        # Verify checksum
        if not self._verify_checksum(backup_to_restore):
            logger.error(f"Checksum verification failed for {backup_to_restore}")
            return False

        # Restore file
        shutil.copy2(backup_to_restore, state_file)
        logger.info(f"✓ State restored from backup: {backup_to_restore.name}")
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
            logger.info(f"✓ Backup uploaded to S3: {self.s3_bucket}")
        except Exception as e:
            # Log error but don't fail backup
            logger.warning(f"Cloud backup failed: {e}")
