# Upstage Document Parser

## Overview

The Upstage Document Parser is an advanced tool plugin that leverages the Upstage API to extract and parse content from various document formats including PDFs, images, and office documents. The plugin provides high-accuracy OCR and intelligent layout detection capabilities.

## Features

### Supported File Formats
- **Documents**: PDF, DOCX, XLSX, PPTX
- **Images**: JPEG, PNG, BMP, TIFF, HEIC

### Output Formats
- **Markdown**: Structured text with formatting
- **HTML**: Web-ready formatted content
- **Plain Text**: Clean text without formatting

### Advanced Capabilities
- **Automatic OCR**: Intelligent text recognition
- **Chart Recognition**: Converts charts to tables
- **Layout Detection**: Preserves document structure
- **Multi-language Support**: Handles various languages
- **Intelligent Memory Cache**: In-memory caching for improved performance

## Installation

1. **Get API Key**
   - Visit [Upstage Console](https://console.upstage.ai/api-keys)
   - Create an account and generate your API key

2. **Install Plugin**
   - Upload the `.difypkg` file to your Dify instance
   - Or install from Dify Plugin Marketplace

3. **Configure Credentials**
   - Enter your Upstage API key in plugin settings
   - Test the connection to ensure proper setup

## Usage

### Basic Usage
1. Add the "Upstage Document Parser" tool to your workflow
2. Connect a file input to the tool
3. Select your preferred output format (markdown/html/text)
4. Run the workflow to parse your document

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | Document file to be parsed |
| `output_format` | select | No | Output format (markdown, html, text) |

### Example Workflow

```
[File Upload] → [Upstage Document Parser] → [Text Output]
                       ↓
                [output_format: markdown]
```

## Performance Optimization

### Memory Cache System
The plugin implements an intelligent memory cache that:
- **Reduces API Costs**: Identical files are served from cache
- **Improves Response Time**: Cached results return instantly
- **Smart Cache Management**: Automatic expiration and LRU eviction
- **Thread-Safe**: Concurrent request handling with proper locking

### Cache Configuration
- **Cache Duration**: 1 hour (3600 seconds)
- **Maximum Entries**: 100 cached documents
- **Cache Key**: MD5 hash of file content + output format
- **Eviction Strategy**: Least Recently Used (LRU)

## API Details

This plugin uses the Upstage Document Parse API v1 with the following configuration:

- **Model**: `document-parse`
- **OCR Mode**: `auto` (optimized for each file type)
- **Chart Recognition**: Enabled
- **Coordinates**: Enabled for layout detection
- **Timeout**: 300 seconds (5 minutes)

## Troubleshooting

### Common Issues

1. **"Invalid API key"**
   - Verify your API key is correct
   - Check API key permissions in Upstage Console

2. **"No content extracted"**
   - Ensure file is not corrupted
   - Try different output formats
   - Check if file format is supported

3. **"API timeout"**
   - Large files may take longer to process
   - Consider splitting large documents

### Support

For API-related issues, consult the [Upstage API Documentation](https://console.upstage.ai/api/document-digitization/document-parsing).

## Technical Specifications

- **Minimum Dify Version**: 1.5.0
- **Plugin Type**: Tool
- **Memory Requirements**: 256MB
- **Network**: Requires internet connection to Upstage API

## License

This plugin is provided as-is for integration with Dify workflows. Please refer to Upstage's terms of service for API usage limitations.