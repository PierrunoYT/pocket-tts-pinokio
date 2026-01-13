# 🔊 PocketTTS - Lightweight CPU Text-to-Speech

A fast, efficient Text-to-Speech (TTS) application that runs entirely on CPU. Powered by Kyutai Labs' PocketTTS model, this application provides natural-sounding speech synthesis with low latency and voice cloning capabilities.

## ✨ Features

- ⚡ **Low Latency**: ~200ms for first audio chunk
- 🚀 **Fast Performance**: ~6x faster than real-time
- 🎭 **Voice Cloning**: Clone voices from short audio samples (3-10 seconds)
- 📝 **Long Text Support**: Handles infinitely long text
- 💻 **CPU Optimized**: Uses only 2 CPU cores, no GPU required
- 🎤 **8 Preset Voices**: Choose from a catalog of pre-defined voices
- 🌐 **Web Interface**: User-friendly Gradio web UI

## 📋 Requirements

- Python 3.10+ (3.12 recommended)
- ~200MB disk space for model download (on first use)
- 2 CPU cores minimum

## 🚀 Installation

### Using Pinokio

This project is designed to work with [Pinokio](https://pinokio.computer/). Simply:

1. Install Pinokio
2. Add this repository to Pinokio
3. Click "Install" to set up dependencies
4. Click "Start" to launch the web interface

### Manual Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd PocketTTS
```

2. Create a virtual environment (Python 3.12 recommended):
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install PyTorch (CPU version):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 🎯 Usage

### Starting the Application

Run the Gradio web interface:
```bash
python app.py
```

The web interface will be available at `http://localhost:7860`

### Using Preset Voices

1. Select a voice from the "Preset Voices" tab
2. Enter your text in the text box
3. Click "🎵 Generate Speech"
4. Listen to the generated audio

**Available Preset Voices:**
- **Alba**: Casual, friendly tone
- **Marius**: Young, energetic
- **Javert**: Authoritative
- **Jean**: Mature, wise
- **Fantine**: Gentle, emotional
- **Cosette**: Youthful, bright
- **Eponine**: Expressive
- **Azelma**: Playful

### Voice Cloning

1. Switch to the "Voice Cloning" tab
2. Upload a WAV file (3-10 seconds recommended)
3. Enable "Use Custom Voice"
4. Enter your text and generate speech

**Voice Cloning Tips:**
- Use clear audio with minimal background noise
- 3-10 seconds is ideal
- Single speaker only
- WAV format preferred

## 📦 Model Information

- **Model Size**: 100M parameters
- **Sample Rate**: 24kHz
- **Language**: English only
- **Platform**: CPU optimized (GPU supported but not required)
- **Model Source**: Automatically downloaded from Hugging Face on first use

## 🛠️ Project Structure

```
PocketTTS/
├── app.py              # Main Gradio application
├── requirements.txt     # Python dependencies
├── install.js          # Pinokio installation script
├── start.js            # Pinokio start script
├── update.js           # Pinokio update script
├── reset.js            # Pinokio reset script
├── link.js             # Pinokio deduplication script
├── torch.js            # PyTorch installation script
├── pinokio.js          # Pinokio configuration
└── icon.png            # Application icon
```

## 🔧 Scripts

### Pinokio Scripts

- **install.js**: Installs all dependencies and sets up the environment
- **start.js**: Launches the Gradio web interface
- **update.js**: Updates dependencies and pulls latest changes
- **reset.js**: Removes the virtual environment (resets to pre-install state)
- **link.js**: Deduplicates redundant library files to save disk space

## 📝 Example Usage

```python
from pocket_tts import TTSModel

# Load the model
tts_model = TTSModel.load_model()

# Generate speech with a preset voice
voice_state = tts_model.get_state_for_audio_prompt("hf://kyutai/tts-voices/alba-mackenna/casual.wav")
audio = tts_model.generate_audio(voice_state, "Hello, world!")

# Or use a custom voice file
voice_state = tts_model.get_state_for_audio_prompt("path/to/your/voice.wav")
audio = tts_model.generate_audio(voice_state, "Your text here")
```

## ⚠️ Important Notes

### Prohibited Use

Use of this model must comply with all applicable laws and regulations. Prohibited uses include:

- Voice impersonation without explicit and lawful consent
- Misinformation, disinformation, or deception
- Generating unlawful, harmful, or privacy-invasive content

**Always obtain explicit and lawful consent before cloning someone's voice.**

## 🔗 Links

- [GitHub Repository](https://github.com/kyutai-labs/pocket-tts)
- [Hugging Face Model](https://huggingface.co/kyutai/pocket-tts)
- [Research Paper](https://kyutai.org/research/pocket-tts)

## 📄 License

Please refer to the original PocketTTS repository for license information.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues related to:
- **PocketTTS model**: Check the [official repository](https://github.com/kyutai-labs/pocket-tts)
- **This application**: Open an issue in this repository

---

**Note**: This application is a wrapper around Kyutai Labs' PocketTTS model, providing an easy-to-use web interface for text-to-speech synthesis.

