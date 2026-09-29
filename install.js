module.exports = {
  requires: {
    bundle: "ai"
  },
  run: [
    // Install torch first so the requirements step finds it already satisfied
    // instead of pulling PyPI's default build only to have it replaced.
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          path: "app",
          venv: "env",
          xformers: false,
          flashattn: false
        }
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "uv pip install -r requirements.txt"
        ]
      }
    },
    {
      method: "input",
      params: {
        title: "Install Complete",
        description: "PocketTTS is installed. Preset voices work after the model downloads. For voice cloning, open Hugging Face Login after accepting the kyutai/pocket-tts terms."
      }
    }
  ]
}
