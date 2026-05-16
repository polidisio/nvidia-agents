#!/usr/bin/env python3
"""
Newsletter Agent with Email Delivery
Sends newsletter via Resend API to Jose's email
"""

import os
import sys
import json
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

# Resend API Config
RESEND_API_KEY = "re_BNZqQcAu_CXy8q5qscoZ8XcwoehfVdZfx"
RESEND_URL = "https://api.resend.com/emails"

# Models
MODELS = {
    "nemotron": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "glm": "z-ai/glm-5.1",
    "deepseek": "deepseek-ai/deepseek-v4-pro",
    "gemma": "google/gemma-4-31b-it",
}

TOPICS_CONFIG = {
    "cycling": {
        "description": "Noticias de ciclismo, Zwift, indoor training",
        "emoji": "🚴",
        "preferred_model": "nemotron",
    },
    "ai": {
        "description": "Novedades en IA, LLMs, herramientas de IA",
        "emoji": "🤖",
        "preferred_model": "nemotron",
    },
    "dev": {
        "description": "Desarrollo, programación, herramientas",
        "emoji": "💻",
        "preferred_model": "nemotron",
    },
    "gaming": {
        "description": "Videojuegos, gaming, nuevos títulos",
        "emoji": "🎮",
        "preferred_model": "nemotron",
    },
}

TOPICS_ORDER = ["cycling", "ai", "dev", "gaming"]


def call_nvidia_model(model_id: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> Optional[str]:
    url = f"{BASE_URL}/chat/completions"
    
    extra_body = {}
    if "nemotron" in model_id:
        extra_body = {"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 16384}
        temperature = 0.6
    
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
            return response.json()["choices"][0]["message"]["content"]
        else:
            return None
    except:
        return None


def generate_topic_html(topic: str, model_key: str = "nemotron") -> str:
    config = TOPICS_CONFIG.get(topic, TOPICS_CONFIG["ai"])
    model_id = MODELS.get(model_key, MODELS["nemotron"])
    
    prompt = f"""Eres un editor de newsletter tecnológico. Escribe una sección llamada "{topic.upper()}" con:
1. 2-3 noticias concretas sobre {config['description']}
2. Incluya fuente y enlace cuando sea relevante
3. Un dato o reflexión interesante
4. Máximo 250 palabras. Usa emojis cuando adda valor.
No inventes datos."""

    result = call_nvidia_model(model_id, prompt, max_tokens=800)
    
    if result:
        return f"""
<h2>{config['emoji']} {topic.upper()}</h2>
<p>{result}</p>
"""
    else:
        return f"""
<h2>{config['emoji']} {topic.upper()}</h2>
<p>Sin noticias relevantes esta semana.</p>
"""


def send_email(subject: str, html_content: str) -> bool:
    """Send email via Resend API."""
    payload = {
        "from": "Aria Agent <aria.agent@saraiba.eu>",
        "to": ["aspontes@saraiba.eu"],
        "subject": subject,
        "html": html_content
    }
    
    try:
        response = requests.post(
            RESEND_URL,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Email error: {e}")
        return False


def generate_and_send_newsletter():
    """Generate newsletter and send to Jose via email."""
    print("📬 Generating newsletter...")
    
    date = datetime.now().strftime("%A, %d de %B de %Y")
    
    html_parts = [
        f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #1a1a2e; border-bottom: 2px solid #e94560; padding-bottom: 10px;">
                📬 Saraiba Newsletter - {date}
            </h1>
            <p style="color: #666; font-size: 12px;">
                Generado por NVIDIA AI Multi-Model Agent | Model: Nemotron
            </p>
        """
    ]
    
    for topic in TOPICS_ORDER:
        print(f"  📝 {topic}...")
        html_parts.append(generate_topic_html(topic))
    
    html_parts.append("""
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 11px;">
                Enviado por Aria Agent | NVIDIA API Multi-Model Newsletter
            </p>
        </div>
    """)
    
    html_content = "\n".join(html_parts)
    subject = f"📬 Saraiba Newsletter - {date}"
    
    print("📧 Sending email...")
    success = send_email(subject, html_content)
    
    if success:
        print("✅ Newsletter sent successfully!")
    else:
        print("❌ Failed to send email")
    
    return success


if __name__ == "__main__":
    generate_and_send_newsletter()