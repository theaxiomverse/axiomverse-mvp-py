# vm_module/vm_interface.py

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class VMInterface(ABC):
    @abstractmethod
    def execute_opcode(self, opcode: str, *args, **kwargs):
        """Executes an opcode"""
        pass

    @abstractmethod
    def load_contract(self, contract_code: str):
        """Loads contract code into the VM"""
        pass

    @abstractmethod
    def run_contract(self, contract_id: str):
        """Runs the specified contract using the VM"""
        pass

    def emit_debug_event(self, message: str):
        """Emit a debug event for VM operations"""
        logger.debug(f"VM Debug: {message}")

    def emit_log_event(self, message: str):
        """Emit a log event for VM operations"""
        logger.info(f"VM Log: {message}")
