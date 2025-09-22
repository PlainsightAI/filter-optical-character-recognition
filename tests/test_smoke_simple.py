"""
Smoke tests for OCR filter core behavior following Navar's guidelines.

Covers:
- Config normalization basics
- Processing multiple topics and forwarding behavior
- Ensuring 'main' appears first in outputs
"""

import numpy as np
import pytest
from unittest.mock import patch

from openfilter.filter_runtime.filter import Frame
from filter_optical_character_recognition.filter import (
    FilterOpticalCharacterRecognition,
    FilterOpticalCharacterRecognitionConfig,
    OCREngine,
)


class TestSmokeSimple:
    def create_frame(self, w=320, h=240):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        return Frame(img, {"meta": {"src": "file://test.mp4"}}, "BGR")

    def test_config_normalization(self):
        cfg = {
            "debug": False,
            "ocr_engine": OCREngine.EASYOCR.value,
            "forward_ocr_texts": True,
            "write_output_file": False,
            "forward_upstream_data": True,
        }
        normalized = FilterOpticalCharacterRecognition.normalize_config(cfg)
        assert normalized.forward_upstream_data is True
        assert normalized.forward_ocr_texts is True
        assert normalized.write_output_file is False

    @patch("filter_optical_character_recognition.filter.easyocr.Reader")
    def test_multi_topic_processing_and_main_first(self, mock_reader_cls):
        mock_reader = mock_reader_cls.return_value
        # Simulate no text results
        mock_reader.readtext.return_value = []

        cfg = FilterOpticalCharacterRecognitionConfig(
            ocr_engine=OCREngine.EASYOCR.value,
            write_output_file=False,
            forward_ocr_texts=True,
            forward_upstream_data=True,
        )

        filt = FilterOpticalCharacterRecognition(cfg)
        filt.setup(cfg)

        frames = {
            "stream2": self.create_frame(),
            "main": self.create_frame(),
            "data_only": Frame({"some": "data"}),
        }

        out = filt.process(frames)
        assert isinstance(out, dict)
        # main must be first
        assert list(out.keys())[0] == "main"
        # non-image forwarded when enabled
        assert "data_only" in out

    @patch("filter_optical_character_recognition.filter.easyocr.Reader")
    def test_upstream_forwarding_disabled(self, mock_reader_cls):
        mock_reader = mock_reader_cls.return_value
        mock_reader.readtext.return_value = []

        cfg = FilterOpticalCharacterRecognitionConfig(
            ocr_engine=OCREngine.EASYOCR.value,
            write_output_file=False,
            forward_ocr_texts=True,
            forward_upstream_data=False,
        )
        filt = FilterOpticalCharacterRecognition(cfg)
        filt.setup(cfg)

        frames = {
            "main": self.create_frame(),
            "telemetry": Frame({"only": "data"}),
        }
        out = filt.process(frames)
        assert "main" in out
        assert "telemetry" not in out  # not forwarded


