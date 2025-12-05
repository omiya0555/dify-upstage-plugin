from collections.abc import Generator
from typing import Any
import requests
import hashlib
import time
import threading
import json
import base64

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class UpstageInformationExtractTool(Tool):
    # Class-level memory cache
    _cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl = 3600  # 1 hour cache TTL
    _max_cache_size = 100  # Maximum number of cached items

    @classmethod
    def _get_cache_key(cls, file_content: bytes, schema: str) -> str:
        """Generate cache key from file content and schema"""
        file_hash = hashlib.md5(file_content).hexdigest()
        schema_hash = hashlib.md5(schema.encode()).hexdigest()
        return f"{file_hash}_{schema_hash}"

    @classmethod
    def _get_from_cache(cls, cache_key: str) -> dict | None:
        """Retrieve content from memory cache if valid"""
        with cls._cache_lock:
            if cache_key in cls._cache:
                cached_item = cls._cache[cache_key]
                # Check if cache is still valid
                if time.time() - cached_item['timestamp'] < cls._cache_ttl:
                    return cached_item['content']
                else:
                    # Remove expired cache
                    del cls._cache[cache_key]
        return None

    @classmethod
    def _save_to_cache(cls, cache_key: str, content: dict) -> None:
        """Save content to memory cache"""
        with cls._cache_lock:
            # Implement LRU-style cache size management
            if len(cls._cache) >= cls._max_cache_size:
                # Remove oldest cache entry
                oldest_key = min(cls._cache.keys(),
                               key=lambda k: cls._cache[k]['timestamp'])
                del cls._cache[oldest_key]

            cls._cache[cache_key] = {
                'content': content,
                'timestamp': time.time()
            }

    @classmethod
    def _cleanup_expired_cache(cls) -> None:
        """Clean up expired cache entries"""
        with cls._cache_lock:
            current_time = time.time()
            expired_keys = [
                key for key, value in cls._cache.items()
                if current_time - value['timestamp'] >= cls._cache_ttl
            ]
            for key in expired_keys:
                del cls._cache[key]

    def _parse_schema(self, schema_text: str) -> dict:
        """
        Parse extraction schema from JSON string

        Args:
            schema_text: JSON string defining fields to extract

        Returns:
            Dictionary mapping field names to descriptions
        """
        try:
            schema = json.loads(schema_text.strip())
            if not isinstance(schema, dict):
                raise ValueError("Schema must be a JSON object (dictionary)")
            return schema
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    def _build_json_schema(self, field_definitions: dict) -> dict:
        """
        Build JSON Schema for Upstage API from field definitions

        Args:
            field_definitions: Dict mapping field names to descriptions

        Returns:
            JSON Schema object for API request
        """
        properties = {}
        for field_name, description in field_definitions.items():
            properties[field_name] = {
                "type": "string",
                "description": str(description)
            }

        return {
            "type": "object",
            "properties": properties
        }

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        Extract structured information from documents using Upstage Information Extract API

        Args:
            tool_parameters: Dictionary containing:
                - file: File object to be analyzed
                - extraction_schema: JSON string defining fields to extract

        Yields:
            ToolInvokeMessage: JSON message with extracted data
        """
        try:
            # Extract parameters
            file_obj = tool_parameters.get("file")
            if not file_obj:
                yield self.create_text_message("Error: No file provided for extraction.")
                return

            schema_text = tool_parameters.get("extraction_schema", "")
            if not schema_text:
                yield self.create_text_message("Error: No extraction schema provided.")
                return

            # Get file information
            filename = getattr(file_obj, 'filename', 'document')

            # Get API key from credentials
            api_key = self.runtime.credentials.get("upstage_api_key")
            if not api_key:
                yield self.create_text_message("Error: Upstage API key not found in credentials.")
                return

            # Get file content directly from blob
            try:
                file_content = file_obj.blob
                if not file_content:
                    yield self.create_text_message("Error: Failed to read file content.")
                    return
            except Exception as e:
                yield self.create_text_message(f"Error reading file: {str(e)}")
                return

            # Parse extraction schema
            try:
                field_definitions = self._parse_schema(schema_text)
                if not field_definitions:
                    yield self.create_text_message("Error: Extraction schema is empty.")
                    return
            except ValueError as e:
                yield self.create_text_message(f"Error parsing schema: {str(e)}")
                return

            # Generate cache key and check cache
            cache_key = self._get_cache_key(file_content, schema_text)
            cached_content = self._get_from_cache(cache_key)

            if cached_content:
                # Return cached result
                yield self.create_json_message(cached_content)
                return

            # Clean up expired cache entries periodically
            self._cleanup_expired_cache()

            # Convert file to base64
            base64_data = base64.b64encode(file_content).decode('utf-8')

            # Determine MIME type based on filename
            mime_type = "image/png"
            if filename.lower().endswith(('.jpg', '.jpeg')):
                mime_type = "image/jpeg"
            elif filename.lower().endswith('.pdf'):
                mime_type = "application/pdf"
            elif filename.lower().endswith('.png'):
                mime_type = "image/png"

            # Build JSON Schema for API
            json_schema = self._build_json_schema(field_definitions)

            # Prepare API request
            url = "https://api.upstage.ai/v1/information-extraction"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8"
            }

            payload = {
                "model": "information-extract",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_data}"
                                }
                            }
                        ]
                    }
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "extraction_schema",
                        "schema": json_schema
                    }
                }
            }

            # Make API request
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=300
                )

                if response.status_code != 200:
                    error_msg = f"API request failed with status {response.status_code}"
                    if response.text:
                        error_msg += f": {response.text}"
                    yield self.create_text_message(f"Error: {error_msg}")
                    return

            except requests.RequestException as e:
                yield self.create_text_message(f"Error: Failed to connect to Upstage API: {str(e)}")
                return

            # Parse API response
            try:
                result_data = response.json()

                # Extract the content from OpenAI-compatible response format
                if 'choices' in result_data and len(result_data['choices']) > 0:
                    message_content = result_data['choices'][0].get('message', {}).get('content', '')
                    if message_content:
                        extracted_data = json.loads(message_content)
                    else:
                        yield self.create_text_message("Error: No content in API response.")
                        return
                else:
                    yield self.create_text_message("Error: Unexpected API response format.")
                    return

                if not extracted_data:
                    yield self.create_text_message("Error: No data was extracted from the document.")
                    return

                # Save to cache before returning
                self._save_to_cache(cache_key, extracted_data)

                # Return result as JSON message
                yield self.create_json_message(extracted_data)

            except json.JSONDecodeError as e:
                yield self.create_text_message(f"Error: Failed to parse API response as JSON: {str(e)}")
                return
            except Exception as e:
                yield self.create_text_message(f"Error: Failed to process API response: {str(e)}")
                return

        except Exception as e:
            yield self.create_text_message(f"Error: An unexpected error occurred: {str(e)}")
