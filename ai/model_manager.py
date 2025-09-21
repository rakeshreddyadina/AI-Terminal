"""
AI Model Manager - Connects to the Google Gemini API
=====================================================

This module contains the ModelManager class, which serves as the primary
interface to Google's Generative AI services. It handles API key configuration,
model initialization, and the logic for translating natural language prompts
into shell commands.
"""

import re
from typing import Dict, Any
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Local application imports
from config import settings
from logs.logger import setup_logger

logger = setup_logger(__name__)

# --- Prompt Engineering: System Prompt ---
SYSTEM_PROMPT = """You are a specialized AI assistant that functions as an expert Linux shell command translator.
Your SOLE purpose is to convert a user's natural language request into a single, precise, and executable shell command.

**CRITICAL RULE:** Your response MUST contain ONLY the raw shell command. Do NOT include any other text, explanations, apologies, or markdown formatting like ` ```bash `. Your output must be directly runnable in a terminal.

**SAFETY PRECAUTIONS:**
1.  Absolutely NO destructive commands (`rm -rf`, `mkfs`, `dd`).
2.  NO commands requiring superuser privileges (`sudo`, `su`).
3.  NO system-altering commands (`shutdown`, `reboot`, `systemctl`, `init`).

**EXAMPLES:**
- User Request: "list all files in the current directory, including hidden ones, in a long format"
- Your Correct Output: ls -la

- User Request: "find any file named 'package.json' in any subfolder"
- Your Correct Output: find . -name "package.json"

- User Request: "show me the manual for the grep command"
- Your Correct Output: man grep
"""


class ModelManager:
    """
    Manages all API interactions with the Google Gemini model.
    """

    def __init__(self):
        self.model = None
        self._model_ready = False
        self.model_name = settings.AI_MODEL_NAME
        self.api_key = settings.GOOGLE_API_KEY
        self.initialize_model()

    def initialize_model(self):
        if not self.api_key or self.api_key == "YOUR_GOOGLE_API_KEY_HERE":
            logger.error("Google API key is not configured in settings.py. The AI assistant will be disabled.")
            self._model_ready = False
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self._model_ready = True
            logger.info(f"✅ Gemini model '{self.model_name}' client initialized and ready.")
        except google_exceptions.PermissionDenied:
            logger.critical("❌ Gemini API permission denied. Your API key may be invalid or expired.", exc_info=True)
            self._model_ready = False
        except Exception as e:
            logger.critical(f"❌ An unexpected error occurred while configuring the Gemini client: {e}", exc_info=True)
            self._model_ready = False

    def is_model_ready(self) -> bool:
        return self._model_ready

    def translate_command(self, natural_language: str, context: Dict[str, Any]) -> str:
        if not self.is_model_ready():
            return "echo 'AI model is not configured. Please check your API key in settings.py.'"

        try:
            current_dir = context.get('current_dir', '~')
            dir_contents = ", ".join(context.get('dir_contents', []))

            final_prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
Current Directory: `{current_dir}`
Directory Contents: `{dir_contents}`

TASK:
Translate this request: "{natural_language}"
"""
            generation_config = genai.types.GenerationConfig(
                temperature=0.0,
            )

            safety_settings = {
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_MEDIUM_AND_ABOVE',
            }

            response = self.model.generate_content(
                final_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            raw_output = response.text.strip()
            command = ""

            # --- Definitive Command Extraction Logic ---
            match = re.search(r"```(?:bash\n|sh\n)?(.*?)```", raw_output, re.DOTALL)
            if match:
                command = match.group(1).strip()
            else:
                lines = raw_output.strip().split('\n')
                command = next((line for line in reversed(lines) if line.strip()), "").strip()

            # --- Final Cleanup: strip quotes/backticks ---
            command = command.strip()
            while (command.startswith(("'", '"', "`")) and command.endswith(("'", '"', "`"))) and len(command) > 1:
                command = command[1:-1].strip()

            logger.info(f"Gemini translated '{natural_language}' to cleaned command: '{command}'")
            return command if command else "echo 'AI failed to generate a command.'"

        except google_exceptions.PermissionDenied:
            logger.error("Gemini API permission denied during translation. Check API key.")
            return "echo 'Error: Gemini API key is invalid.'"
        except google_exceptions.ResourceExhausted:
            logger.error("Gemini API quota exceeded. Please check your billing or usage limits.")
            return "echo 'Error: API quota exceeded. Please try again later.'"
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}", exc_info=True)
            if hasattr(e, 'response') and "was blocked" in str(e.response):
                 return "echo 'AI response blocked by safety filters.'"
            return "echo 'Error: An unexpected error occurred during AI translation.'"
