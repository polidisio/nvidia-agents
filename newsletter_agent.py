#!/usr/bin/env python3
"""
Newsletter Agent - Multi-Model AI Newsletter Generator
Uses NVIDIA API (80+ models available)
Supports: GLM, DeepSeek, Nemotron, Gemma4, MiniMax, and more

Usage:
  python3 newsletter_agent.py              # Full newsletter (all topics)
  python3 newsletter_agent.py --topic ai   # Single topic
  python3 newsletter_agent.py --models glm,nemotron  # Specific models only
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional

# NVIDIA API Config
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "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")
BASE_URL = "https://integrate.api.nvidia.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

# Available models (NVIDIA API)
MODELS = {
    "nemotron": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "glm": "z-ai/glm-5.1",
    "deepseek": "deepseek-ai/deepseek-v4-pro",
    "gemma": "google/gemma-4-31b-it",
    "minimax": "minimaxai/minimax-m2.7",
    "qwen": "Qwen/Qwen2.5-72B-Instruct",
}

# Newsletter topics with model preferences
TOPIC_CONFIG = {
    "cycling": {
        "description": "Noticias de ciclismo, Zwift, indoor training",
        "sources": ["cyclingnews.com", "bikeradar.com", "zwiftinsider.com"],
        "preferred_model": "glm",  # Good for summaries
    },
    "ai": {
        "description": "Novedades en IA, LLMs, herramientas",
        "sources": ["venturebeat.com/ai", "techcrunch.com/ai", "github.com/trending"],
        "preferred_model": "nemotron",  # Good reasoning
    },
    "dev": {
        "description": "Desarrollo, programación, herramientas",
        "sources": ["swift.org/blog", "hackingwithswift.com"],
        "preferred_model": "deepseek",  # Good for code-related content
    },
    "gaming": {
        "description": "Videojuegos, gaming, nuevos títulos",
        "sources": ["ign.com", "gamespot.com"],
        "preferred_model": "gemma",  # Creative content
    },
}

# Topics order for full newsletter
TOPICS_ORDER = ["cycling", "ai", "dev", "gaming"]


def call_nvidia_model(model_id: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> Optional[str]:
    """Call NVIDIA API with a model. Returns None on failure."""
    url = f"{BASE_URL}/chat/completions"
    
    # Model-specific settings
    extra_body = {}
    if "nemotron" in model_id:
        extra_body = {
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 16384
        }
        temperature = 0.6
    elif "glm" in model_id:
        extra_body = {"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}}
        temperature = 1.0
    elif "gemma" in model_id:
        extra_body = {"chat_template_kwargs": {"enable_thinking": True}}
        temperature = 1.0
    
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": max_tokens,
        "stream": False
    }
    if extra_body:
        payload["extra_body"] = extra_body
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"  ⚠ {model_id}: status={response.status_code}")
            return None
    except Exception as e:
        print(f"  ⚠ {model_id}: {str(e)[:50]}")
        return None


def generate_topic_content(topic: str, model_key: str = None) -> str:
    """Generate content for a specific topic using the preferred model."""
    config = TOPIC_CONFIG.get(topic, TOPIC_CONFIG["ai"])
    model_key = model_key or config["preferred_model"]
    model_id = MODELS.get(model_key, MODELS["glm"])
    
    print(f"\n  📝 Topic: {topic.upper()} | Model: {model_key}")
    
    prompt = f"""Eres un editor de newsletter tecnológico. Escribe una sección de newsletter llamada "{topic.upper()}" con:

1. 2-3 noticias concretas y recientes sobre {config['description']}
2. Incluya fuente y enlace cuando sea relevante
3. Un dato o reflexión interesante
4. Formato: titular corto → descripción 1-2 líneas → enlace

Sé conciso, máximo 300 palabras. Usa emojis cuando adda valor.
No inventes datos. Si no tienes información reciente, indica "Sin noticias relevantes esta semana"."""
    
    result = call_nvidia_model(model_id, prompt)
    return result if result else f"[{topic.upper()}] Sin contenido disponible esta semana."


def generate_full_newsletter() -> str:
    """Generate the complete multi-model newsletter."""
    print("\n" + "="*60)
    print("📬 NEWSLETTER AGENT - NVIDIA AI Multi-Model")
    print("="*60)
    
    date = datetime.now().strftime("%A, %d de %B de %Y")
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"📬 SARAIBANewsletter - {date}")
    output.append(f"{'='*60}")
    
    for topic in TOPICS_ORDER:
        print(f"\n🔄 Processing {topic}...")
        content = generate_topic_content(topic)
        output.append(f"\n{content}")
    
    output.append(f"\n{'='*60}")
    output.append("Generado por NVIDIA AI API Multi-Model Agent")
    output.append(f"Models used: {', '.join(set(c['preferred_model'] for c in TOPIC_CONFIG.values()))}")
    output.append("="*60)
    
    return "\n".join(output)


def compare_models_on_prompt(prompt: str, model_keys: list = None) -> dict:
    """Compare multiple models on the same prompt (for testing)."""
    if model_keys is None:
        model_keys = ["nemotron", "glm", "gemma"]
    
    results = {}
    print(f"\n🔬 Benchmarking {len(model_keys)} models...\n")
    
    for key in model_keys:
        if key not in MODELS:
            print(f"⚠ Unknown model: {key}")
            continue
        
        print(f"  → Testing {key} ({MODELS[key]})...")
        start = datetime.now()
        result = call_nvidia_model(MODELS[key], prompt, max_tokens=512)
        elapsed = (datetime.now() - start).total_seconds()
        
        results[key] = {
            "model_id": MODELS[key],
            "result": result[:200] + "..." if result and len(result) > 200 else result,
            "time": round(elapsed, 2),
            "success": result is not None
        }
        print(f"  ✓ {key}: {elapsed:.1f}s")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="NVIDIA Multi-Model Newsletter Agent")
    parser.add_argument("--topic", choices=list(TOPIC_CONFIG.keys()), help="Single topic to generate")
    parser.add_argument("--models", help="Comma-separated model keys (nemotron,glm,deepseek,gemma)")
    parser.add_argument("--compare", action="store_true", help="Run model comparison benchmark")
    parser.add_argument("--output", "-o", help="Save output to file")
    
    args = parser.parse_args()
    
    if args.compare:
        # Benchmark mode
        test_prompt = "Explica en 3 líneas qué es un LLM y por qué importa para desarrolladores."
        results = compare_models_on_prompt(test_prompt, args.models.split(",") if args.models else None)
        print("\n📊 RESULTS:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    
    if args.topic:
        content = generate_topic_content(args.topic)
        print(f"\n📬 {args.topic.upper()}:\n{content}")
    else:
        newsletter = generate_full_newsletter()
        print(newsletter)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(newsletter)
            print(f"\n💾 Saved to {args.output}")
    
    print(f"\n✅ Done at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()