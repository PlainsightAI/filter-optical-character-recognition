# Changelog
Optical character recognition filter release notes

## [Unreleased]

## v0.1.1 - 2025-05-22

### Changed
- Update dependencies

## v0.1.0 - 2025-05-22

### Added
- Initial release of OCR filter to extract text from image frames using OCR engines.
- Dual OCR Engine Support:
  - Supports both `tesseract` and `easyocr`
  - Selectable via the `ocr_engine` config field
- Multi-language OCR:
  - Accepts a list of language codes (e.g. `['en', 'zh']`) via `ocr_language`
- Output to JSON:
  - Writes OCR results per frame to a configurable `output_json_path`
  - Each entry includes `frame_id` and detected `texts`
- Debug Mode:
  - Optional `debug` mode enables verbose logging
- Frame-level Skipping:
  - Skips OCR for frames tagged with metadata flag `skip_ocr: true`
- Tesseract Binary Configurable:
  - Customizable Tesseract binary path via `tesseract_cmd` (defaults to packaged AppImage)
- Safe Streaming Output:
  - Results are flushed to disk in real-time to avoid data loss (future enhancement planned for configurable flush behavior)
- Support for `topic_pattern` configuration to selectively OCR frames based on topic name:
  - New env var: `FILTER_TOPIC_PATTERN`
  - Supports regular expressions to match topics
- Optional forwarding of OCR results into `frame.data['meta']['ocr_texts']` via `forward_ocr_texts` (default: true)
- Optional file output via `write_output_file` (default: true)
- Support for `.env` and `FILTER_*` environment variable overrides
- `docs/~internal` directory added (excluded from production)
- Enhanced documentation:
  - Detailed topic-based processing and environment variable config
  - Updated examples and configuration table
  - Multi-camera use case

### Changed
- Updated default config values to match implementation
- Improved configuration parsing:
  - Proper handling of booleans, lists, and validation
  - Clear error messages for invalid env vars
- Improved shutdown behavior and logging
- Reduced redundant OCR calls in Tesseract
- Improved FPS performance through internal tweaks
- Improved documentation readability and structure

### Fixed
- `FILTER_OCR_LANGUAGE` is now parsed correctly
- Fixed incorrect detection of PROMO labels as line items
- Fixed logic for `transaction_status` updates (ENG-1373)
- Replaced `external_id_type` with `external_id` (ENG-1371)
- Fixed double OCR processing and shutdown behavior issues
- Fixed template for temporary JSON Formatter

### Feature
- Added `frame_skip` variable to improve processing efficiency

### Internal
- Internal improvements and refactoring

### Experimental
- Temporary JSON Formatter added:
  - Enabled via `transform_to_mqtt` flag
  - Will be removed after integration with `JSONOutputFormaterFilter`

### Payload Enhancements
- `video_chunks` added to the outgoing payload
