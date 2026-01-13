module.exports = {
  run: [
    // Install PocketTTS dependencies first (before torch to prevent version conflicts)
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uv pip install -r requirements.txt"
      }
    },
    // Install PyTorch (CPU version is sufficient, but GPU will work too)
    // PocketTTS is optimized for CPU and doesn't need xformers or flashattn
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env",
          xformers: false,
          flashattn: false
        }
      }
    },
    {
      method: "notify",
      params: {
        html: "Installation complete! Click 'Start' to launch PocketTTS. The 100M parameter model and voice samples will be downloaded automatically from Hugging Face on first use (~200MB)."
      }
    }
  ]
}
