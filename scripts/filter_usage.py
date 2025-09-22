#!/usr/bin/env python

import argparse
import logging
import os
import sys

from openfilter.filter_runtime import Filter
from openfilter.filter_runtime.filters.video_in import VideoIn
from openfilter.filter_runtime.filters.webvis import Webvis

# Import our OCR filter
from filter_optical_character_recognition.filter import (
    FilterOpticalCharacterRecognition,
    FilterOpticalCharacterRecognitionConfig,
)

# Import the MultiSourceProducer filter to create multiple topics
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer import MultiSourceProducer, MultiSourceProducerConfig


def main():
    """
    Main function to run the OCR pipeline with multi-topic support.
    This demonstrates how to use the OCR filter with multiple input topics.
    """
    parser = argparse.ArgumentParser(
        description="Run the OCR filter with multiple input topics."
    )
    parser.add_argument(
        "--input",
        default=os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "video_example.mp4"
        ),
        help="Input video file path",
    )
    parser.add_argument(
        "--output_dir",
        default=os.path.join(os.path.dirname(__file__), "output"),
        help="Directory for output videos",
    )
    parser.add_argument(
        "--fps", type=int, default=5, help="Frames per second for output video"
    )
    parser.add_argument(
        "--ocr_engine",
        choices=["tesseract", "easyocr"],
        default="easyocr",
        help="OCR engine to use",
    )
    parser.add_argument(
        "--ocr_topic_pattern",
        default="region_.*",
        help="Regex pattern for OCR filter to process topics",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "ocr"), exist_ok=True)

    # Configure output paths
    ocr_json_path = os.path.join(args.output_dir, "ocr", "ocr_results.json")
    main_output = (
        f"file://{os.path.join(args.output_dir, 'main_output.mp4')}!fps={args.fps}"
    )

    # Print configuration summary
    print("OCR Demo Pipeline")
    print(f"Input: {args.input}")
    print(f"Output dir: {args.output_dir}")
    print(f"OCR engine: {args.ocr_engine}")
    print(f"OCR JSON path: {ocr_json_path}")
    print(f"Topic regex: {args.ocr_topic_pattern}")

    Filter.run_multi(
        [
            # Input video source
            (
                VideoIn,
                dict(
                    id="video_in",
                    sources=f"file://{args.input}!resize=960x540lin!loop",
                    outputs="tcp://127.0.0.1:6010",
                ),
            ),
            # Producer filter that generates synthetic image with text regions
            (
                MultiSourceProducer,
                MultiSourceProducerConfig(
                    id="producer",
                    sources="tcp://127.0.0.1:6010",
                    outputs="tcp://127.0.0.1:6012",
                    num_regions=5,
                    font_scale=2.0,
                    font_thickness=3,
                    padding=20,
                ),
            ),
            # OCR filter - processes selected topics and forwards non-image data when enabled
            (
                FilterOpticalCharacterRecognition,
                FilterOpticalCharacterRecognitionConfig(
                    id="ocr_filter",
                    sources="tcp://127.0.0.1:6012",
                    outputs="tcp://127.0.0.1:6014",
                    mq_log="pretty",
                    ocr_engine=args.ocr_engine,
                    topic_pattern=args.ocr_topic_pattern,
                    forward_ocr_texts=True,
                    write_output_file=True,
                    forward_upstream_data=True,
                    exclude_topics=["main"],
                ),
            ),
            # Web visualization for all streams
            (
                Webvis,
                dict(
                    id="webvis",
                    sources="tcp://127.0.0.1:6014",
                    port=8002,
                ),
            ),
        ]
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("filter_optical_character_recognition").setLevel(logging.DEBUG)
    logging.getLogger("filter_example").setLevel(logging.DEBUG)
    main()
