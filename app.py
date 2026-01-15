"""
Gradio UI for PocketTTS - A lightweight CPU-based Text-to-Speech application
"""
import gradio as gr
import torch
import numpy as np
from pocket_tts import TTSModel
import tempfile
import os
from huggingface_hub import login as hf_login
import soundfile as sf

# Global model variable - will be loaded after token is set
tts_model = None

def load_model():
    """Load the TTS model"""
    global tts_model
    if tts_model is None:
        print("Loading PocketTTS model...")
        tts_model = TTSModel.load_model()
        print(f"Model loaded successfully! Sample rate: {tts_model.sample_rate}Hz")
    return tts_model

# Pre-defined voices from the catalog
# Use voice name aliases directly - pocket-tts has built-in support for these
PRESET_VOICES = {
    "Alba": "alba",
    "Marius": "marius",
    "Javert": "javert",
    "Jean": "jean",
    "Fantine": "fantine",
    "Cosette": "cosette",
    "Eponine": "eponine",
    "Azelma": "azelma",
}

# Cache for voice states to avoid reloading
voice_state_cache = {}


def get_voice_state(voice_path):
    """Get or create a cached voice state"""
    model = load_model()
    if voice_path not in voice_state_cache:
        print(f"Loading voice state for: {voice_path}")
        voice_state_cache[voice_path] = model.get_state_for_audio_prompt(voice_path)
    return voice_state_cache[voice_path]


def convert_audio_format(audio_path):
    """
    Convert uploaded audio to a compatible PCM WAV format
    
    Args:
        audio_path: Path to the uploaded audio file
    
    Returns:
        str: Path to the converted audio file (temp file)
    """
    try:
        # Read the audio file
        audio_data, sample_rate = sf.read(audio_path)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Normalize to [-1, 1] range if needed
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        
        # Create a temporary file for the converted audio
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Write as PCM WAV (subtype='PCM_16')
        sf.write(temp_path, audio_data, sample_rate, subtype='PCM_16')
        
        print(f"Converted audio: {sample_rate}Hz, {len(audio_data)/sample_rate:.2f}s")
        return temp_path
        
    except Exception as e:
        print(f"Error converting audio: {str(e)}")
        raise


def generate_speech(text, preset_voice, custom_voice_file):
    """
    Generate speech from text using either a preset voice or custom voice clone
    
    Args:
        text: The text to synthesize
        preset_voice: Selected preset voice name
        custom_voice_file: Uploaded audio file for voice cloning (if None, uses preset)
    
    Returns:
        tuple: (sample_rate, audio_array) for Gradio audio output
    """
    if not text or text.strip() == "":
        return None, "⚠️ Please enter some text to synthesize."
    
    try:
        model = load_model()
        
        # Determine which voice to use
        converted_audio_path = None
        if custom_voice_file is not None:
            # Use custom voice from uploaded file
            status_msg = f"🎤 Generating with custom voice clone..."
            print(status_msg)
            # Convert the uploaded audio to a compatible format
            print(f"Converting uploaded audio: {custom_voice_file}")
            converted_audio_path = convert_audio_format(custom_voice_file)
            voice_path = converted_audio_path
        else:
            # Use preset voice
            if preset_voice not in PRESET_VOICES:
                return None, f"⚠️ Invalid preset voice: {preset_voice}"
            voice_path = PRESET_VOICES[preset_voice]
            status_msg = f"🎤 Generating with voice: {preset_voice}..."
            print(status_msg)
        
        # Get voice state (cached for preset voices)
        if custom_voice_file is not None:
            # Don't cache custom voice files
            voice_state = model.get_state_for_audio_prompt(voice_path)
        else:
            voice_state = get_voice_state(voice_path)
        
        # Generate audio
        print(f"Synthesizing text: {text[:50]}...")
        audio_tensor = model.generate_audio(voice_state, text)
        
        # Convert to numpy array for Gradio
        audio_np = audio_tensor.numpy()
        
        # Get audio duration
        duration = len(audio_np) / model.sample_rate
        
        success_msg = f"✅ Generated {duration:.2f}s of audio at {model.sample_rate}Hz"
        print(success_msg)
        
        # Clean up temporary converted audio file
        if converted_audio_path and os.path.exists(converted_audio_path):
            try:
                os.unlink(converted_audio_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not delete temp file: {cleanup_error}")
        
        return (model.sample_rate, audio_np), success_msg
    
    except Exception as e:
        error_msg = f"❌ Error generating speech: {str(e)}"
        print(error_msg)
        
        # Clean up temporary converted audio file in case of error
        if converted_audio_path and os.path.exists(converted_audio_path):
            try:
                os.unlink(converted_audio_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not delete temp file: {cleanup_error}")
        
        return None, error_msg


def clear_custom_voice_cache():
    """Clear the voice state cache to free memory"""
    global voice_state_cache
    # Keep only preset voices in cache
    preset_paths = set(PRESET_VOICES.values())
    voice_state_cache = {k: v for k, v in voice_state_cache.items() if k in preset_paths}
    return "🗑️ Custom voice cache cleared"


def set_hf_token(token):
    """Set Hugging Face API token for voice cloning"""
    global tts_model
    if not token or token.strip() == "":
        return "⚠️ Please enter a valid Hugging Face API token"
    try:
        # Set environment variable for huggingface_hub
        os.environ['HF_TOKEN'] = token
        # Also try to login
        hf_login(token=token, add_to_git_credential=False)
        # Reset model so it reloads with the new token
        tts_model = None
        # Load the model with the new token
        load_model()
        return "✅ Hugging Face token set successfully! Model loaded with voice cloning support."
    except Exception as e:
        return f"❌ Error setting token: {str(e)}"


# Create the Gradio interface
with gr.Blocks(title="PocketTTS - CPU-based Text-to-Speech", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🔊 PocketTTS - Lightweight CPU Text-to-Speech
    
    A fast, efficient TTS model that runs entirely on CPU. Features:
    - ⚡ Low latency (~200ms for first audio chunk)
    - 🚀 ~6x faster than real-time
    - 🎭 Voice cloning support
    - 📝 Handles infinitely long text
    - 💻 Uses only 2 CPU cores
    
    **Note:** This model currently supports English only.
    """)
    
    # Hugging Face API Key section
    with gr.Accordion("🔑 Hugging Face API Key (Optional - for voice cloning)", open=False):
        with gr.Row():
            hf_token_input = gr.Textbox(
                label="Hugging Face API Token",
                placeholder="Enter your HF token here (hf_...)",
                type="password"
            )
            set_token_btn = gr.Button("Set Token", size="sm", variant="secondary")
        token_status = gr.Textbox(
            label="Token Status",
            interactive=False,
            value="ℹ️ Token not set. Voice cloning will use cached voices only."
        )
        
        gr.Markdown("""
        To enable voice cloning:
        1. Get your token from [Hugging Face Settings](https://huggingface.co/settings/tokens)
        2. Accept the terms at [pocket-tts model card](https://huggingface.co/kyutai/pocket-tts)
        3. Paste your token here and click "Set Token"
        """)
        
        set_token_btn.click(
            fn=set_hf_token,
            inputs=hf_token_input,
            outputs=token_status
        )
    
    
    with gr.Row():
        with gr.Column(scale=2):
            # Text input
            text_input = gr.Textbox(
                label="Text to Synthesize",
                placeholder="Enter the text you want to convert to speech...",
                lines=5,
                value="Hello world, this is a test of the Pocket TTS system. It runs efficiently on CPU without requiring a GPU."
            )
            
            # Voice selection tabs
            with gr.Tabs() as tabs:
                with gr.Tab("Preset Voices", id=0):
                    preset_voice = gr.Dropdown(
                        choices=list(PRESET_VOICES.keys()),
                        value="Alba",
                        label="Select Voice",
                        info="Choose from our catalog of pre-defined voices"
                    )
                    gr.Markdown("""
                    **Available Voices:**
                    - **Alba**: Casual, friendly tone
                    - **Marius**: Young, energetic
                    - **Javert**: Authoritative
                    - **Jean**: Mature, wise
                    - **Fantine**: Gentle, emotional
                    - **Cosette**: Youthful, bright
                    - **Eponine**: Expressive
                    - **Azelma**: Playful
                    """)
                
                with gr.Tab("Voice Cloning", id=1):
                    custom_voice = gr.Audio(
                        label="Upload Voice Sample",
                        type="filepath"
                    )
                    gr.Markdown("""
                    **Voice Cloning Tips:**
                    - Use clear audio with minimal background noise
                    - 3-10 seconds is ideal
                    - Single speaker only
                    - Supports WAV, MP3, FLAC, OGG formats
                    - Audio will be automatically converted to compatible format
                    
                    ⚠️ **Important:** Use only with explicit and lawful consent. Voice cloning without consent is prohibited.
                    """)
            
            # Generate button
            generate_btn = gr.Button("🎵 Generate Speech", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            # Audio output
            audio_output = gr.Audio(
                label="Generated Speech",
                type="numpy",
                interactive=False
            )
            
            # Status message
            status_output = gr.Textbox(
                label="Status",
                interactive=False,
                lines=2
            )
            
            # Additional info
            gr.Markdown("""
            ### ℹ️ Model Info
            - **Model Size**: 100M parameters
            - **Sample Rate**: 24kHz
            - **Language**: English only
            - **Runs on**: CPU (no GPU needed)
            """)
            
            # Clear cache button
            clear_cache_btn = gr.Button("🗑️ Clear Cache", size="sm", variant="secondary")
    
    # Examples section
    gr.Markdown("### 📝 Example Texts")
    gr.Examples(
        examples=[
            ["Hello world, this is a test of the Pocket TTS system.", "Alba", None],
            ["The quick brown fox jumps over the lazy dog.", "Marius", None],
            ["Welcome to the world of efficient text-to-speech synthesis, powered by Kyutai's Pocket TTS.", "Jean", None],
            ["Text-to-speech technology has come a long way. Now we can generate natural-sounding speech entirely on CPU.", "Fantine", None],
            ["With voice cloning, we can replicate speaking styles and characteristics from just a short audio sample.", "Cosette", None],
        ],
        inputs=[text_input, preset_voice, custom_voice],
        label="Click an example to try it out"
    )
    
    # Footer with warnings
    gr.Markdown("""
    ---
    ### ⚠️ Prohibited Use
    Use of this model must comply with all applicable laws and regulations. Prohibited uses include:
    - Voice impersonation without explicit and lawful consent
    - Misinformation, disinformation, or deception
    - Generating unlawful, harmful, or privacy-invasive content
    
    🔗 [GitHub](https://github.com/kyutai-labs/pocket-tts) | [Hugging Face](https://huggingface.co/kyutai/pocket-tts) | [Paper](https://kyutai.org/research/pocket-tts)
    """)
    
    # Event handlers
    generate_btn.click(
        fn=generate_speech,
        inputs=[text_input, preset_voice, custom_voice],
        outputs=[audio_output, status_output]
    )
    
    clear_cache_btn.click(
        fn=clear_custom_voice_cache,
        outputs=status_output
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting PocketTTS Gradio Interface")
    print("="*60)
    print("Model will be loaded on first use or after setting HF token")
    print(f"Available voices: {', '.join(PRESET_VOICES.keys())}")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )

