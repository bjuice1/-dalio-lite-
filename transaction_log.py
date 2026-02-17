"""Transaction logging for rebalance operations."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import uuid


@dataclass
class TransactionLogEntry:
    """Single transaction log entry."""
    transaction_id: str
    timestamp: str
    operation: str  # "rebalance", "force_rebalance", "autopilot_check"
    target_orders: Dict[str, float]  # ticker -> amount_usd
    executed_orders: List[Dict]  # List of OrderResult dicts
    status: str  # "completed", "partial", "failed", "aborted"
    error_message: Optional[str] = None
    reconciliation_notes: Optional[str] = None


class TransactionLogger:
    """
    Logs all rebalancing operations for audit trail.

    Purpose:
    - Track what was intended vs what actually executed
    - Provide audit trail for financial transactions
    - Enable reconciliation after partial failures
    - Support debugging and root cause analysis
    """

    def __init__(self, log_dir: str = "state/transactions"):
        """
        Initialize transaction logger.

        Args:
            log_dir: Directory to store transaction logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def begin_transaction(
        self,
        operation: str,
        target_orders: Dict[str, float]
    ) -> str:
        """
        Begin a new transaction.

        Args:
            operation: Operation type (e.g., "rebalance")
            target_orders: Intended orders {ticker: amount_usd}

        Returns:
            transaction_id: UUID for this transaction
        """
        transaction_id = str(uuid.uuid4())

        entry = TransactionLogEntry(
            transaction_id=transaction_id,
            timestamp=datetime.now().isoformat(),
            operation=operation,
            target_orders=target_orders,
            executed_orders=[],
            status="in_progress"
        )

        self._save_log(entry)
        return transaction_id

    def record_order(
        self,
        transaction_id: str,
        order_result: Dict
    ):
        """
        Record executed order in transaction log.

        Args:
            transaction_id: Transaction UUID
            order_result: Result of order execution (dict format)
        """
        entry = self._load_log(transaction_id)

        # Append order result with timestamp
        order_with_timestamp = {
            **order_result,
            'timestamp': datetime.now().isoformat()
        }
        entry.executed_orders.append(order_with_timestamp)

        self._save_log(entry)

    def complete_transaction(
        self,
        transaction_id: str,
        status: str,  # "completed", "partial", "failed"
        reconciliation_notes: Optional[str] = None
    ):
        """
        Mark transaction as complete.

        Args:
            transaction_id: Transaction UUID
            status: Final status
            reconciliation_notes: Notes from reconciliation check
        """
        entry = self._load_log(transaction_id)
        entry.status = status
        entry.reconciliation_notes = reconciliation_notes
        self._save_log(entry)

    def _save_log(self, entry: TransactionLogEntry):
        """Save transaction log entry to file."""
        log_file = self.log_dir / f"{entry.transaction_id}.json"

        with open(log_file, 'w') as f:
            json.dump(asdict(entry), f, indent=2)

    def _load_log(self, transaction_id: str) -> TransactionLogEntry:
        """Load transaction log entry from file."""
        log_file = self.log_dir / f"{transaction_id}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        return TransactionLogEntry(**data)

    def get_recent_transactions(self, limit: int = 10) -> List[TransactionLogEntry]:
        """
        Get recent transactions (for dashboard display).

        Args:
            limit: Max number of transactions to return

        Returns:
            List of transactions, newest first
        """
        log_files = sorted(
            self.log_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        transactions = []
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
                transactions.append(TransactionLogEntry(**data))
            except Exception:
                continue  # Skip corrupted logs

        return transactions
