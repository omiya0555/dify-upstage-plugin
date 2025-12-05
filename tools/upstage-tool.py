from collections.abc import Generator
from typing import Any
import requests
import hashlib
import time
import threading

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class UpstageDocumentParserTool(Tool):
    # Class-level memory cache
    _cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl = 3600  # 1 hour cache TTL
    _max_cache_size = 100  # Maximum number of cached items

    @classmethod
    def _get_cache_key(cls, file_content: bytes, output_format: str) -> str:
        """Generate cache key from file content and output format"""
        file_hash = hashlib.md5(file_content).hexdigest()
        return f"{file_hash}_{output_format}"

    @classmethod
    def _get_from_cache(cls, cache_key: str) -> str | None:
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
    def _save_to_cache(cls, cache_key: str, content: str) -> None:
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

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        Parse documents using Upstage Document Parse API

        Args:
            tool_parameters: Dictionary containing:
                - file: File object to be parsed
                - output_format: Format for output (markdown, html, text)

        Yields:
            ToolInvokeMessage: Text message with parsed content
        """
        try:
            # Extract parameters
            file_obj = tool_parameters.get("file")
            if not file_obj:
                yield self.create_text_message("Error: No file provided for parsing.")
                return

            output_format = tool_parameters.get("output_format", "markdown")

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

            # Generate cache key and check cache
            cache_key = self._get_cache_key(file_content, output_format)
            cached_content = self._get_from_cache(cache_key)

            if cached_content:
                # Return cached result
                yield self.create_text_message(cached_content)
                return

            # Clean up expired cache entries periodically
            self._cleanup_expired_cache()

            # Prepare API request
            url = "https://api.upstage.ai/v1/document-digitization"
            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            # Map output format to API parameter (must be JSON string format)
            format_mapping = {
                "markdown": '["markdown"]',
                "html": '["html"]',
                "text": '["text"]'
            }
            output_formats = format_mapping.get(output_format, '["markdown"]')

            # Prepare multipart form data
            files_data = {
                'document': (filename, file_content)
            }
            data = {
                'model': 'document-parse',
                'output_formats': output_formats,
                'ocr': 'auto',
                'chart_recognition': 'true',
                'merge_multipage_tables': 'false',
                'coordinates': 'true',
                'base64_encoding': '[]'
            }

            # Make API request
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    files=files_data,
                    data=data,
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
                content = result_data.get('content', {})

                # Get the parsed content based on selected format
                if output_format == "markdown":
                    parsed_content = content.get('markdown', '')
                elif output_format == "html":
                    parsed_content = content.get('html', '')
                elif output_format == "text":
                    parsed_content = content.get('text', '')
                else:
                    parsed_content = content.get('markdown', '')

                if not parsed_content:
                    yield self.create_text_message("Error: No content was extracted from the document.")
                    return

                # Save to cache before returning
                self._save_to_cache(cache_key, parsed_content)

                # Return result as text message
                yield self.create_text_message(parsed_content)

            except Exception as e:
                yield self.create_text_message(f"Error: Failed to parse API response: {str(e)}")
                return

        except Exception as e:
            yield self.create_text_message(f"Error: An unexpected error occurred: {str(e)}")
