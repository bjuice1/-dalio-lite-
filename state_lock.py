"""State locking mechanism for concurrency control."""

from filelock import FileLock, Timeout
from pathlib import Path
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class StateLockManager:
    """
    Manages file-based locking for Dalio Lite state operations.

    Prevents race conditions between AutoPilot and Dashboard by ensuring
    only one process can access state files at a time.

    Usage:
        with state_lock_manager.acquire():
            # Safe to read/write state files
            state = load_state()
            modify_state(state)
            save_state(state)
    """

    def __init__(self, lock_file_path: str = "state/dalio_lite.lock", timeout: int = 30):
        """
        Initialize lock manager.

        Args:
            lock_file_path: Path to lock file (created if doesn't exist)
            timeout: Seconds to wait for lock before raising error (default: 30)
        """
        self.lock_file_path = Path(lock_file_path)
        self.timeout = timeout
        self.lock: Optional[FileLock] = None

        # Ensure lock file directory exists
        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create FileLock instance
        self.lock = FileLock(self.lock_file_path, timeout=self.timeout)

        logger.debug(f"StateLockManager initialized: {self.lock_file_path}")

    @contextmanager
    def acquire(self):
        """
        Acquire lock as context manager.

        Blocks until lock is available or timeout expires.
        Automatically releases lock when context exits (even on exception).

        Raises:
            RuntimeError: If lock can't be acquired within timeout period

        Example:
            with lock_manager.acquire():
                # Critical section - only one process can be here
                state = read_state()
                modify_state()
                write_state()
        """
        logger.info("Attempting to acquire state lock...")

        try:
            with self.lock.acquire(timeout=self.timeout):
                logger.info("✓ State lock acquired")
                yield
                logger.info("State lock released")

        except Timeout:
            logger.error(
                f"Failed to acquire state lock after {self.timeout}s. "
                f"Another process may be stuck or long-running operation in progress."
            )
            raise RuntimeError(
                f"Could not acquire state lock after {self.timeout} seconds. "
                f"Another Dalio Lite process may be running. "
                f"Check logs or kill stuck processes."
            )

        except Exception as e:
            logger.error(f"Unexpected error acquiring lock: {e}")
            raise

    def is_locked(self) -> bool:
        """
        Check if lock is currently held (by any process).

        Returns:
            True if lock is held, False if available

        Note: This is a point-in-time check. Lock state may change immediately
        after this call returns.
        """
        return self.lock.is_locked

    def force_release(self):
        """
        Forcefully release lock (use with extreme caution).

        Only use this for administrative cleanup (e.g., after process crash).
        Do NOT call this during normal operation.
        """
        if self.lock.is_locked:
            logger.warning("Force-releasing state lock (administrative action)")
            self.lock.release(force=True)
        else:
            logger.info("Lock not held, nothing to release")
