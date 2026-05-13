import re
from datetime import datetime

class SecureInferenceLayer:

    def __init__(self):
        self.secure_mode = True

    def sanitize_input(self, text: str):

        text = re.sub(r'\d{10,}', '[ACCOUNT_MASKED]', text)

        text = re.sub(
            r'[A-Z]{5}[0-9]{4}[A-Z]',
            '[PAN_MASKED]',
            text
        )

        return text

    def secure_inference(self, prompt, llm_function):

        sanitized_prompt = self.sanitize_input(prompt)

        response = llm_function(sanitized_prompt)

        return response

    def get_security_metadata(self):

        return {
            "mode": "confidential-inference",
            "tee_compatible": True,
            "deployment": "on-premise-ready",
            "timestamp": datetime.utcnow().isoformat()
        }