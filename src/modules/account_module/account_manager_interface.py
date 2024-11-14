from abc import ABC, abstractmethod

class AccountManagerInterface(ABC):
    @abstractmethod
    def create_account(self, account_id: str, address_id: str) -> None:
        pass

    @abstractmethod
    def lock_account(self, account_id: str) -> None:
        pass

    @abstractmethod
    def unlock_account(self, account_id: str, signature: bytes) -> None:
        pass

    @abstractmethod
    def is_account_locked(self, account_id: str) -> bool:
        pass
