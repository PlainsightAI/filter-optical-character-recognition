import logging
import os
import json
import re
import easyocr
import pytesseract
from enum import Enum
from openfilter.filter_runtime.filter import FilterConfig, Filter, Frame
from dotenv import load_dotenv
from typing import Optional
import cv2
from pytesseract import Output

load_dotenv()

__all__ = [
    "FilterOpticalCharacterRecognitionConfig",
    "FilterOpticalCharacterRecognition",
]

logger = logging.getLogger(__name__)

SKIP_OCR_FLAG = "skip_ocr"


class OCREngine(Enum):
    """
    Enumeration of supported OCR engines.

    Attributes:
        TESSERACT: Uses Tesseract OCR engine
        EASYOCR: Uses EasyOCR engine
    """

    TESSERACT = "tesseract"
    EASYOCR = "easyocr"

    @classmethod
    def from_str(cls, value: str) -> "OCREngine":
        """
        Convert a string to an OCREngine enum value.

        Args:
            value (str): String representation of the OCR engine

        Returns:
            OCREngine: Corresponding enum value

        Raises:
            ValueError: If the string doesn't match any enum value
        """
        # Already an enum instance
        if isinstance(value, OCREngine):
            return value

        # Normalize text like "OCREngine.EASYOCR" or "ocrengine.easyocr" → "easyocr"
        text = str(value).strip().lower()
        if "." in text:
            text = text.split(".")[-1]
        try:
            return cls(text)
        except ValueError:
            raise ValueError(
                f"Invalid mode: {value!r}. Expected one of: {[s.value for s in cls]}"
            )


class FilterOpticalCharacterRecognitionConfig(FilterConfig):
    """
    Configuration for the OCR filter.

    Attributes:
        debug (bool): Enable debug logging (default: False)
        ocr_engine (OCREngine): OCR engine to use (default: EASYOCR)
        output_json_path (str): Path to save OCR results (default: './output/ocr_results.json')
        ocr_language (list[str]): List of languages for OCR (default: ['en'])
        tesseract_cmd (str): Path to Tesseract executable
        forward_ocr_texts (bool): Forward OCR results in frame metadata (default: True)
        write_output_file (bool): Write results to output file (default: True)
        topic_pattern (str | None): Regex pattern to match topic names (default: None)
        exclude_topics (list[str]): List of topics to exclude from OCR processing.
            Can be exact topic names or regex patterns (default: [])
        draw_visualization (bool): Enable visualization of OCR text in their bounding boxes (default: False)
        visualization_topic (str): Topic name for the visualization output (default: "viz")
        visualization_resize_factor (float): Factor to resize the visualization by (default: 0.5)
        text_scale_factor (float): Factor to scale text size independently (default: 1.0)
        frame_skip (int): Process OCR only every N frames to improve performance (default: 1)
        confidence_threshold (float): Minimum confidence threshold for EasyOCR (default: 0.2)
        gpu (bool): Use GPU for EasyOCR if available (default: True)
        optimize_params (bool): Use optimized parameters for EasyOCR (default: True)
        video_chunks_dir (str): Directory path containing video chunks (default: './video_chunks')
    """

    debug: Optional[bool] = False
    ocr_engine: Optional[OCREngine] = OCREngine.EASYOCR.value
    output_json_path: Optional[str] = "./output/ocr_results.json"
    ocr_language: Optional[list[str]] = ["en"]
    tesseract_cmd: Optional[
        str
    ] = f"{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin', 'tesseract', 'tesseract.AppImage'))}"
    forward_ocr_texts: Optional[bool] = True
    write_output_file: Optional[bool] = True
    topic_pattern: Optional[str | None] = None
    exclude_topics: Optional[list[str]] = []
    # Visualization options
    draw_visualization: Optional[bool] = False
    visualization_topic: Optional[str] = "viz"
    visualization_resize_factor: Optional[float] = 1.0
    text_scale_factor: Optional[float] = 1.0
    # Performance optimization options
    frame_skip: Optional[int] = 1
    confidence_threshold: Optional[float] = 0.2
    gpu: Optional[bool] = True
    optimize_params: Optional[bool] = True
    # Video chunks directory
    video_chunks_dir: Optional[str] = "/output/"
    # Forward non-image upstream data frames as-is
    forward_upstream_data: Optional[bool] = True


class FilterOpticalCharacterRecognition(Filter):
    """
    A filter that performs Optical Character Recognition (OCR) on input frames.

    This filter can:
    1. Process multiple input topics matching a specified pattern
    2. Use either Tesseract or EasyOCR engine for text extraction
    3. Support multiple languages for OCR
    4. Forward OCR results in frame metadata
    5. Write results to a JSON file

    Configuration:
    See FilterOpticalCharacterRecognitionConfig for available optionsw

    Processing:
        1. Filters input topics based on pattern if specified
        2. Performs OCR on each selected frame
        3. Stores results in frame metadata
        4. Writes results to output file if configured
    """

    @classmethod
    def normalize_config(
        cls, config: "FilterOpticalCharacterRecognitionConfig"
    ) -> "FilterOpticalCharacterRecognitionConfig":
        """
        Normalize and validate the filter configuration.

        Args:
            config (FilterOpticalCharacterRecognitionConfig): Input configuration

        Returns:
            FilterOpticalCharacterRecognitionConfig: Normalized configuration

        Raises:
            ValueError: If configuration values are invalid
            TypeError: If configuration values have incorrect types
        """
        # First, let the base class do its normalization
        base_normalized = super().normalize_config(config)

        # If a raw dict was provided, coerce string values to proper types
        if isinstance(base_normalized, dict):
            direct_mapping = {
                "debug": (bool, lambda x: str(x).strip().lower() == "true"),
                "ocr_engine": (str, lambda x: str(x).strip()),
                "output_json_path": (str, lambda x: str(x).strip()),
                "ocr_language": (list, lambda x: [lang.strip() for lang in str(x).split(",")] if isinstance(x, str) else x),
                "tesseract_cmd": (str, lambda x: str(x).strip()),
                "forward_ocr_texts": (bool, lambda x: str(x).strip().lower() == "true"),
                "write_output_file": (bool, lambda x: str(x).strip().lower() == "true"),
                "topic_pattern": (str, lambda x: str(x).strip()),
                "exclude_topics": (list, lambda x: json.loads(x) if isinstance(x, str) and x.strip().startswith("[") else ([t.strip() for t in str(x).split(",")] if isinstance(x, str) else x)),
                "draw_visualization": (bool, lambda x: str(x).strip().lower() == "true"),
                "visualization_topic": (str, lambda x: str(x).strip()),
                "visualization_resize_factor": (float, lambda x: float(str(x).strip())),
                "text_scale_factor": (float, lambda x: float(str(x).strip())),
                "frame_skip": (int, lambda x: int(str(x).strip())),
                "confidence_threshold": (float, lambda x: float(str(x).strip())),
                "gpu": (bool, lambda x: str(x).strip().lower() == "true"),
                "optimize_params": (bool, lambda x: str(x).strip().lower() == "true"),
                "video_chunks_dir": (str, lambda x: str(x).strip()),
                "forward_upstream_data": (bool, lambda x: str(x).strip().lower() == "true"),
            }

            for key, (expected_type, converter) in direct_mapping.items():
                if key in base_normalized and base_normalized[key] is not None:
                    val = base_normalized[key]
                    # Only convert if it's a string or mismatched type
                    if isinstance(val, str) or not isinstance(val, expected_type):
                        try:
                            base_normalized[key] = converter(val)
                        except Exception:
                            # Keep original; validation below will raise a clear error
                            pass

        # Now construct the config object
        config = FilterOpticalCharacterRecognitionConfig(base_normalized)

        # Environment variable mapping with type information
        env_mapping = {
            "debug": (bool, lambda x: x.strip().lower() == "true"),
            "ocr_engine": (str, str.strip),
            "output_json_path": (str, str.strip),
            "ocr_language": (list, lambda x: [lang.strip() for lang in x.split(",")]),
            "tesseract_cmd": (str, str.strip),
            "forward_ocr_texts": (bool, lambda x: x.strip().lower() == "true"),
            "write_output_file": (bool, lambda x: x.strip().lower() == "true"),
            "topic_pattern": (str, str.strip),
            "exclude_topics": (
                list,
                lambda x: json.loads(x)
                if x.strip().startswith("[")
                else [topic.strip() for topic in x.split(",")],
            ),
            "draw_visualization": (bool, lambda x: x.strip().lower() == "true"),
            "visualization_topic": (str, str.strip),
            "visualization_resize_factor": (float, lambda x: float(x.strip())),
            "text_scale_factor": (float, lambda x: float(x.strip())),
            "frame_skip": (int, lambda x: int(x.strip())),
            "confidence_threshold": (float, lambda x: float(x.strip())),
            "gpu": (bool, lambda x: x.strip().lower() == "true"),
            "optimize_params": (bool, lambda x: x.strip().lower() == "true"),
            "video_chunks_dir": (str, str.strip),
            "forward_upstream_data": (bool, lambda x: x.strip().lower() == "true"),
        }

        # Process environment variables
        for key, (expected_type, converter) in env_mapping.items():
            env_key = f"FILTER_{key.upper()}"
            env_val = os.getenv(env_key)
            if env_val is not None:
                try:
                    converted_val = converter(env_val)
                    if not isinstance(converted_val, expected_type):
                        raise TypeError(
                            f"Environment variable {env_key} must be of type {expected_type.__name__}"
                        )
                    setattr(config, key, converted_val)
                except Exception as e:
                    raise ValueError(
                        f"Failed to convert environment variable {env_key}: {str(e)}"
                    )

        # Validate debug mode
        if not isinstance(config.debug, bool):
            raise TypeError("debug must be a boolean")

        # Validate OCR engine
        if not isinstance(config.ocr_engine, (str, OCREngine)):
            raise TypeError("ocr_engine must be a string or OCREngine enum")
        try:
            config.ocr_engine = OCREngine.from_str(config.ocr_engine)
        except ValueError as e:
            raise ValueError(f"Invalid OCR engine: {str(e)}")

        if config.ocr_engine == OCREngine.TESSERACT and config.ocr_language == ["en"]:
            config.ocr_language = ["eng"]

        # Validate output path
        if not isinstance(config.output_json_path, str):
            raise TypeError("output_json_path must be a string")
        if not config.output_json_path.endswith(".json"):
            raise ValueError("output_json_path must end with .json")

        # Validate language list
        if not isinstance(config.ocr_language, list):
            raise TypeError("ocr_language must be a list")
        if not all(isinstance(lang, str) for lang in config.ocr_language):
            raise TypeError("All elements in ocr_language must be strings")
        if not config.ocr_language:
            raise ValueError("ocr_language list cannot be empty")

        # Validate Tesseract command
        if not isinstance(config.tesseract_cmd, str):
            raise TypeError("tesseract_cmd must be a string")
        if config.ocr_engine == OCREngine.TESSERACT and not os.path.exists(
            config.tesseract_cmd
        ):
            raise ValueError(
                f"Tesseract executable not found at {config.tesseract_cmd}"
            )

        # Validate boolean flags
        for flag in ["forward_ocr_texts", "write_output_file", "forward_upstream_data"]:
            if not isinstance(getattr(config, flag), bool):
                raise TypeError(f"{flag} must be a boolean")

        # Validate topic pattern
        if config.topic_pattern is not None:
            if not isinstance(config.topic_pattern, str):
                raise TypeError("topic_pattern must be a string or None")
            try:
                re.compile(config.topic_pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {str(e)}")

        # Validate exclude topics
        if not isinstance(config.exclude_topics, list):
            raise TypeError("exclude_topics must be a list")
        if not all(isinstance(topic, str) for topic in config.exclude_topics):
            raise TypeError("All elements in exclude_topics must be strings")
        # Validate that each exclude pattern is either a valid regex or a valid topic name
        for pattern in config.exclude_topics:
            try:
                re.compile(pattern)
            except re.error:
                # If it's not a valid regex, it should be treated as an exact topic name
                if not pattern.strip():
                    raise ValueError("Empty topic name in exclude_topics")
                if not pattern.isidentifier():
                    raise ValueError(f"Invalid topic name in exclude_topics: {pattern}")

        # Validate visualization settings
        if not isinstance(config.draw_visualization, bool):
            raise TypeError("draw_visualization must be a boolean")

        if not isinstance(config.visualization_topic, str):
            raise TypeError("visualization_topic must be a string")

        if config.visualization_topic == "":
            raise ValueError(
                "visualization_topic cannot be empty if visualization is enabled"
            )

        if not isinstance(config.visualization_resize_factor, float):
            raise TypeError("visualization_resize_factor must be a float")

        if (
            config.visualization_resize_factor <= 0
            or config.visualization_resize_factor > 1.0
        ):
            raise ValueError("visualization_resize_factor must be between 0 and 1.0")

        if not isinstance(config.text_scale_factor, float):
            raise TypeError("text_scale_factor must be a float")

        if config.text_scale_factor <= 0:
            raise ValueError("text_scale_factor must be greater than 0")

        # Validate performance optimization settings
        if not isinstance(config.frame_skip, int):
            raise TypeError("frame_skip must be an integer")
        if config.frame_skip < 1:
            raise ValueError("frame_skip must be at least 1")

        if not isinstance(config.confidence_threshold, float):
            raise TypeError("confidence_threshold must be a float")
        if config.confidence_threshold < 0 or config.confidence_threshold > 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1.0")

        if not isinstance(config.gpu, bool):
            raise TypeError("gpu must be a boolean")

        if not isinstance(config.optimize_params, bool):
            raise TypeError("optimize_params must be a boolean")

        return config

    def setup(self, config: FilterOpticalCharacterRecognitionConfig):
        """
        Initialize the OCR filter with configuration.

        Args:
            config (FilterOpticalCharacterRecognitionConfig): Filter configuration

        Raises:
            ValueError: If configuration is invalid
            Exception: If output file cannot be opened
        """
        # Normalize incoming config to ensure enums/booleans are correct
        config = self.normalize_config(config)

        logger.info("===========================================")
        logger.info(f"FilterOpticalCharacterRecognition setup: {config}")
        logger.info("===========================================")

        self.ocr_engine = config.ocr_engine
        self.output_json_path = config.output_json_path
        self.debug = config.debug
        self.language = config.ocr_language
        self.forward_ocr_texts = config.forward_ocr_texts
        self.write_output_file = config.write_output_file
        self.topic_pattern = config.topic_pattern
        self.exclude_topics = config.exclude_topics
        self.output_file = None
        self.subject_data = list()
        # Visualization settings
        self.draw_visualization = config.draw_visualization
        self.visualization_topic = config.visualization_topic
        self.visualization_resize_factor = config.visualization_resize_factor
        self.text_scale_factor = config.text_scale_factor
        # Performance optimization settings
        self.frame_skip = config.frame_skip
        self.confidence_threshold = config.confidence_threshold
        self.gpu = config.gpu
        self.optimize_params = config.optimize_params
        self.frame_counter = 0
        # Cache for OCR results to reuse during skipped frames
        self.ocr_cache = {}
        # Video chunks directory
        self.video_chunks_dir = config.video_chunks_dir
        # Upstream forwarding behavior
        self.forward_upstream_data = config.forward_upstream_data

        if self.topic_pattern:
            try:
                self.topic_regex = re.compile(self.topic_pattern)
                logger.info(f"Using topic pattern: {self.topic_pattern}")
            except re.error as e:
                logger.error(f"Invalid regex pattern '{self.topic_pattern}': {e}")
                raise ValueError(f"Invalid regex pattern: {e}")
        else:
            self.topic_regex = None
            logger.info("No topic pattern specified, will process all topics")

        if self.ocr_engine == OCREngine.TESSERACT:
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd
        elif self.ocr_engine == OCREngine.EASYOCR:
            gpu_param = self.gpu  # Only use GPU if specifically enabled
            logger.info(
                f"Initializing EasyOCR with languages: {self.language}, GPU: {gpu_param}"
            )
            self.easyocr_reader = easyocr.Reader(self.language, gpu=gpu_param)
        else:
            raise ValueError("Invalid OCR engine selection.")

        if config.debug:
            logger.setLevel(logging.DEBUG)

        if self.write_output_file:
            os.makedirs(os.path.dirname(self.output_json_path), exist_ok=True)
            try:
                self.output_file = open(self.output_json_path, "a", encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to open output JSON file: {e}")
                raise

    def shutdown(self):
        """
        Clean up resources when the filter is shutting down.

        Closes the output file if it was opened and logs the shutdown status.
        """
        if self.output_file:
            self.output_file.close()
            logger.info("Closed output JSON file.")
            # Save subject data to JSON file
            # Save subject data to JSON file
            subject_data_file = os.path.join(
                os.path.dirname(self.output_json_path), "subject_data.json"
            )
            with open(subject_data_file, "w") as f:
                json.dump(self.subject_data, f, indent=4)

            logger.info(f"Saved subject data to {subject_data_file}")

        if self.write_output_file:
            logger.info(
                f"OCR Filter shutting down. Processed data saved at {self.output_json_path}"
            )
        else:
            logger.info("OCR Filter shutting down. No output file was written.")

    def draw_text_visualization(self, image, texts):
        """
        Overlay all recognized OCR text on the image.

        Args:
            image: Original image
            texts: List of OCR text strings

        Returns:
            Annotated image with text drawn in a list-style overlay
        """
        vis_image = image.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(
            0.3, 0.5 * self.visualization_resize_factor * self.text_scale_factor
        )
        font_thickness = max(1, int(self.text_scale_factor))
        font_color = (0, 255, 0)  # Green text
        line_height = int(20 * self.text_scale_factor)

        for i, text in enumerate(texts):
            y = 30 + i * line_height
            cv2.putText(
                vis_image, text, (10, y), font, font_scale, font_color, font_thickness
            )

        if self.visualization_resize_factor != 1.0:
            new_w = int(vis_image.shape[1] * self.visualization_resize_factor)
            new_h = int(vis_image.shape[0] * self.visualization_resize_factor)
            vis_image = cv2.resize(vis_image, (new_w, new_h))

        return vis_image

    def process(self, frames: dict[str, Frame]):
        # Initialize OCR results structure
        ocr_results: dict[str, dict[str, list]] = {}
        processed_topics = []

        # Frame skipping for performance optimization
        self.frame_counter += 1
        should_run_ocr = self.frame_counter % self.frame_skip == 0

        # If skipping this frame, use cached results if available
        if not should_run_ocr and self.ocr_cache:
            logger.debug(
                f"Skipping OCR on frame {self.frame_counter}, using cached results"
            )
            ocr_results = self.ocr_cache
        else:
            for topic, frame in frames.items():
                # Skip non-image frames for OCR, may be forwarded later
                if not getattr(frame, 'has_image', False):
                    continue
                # Check if topic should be excluded (either exact match or regex pattern)
                should_exclude = False
                for pattern in self.exclude_topics:
                    try:
                        if re.match(pattern, topic):
                            should_exclude = True
                            break
                    except re.error:
                        # If pattern is not a valid regex, treat it as an exact match
                        if pattern == topic:
                            should_exclude = True
                            break

                if should_exclude:
                    logger.debug(
                        f"Skipping OCR for topic {topic} as it matches exclude pattern"
                    )
                    continue

                # Skip if topic doesn't match pattern (if pattern is specified)
                if self.topic_regex and not self.topic_regex.search(topic):
                    logger.debug(
                        f"Skipping OCR for topic {topic} due to topic_regex mismatch"
                    )
                    continue

                frame_meta = frame.data.get("meta", {})
                if frame_meta.get(SKIP_OCR_FLAG, False):
                    logger.debug(f"Skipping OCR for topic {topic} due to skip_ocr flag")
                    continue

                processed_topics.append(topic)
                image = frame.rw_bgr.image
                frame_id = frame_meta.get("id", None)
                texts: list[str] = []
                confidences: list[float] = []

                if self.ocr_engine == OCREngine.TESSERACT:
                    data = pytesseract.image_to_data(
                        image, lang="+".join(self.language), output_type=Output.DICT
                    )
                    lines: dict[int, dict[str, list]] = {}
                    for i, word in enumerate(data["text"]):
                        txt = word.strip()
                        if not txt:
                            continue
                        ln = data["line_num"][i]
                        try:
                            conf = int(data["conf"][i])
                        except Exception:
                            conf = 0

                        if ln not in lines:
                            lines[ln] = {"words": [], "confs": []}
                        lines[ln]["words"].append(txt)
                        lines[ln]["confs"].append(conf)

                    for ln in sorted(lines):
                        words = lines[ln]["words"]
                        confs = lines[ln]["confs"]
                        texts.append(" ".join(words))
                        # confidence per line
                        line_conf = sum(confs) / len(confs)
                        confidences.append(line_conf / 100.0)

                elif self.ocr_engine == OCREngine.EASYOCR:
                    # Use optimized parameters if configured
                    if self.optimize_params:
                        # optimized branch: still ask for (bbox, text, conf)
                        results = self.easyocr_reader.readtext(
                            image,
                            detail=1,
                            paragraph=False,
                            min_size=3,
                            contrast_ths=0.1,
                            adjust_contrast=0.5,
                            text_threshold=self.confidence_threshold,
                        )
                        for _, txt, conf in results:
                            if conf >= self.confidence_threshold:
                                texts.append(txt)
                                confidences.append(conf)
                    else:
                        results = self.easyocr_reader.readtext(image, detail=1)
                        texts = [t for _, t, _ in results]
                        confidences = [c for _, _, c in results]
                else:
                    raise ValueError("Invalid OCR engine selected.")

                # ocr confidence per frame
                avg_confidence = 0.0
                if confidences:
                    avg_confidence = round(sum(confidences) / len(confidences), 4)

                # Store OCR results in the appropriate structure
                if self.forward_ocr_texts:
                    main_frame = frames.get("main")
                    if main_frame:
                        ocr_results.update(
                            {topic: {"texts": texts, "ocr_confidence": avg_confidence}}
                        )

                if self.output_file and topic == "main":
                    # Check if any frame has skip_ocr=True
                    should_skip = any(
                        f.data.get("meta", {}).get(SKIP_OCR_FLAG, False)
                        for f in frames.values()
                    )
                    if not should_skip:
                        ocr_result = {
                            "topic": topic,
                            "frame_id": frame_id,
                            "texts": texts,
                            "ocr_confidence": avg_confidence,
                        }
                        self.output_file.write(
                            json.dumps(ocr_result, ensure_ascii=False) + "\n"
                        )
                        self.output_file.flush()

            # Cache results for future frames
            if should_run_ocr:
                self.ocr_cache = ocr_results.copy()

        # Prepare result dictionary with updated OCR metadata per frame
        output_frames = {}

        for topic, frame in frames.items():
            # Forward non-image frames as-is if enabled
            if not getattr(frame, 'has_image', False):
                if self.forward_upstream_data:
                    output_frames[topic] = frame
                continue
            # Start with original metadata
            meta = dict(frame.data.get("meta", {}))

            # Add OCR texts if forwarding is enabled
            if self.forward_ocr_texts:
                meta["ocr_texts"] = ocr_results.get(topic, {}).get("texts", [])
                meta["ocr_confidence"] = ocr_results.get(topic, {}).get(
                    "ocr_confidence", 0.0
                )

            # Add the frame to result
            output_frames[topic] = Frame(frame.rw_bgr.image, {"meta": meta}, "BGR")

        # Write subject data only once for main frame (or any one frame)
        if self.write_output_file:
            main_meta = output_frames["main"].data.get("meta", {})
            self.subject_data.append({"meta": main_meta})

        # Add visualization frame if enabled
        if self.draw_visualization:
            main_frame = frames["main"]
            texts = ocr_results.get("main", {}).get("texts", []) if self.forward_ocr_texts else []
            vis_image = self.draw_text_visualization(main_frame.rw_bgr.image, texts)
            output_frames[self.visualization_topic] = Frame(vis_image, {}, "BGR")

        # Ensure main topic comes first in the output dictionary
        if 'main' in output_frames:
            main_frame = output_frames.pop('main')
            return {'main': main_frame, **output_frames}

        return output_frames


if __name__ == "__main__":
    FilterOpticalCharacterRecognition.run()
