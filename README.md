# PocketTTS Pinokio Launcher

PocketTTS is a lightweight CPU text-to-speech launcher for Kyutai's PocketTTS model. It provides a Gradio Web UI for preset voices and optional voice cloning from a short audio sample.

## Features

- CPU-friendly PocketTTS speech generation.
- Eight built-in preset voices: Alba, Marius, Javert, Jean, Fantine, Cosette, Eponine, and Azelma.
- Optional custom voice cloning with a Hugging Face account that has accepted the `kyutai/pocket-tts` model terms.
- Pinokio install, start, update, reset, disk deduplication, and Hugging Face login actions.

Intel Macs are not supported: pocket-tts requires torch 2.5 or newer, and PyTorch stopped publishing Intel macOS wheels after 2.2.2.

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
- `start.js`: launches `app/app.py` in the `app/env` virtual environment and captures the local Gradio URL.
- `hf-login.js`: opens an interactive Hugging Face CLI login terminal for gated voice-cloning access.
- `update.js`: pulls the latest launcher code and upgrades app dependencies.
- `reset.js`: removes the `app/env` virtual environment, leaving the app source in place.
- `link.js`: deduplicates redundant `app/env` files to save disk space.
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
├── .gitignore
├── README.md
└── icon.png
```

The launcher creates its virtual environment at `app/env`, which is gitignored.

## Manual Run

Use `app/env` so a manual run shares the virtual environment the launcher creates.

Install torch before the requirements: pocket-tts depends on torch, so installing the requirements first pulls PyPI's default build (CUDA on Linux) and the CPU install afterwards is skipped as already satisfied.

On Windows:

```bat
python -m venv app\env
app\env\Scripts\activate
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
uv pip install -r app\requirements.txt
cd app
python app.py
```

On macOS or Linux:

```bash
python -m venv app/env
source app/env/bin/activate
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
uv pip install -r app/requirements.txt
cd app
python app.py
```

A manual run listens on port 7860 unless you set `PORT`.

## API Usage

When the Gradio app is running, the generation function is exposed as the `generate` API route. The port is assigned dynamically by Pinokio — check the `Open Web UI` URL in the launcher for the actual port (e.g. `http://127.0.0.1:PORT`).

### Python

```python
from gradio_client import Client

client = Client("http://127.0.0.1:PORT")  # replace PORT with the port shown in the launcher
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

const client = await Client.connect("http://127.0.0.1:PORT");  // replace PORT with the port shown in the launcher
const result = await client.predict("/generate", {
  text: "Hello from PocketTTS.",
  preset_voice: "Alba",
  custom_voice_file: null
});
console.log(result);
```

### Curl

Gradio's HTTP API is two-step: the POST queues the job and returns an
`event_id`, then a GET on that id streams the result.

```bash
EVENT_ID=$(curl -s -X POST http://127.0.0.1:PORT/gradio_api/call/generate \
  -H "Content-Type: application/json" \
  -d '{"data":["Hello from PocketTTS.","Alba",null]}' \
  | grep -o '"event_id":"[^"]*"' | cut -d'"' -f4)

curl -N http://127.0.0.1:PORT/gradio_api/call/generate/$EVENT_ID
```

## Safety

Use voice cloning only with explicit and lawful consent. Prohibited uses include impersonation without consent, misinformation, deception, and unlawful or privacy-invasive content.

## Links

- PocketTTS model: https://huggingface.co/kyutai/pocket-tts
- PocketTTS source: https://github.com/kyutai-labs/pocket-tts
- Research: https://kyutai.org/research/pocket-tts

