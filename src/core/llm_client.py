import logging
from typing import Any, Dict, AsyncGenerator
import litellm
from src.models.schemas import ChatCompletionRequest

logger = logging.getLogger(__name__)

class LLMClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing LiteLLM Client...")
        # Optional: Configure LiteLLM settings here
        # litellm.set_verbose = True

    async def forward_request(self, request: ChatCompletionRequest) -> Any:
        """
        Forwards the anonymized request to the target LLM using LiteLLM.
        Supports both streaming and non-streaming responses.
        """
        logger.info(f"Forwarding request to model: {request.model}, stream: {request.stream}")
        
        # Convert Pydantic model to dict, excluding None values
        kwargs = request.model_dump(exclude_none=True)
        
        # Log the actual payload being sent to the LLM for verification
        logger.info(f"--- PAYLOAD SENT TO LLM ---")
        for msg in kwargs.get("messages", []):
            logger.info(f"Role: {msg.get('role')} | Content: {msg.get('content')}")
        logger.info(f"---------------------------")
        
        try:
            response = await litellm.acompletion(**kwargs)
            return response
        except Exception as e:
            logger.error(f"Error forwarding request to LLM: {e}")
            raise e

# Global instance
llm_client = LLMClient()
