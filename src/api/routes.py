import uuid
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.models.schemas import ChatCompletionRequest, ChatCompletionResponse
from src.core.anonymizer import anonymizer_engine
from src.core.state import state_manager
from src.core.llm_client import llm_client
from src.core.deanonymizer import deanonymizer_engine

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    request_id = str(uuid.uuid4())
    logger.info(f"Processing request {request_id}")

    try:
        # 1. Anonymize the request messages
        global_mapping = {}
        anonymized_messages = []
        
        for msg in request.messages:
            if msg.role in ["user", "system", "assistant"]:
                # Anonymize content
                anon_text, mapping = anonymizer_engine.anonymize_text(msg.content)
                global_mapping.update(mapping)
                anonymized_messages.append({"role": msg.role, "content": anon_text})
            else:
                anonymized_messages.append({"role": msg.role, "content": msg.content})
        
        # Save mapping to state
        state_manager.save_mapping(request_id, global_mapping)
        
        # Update request with anonymized messages
        anon_request = request.model_copy(deep=True)
        for i, msg in enumerate(anon_request.messages):
            msg.content = anonymized_messages[i]["content"]

        # 2. Forward to LLM
        response = await llm_client.forward_request(anon_request)

        # 3. Handle response (Streaming vs Non-Streaming)
        if request.stream:
            # Streaming response
            async def stream_generator():
                try:
                    async for chunk in deanonymizer_engine.stream_deanonymizer(response, global_mapping):
                        yield chunk
                finally:
                    # Clean up state after stream finishes
                    state_manager.delete_mapping(request_id)
            
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            # Non-streaming response
            try:
                # Deanonymize the response content
                for choice in response.choices:
                    if choice.message and choice.message.content:
                        deanonymized_content = deanonymizer_engine.deanonymize_text(
                            choice.message.content, global_mapping
                        )
                        choice.message.content = deanonymized_content
                
                # Convert LiteLLM response to our Pydantic model
                response_dict = response.model_dump()
                return ChatCompletionResponse(**response_dict)
            finally:
                # Clean up state
                state_manager.delete_mapping(request_id)

    except Exception as e:
        logger.error(f"Error processing request {request_id}: {e}")
        # Ensure state is cleaned up on error
        state_manager.delete_mapping(request_id)
        raise HTTPException(status_code=500, detail=str(e))
