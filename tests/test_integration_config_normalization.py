"""
Integration tests for OCR config normalization following Navar's pattern.
"""

import os
import pytest

from filter_optical_character_recognition.filter import (
    FilterOpticalCharacterRecognition,
    FilterOpticalCharacterRecognitionConfig,
)


class TestIntegrationConfigNormalization:
    def test_string_to_type_conversions(self):
        cfg = {
            "debug": "true",
            "ocr_engine": "easyocr",
            "forward_ocr_texts": "true",
            "write_output_file": "false",
            "frame_skip": "2",
            "confidence_threshold": "0.5",
            "gpu": "false",
            "optimize_params": "true",
            "visualization_resize_factor": "0.5",
            "text_scale_factor": "1.5",
            "forward_upstream_data": "true",
        }
        normalized = FilterOpticalCharacterRecognition.normalize_config(cfg)
        assert normalized.debug is True
        assert normalized.forward_ocr_texts is True
        assert normalized.write_output_file is False
        assert normalized.frame_skip == 2
        assert normalized.confidence_threshold == 0.5
        assert normalized.gpu is False
        assert normalized.optimize_params is True
        assert normalized.visualization_resize_factor == 0.5
        assert normalized.text_scale_factor == 1.5
        assert normalized.forward_upstream_data is True

    def test_boolean_validation(self):
        normalized = FilterOpticalCharacterRecognition.normalize_config({
            "forward_upstream_data": True
        })
        assert normalized.forward_upstream_data is True

    def test_runtime_keys_ignored(self):
        cfg = {
            "id": "ocr",
            "sources": "tcp://localhost:5550",
            "outputs": "tcp://localhost:5551",
            "forward_upstream_data": True,
        }
        normalized = FilterOpticalCharacterRecognition.normalize_config(cfg)
        assert normalized.forward_upstream_data is True

    def test_env_loading(self, monkeypatch):
        monkeypatch.setenv("FILTER_FORWARD_UPSTREAM_DATA", "false")
        normalized = FilterOpticalCharacterRecognition.normalize_config({})
        assert normalized.forward_upstream_data is False


