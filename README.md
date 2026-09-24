# vibepod-providers

Curated provider templates for the [VibePod](https://vibepod.dev) global model
provider registry (`vp provider`). Each file is a credential-free provider
definition that `vp provider import` turns into a ready-to-use provider.

```bash
vp provider import https://raw.githubusercontent.com/VibePod/vibepod-providers/main/providers/openrouter.toml
export OPENROUTER_API_KEY=...          # hosted templates reference a variable, no key is stored
vp provider refresh openrouter         # pull the model list, pick models and a default
vp run pi --provider openrouter
```

Hosted templates carry a model list with context window, output limit, reasoning
flag, and accepted reasoning levels, synced from the open
[models.dev](https://models.dev) database (tool-calling, non-deprecated models
only). No default model is chosen for you. `vp provider refresh` re-syncs the
list from the endpoint itself at any time. Local templates ship without models;
run `refresh` after starting the server.

## Hosted endpoints

<!-- hosted:start -->
| Name | Protocol | Base URL | Key variable | Models | Reference |
| --- | --- | --- | --- | --- | --- |
| `anthropic` | `anthropic` | `https://api.anthropic.com` | `ANTHROPIC_API_KEY` | 15 | [docs](https://docs.anthropic.com/en/api) |
| `cerebras` | `openai-chat` | `https://api.cerebras.ai/v1` | `CEREBRAS_API_KEY` | 2 | [docs](https://inference-docs.cerebras.ai) |
| `dashscope` | `openai-chat` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | `DASHSCOPE_API_KEY` | 51 | [docs](https://www.alibabacloud.com/help/en/model-studio) |
| `deepseek-anthropic` | `anthropic` | `https://api.deepseek.com/anthropic` | `DEEPSEEK_API_KEY` | 2 | [docs](https://api-docs.deepseek.com/guides/anthropic_api) |
| `deepseek` | `openai-chat` | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` | 2 | [docs](https://api-docs.deepseek.com) |
| `fireworks` | `openai-chat` | `https://api.fireworks.ai/inference/v1` | `FIREWORKS_API_KEY` | 25 | [docs](https://docs.fireworks.ai) |
| `gemini-openai` | `openai-chat` | `https://generativelanguage.googleapis.com/v1beta/openai` | `GEMINI_API_KEY` | 21 | [docs](https://ai.google.dev/gemini-api/docs/openai) |
| `groq` | `openai-chat` | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | 7 | [docs](https://console.groq.com/docs/openai) |
| `huggingface` | `openai-chat` | `https://router.huggingface.co/v1` | `HF_TOKEN` | 76 | [docs](https://huggingface.co/docs/inference-providers) |
| `minimax-anthropic` | `anthropic` | `https://api.minimax.io/anthropic` | `MINIMAX_API_KEY` | 7 | [docs](https://platform.minimax.io/docs) |
| `minimax` | `openai-chat` | `https://api.minimax.io/v1` | `MINIMAX_API_KEY` | 7 | [docs](https://platform.minimax.io/docs) |
| `mistral` | `openai-chat` | `https://api.mistral.ai/v1` | `MISTRAL_API_KEY` | 24 | [docs](https://docs.mistral.ai) |
| `moonshot-anthropic` | `anthropic` | `https://api.moonshot.ai/anthropic` | `MOONSHOT_API_KEY` | 4 | [docs](https://platform.moonshot.ai/docs) |
| `moonshot` | `openai-chat` | `https://api.moonshot.ai/v1` | `MOONSHOT_API_KEY` | 4 | [docs](https://platform.moonshot.ai/docs) |
| `nebius` | `openai-chat` | `https://api.tokenfactory.nebius.com/v1` | `NEBIUS_API_KEY` | 19 | [docs](https://docs.nebius.com/studio/inference) |
| `ollama-cloud` | `openai-chat` | `https://ollama.com/v1` | `OLLAMA_API_KEY` | 24 | [docs](https://docs.ollama.com/cloud) |
| `openai` | `openai-responses` | `https://api.openai.com/v1` | `OPENAI_API_KEY` | 31 | [docs](https://platform.openai.com/docs/api-reference) |
| `openrouter` | `openai-chat` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | 319 | [docs](https://openrouter.ai/docs) |
| `perplexity` | `openai-chat` | `https://api.perplexity.ai` | `PERPLEXITY_API_KEY` | 0 | [docs](https://docs.perplexity.ai) |
| `scaleway` | `openai-chat` | `https://api.scaleway.ai/v1` | `SCALEWAY_API_KEY` | 12 | [docs](https://www.scaleway.com/en/docs/generative-apis) |
| `together` | `openai-chat` | `https://api.together.xyz/v1` | `TOGETHER_API_KEY` | 22 | [docs](https://docs.together.ai) |
| `xai` | `openai-chat` | `https://api.x.ai/v1` | `XAI_API_KEY` | 7 | [docs](https://docs.x.ai) |
| `zai-anthropic` | `anthropic` | `https://api.z.ai/api/anthropic` | `ZHIPU_API_KEY` | 18 | [docs](https://docs.z.ai) |
| `zai` | `openai-chat` | `https://api.z.ai/api/paas/v4` | `ZHIPU_API_KEY` | 18 | [docs](https://docs.z.ai) |
<!-- hosted:end -->

Endpoints marked `-anthropic` speak the Anthropic Messages API (for Claude Code
and other Anthropic-native agents); the plain entries speak OpenAI Chat
Completions, `openai` uses the Responses API.

## Local servers

<!-- local:start -->
| Name | Protocol | Base URL | Key variable | Models | Reference |
| --- | --- | --- | --- | --- | --- |
| `lemonade` | `openai-chat` | `http://host.docker.internal:8000/api/v1` | none | 0 | [docs](https://lemonade-server.ai/docs) |
| `llamacpp` | `openai-chat` | `http://host.docker.internal:8080/v1` | none | 0 | [docs](https://github.com/ggml-org/llama.cpp/tree/master/tools/server) |
| `lmstudio` | `openai-chat` | `http://host.docker.internal:1234/v1` | none | 0 | [docs](https://lmstudio.ai/docs/app/api/endpoints/openai) |
| `ollama-anthropic` | `anthropic` | `http://host.docker.internal:11434` | none | 0 | [docs](https://docs.ollama.com/api/anthropic-compatibility) |
| `ollama` | `openai-chat` | `http://host.docker.internal:11434/v1` | none | 0 | [docs](https://docs.ollama.com/api/openai-compatibility) |
| `vllm` | `openai-chat` | `http://host.docker.internal:8000/v1` | none | 0 | [docs](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html) |
<!-- local:end -->

`host.docker.internal` reaches the Docker host from an agent container; the
server must listen on `0.0.0.0` (or the Docker bridge address), not only on
`127.0.0.1`. Jcode refuses plain-http hostnames, so for it import with `--name`
and edit the URL to the machine's LAN IP. See
[Local providers](https://github.com/VibePod/vibepod-cli/blob/main/docs/providers.md#local-providers).

## File format

The exchange format is documented in
[Sharing providers](https://github.com/VibePod/vibepod-cli/blob/main/docs/providers.md#sharing-providers).
Rules for this repository:

- one provider per file, `providers/<name>.toml`, `name` equal to the filename;
- never a key, token, or credential of any kind; hosted templates use
  `auth = "env"` with the vendor's conventional variable name;
- `base_url` exactly as the vendor documents it (Anthropic-style endpoints
  without the `/v1` suffix); a `# Docs:` comment linking the reference;
- optional `[model_settings."<id>"]` tables only with values taken from the
  vendor documentation (context window, output limit, reasoning levels).

`python scripts/validate.py` checks every file; CI runs it on each pull request.
`python scripts/sync_models.py` refreshes the hosted model lists and settings
from models.dev and `python scripts/build_readme.py` regenerates the tables;
run both before opening a pull request that touches hosted templates.

## Contributing

Open a pull request adding or updating a file under `providers/`. Reviewers
verify the `base_url` against the vendor documentation, since that is where an
imported provider will send the user's key.

## License

MIT
