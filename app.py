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

# Initialize the TTS model (loaded once at startup)
print("Loading PocketTTS model...")
tts_model = TTSModel.load_model()
print(f"Model loaded successfully! Sample rate: {tts_model.sample_rate}Hz")

# Pre-defined voices from the catalog
PRESET_VOICES = {
    "Alba": "hf://kyutai/tts-voices/alba-mackenna/casual.wav",
    "Marius": "hf://kyutai/tts-voices/marius-pontmercy/casual.wav",
    "Javert": "hf://kyutai/tts-voices/javert/casual.wav",
    "Jean": "hf://kyutai/tts-voices/jean-valjean/casual.wav",
    "Fantine": "hf://kyutai/tts-voices/fantine/casual.wav",
    "Cosette": "hf://kyutai/tts-voices/cosette/casual.wav",
    "Eponine": "hf://kyutai/tts-voices/eponine/casual.wav",
    "Azelma": "hf://kyutai/tts-voices/azelma/casual.wav",
}

# Cache for voice states to avoid reloading
voice_state_cache = {}


def get_voice_state(voice_path):
    """Get or create a cached voice state"""
    if voice_path not in voice_state_cache:
        print(f"Loading voice state for: {voice_path}")
        voice_state_cache[voice_path] = tts_model.get_state_for_audio_prompt(voice_path)
    return voice_state_cache[voice_path]


def generate_speech(text, preset_voice, custom_voice_file, use_custom_voice):
    """
    Generate speech from text using either a preset voice or custom voice clone
    
    Args:
        text: The text to synthesize
        preset_voice: Selected preset voice name
        custom_voice_file: Uploaded audio file for voice cloning
        use_custom_voice: Whether to use custom voice or preset
    
    Returns:
        tuple: (sample_rate, audio_array) for Gradio audio output
    """
    if not text or text.strip() == "":
        return None, "⚠️ Please enter some text to synthesize."
    
    try:
        # Determine which voice to use
        if use_custom_voice and custom_voice_file is not None:
            # Use custom voice from uploaded file
            voice_path = custom_voice_file
            status_msg = f"🎤 Generating with custom voice clone..."
        else:
            # Use preset voice
            if preset_voice not in PRESET_VOICES:
                return None, f"⚠️ Invalid preset voice: {preset_voice}"
            voice_path = PRESET_VOICES[preset_voice]
            status_msg = f"🎤 Generating with voice: {preset_voice}..."
        
        print(status_msg)
        
        # Get voice state (cached for preset voices)
        if use_custom_voice and custom_voice_file is not None:
            # Don't cache custom voice files
            voice_state = tts_model.get_state_for_audio_prompt(voice_path)
        else:
            voice_state = get_voice_state(voice_path)
        
        # Generate audio
        print(f"Synthesizing text: {text[:50]}...")
        audio_tensor = tts_model.generate_audio(voice_state, text)
        
        # Convert to numpy array for Gradio
        audio_np = audio_tensor.numpy()
        
        # Get audio duration
        duration = len(audio_np) / tts_model.sample_rate
        
        success_msg = f"✅ Generated {duration:.2f}s of audio at {tts_model.sample_rate}Hz"
        print(success_msg)
        
        return (tts_model.sample_rate, audio_np), success_msg
    
    except Exception as e:
        error_msg = f"❌ Error generating speech: {str(e)}"
        print(error_msg)
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
    if not token or token.strip() == "":
        return "⚠️ Please enter a valid Hugging Face API token"
    try:
        hf_login(token=token, add_to_git_credential=False)
        return "✅ Hugging Face token set successfully! You can now use voice cloning."
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
            with gr.Tabs():
                with gr.Tab("Preset Voices"):
                    use_custom = gr.Checkbox(value=False, visible=False)
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
                
                with gr.Tab("Voice Cloning"):
                    use_custom = gr.Checkbox(
                        value=True,
                        label="Use Custom Voice",
                        info="Enable to use your uploaded audio for voice cloning"
                    )
                    custom_voice = gr.Audio(
                        label="Upload Voice Sample",
                        type="filepath"
                    )
                    gr.Markdown("""
                    **Voice Cloning Tips:**
                    - Use clear audio with minimal background noise
                    - 3-10 seconds is ideal
                    - Single speaker only
                    - WAV format preferred
                    
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
            ["Hello world, this is a test of the Pocket TTS system.", "Alba", None, False],
            ["The quick brown fox jumps over the lazy dog.", "Marius", None, False],
            ["Welcome to the world of efficient text-to-speech synthesis, powered by Kyutai's Pocket TTS.", "Jean", None, False],
            ["Text-to-speech technology has come a long way. Now we can generate natural-sounding speech entirely on CPU.", "Fantine", None, False],
            ["With voice cloning, we can replicate speaking styles and characteristics from just a short audio sample.", "Cosette", None, False],
        ],
        inputs=[text_input, preset_voice, custom_voice, use_custom],
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
        inputs=[text_input, preset_voice, custom_voice, use_custom],
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
    print(f"Model sample rate: {tts_model.sample_rate}Hz")
    print(f"Available voices: {', '.join(PRESET_VOICES.keys())}")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )

