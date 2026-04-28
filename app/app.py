"""
Gradio UI for PocketTTS.
"""

import os
import tempfile

import gradio as gr
import numpy as np
import soundfile as sf
from huggingface_hub import HfApi
from huggingface_hub import login as hf_login
from pocket_tts import TTSModel


tts_model = None
voice_state_cache = {}

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

HF_HELP = (
    "Voice cloning requires access to https://huggingface.co/kyutai/pocket-tts. "
    "Accept the model terms, then paste a Hugging Face token in the app."
)
MODEL_ID = "kyutai/pocket-tts"


def explain_model_error(error):
    message = str(error)
    if "voice cloning" in message.lower() or "download the weights" in message.lower():
        return f"{message}\n\n{HF_HELP}"
    return message


def load_model():
    global tts_model
    if tts_model is None:
        print("Loading PocketTTS model...")
        tts_model = TTSModel.load_model()
        print(f"Model loaded successfully. Sample rate: {tts_model.sample_rate}Hz")
    return tts_model


def get_voice_state(voice_path):
    model = load_model()
    if voice_path not in voice_state_cache:
        print(f"Loading voice state for: {voice_path}")
        voice_state_cache[voice_path] = model.get_state_for_audio_prompt(voice_path)
    return voice_state_cache[voice_path]


def convert_audio_format(audio_path):
    audio_data, sample_rate = sf.read(audio_path)

    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = temp_file.name

    sf.write(temp_path, audio_data, sample_rate, subtype="PCM_16")
    print(f"Converted audio: {sample_rate}Hz, {len(audio_data) / sample_rate:.2f}s")
    return temp_path


def generate_speech(text, preset_voice, custom_voice_file):
    if not text or not text.strip():
        return None, "Please enter text to synthesize."

    converted_audio_path = None

    try:
        model = load_model()

        if custom_voice_file is not None:
            print(f"Converting uploaded audio: {custom_voice_file}")
            converted_audio_path = convert_audio_format(custom_voice_file)
            voice_state = model.get_state_for_audio_prompt(converted_audio_path)
            voice_label = "custom voice clone"
        else:
            if preset_voice not in PRESET_VOICES:
                return None, f"Invalid preset voice: {preset_voice}"
            voice_state = get_voice_state(PRESET_VOICES[preset_voice])
            voice_label = preset_voice

        print(f"Synthesizing with {voice_label}: {text[:80]}")
        audio_tensor = model.generate_audio(voice_state, text)
        audio_np = audio_tensor.detach().cpu().numpy()
        duration = len(audio_np) / model.sample_rate

        return (model.sample_rate, audio_np), f"Generated {duration:.2f}s of audio."
    except Exception as error:
        error_msg = f"Error generating speech: {explain_model_error(error)}"
        print(error_msg)
        return None, error_msg
    finally:
        if converted_audio_path and os.path.exists(converted_audio_path):
            try:
                os.unlink(converted_audio_path)
            except OSError as cleanup_error:
                print(f"Warning: could not delete temp file: {cleanup_error}")


def clear_custom_voice_cache():
    global voice_state_cache
    preset_paths = set(PRESET_VOICES.values())
    voice_state_cache = {k: v for k, v in voice_state_cache.items() if k in preset_paths}
    return "Custom voice cache cleared."


def initial_token_status():
    if os.environ.get("HF_TOKEN"):
        return "HF_TOKEN is already set for this session."
    return "No token set yet. Accept the model terms, then paste your token here."


def set_hf_token(accepted_terms, token):
    global tts_model
    global voice_state_cache
    if not accepted_terms:
        return "Please confirm that you accepted the kyutai/pocket-tts terms on Hugging Face."

    if not token or not token.strip():
        return "Please enter a valid Hugging Face token."

    token = token.strip()
    if not token.startswith("hf_"):
        return "That does not look like a Hugging Face token. It should start with hf_."

    try:
        HfApi(token=token).model_info(MODEL_ID)
        os.environ["HF_TOKEN"] = token
        hf_login(token=token, add_to_git_credential=False)
        tts_model = None
        voice_state_cache = {}
        return "Token saved and model access verified. Voice cloning is ready."
    except Exception as error:
        return (
            "Could not verify access to kyutai/pocket-tts. Make sure you accepted "
            f"the terms at https://huggingface.co/{MODEL_ID}, then try again.\n\n"
            f"Details: {explain_model_error(error)}"
        )


with gr.Blocks(title="PocketTTS", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # PocketTTS

        Lightweight CPU text-to-speech using Kyutai's PocketTTS model. Preset
        voices work without extra setup. Voice cloning requires Hugging Face
        access to the gated `kyutai/pocket-tts` model.
        """
    )

    with gr.Accordion("Hugging Face Token for Voice Cloning", open=True):
        gr.Markdown(
            """
            Voice cloning uses the gated `kyutai/pocket-tts` model. After you
            accept the terms on Hugging Face, paste your access token below.
            Preset voices do not need this step.
            """
        )
        accepted_terms = gr.Checkbox(
            label="I accepted the kyutai/pocket-tts terms on Hugging Face",
            value=False,
        )
        with gr.Row():
            hf_token_input = gr.Textbox(
                label="Hugging Face Token",
                placeholder="hf_...",
                type="password",
            )
            set_token_btn = gr.Button("Save and Verify Token", size="sm", variant="primary")
        token_status = gr.Textbox(
            label="Token Status",
            interactive=False,
            value=initial_token_status(),
            lines=4,
        )
        gr.Markdown(
            """
            Get or create a token at https://huggingface.co/settings/tokens.
            The token only needs read access. If you use the Pinokio
            `Hugging Face Login` action instead, restart this app afterward.
            """
        )
        set_token_btn.click(
            set_hf_token,
            inputs=[accepted_terms, hf_token_input],
            outputs=token_status,
        )

    with gr.Row():
        with gr.Column(scale=2):
            text_input = gr.Textbox(
                label="Text to Synthesize",
                placeholder="Enter the text you want to convert to speech...",
                lines=5,
                value="Hello world, this is a test of the PocketTTS system.",
            )

            with gr.Tabs():
                with gr.Tab("Preset Voices"):
                    preset_voice = gr.Dropdown(
                        choices=list(PRESET_VOICES.keys()),
                        value="Alba",
                        label="Select Voice",
                        info="Choose from the built-in voice catalog.",
                    )
                    gr.Markdown(
                        "Available voices: Alba, Marius, Javert, Jean, Fantine, "
                        "Cosette, Eponine, and Azelma."
                    )

                with gr.Tab("Voice Cloning"):
                    custom_voice = gr.Audio(label="Upload Voice Sample", type="filepath")
                    gr.Markdown(
                        """
                        Use a clear single-speaker clip, ideally 3-10 seconds.
                        Only clone voices with explicit and lawful consent.
                        """
                    )

            generate_btn = gr.Button("Generate Speech", variant="primary", size="lg")

        with gr.Column(scale=1):
            audio_output = gr.Audio(label="Generated Speech", type="numpy", interactive=False)
            status_output = gr.Textbox(label="Status", interactive=False, lines=5)
            clear_cache_btn = gr.Button("Clear Cache", size="sm", variant="secondary")

    gr.Examples(
        examples=[
            ["Hello world, this is a test of the PocketTTS system.", "Alba", None],
            ["The quick brown fox jumps over the lazy dog.", "Marius", None],
            ["PocketTTS can generate natural-sounding speech on CPU.", "Jean", None],
        ],
        inputs=[text_input, preset_voice, custom_voice],
        label="Examples",
    )

    gr.Markdown(
        """
        Prohibited uses include voice impersonation without consent,
        misinformation, deception, and unlawful or privacy-invasive content.
        """
    )

    generate_btn.click(
        fn=generate_speech,
        inputs=[text_input, preset_voice, custom_voice],
        outputs=[audio_output, status_output],
        api_name="generate",
    )
    clear_cache_btn.click(clear_custom_voice_cache, outputs=status_output)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    print("Starting PocketTTS Gradio interface")
    print(f"Available voices: {', '.join(PRESET_VOICES.keys())}")
    demo.launch(
        server_name="127.0.0.1",
        server_port=port,
        share=False,
        show_error=True,
    )
