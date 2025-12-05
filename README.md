# Upstage Document AI

**Developer:** omiya0555
**Organization:** Fusic
**Version:** 0.0.1
**Type:** Tool Plugin
**Contact:** omiya@fusic.co.jp
**Repository:** https://github.com/omiya0555/dify-upstage-plugin.git

## Description

Advanced Document AI plugin using Upstage API. Provides two powerful tools for document processing: parse documents into text/HTML/Markdown format, or extract structured data using custom JSON schemas.

## Tools Included

### 1. Upstage Document Parser
Parse PDFs, images, and office documents into text, HTML, or Markdown format with high accuracy OCR and layout detection.

**Features:**
- **Multi-format Support**: PDF, DOCX, XLSX, PPTX, JPEG, PNG, BMP, TIFF, HEIC
- **Multiple Output Formats**: Markdown, HTML, Plain Text
- **Advanced OCR**: Automatic text recognition with chart detection

### 2. Upstage Information Extract
Extract structured data from documents using custom JSON schemas. Perfect for automating data entry from invoices, receipts, forms, and contracts.

**Features:**
- **Custom Schema Definition**: Define extraction fields in simple JSON format
- **Structured JSON Output**: Get clean, structured data ready for database integration
- **High Accuracy**: 90-95% accuracy on complex documents
- **Flexible Extraction**: Works with any document type without templates or training

## Common Features

- **Intelligent Memory Cache**: In-memory caching reduces API calls and improves performance
- **Simple Configuration**: Only requires Upstage API key
- **Error Handling**: Comprehensive error messages and validation

## Setup

1. Get your API key from [Upstage Console](https://console.upstage.ai/api-keys)
2. Install the plugin in Dify
3. Configure the API key in plugin settings

## Usage

### Document Parser
1. Upload a document file
2. Select your preferred output format (Markdown, HTML, or Text)
3. The tool will parse the document and return the extracted content

### Information Extract
1. Upload a document file
2. Define your extraction schema in JSON format:
```json
{
  "invoice_number": "Invoice number from the document",
  "total_amount": "Total amount to be paid",
  "issue_date": "Date when invoice was issued",
  "company_name": "Name of the company"
}
```
3. The tool will extract the specified fields and return structured JSON data

## Requirements

- Upstage API key
- Supported file formats: PDF, images, office documents
- Network connection to Upstage API

## Performance Optimization

### Memory Cache
The plugin implements an intelligent memory cache system that:
- Reduces API calls for identical documents
- Uses MD5 hashing for efficient cache key generation
- Automatically expires cached content after 1 hour
- Maintains a maximum of 100 cached items with LRU eviction
- Thread-safe operations for concurrent requests

### Cache Behavior
- Document Parser: Same file + same output format = Cache hit
- Information Extract: Same file + same schema = Cache hit
- Cache automatically cleans up expired entries

## API Reference

This plugin uses two Upstage APIs:

### Document Parse API
- **Endpoint**: `https://api.upstage.ai/v1/document-digitization`
- **Model**: `document-parse`
- **OCR Mode**: `auto` (optimized for each file type)
- **Chart Recognition**: Enabled
- **Timeout**: 300 seconds (5 minutes)

### Information Extract API
- **Endpoint**: `https://api.upstage.ai/v1/information-extraction`
- **Model**: `information-extract`
- **Input**: Base64-encoded documents with JSON schema
- **Output**: Structured JSON matching your schema
- **Timeout**: 300 seconds (5 minutes)

For more details, visit [Upstage API Documentation](https://console.upstage.ai/docs/capabilities).
