module.exports = {
  run: [
    {
      method: "input",
      params: {
        title: "Hugging Face Login",
        description: "Accept the terms at https://huggingface.co/kyutai/pocket-tts, then paste a Hugging Face token when prompted. This is required for voice cloning."
      }
    },
    {
      method: "shell.run",
      params: {
        message: "uvx hf auth login",
        input: true
      }
    },
    {
      method: "notify",
      params: {
        html: "Hugging Face login finished. Restart PocketTTS if it was already running."
      }
    }
  ]
}
