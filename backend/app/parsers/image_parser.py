"""Image parser — OCR via pytesseract + Pillow.

Graceful degradation
---------------------
Both pytesseract (Python binding) and the Tesseract binary are optional.
When either is absent the parser returns an empty result with a metadata flag
``ocr_available: false`` instead of raising ParserError, so images don't block
the processing pipeline.

To enable OCR:
    1. Install Tesseract:  https://tesseract-ocr.github.io/tessdoc/Installation
    2. pip install pytesseract Pillow
    3. Ensure the ``tesseract`` binary is on PATH (or set
       ``pytesseract.pytesseract.tesseract_cmd`` in your environment).
"""

from __future__ import annotations

import io

from app.parsers.base import DocumentParser, ExtractionResult, ParserError


def _ocr_available() -> bool:
    """Return True if both pytesseract and Pillow can be imported."""
    try:
        import PIL  # noqa: F401, PLC0415
        import pytesseract  # noqa: F401, PLC0415
        return True
    except ImportError:
        return False


class ImageParser(DocumentParser):
    """Extract text from PNG / JPEG images using Tesseract OCR."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        return frozenset({"image/png", "image/jpeg"})

    async def extract(self, content: bytes, filename: str) -> ExtractionResult:
        if not _ocr_available():
            return ExtractionResult(
                text="",
                word_count=0,
                parser_name="image",
                page_count=1,
                metadata={
                    "ocr_available": False,
                    "note": (
                        "OCR is not enabled on this server. "
                        "Install pytesseract and Tesseract to extract text from images."
                    ),
                },
            )
        return await self._run_sync(self._extract_sync, content, filename)

    @staticmethod
    def _extract_sync(content: bytes, filename: str) -> ExtractionResult:
        from PIL import Image  # noqa: PLC0415
        import pytesseract  # noqa: PLC0415

        try:
            image = Image.open(io.BytesIO(content))
        except Exception as exc:
            raise ParserError(f"Cannot open image '{filename}': {exc}") from exc

        width, height = image.size

        try:
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config="--psm 3",  # fully automatic page segmentation
            )
            # Collect words with non-empty text and confidence > 0.
            words = [
                w
                for w, conf in zip(ocr_data["text"], ocr_data["conf"])
                if w.strip() and int(conf) > 0
            ]
            confidences = [
                int(c)
                for c, w in zip(ocr_data["conf"], ocr_data["text"])
                if w.strip() and int(c) > 0
            ]
            text = pytesseract.image_to_string(image, config="--psm 3").strip()
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        except pytesseract.TesseractNotFoundError:
            return ExtractionResult(
                text="",
                word_count=0,
                parser_name="image",
                page_count=1,
                metadata={
                    "ocr_available": False,
                    "note": "Tesseract binary not found on PATH.",
                    "width": width,
                    "height": height,
                },
            )
        except Exception as exc:
            # A decodable image can still be rejected by an OCR dependency
            # (for example, a truncated scan accepted by Pillow's header
            # parser). Treat that as unavailable OCR rather than allowing one
            # problematic image to fail the whole evidence-processing job.
            return ExtractionResult(
                text="",
                word_count=0,
                parser_name="image",
                page_count=1,
                metadata={
                    "ocr_available": False,
                    "note": f"OCR could not process this image: {type(exc).__name__}.",
                    "width": width,
                    "height": height,
                },
            )

        return ExtractionResult(
            text=text,
            word_count=len(text.split()),
            parser_name="image",
            page_count=1,
            metadata={
                "ocr_available": True,
                "width": width,
                "height": height,
                "ocr_confidence": round(avg_conf, 2),
            },
        )
