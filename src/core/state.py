import logging
from typing import Dict

logger = logging.getLogger(__name__)

class StateManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing State Manager (Memory Dict)...")
        self._mappings: Dict[str, Dict[str, str]] = {}

    def save_mapping(self, request_id: str, mapping: Dict[str, str]):
        """
        Saves the anonymization mapping for a specific request ID.
        """
        if mapping:
            self._mappings[request_id] = mapping
            logger.debug(f"Saved mapping for request {request_id}: {mapping}")

    def get_mapping(self, request_id: str) -> Dict[str, str]:
        """
        Retrieves the anonymization mapping for a specific request ID.
        """
        return self._mappings.get(request_id, {})

    def delete_mapping(self, request_id: str):
        """
        Deletes the anonymization mapping for a specific request ID to free memory.
        """
        if request_id in self._mappings:
            del self._mappings[request_id]
            logger.debug(f"Deleted mapping for request {request_id}")

# Global instance
state_manager = StateManager()
