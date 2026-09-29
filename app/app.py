"""
Gradio UI for PocketTTS.
"""

import os
import tempfile
import threading

import gradio as gr
import numpy as np
import soundfile as sf
from huggingface_hub import HfApi, get_token
from huggingface_hub import login as hf_login
from pocket_tts import TTSModel


tts_model = None
voice_state_cache = {}

# Gradio serves requests from a worker thread pool, so the lazily initialized
# model and the voice-state cache both need guarding against concurrent access.
_model_lock = threading.Lock()
_cache_lock = threading.Lock()

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

# Mirrors the selected voice tab. API callers never send one, because gr.State
# is excluded from the API schema, so None means "decide from the arguments".
VOICE_MODE_PRESET = "preset"
VOICE_MODE_CLONE = "clone"


def explain_model_error(error):
    message = str(error)
    if "voice cloning" in message.lower() or "download the weights" in message.lower():
        return f"{message}\n\n{HF_HELP}"
    return message


def load_model():
    global tts_model
    with _model_lock:
        if tts_model is None:
            print("Loading PocketTTS model...")
            tts_model = TTSModel.load_model()
            print(f"Model loaded successfully. Sample rate: {tts_model.sample_rate}Hz")
        return tts_model


def get_voice_state(voice_path):
    model = load_model()
    with _cache_lock:
        if voice_path not in voice_state_cache:
            print(f"Loading voice state for: {voice_path}")
            voice_state_cache[voice_path] = model.get_state_for_audio_prompt(voice_path)
        return voice_state_cache[voice_path]


def convert_audio_format(audio_path):
    # soundfile normalizes every input subtype to float32 for us, so the sample
    # values are already in [-1, 1] regardless of the source encoding.
    audio_data, sample_rate = sf.read(audio_path, dtype="float32")

    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    if audio_data.size == 0:
        raise ValueError("The uploaded voice sample contains no audio.")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        sf.write(temp_path, audio_data, sample_rate, subtype="PCM_16")
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise

    print(f"Converted audio: {sample_rate}Hz, {len(audio_data) / sample_rate:.2f}s")
    return temp_path


def to_gradio_audio(audio_tensor):
    """Normalize a model output tensor into the sample-major array Gradio wants."""
    audio_np = np.asarray(audio_tensor.detach().cpu().numpy())
    audio_np = np.squeeze(audio_np)

    if audio_np.ndim == 0:
        audio_np = audio_np.reshape(1)
    elif audio_np.ndim > 1:
        # Multi-channel output can arrive as (channels, samples); Gradio expects
        # (samples, channels), so put the longest axis first.
        if audio_np.shape[0] < audio_np.shape[-1]:
            audio_np = audio_np.T
        audio_np = audio_np.reshape(audio_np.shape[0], -1)

    return np.ascontiguousarray(audio_np)


def generate_speech(text, preset_voice, custom_voice_file, voice_mode=None):
    if not text or not text.strip():
        return None, "Please enter text to synthesize."

    # The tab the user is on decides the voice source, so an upload left behind
    # on the cloning tab no longer overrides an explicit preset selection.
    # voice_mode is None for API callers, who instead get the documented
    # behavior of cloning whenever a sample is supplied.
    if voice_mode is None:
        use_clone = custom_voice_file is not None
    else:
        use_clone = voice_mode == VOICE_MODE_CLONE

    if use_clone and custom_voice_file is None:
        return None, (
            "Upload a voice sample on the Voice Cloning tab, "
            "or switch to the Preset Voices tab."
        )

    converted_audio_path = None

    try:
        model = load_model()

        if use_clone:
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
        audio_np = to_gradio_audio(audio_tensor)

        if audio_np.size == 0:
            return None, "The model returned no audio. Try different text."

        duration = audio_np.shape[0] / model.sample_rate

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


def clear_voice_cache():
    with _cache_lock:
        cleared = len(voice_state_cache)
        voice_state_cache.clear()
    return f"Cleared {cleared} cached voice state(s)."


def initial_token_status():
    # get_token() checks HF_TOKEN and the token file that `hf auth login`
    # (the Pinokio Hugging Face Login action) writes.
    if get_token():
        return "A Hugging Face token is already configured."
    return "No token set yet. Accept the model terms, then paste your token here."


def set_hf_token(accepted_terms, token):
    global tts_model
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
        with _model_lock:
            tts_model = None
        with _cache_lock:
            voice_state_cache.clear()
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
            # Passing the function re-evaluates the status on every page load.
            value=initial_token_status,
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

            voice_mode = gr.State(None)

            with gr.Tabs():
                with gr.Tab("Preset Voices") as preset_tab:
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

                with gr.Tab("Voice Cloning") as clone_tab:
                    custom_voice = gr.Audio(label="Upload Voice Sample", type="filepath")
                    gr.Markdown(
                        """
                        Use a clear single-speaker clip, ideally 3-10 seconds.
                        The uploaded sample is used only while this tab is
                        selected; switch to Preset Voices to use a preset again.
                        Only clone voices with explicit and lawful consent.
                        """
                    )

            # api_name=False keeps these UI-only handlers out of the API schema.
            # Gradio 6.0 replaces it with api_visibility="private", which the
            # pinned gradio==5.50 does not yet accept.
            preset_tab.select(
                lambda: VOICE_MODE_PRESET, outputs=voice_mode, api_name=False
            )
            clone_tab.select(
                lambda: VOICE_MODE_CLONE, outputs=voice_mode, api_name=False
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
        inputs=[text_input, preset_voice, custom_voice, voice_mode],
        outputs=[audio_output, status_output],
        api_name="generate",
    )
    clear_cache_btn.click(clear_voice_cache, outputs=status_output)


def resolve_port(default=7860):
    raw = os.environ.get("PORT", "").strip()
    if not raw:
        return default
    try:
        port = int(raw)
    except ValueError:
        print(f"Ignoring invalid PORT value {raw!r}; falling back to {default}.")
        return default
    if not 1 <= port <= 65535:
        print(f"Ignoring out-of-range PORT value {port}; falling back to {default}.")
        return default
    return port


if __name__ == "__main__":
    port = resolve_port()
    print("Starting PocketTTS Gradio interface")
    print(f"Available voices: {', '.join(PRESET_VOICES.keys())}")
    demo.launch(
        server_name="127.0.0.1",
        server_port=port,
        share=False,
        show_error=True,
    )
