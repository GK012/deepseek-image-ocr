# Provider Environment

Use environment variables so API keys are not written into prompts, shell history beyond the current session, or skill files.

## DeepSeek

```powershell
$env:DEEPSEEK_API_KEY="..."
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-chat"
```

## Reasonix or another OpenAI-compatible gateway

```powershell
$env:REASONIX_API_KEY="..."
$env:REASONIX_BASE_URL="https://your-reasonix-compatible-endpoint"
$env:REASONIX_MODEL="your-model"
```

Then run:

```powershell
& "C:\Users\gongz\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" C:\Users\gongz\.codex\skills\deepseek-image-ocr\scripts\image_ocr_bridge.py image.png --provider reasonix --ask
```
