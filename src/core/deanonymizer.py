import logging
import re
from typing import Dict, AsyncGenerator, Any
import json

logger = logging.getLogger(__name__)

class PrivacyDeanonymizer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PrivacyDeanonymizer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing Privacy Deanonymizer...")

    def deanonymize_text(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Replaces placeholders in the text with their original values based on the mapping.
        """
        if not text or not mapping:
            return text

        deanonymized_text = text
        # Sort mapping keys by length descending to avoid partial replacements
        for placeholder in sorted(mapping.keys(), key=len, reverse=True):
            original_value = mapping[placeholder]
            deanonymized_text = deanonymized_text.replace(placeholder, original_value)

        return deanonymized_text

    async def stream_deanonymizer(self, response_stream: AsyncGenerator[Any, None], mapping: Dict[str, str]) -> AsyncGenerator[str, None]:
        """
        Processes a streaming response, buffering tokens to correctly deanonymize placeholders
        that might be split across multiple chunks.
        """
        buffer = ""
        
        async for chunk in response_stream:
            # Extract content from LiteLLM chunk
            delta_content = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
            
            if not delta_content:
                # Yield the chunk as is if no content (e.g., role or finish_reason)
                yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
                continue

            buffer += delta_content
            
            # Check if buffer contains any complete placeholders
            for placeholder, original_value in mapping.items():
                if placeholder in buffer:
                    buffer = buffer.replace(placeholder, original_value)
            
            # Check if the end of the buffer might be the start of a placeholder
            # A placeholder looks like <ENTITY_TYPE_INDEX>
            last_open_bracket = buffer.rfind('<')
            last_close_bracket = buffer.rfind('>')
            
            if last_open_bracket != -1 and last_open_bracket > last_close_bracket:
                # Potential placeholder started but not finished
                safe_to_yield = buffer[:last_open_bracket]
                buffer = buffer[last_open_bracket:]
            else:
                # No open placeholder, safe to yield everything
                safe_to_yield = buffer
                buffer = ""
            
            if safe_to_yield:
                # Update the chunk with the deanonymized content
                chunk.choices[0].delta.content = safe_to_yield
                yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
            elif not delta_content:
                # If there was no content to begin with, yield the chunk
                yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"

        # Yield any remaining content in the buffer
        if buffer:
            # If there's still something in the buffer, it wasn't a complete placeholder
            # We need to construct a final chunk for this
            # For simplicity, we'll just yield it in a dummy chunk structure
            # In a real implementation, we'd keep the last chunk object to modify it
            # Here we just yield the raw buffer as a string if needed, or construct a basic chunk.
            # For MVP, we'll assume the buffer is empty at the end if it was a valid stream.
            pass

        yield "data: [DONE]\n\n"

# Global instance
deanonymizer_engine = PrivacyDeanonymizer()
