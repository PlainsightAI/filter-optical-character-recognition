# 🔤 Optical Character Recognition (OCR) Filter

**OCR Filter** is a modular [OpenFilter](https://github.com/PlainsightAI/openfilter)-based filter for extracting text from video frames using EasyOCR or Tesseract.

It supports frame-by-frame OCR, optional skipping via metadata, and flexible deployment as part of OpenFilter pipelines.

[![PyPI version](https://img.shields.io/pypi/v/filter-optical-character-recognition.svg?style=flat-square)](https://pypi.org/project/filter-optical-character-recognition/)
[![Docker Version](https://img.shields.io/docker/v/plainsightai/openfilter-optical-character-recognition?sort=semver)](https://hub.docker.com/r/plainsightai/openfilter-optical-character-recognition)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/PlainsightAI/filter-optical-character-recognition/blob/main/LICENSE)
![Build Status](https://github.com/PlainsightAI/filter-optical-character-recognition/actions/workflows/ci.yaml/badge.svg)

---

## ✨ Features

* 🧾 Extracts text using EasyOCR or Tesseract from frames
* 🔍 Supports per-frame metadata control (e.g. skip OCR)
* ⚙️ Configurable via CLI args, code, or environment variables
* 🧩 Plug-and-play compatibility with [OpenFilter](https://github.com/PlainsightAI/openfilter)
* 📤 Outputs recognized text, ocr confidence score and bounding boxes as metadata

---

## 📦 Installation

Install the latest version from PyPI:

```bash
pip install filter-optical-character-recognition
```

Or install from source:

```bash
# Clone the repo
git clone https://github.com/PlainsightAI/filter-optical-character-recognition.git
cd filter-optical-character-recognition

# (Optional but recommended) create a virtual environemnt:
python -m venv venv && source venv/bin/activate

# Install the filter
make install
```

> 💡 The `make install` target installs `openfilter[all]`, ensuring dependencies like `VideoIn` and `Webvis` work out of the box.

---

## 🚀 Quick Start (CLI)

Run the OCR Filter using the OpenFilter CLI:

```bash
# Most basic version, no annotion or result logging
openfilter run \
  - VideoIn --sources 'file://video_example.mp4!loop' \
  - filter_optical_character_recognition.filter.FilterOpticalCharacterRecognition \
  - Webvis

# Log results into stdout
openfilter run \
  - VideoIn --sources 'file://video_example.mp4!loop' \
  - filter_optical_character_recognition.filter.FilterOpticalCharacterRecognition \
    --mq_log pretty
  - Webvis

# Annotation enabled, overlaying detected text out output
openfilter run \
  - VideoIn --sources 'file://video_example.mp4!loop' \
  - filter_optical_character_recognition.filter.FilterOpticalCharacterRecognition \
      --ocr_engine easyocr \
      --forward_ocr_texts true \
      --draw_visualization true \
      --visualization_topic "main" \
      --topic_pattern "main" \
  - Webvis
```

Or simply:

```bash
make run
```

Then open [http://localhost:8000](http://localhost:8000) to view the output.

> 📄 See the [`.env.example` file](https://github.com/PlainsightAI/filter-optical-character-recognition/blob/main/.env.example) for environment variable options.

---

## 🧰 Using from PyPI

After installing with:

```bash
pip install filter-optical-character-recognition
```

you can use the OCR Filter directly in code:

### Example usage

```python
from openfilter.filter_runtime.filter import Filter
from openfilter.filter_runtime.filters.video_in import VideoIn
from openfilter.filter_runtime.filters.webvis import Webvis
from filter_optical_character_recognition.filter import FilterOpticalCharacterRecognition

if __name__ == "__main__":
    Filter.run_multi([
      (VideoIn, dict(
          sources='file://video_example.mp4!loop',
          outputs='tcp://*:5550'
      )),
      (FilterOpticalCharacterRecognition, dict(
          sources='tcp://localhost:5550',
          outputs='tcp://*:5552',
          draw_visualization=True,
          visualization_topic="main"
      )),
      (Webvis, dict(
          sources='tcp://localhost:5552'
      )),
    ])
```

---

## 🧪 Testing

Run tests locally:

```bash
make test
```

Or run a specific test file:

```bash
pytest -v tests/test_filter_ocr.py
```

Tests cover:

* OCR accuracy and bounding box parsing
* `skip_ocr` handling
* Frame metadata propagation
* Integration in multi-filter pipelines

---

## 🔧 Special Features

### Metadata-Based Skipping

You can skip OCR on specific frames by setting this field:

```json
"meta": {
  "skip_ocr": true
}
```

This allows selective processing and performance tuning.

---

## 🔩 Requirements

The OCR Filter depends on the following tools:

* [`easyocr`](https://github.com/JaidedAI/EasyOCR)
* [`pytesseract`](https://github.com/madmaze/pytesseract)
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) binary (AppImage or system install)

Ensure the tesseract binary is available in your environment when running OCR with Tesseract.

---

## 🤝 Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](https://github.com/PlainsightAI/filter-optical-character-recognition/blob/main/CONTRIBUTING.md) for instructions.

**Highlights**:

* Format code with `black`
* Lint with `ruff`
* Use type hints on public methods
* Sign commits using DCO (`git commit -s`)
* Include tests when relevant

---

## 📄 License

Licensed under the [Apache 2.0 License](https://github.com/PlainsightAI/filter-optical-character-recognition/blob/main/LICENSE).

---

## 🙏 Acknowledgements

Thanks for using the OCR Filter!
For questions or feature requests, [open a GitHub issue](https://github.com/PlainsightAI/filter-optical-character-recognition/issues/new/choose).
