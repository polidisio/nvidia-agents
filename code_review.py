#!/usr/bin/env python3
"""
Multi-Model Code Reviewer - NVIDIA AI Edition
Sends code to multiple AI models and compares their reviews

Usage:
  python3 code_review.py "tu código aquí"
  python3 code_review.py --file path/to/file.py
  python3 code_review.py --lang python --compare glm,nemotron,deepseek
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, List

# NVIDIA API Config
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "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")
BASE_URL = "https://integrate.api.nvidia.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

# Models with their strengths
MODELS = {
    "nemotron": {
        "id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        "strength": " razonamiento profundo, análisis lógico",
        "temperature": 0.6
    },
    "glm": {
        "id": "z-ai/glm-5.1",
        "strength": " análisis técnico detallado",
        "temperature": 1.0
    },
    "deepseek": {
        "id": "deepseek-ai/deepseek-v4-pro",
        "strength": " código limpio, mejores prácticas",
        "temperature": 1.0
    },
    "gemma": {
        "id": "google/gemma-4-31b-it",
        "strength": " calidad de código, sugerencias creativas",
        "temperature": 1.0
    },
}

DEFAULT_MODELS = ["nemotron", "glm", "deepseek", "gemma"]


def call_nvidia_model(model_id: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> Optional[str]:
    """Call NVIDIA API. Returns None on failure."""
    url = f"{BASE_URL}/chat/completions"
    
    extra_body = {}
    if "nemotron" in model_id:
        extra_body = {
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 16384
        }
        temperature = 0.6
    elif "glm" in model_id:
        extra_body = {"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}}
    elif "gemma" in model_id:
        extra_body = {"chat_template_kwargs": {"enable_thinking": True}}
    
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
        response = requests.post(url, headers=HEADERS, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"[ERROR {response.status_code}]: {response.text[:200]}"
    except Exception as e:
        return f"[ERROR]: {str(e)[:100]}"


def review_code(code: str, language: str, models: List[str] = None) -> dict:
    """Get multi-model review of code."""
    if models is None:
        models = DEFAULT_MODELS
    
    print("\n" + "="*70)
    print("🔍 MULTI-MODEL CODE REVIEW - NVIDIA AI")
    print("="*70)
    
    results = {}
    
    for model_key in models:
        if model_key not in MODELS:
            print(f"\n⚠ Unknown model: {model_key}")
            continue
        
        model_info = MODELS[model_key]
        model_id = model_info["id"]
        
        print(f"\n🤖 [{model_key.upper()}] {model_info['strength']}")
        print(f"   Model: {model_id}")
        
        prompt = f"""Eres un revisor de código experto. Analiza el siguiente código en {language}:

```{language}
{code}
```

Devuelve tu revisión en este formato:

## {model_key.upper()} Review

### ✅ Fortalezas
- (lista de puntos positivos)

### ⚠️ Problemas
- (lista de problemas encontrados con línea si es posible)

### 💡 Sugerencias
- (mejoras específicas)

### 🏆 Veredicto
Bueno / Mejorable / Problemático

Sé específico. Si no encuentras problemas, dilo claramente.
Máximo 400 palabras."""

        start = datetime.now()
        review = call_nvidia_model(model_id, prompt, max_tokens=1024)
        elapsed = (datetime.now() - start).total_seconds()
        
        results[model_key] = {
            "review": review,
            "time": round(elapsed, 1),
            "success": not review.startswith("[ERROR")
        }
        
        print(f"   ⏱ {elapsed:.1f}s")
        if review:
            preview = review[:150] + "..." if len(review) > 150 else review
            print(f"   💬 {preview}")
    
    return results


def generate_summary(results: dict) -> str:
    """Generate a consensus summary from all reviews."""
    summary = []
    summary.append("\n" + "="*70)
    summary.append("📊 CONSENSUS SUMMARY")
    summary.append("="*70)
    
    verdicts = {}
    all_issues = []
    
    for model_key, data in results.items():
        review = data.get("review", "")
        if review and not review.startswith("[ERROR"):
            # Extract verdict
            for line in review.split("\n"):
                if "Veredicto" in line or "veredicto" in line:
                    for v in ["Bueno", "Bueno ✅", "Mejorable", "Mejorable ⚠️", "Problemático", "Problemático ❌"]:
                        if v in line:
                            verdicts[model_key] = v
    
    # Count verdicts
    good = sum(1 for v in verdicts.values() if "Bueno" in v)
    medium = sum(1 for v in verdicts.values() if "Mejorable" in v)
    bad = sum(1 for v in verdicts.values() if "Problemático" in v)
    
    summary.append(f"\n📈 Votos: ✅ {good} | ⚠️ {medium} | ❌ {bad}")
    
    if good >= len(results) / 2:
        summary.append("\n🏆 **CONCLUSIÓN: El código parece BUENO**")
    elif bad >= len(results) / 2:
        summary.append("\n🏆 **CONCLUSIÓN: El código tiene problemas significativos**")
    else:
        summary.append("\n🏆 **CONCLUSIÓN: El código es MEJORABLE**")
    
    times_str = ', '.join(f'{k}:{v["time"]}s' for k,v in results.items())
    summary.append(f"\n⏱ Tiempos: {times_str}")
    
    return "\n".join(summary)


def main():
    parser = argparse.ArgumentParser(description="NVIDIA Multi-Model Code Reviewer")
    parser.add_argument("code", nargs="?", help="Code to review (as string)")
    parser.add_argument("--file", "-f", help="Path to file to review")
    parser.add_argument("--lang", "-l", default="python", help="Programming language")
    parser.add_argument("--models", "-m", help=f"Comma-separated models: {','.join(MODELS.keys())}")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Get code to review
    if args.file:
        try:
            with open(args.file, "r") as f:
                code = f.read()
            print(f"📂 Reading: {args.file} ({len(code)} chars)")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
    elif args.code:
        code = args.code
    else:
        print("❌ Provide code via argument or --file")
        print("   Example: python3 code_review.py 'print(hello)'")
        return
    
    # Parse models
    models = args.models.split(",") if args.models else DEFAULT_MODELS
    
    print(f"\n📝 Reviewing {len(code)} chars of {args.lang} with {len(models)} models")
    
    # Run reviews
    results = review_code(code, args.lang, models)
    
    # Generate summary
    summary = generate_summary(results)
    print(summary)
    
    # Save full report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"review_report_{timestamp}.txt"
    
    with open(report_file, "w") as f:
        f.write(f"# Multi-Model Code Review Report\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Language: {args.lang}\n")
        f.write(f"# Models: {', '.join(results.keys())}\n\n")
        
        for model_key, data in results.items():
            f.write(f"\n{'='*50}\n")
            f.write(f"# MODEL: {model_key.upper()} ({data['time']}s)\n")
            f.write(f"{'='*50}\n\n")
            f.write(data.get("review", "No review available"))
            f.write("\n")
        
        f.write(summary)
    
    print(f"\n💾 Full report saved to: {report_file}")


if __name__ == "__main__":
    main()