from src.modules.account_module.account_manager_interface import AccountManagerInterface
from src.modules.crypto_module.key_management import KeyManagement
from src.modules.trust_module.trust_manager import TrustManager
from src.modules.address_module.address_manager import AddressManager
from src.modules.transaction_module.transaction_manager import TransactionManager
from src.modules.events_module.event_emitter import EventEmitter
from src.modules.crypto_module.signature_management import SignatureManagement
import shelve
import logging
import threading
import asyncio

logger = logging.getLogger(__name__)


class AccountManager(AccountManagerInterface):
    def __init__(self):
        self.lock = threading.Lock()
        self.key_management = KeyManagement()
        self.signature_management = SignatureManagement()
        self.address_manager = AddressManager()
        self.trust_manager = TrustManager()
        self.transaction_manager = TransactionManager()
        self.event_emitter = EventEmitter()
        self._store = None

    def _get_store(self):
        """Get or create shelf store."""
        if not self._store:
            self._store = shelve.open("account_store", writeback=True)
        return self._store

    async def create_account(self, account_id: str, address_id: str) -> None:
        store = self._get_store()
        with self.lock:
            if account_id in store:
                raise AccountExistsError(f"Account {account_id} already exists.")

            public_key, private_key = self.key_management.generate_keypair()
            address = self.address_manager.generate_geohashed_address(address_id, "account")

            store[account_id] = {
                "public_key": public_key,
                "private_key": private_key,
                "address": address,
                "locked": True
            }
            store.sync()

    def is_account_locked(self, account_id: str) -> bool:
        store = self._get_store()
        with self.lock:
            if account_id not in store:
                raise AccountNotFoundError(f"Account {account_id} does not exist.")
            return store[account_id]["locked"]

    def lock_account(self, account_id: str) -> None:
        store = self._get_store()
        with self.lock:
            if account_id not in store:
                raise AccountNotFoundError(f"Account {account_id} does not exist.")
            store[account_id]["locked"] = True
            store.sync()

    def unlock_account(self, account_id: str, signature: str) -> None:
        store = self._get_store()
        with self.lock:
            if account_id not in store:
                raise AccountNotFoundError(f"Account {account_id} does not exist.")

            public_key = store[account_id]["public_key"]
            message = f"Unlock {account_id}"

            if not self.signature_management.verify_signature(public_key, message, signature):
                raise ValueError("Invalid signature")

            store[account_id]["locked"] = False
            store.sync()

    def get_account(self, account_id: str) -> dict:
        store = self._get_store()
        with self.lock:
            if account_id not in store:
                raise AccountNotFoundError(f"Account {account_id} does not exist.")
            return dict(store[account_id])

    def get_address(self, account_id: str) -> str:
        store = self._get_store()
        with self.lock:
            if account_id not in store:
                raise AccountNotFoundError(f"Account {account_id} does not exist.")
            return store[account_id]["address"]

    async def cleanup(self):
        """Cleanup resources."""
        if self._store:
            try:
                self._store.close()
                await self.event_emitter.cleanup()
                if hasattr(self.transaction_manager, 'cleanup'):
                    await self.transaction_manager.cleanup()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                self._store = None


class AccountExistsError(Exception):
    pass


class AccountNotFoundError(Exception):
    pass