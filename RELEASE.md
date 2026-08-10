# Changelog
TextScan release notes


## [Unreleased]

### Changed

- Bump the openfilter dependency to 1.2.2

## v0.1.12 - 2026-08-04

### Changed
- Update `openfilter[all]` to `>=1.2.1`.
- Grant `id-token: write` in `create-release.yaml` so the public release workflow can produce a keyless (cosign) SBOM attestation for the published image (once the shared SBOM steps land).
- Pin the Docker base to `python:3.11.12-slim` (was `python:3.11-slim`).
- Point the compose utility images at `containers.openfilter.io/plainsightai/openfilter-{video-in,webvis}:1.2.1`, and pin the filter's own `docker-compose.yaml` image to the release version (`openfilter-optical-character-recognition:0.1.12`).
- Update dev-tooling floors (`setuptools>=83.0.0`) and switch dev pins to range pins.

## v0.1.11 - 2026-07-30

### Changed

- Update the openfilter dependency to `>=1.2.0,<2.0.0` (openfilter 1.2.0 moves to OpenCV 5).

## v0.1.10 - 2026-04-23

### Changed
- Update the openfilter dependency to `>=0.1.30`, and align the CI workflow with the shared release gate (source-paths).
- Fix release workflow secret names: `PYPI_API_TOKEN` → `PLAINSIGHT_PYPI_TOKEN`, `DOCKERHUB_TOKEN` → `DOCKERHUB_ACCESS_TOKEN` (org-level secret names). Without this the PyPI / Docker Hub tokens resolved to empty and no package has been published since the migration.
- Remove redundant ci.yaml (shared workflow handles PR testing)
- Add push + pull_request triggers to create-release.yaml


## v0.1.8 - 2026-04-17

### Changed
- Add CI/CD workflows: create-release.yaml (Docker Hub publishing), ci.yaml (PR testing), security-scan.yaml
- Update openfilter dependency to >=0.1.27
- Add Makefile IMAGE for Docker Hub
- Loosen build dependency to >=1.2.2


## v0.1.7 - 2025-09-27

### Changed
- Updated documentation.

## v0.1.6 - 2025-09-22

### Added
- **Multi-topic processing** - Process multiple video regions simultaneously using pub/sub topics
- **Data forwarding** - New `forward_upstream_data` configuration to forward non-image frames
- **Main-first ordering** - Ensures consistent output structure with 'main' topic first
- **Enhanced configuration normalization** - Robust string-to-type coercion and validation
- **Comprehensive test suite** - Added `test_smoke_simple.py` and `test_integration_config_normalization.py`
- **Environment variable support** - `FILTER_FORWARD_UPSTREAM_DATA` for data forwarding control

### Changed
- **Improved `process()` method** - Complete rewrite to handle multi-topic processing
- **Enhanced `OCREngine.from_str()`** - Better handling of various input formats
- **Updated `normalize_config()`** - Comprehensive configuration validation and type coercion
- **Updated documentation** - README.md and docs/overview.md reflect new multi-topic capabilities
- **Updated usage script** - `scripts/filter_usage.py` now demonstrates multi-topic processing

### Technical Improvements
- **Performance optimization** - Efficient processing of multiple topics in single pass
- **Error handling** - Robust validation and graceful error handling
- **Code consistency** - Follows established patterns from other Plainsight filters

## v0.1.5 - 2025-08-12

### Modified
- Lock Setuptools-SCM version

## v0.1.4 - 2025-08-06

### Modified
- Support for model info 
- Updated dependencies

## v0.1.3 - 2025-07-30

### Added
- Support for model info

## v0.1.2 - 2025-07-14

### Changed
- Removed unnecessary imports
- Updated openfilter version in pyproject

### Added
- Feature that computes and sends ocr confidence score for each frame to `metadata`
- Each entry in output jsons now include detected `ocr_confidence`
- Support for `ocr_language=eng` for tesseract
- Tests for ocr confidence score

## v0.1.1 - 2025-05-22

### Changed
- Update dependencies

## v0.1.0 - 2025-05-22

### Added
- Initial release of TextScan to extract text from image frames using OCR engines.
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
