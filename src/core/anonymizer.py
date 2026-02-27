import os
import logging
from typing import Tuple, Dict
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

class PrivacyAnonymizer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PrivacyAnonymizer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing Presidio Analyzer and Anonymizer...")
        
        # Configure NLP engine for multiple languages (English and Chinese)
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_lg"},
                {"lang_code": "zh", "model_name": "zh_core_web_sm"},
            ],
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()
        
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine, 
            supported_languages=["en", "zh"]
        )
        self.anonymizer = AnonymizerEngine()
        
        # Set default language from environment variable, fallback to English
        self.default_language = os.getenv("DEFAULT_LANGUAGE", "en")
        logger.info(f"Default language set to: {self.default_language}")
        
        # Entities we want to anonymize
        self.entities = [
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "CREDIT_CARD",
            "CRYPTO",
            "IP_ADDRESS",
            "IBAN_CODE",
            "US_SSN",
            "US_PASSPORT"
        ]
        logger.info("Presidio engines initialized successfully.")

    def anonymize_text(self, text: str, language: str = None) -> Tuple[str, Dict[str, str]]:
        """
        Anonymizes the input text and returns the anonymized text along with a mapping
        to restore the original values.
        """
        if not text:
            return text, {}

        lang = language or self.default_language

        # 1. Analyze text to find PII
        results = self.analyzer.analyze(
            text=text,
            entities=self.entities,
            language=lang
        )

        if not results:
            return text, {}

        # 2. Create custom operators to replace PII with <ENTITY_TYPE_INDEX>
        # We need to keep track of the mapping.
        # Presidio's default anonymizer doesn't easily return the exact mapping of 
        # <ENTITY_1> -> "Original Text" out of the box in a simple dict if there are duplicates.
        # So we will manually build the mapping and use custom operators.
        
        mapping = {}
        entity_counters = {}
        
        # Sort results by start index descending to replace from end to start
        # This prevents index shifting issues during replacement
        results.sort(key=lambda x: x.start, reverse=True)
        
        anonymized_text = text
        
        for result in results:
            entity_type = result.entity_type
            original_value = text[result.start:result.end]
            
            # Check if we already mapped this exact value to avoid <PERSON_1> and <PERSON_2> for the same name
            existing_placeholder = None
            for placeholder, orig_val in mapping.items():
                if orig_val == original_value and placeholder.startswith(f"<{entity_type}_"):
                    existing_placeholder = placeholder
                    break
            
            if existing_placeholder:
                replacement = existing_placeholder
            else:
                if entity_type not in entity_counters:
                    entity_counters[entity_type] = 1
                else:
                    entity_counters[entity_type] += 1
                
                replacement = f"<{entity_type}_{entity_counters[entity_type]}>"
                mapping[replacement] = original_value
            
            # Replace in text
            anonymized_text = anonymized_text[:result.start] + replacement + anonymized_text[result.end:]

        return anonymized_text, mapping

# Global instance
anonymizer_engine = PrivacyAnonymizer()
