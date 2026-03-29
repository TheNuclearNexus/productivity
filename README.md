## Pre-requisites
**Ollama** - Ollama must be running. The application defaults to using `llama3.1:8b` but can be configured to use any model supported by Ollama. Run `ollama pull llama3.1:8b` to pull the model.
**uv** - UV is a fast Python package installer and resolver. Install it from [here](https://docs.astral.sh/uv/getting-started/installation/).

### Linux
**xdotool** - `sudo apt install xdotool`
**wmctrl** - `sudo apt install wmctrl`

## Usage

```bash
$ git clone https://github.com/TheNuclearNexus/productivity.git
$ cd productivity
$ uv run -m final_project
```

To override the default model, set the `OLLAMA_MODEL` environment variable:

```bash
$ OLLAMA_MODEL=llama3.1:8b uv run -m final_project
```
