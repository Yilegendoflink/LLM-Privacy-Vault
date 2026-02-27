import pytest
from src.core.anonymizer import anonymizer_engine

def test_anonymize_text_basic():
    text = "My name is John Doe and my phone number is 123-456-7890."
    anon_text, mapping = anonymizer_engine.anonymize_text(text)
    
    assert "John Doe" not in anon_text
    assert "123-456-7890" not in anon_text
    assert "<PERSON_1>" in anon_text
    assert "<PHONE_NUMBER_1>" in anon_text
    
    assert mapping["<PERSON_1>"] == "John Doe"
    assert mapping["<PHONE_NUMBER_1>"] == "123-456-7890"

def test_anonymize_text_duplicate_entities():
    text = "John Doe called. Tell John Doe I'll call back."
    anon_text, mapping = anonymizer_engine.anonymize_text(text)
    
    assert "John Doe" not in anon_text
    assert anon_text.count("<PERSON_1>") == 2
    assert "<PERSON_2>" not in anon_text
    
    assert mapping["<PERSON_1>"] == "John Doe"

def test_anonymize_text_no_pii():
    text = "This is a safe text with no personal information."
    anon_text, mapping = anonymizer_engine.anonymize_text(text)
    
    assert anon_text == text
    assert mapping == {}
