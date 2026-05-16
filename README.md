# NVIDIA AI Agents

AI-powered agents using NVIDIA's free API with 80+ models.

## Setup

```bash
# Set your NVIDIA API key
export NVIDIA_API_KEY="nvapi-..."

# Or edit the API_KEY variable directly in the scripts
```

## Scripts

### `newsletter_agent.py` - Multi-Model Newsletter Generator

Generate themed newsletters using different AI models for different topics.

```bash
# Full newsletter (all topics)
python3 newsletter_agent.py

# Single topic
python3 newsletter_agent.py --topic ai
python3 newsletter_agent.py --topic cycling

# Compare models on a prompt
python3 newsletter_agent.py --compare --models nemotron,glm,gemma

# Save output to file
python3 newsletter_agent.py -o newsletter.txt
```

### `code_review.py` - Multi-Model Code Reviewer

Get code reviews from multiple AI models simultaneously.

```bash
# Review code string
python3 code_review.py "def hello(): print('world')" --lang python

# Review a file
python3 code_review.py --file myapp.py --lang python

# Use specific models
python3 code_review.py --file app.py --models nemotron,glm,deepseek,gemma

# JSON output
python3 code_review.py --file app.py --json
```

## Available Models

| Model | ID | Best For |
|-------|----|----------|
| Nemotron | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | Deep reasoning |
| GLM | z-ai/glm-5.1 | Technical analysis |
| DeepSeek | deepseek-ai/deepseek-v4-pro | Code quality |
| Gemma | google/gemma-4-31b-it | Creative content |
| MiniMax | minimaxai/minimax-m2.7 | General tasks |

## NVIDIA API

Free API at [build.nvidia.com](https://build.nvidia.com) with 80+ models:
- Base URL: `https://integrate.api.nvidia.com/v1`
- No credit card required
- Some models may have rate limits

## Requirements

```
pip install requests
```

## Notes

- GLM and DeepSeek models may timeout on NVIDIA's free tier
- Nemotron is the most reliable model on NVIDIA's free API
- Response times vary by model and server load