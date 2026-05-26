---
name: deepseek-image-ocr
description: Use when Codex needs DeepSeek or another text-only/OpenAI-compatible model such as Reasonix to analyze image files, screenshots, scanned documents, photos with text, UI screenshots, forms, receipts, charts, or diagrams by first extracting OCR text and image metadata, then passing the structured evidence to the model for reasoning.
---

# DeepSeek Image OCR

## Core Idea

DeepSeek text models do not receive pixels in this workflow. Convert the image into structured evidence first: OCR text, image dimensions, filename context, and any visible layout notes Codex can infer. Then ask DeepSeek, Reasonix, or another OpenAI-compatible text model to reason over that evidence.

Use the bundled script for repeatable OCR and optional model calls:

```powershell
& "C:\Users\gongz\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" C:\Users\gongz\.codex\skills\deepseek-image-ocr\scripts\image_ocr_bridge.py image.png --question "What does this screenshot say?"
```

## Workflow

1. Locate the image path. If the image is attached in the conversation, use the available local file path or save/export path supplied by the app.
2. Run OCR extraction:

```powershell
& "C:\Users\gongz\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" C:\Users\gongz\.codex\skills\deepseek-image-ocr\scripts\image_ocr_bridge.py path\to\image.png --format markdown
```

3. If OCR is empty, try another language or page segmentation mode:

```powershell
& "C:\Users\gongz\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" C:\Users\gongz\.codex\skills\deepseek-image-ocr\scripts\image_ocr_bridge.py path\to\image.png --lang chi_sim+eng --psm 11
```

4. If a model call is requested, set the provider environment variables and pass `--ask`:

```powershell
$env:DEEPSEEK_API_KEY="..."
& "C:\Users\gongz\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" C:\Users\gongz\.codex\skills\deepseek-image-ocr\scripts\image_ocr_bridge.py image.png --ask --question "Summarize the important content."
```

5. Treat the model response as text-grounded analysis. Mention OCR uncertainty when the image is low resolution, rotated, handwritten, visually dense, or text extraction is sparse.

## Providers

- DeepSeek default: `DEEPSEEK_API_KEY`, optional `DEEPSEEK_BASE_URL`, optional `DEEPSEEK_MODEL`.
- Reasonix-compatible: `REASONIX_API_KEY`, `REASONIX_BASE_URL`, optional `REASONIX_MODEL`, then run with `--provider reasonix`.
- Custom OpenAI-compatible endpoint: use `--provider custom --base-url ... --api-key-env ENV_NAME --model MODEL`.

The script sends only extracted text and metadata unless the chosen endpoint is explicitly extended later to support images.

## OCR Notes

- Prefer Tesseract when available. Install the `tesseract` executable and language packs for best results.
- Use `--lang eng` for English, `--lang chi_sim+eng` for simplified Chinese and English, and `--lang chi_tra+eng` for traditional Chinese and English.
- Use `--psm 6` for blocks of text, `--psm 11` for sparse screenshots/UI, and `--psm 3` for automatic page segmentation.
- For charts or diagrams, include Codex-visible observations in the prompt because OCR only captures labels, not visual relationships.

## Output Discipline

When answering the user, separate:

- **Observed OCR text**: what the script extracted.
- **Visual/context notes**: what Codex can infer from the image file or screenshot.
- **Model reasoning**: DeepSeek/Reasonix conclusions based on the extracted evidence.

Do not claim the text model directly saw the image unless a true vision-capable endpoint was used.
