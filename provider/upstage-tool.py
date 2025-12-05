from typing import Any
import requests

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class UpstageToolProvider(ToolProvider):

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        Validate the Upstage API credentials by making a test request
        """
        try:
            api_key = credentials.get("upstage_api_key")

            if not api_key:
                raise ToolProviderCredentialValidationError("Upstage API key is required")

            if not isinstance(api_key, str) or len(api_key.strip()) == 0:
                raise ToolProviderCredentialValidationError("Invalid Upstage API key format")

            # Test the API key by making a request to the Upstage API
            headers = {
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json"
            }

            # Make a minimal test request to validate the API key
            response = requests.get(
                "https://api.upstage.ai/v1/document-digitization",
                headers=headers,
                timeout=10
            )

            if response.status_code == 401:
                raise ToolProviderCredentialValidationError("Invalid Upstage API key. Please check your credentials.")
            elif response.status_code == 403:
                raise ToolProviderCredentialValidationError("Access denied. Please check your API key permissions.")
            elif response.status_code >= 500:
                raise ToolProviderCredentialValidationError("Upstage API service unavailable. Please try again later.")

        except requests.RequestException as e:
            raise ToolProviderCredentialValidationError(f"Failed to connect to Upstage API: {str(e)}")
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"Credential validation failed: {str(e)}")
