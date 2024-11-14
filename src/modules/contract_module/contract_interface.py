from abc import ABC, abstractmethod
import hashlib
import json
from typing import Any


class ContractInterface(ABC):
    def __init__(self, contract_type: str, **kwargs):
        self.contract_type = contract_type
        self.signature = None
        self.data = kwargs

    @abstractmethod
    def execute(self, action: str, *args, **kwargs) -> Any:
        """Execute an action for the contract."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the contract data."""
        pass

    def generate_signature(self) -> str:
        """Generate a unique hash signature for the contract's data."""
        data_string = json.dumps(self.data, sort_keys=True).encode()
        self.signature = hashlib.sha256(data_string).hexdigest()
        return self.signature

    def verify_signature(self, signature: str) -> bool:
        """Verify the given signature against the current data."""
        return self.generate_signature() == signature

    def post_validate(self):
        """Optional hook to run after validation."""
        pass

    def pre_execute(self):
        """Optional hook to run before execution."""
        pass

    def post_execute(self):
        """Optional hook to run after execution."""
        pass


class ContractTypeAlias:
    TOKEN = "token"
    SUBCHAIN = "subchain"
    MEDIA = "media"
    NFT = "nft"
    SENSITIVE_DATA = "sensitive_data"
    ORACLE = "oracle"
