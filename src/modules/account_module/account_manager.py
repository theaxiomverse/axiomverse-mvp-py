from axiomverse.account_module.account_manager_interface import AccountManagerInterface
from axiomverse.crypto_module.key_management import KeyManagement
from axiomverse.trust_module.trust_manager import TrustManager
from axiomverse.address_module.address_manager import AddressManager
from axiomverse.transaction_module.transaction_manager import TransactionManager
from axiomverse.events_module.event_emitter import EventEmitter
from axiomverse.crypto_module.signature_management import SignatureManagement
import shelve
import logging
import threading
import asyncio

logger = logging.getLogger(__name__)


class AccountExistsError(Exception):
    pass


class AccountNotFoundError(Exception):
    pass


class AccountManager(AccountManagerInterface):
    def __init__(self):
        self.lock = threading.Lock()
        self.key_management = KeyManagement()
        self.signature_management = SignatureManagement()
        self.address_manager = AddressManager()
        self.trust_manager = TrustManager()
        self.transaction_manager = TransactionManager()
        self.event_emitter = EventEmitter()

        with shelve.open("account_store", writeback=True) as store:
            self.account_store = store
            logger.info("AccountManager initialized and account_store opened.")

        # Async connect to EventEmitter
        asyncio.create_task(self.initialize_event_emitter())

    async def initialize_event_emitter(self):
        await self.event_emitter.connect()
        logger.info("EventEmitter connected.")

    async def create_account(self, account_id: str, ip_address: str) -> None:
        """Create a new account with a unique address and emit an event with a transaction."""
        with self.lock:
            if account_id in self.account_store:
                logger.warning(f"Account creation failed: Account {account_id} already exists.")
                raise AccountExistsError(f"Account {account_id} already exists.")

            # Generate a Kyber 512 key pair
            public_key, private_key = self.key_management.generate_keypair()

            # Generate an address based on the public key and geolocation data
            address = self.address_manager.generate_geohashed_address(ip_address, "account")

            # Initialize the account in the store
            self.account_store[account_id] = {
                "public_key": public_key,
                "private_key": private_key,
                "address": address,
                "locked": True  # Default to locked until explicitly unlocked by the user
            }

            # Initialize a neutral trust score
            self.trust_manager.update_trust_score(account_id, {"age": 0, "uptime": 0, "latency": 1.0})

            # Create a transaction for the account creation
            transaction_data = {
                "type": "account_creation",
                "account_id": account_id,
                "address": address,
                "public_key": public_key
            }
            transaction_id = self.transaction_manager.create_transaction(transaction_data)

            self.account_store.sync()
            logger.info(f"Account {account_id} created successfully with address {address}.")

            # Emit an event to notify the network about the new account creation
            account_event_data = {
                "account_id": account_id,
                "public_key": public_key,
                "address": address,
                "transaction_id": transaction_id
            }
            await self.event_emitter.emit_event("account_created", account_event_data)

    def lock_account(self, account_id: str) -> None:
        """Restrict account usage by marking it as locked."""
        with self.lock:
            if account_id not in self.account_store:
                raise AccountNotFoundError(f"Account {account_id} does not exist.")
            self.account_store[account_id]["locked"] = True
            self.account_store.sync()
            logger.info(f"Account {account_id} locked successfully.")

    def unlock_account(self, account_id: str, signature: str) -> None:
        """Enable account usage by unlocking it if authorization is confirmed."""
        with self.lock:
            if account_id not in self.account_store:
                raise AccountNotFoundError(f"Account {account_id} does not exist.")

            # Verify signature for authentication
            public_key = self.account_store[account_id]["public_key"]
            message = f"Unlock request for {account_id}"
            if not self.signature_management.verify_signature(public_key, message, signature):
                logger.error(f"Failed unlock attempt for account {account_id} due to invalid signature.")
                raise ValueError("Invalid signature for unlocking account.")

            # Trust score check (optional, based on network policy)
            trust_score = self.trust_manager.get_trust_score(account_id)
            if trust_score < 0.5:
                raise ValueError("Account trust score is too low to unlock.")

            # Unlock the account
            self.account_store[account_id]["locked"] = False
            self.account_store.sync()
            logger.info(f"Account {account_id} unlocked successfully.")

    def __enter__(self):
        """Ensure shelve store opens in a context."""
        self.account_store = shelve.open("account_store", writeback=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Proper cleanup using context manager."""
        if self.account_store is not None:
            self.account_store.close()
            logger.info("Account store closed.")
