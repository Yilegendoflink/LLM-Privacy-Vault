import pytest
import asyncio
from src.core.deanonymizer import deanonymizer_engine

def test_deanonymize_text_basic():
    text = "Hello <PERSON_1>, your code is <PHONE_NUMBER_1>."
    mapping = {
        "<PERSON_1>": "John Doe",
        "<PHONE_NUMBER_1>": "123-456-7890"
    }
    
    result = deanonymizer_engine.deanonymize_text(text, mapping)
    assert result == "Hello John Doe, your code is 123-456-7890."

def test_deanonymize_text_no_mapping():
    text = "Hello <PERSON_1>."
    mapping = {}
    
    result = deanonymizer_engine.deanonymize_text(text, mapping)
    assert result == "Hello <PERSON_1>."

# Mocking LiteLLM chunk for streaming test
class MockDelta:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.delta = MockDelta(content)

class MockChunk:
    def __init__(self, content):
        self.choices = [MockChoice(content)]
    
    def model_dump_json(self, exclude_none=True):
        return f'{{"choices": [{{"delta": {{"content": "{self.choices[0].delta.content}"}}}}]}}'

async def mock_stream(chunks):
    for chunk in chunks:
        yield MockChunk(chunk)

@pytest.mark.asyncio
async def test_stream_deanonymizer_basic():
    chunks = ["Hello ", "<PERSON", "_1>", ", how are you?"]
    mapping = {"<PERSON_1>": "John Doe"}
    
    stream = mock_stream(chunks)
    result_chunks = []
    
    async for chunk_str in deanonymizer_engine.stream_deanonymizer(stream, mapping):
        result_chunks.append(chunk_str)
    
    # The output should contain "John Doe" and not "<PERSON_1>"
    full_output = "".join(result_chunks)
    assert "John Doe" in full_output
    assert "<PERSON_1>" not in full_output
    assert "data: [DONE]\n\n" in result_chunks[-1]
