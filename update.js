module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: "git pull"
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "uv pip install --upgrade -r requirements.txt"
        ]
      }
    },
    // --upgrade also upgrades torch, a transitive dependency, to PyPI's
    // default build, so restore the platform-specific build afterwards.
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
      method: "notify",
      params: {
        html: "Update complete. The launcher and dependencies have been updated."
      }
    }
  ]
}
