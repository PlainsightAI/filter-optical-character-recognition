---
title: OCR Filter
sidebar_label: Overview
sidebar_position: 1
---

import Admonition from '@theme/Admonition';

# Optical Character Recognition (OCR) Filter

The `FilterOpticalCharacterRecognition` is a pluggable filter that extracts text from image frames using Optical Character Recognition (OCR). It supports multiple OCR backends and offers flexible configuration for language support, output, and debug logging.

## Features

- **Dual OCR Engine Support**  
  Choose between:
  - [`tesseract`](https://github.com/tesseract-ocr/tesseract)
  - [`easyocr`](https://github.com/JaidedAI/EasyOCR)  
  Configure with the `ocr_engine` parameter.

- **Multi-language OCR**  
  Use the `ocr_language` option to specify one or more language codes (e.g., `en,fr`).

- **Multi-topic Processing**  
  - Process multiple video regions simultaneously using pub/sub topics
  - Filter frames by topic using `topic_pattern` regex
  - Exclude specific topics using `exclude_topics` list
  - Support for exact topic names or regex patterns in exclusions
  - **Main-first output ordering** - ensures consistent topic structure

- **Flexible Output Options**  
  - Write results to JSON file (configurable via `write_output_file`)
  - Forward OCR results in frame metadata (configurable via `forward_ocr_texts`)
  - Results are written to `output_json_path` as newline-delimited JSON
  - **Data forwarding** - forwards non-image frames when `forward_upstream_data` is enabled

- **Debug Mode**  
  Enabling `debug: true` will increase logging verbosity for troubleshooting and transparency.

- **Frame-level Skipping**  
  Add the metadata flag `skip_ocr: true` to individual frames to bypass OCR processing.

- **Custom Tesseract Path**  
  You can specify a custom `tesseract_cmd` binary path if using the Tesseract engine (defaults to a bundled AppImage).

- **Safe Streaming Output**  
  Results are flushed to disk immediately after processing each frame.  
  <Admonition type="note" title="Note">
    This may lead to heavy I/O operations. A configurable flushing strategy is planned for future releases.
  </Admonition>

## Example Output

Each processed frame will produce a JSON line similar to:

```json
{
  "topic": "camera",
  "frame_id": "abc123",
  "texts": ["Detected text line 1", "Detected text line 2"]
}
```

When forwarding results in metadata, they are stored under the `ocr_texts` key in the frame metadata, with topics as keys:

```json
{
  "meta": {
    "ocr_texts": {
      "camera": ["Detected text line 1", "Detected text line 2"],
      "thermal": ["Temperature: 25°C"]
    }
  }
}
```

## When to Use

This filter is ideal for any pipeline that requires reading printed or handwritten text from images, such as:

- Scanned documents
- Signboards or product packaging in photos
- Scene text in videos
- Multi-camera systems with different text sources

## Configuration Reference

| Key              | Type       | Default                                        | Description |
|------------------|------------|------------------------------------------------|-------------|
| `ocr_engine`     | `string`   | `"easyocr"`                                    | OCR engine to use: `"tesseract"` or `"easyocr"` |
| `ocr_language`   | `string[]` | `["en"]`                                       | List of language codes for OCR |
| `output_json_path` | `string` | `"./output/ocr_results.json"`                 | Path to save output results |
| `debug`          | `boolean`  | `false`                                        | Enable debug logging |
| `tesseract_cmd`  | `string`   | Packaged AppImage path                         | Path to Tesseract binary |
| `forward_ocr_texts` | `boolean` | `true`                                      | Whether to forward OCR results in frame metadata |
| `write_output_file` | `boolean` | `false`                                    | Whether to write results to output file |
| `topic_pattern`  | `string`   | `null`                                         | Regex pattern to match topic names |
| `exclude_topics` | `string[]` | `[]`                                           | List of topics to exclude from OCR processing |
| `forward_upstream_data` | `boolean` | `true`                                  | Whether to forward non-image frames through the pipeline |

## Environment Variables

All configuration options can be overridden using environment variables with the prefix `FILTER_`. For example:

- `FILTER_OCR_ENGINE`
- `FILTER_OCR_LANGUAGE`
- `FILTER_DEBUG`
- `FILTER_TOPIC_PATTERN`
- `FILTER_EXCLUDE_TOPICS`
- `FILTER_FORWARD_UPSTREAM_DATA`

Boolean values should be set to "true" or "false" (case-insensitive).
List values should be comma-separated strings.
