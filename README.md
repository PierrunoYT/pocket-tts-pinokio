# PocketTTS Pinokio Launcher

PocketTTS is a lightweight CPU text-to-speech launcher for Kyutai's PocketTTS model. It provides a Gradio Web UI for preset voices and optional voice cloning from a short audio sample.

## Features

- CPU-friendly PocketTTS speech generation.
- Eight built-in preset voices: Alba, Marius, Javert, Jean, Fantine, Cosette, Eponine, and Azelma.
- Optional custom voice cloning with a Hugging Face account that has accepted the `kyutai/pocket-tts` model terms.
- Pinokio install, start, update, reset, disk deduplication, and Hugging Face login actions.

## Using With Pinokio

1. Add this repository to Pinokio.
2. Click `Install`.
3. Click `Start`.
4. Open `Open Web UI` when Pinokio detects the Gradio URL.

Preset voices can run without Hugging Face login. Voice cloning requires model access:

1. Accept the terms at https://huggingface.co/kyutai/pocket-tts.
2. Click `Hugging Face Login` in the launcher.
3. Paste a Hugging Face token when `uvx hf auth login` prompts for it.
4. Restart PocketTTS if it was already running.

You can also paste a token in the Web UI's `Hugging Face Token for Voice Cloning` accordion.

## Launcher Scripts

- `install.js`: installs Python dependencies from `app/requirements.txt`, then runs `torch.js`.
- `start.js`: launches `app/app.py` in the `env` virtual environment and captures the local Gradio URL.
- `hf-login.js`: opens an interactive Hugging Face CLI login terminal for gated voice-cloning access.
- `update.js`: pulls the latest launcher code and upgrades app dependencies.
- `reset.js`: removes the `env` virtual environment.
- `link.js`: deduplicates redundant virtual environment files to save disk space.
- `pinokio.js`: renders the Pinokio menu dynamically based on install and running state.

## Project Structure

```text
PocketTTS/
├── app/
│   ├── app.py
│   └── requirements.txt
├── install.js
├── start.js
├── hf-login.js
├── update.js
├── reset.js
├── link.js
├── torch.js
├── pinokio.js
├── pinokio.json
└── icon.png
```

## Manual Run

```bash
python -m venv env
env\Scripts\activate
uv pip install -r app/requirements.txt
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
cd app
python app.py
```

On macOS or Linux, activate the environment with `source env/bin/activate`.

## API Usage

When the Gradio app is running, the generation function is exposed as the `generate` API route.

### Python

```python
from gradio_client import Client

client = Client("http://127.0.0.1:7860")
result = client.predict(
    text="Hello from PocketTTS.",
    preset_voice="Alba",
    custom_voice_file=None,
    api_name="/generate",
)
print(result)
```

### JavaScript

```javascript
import { Client } from "@gradio/client";

const client = await Client.connect("http://127.0.0.1:7860");
const result = await client.predict("/generate", {
  text: "Hello from PocketTTS.",
  preset_voice: "Alba",
  custom_voice_file: null
});
console.log(result);
```

### Curl

```bash
curl -X POST http://127.0.0.1:7860/gradio_api/call/generate \
  -H "Content-Type: application/json" \
  -d '{"data":["Hello from PocketTTS.","Alba",null]}'
```

## Safety

Use voice cloning only with explicit and lawful consent. Prohibited uses include impersonation without consent, misinformation, deception, and unlawful or privacy-invasive content.

## Links

- PocketTTS model: https://huggingface.co/kyutai/pocket-tts
- PocketTTS source: https://github.com/kyutai-labs/pocket-tts
- Research: https://kyutai.org/research/pocket-tts

