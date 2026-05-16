#!/usr/bin/env python3
"""
Newsletter Agent v2 - News Fetching + AI Writing
1. Fetch news from real sources via RSS feeds
2. Use NVIDIA AI (Nemotron) to write engaging newsletter content
"""

import os
import re
import requests
from datetime import datetime
from typing import List, Dict

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

# News sources by topic (RSS feeds)
NEWS_SOURCES = {
    "cycling": [
        {"name": "CyclingNews", "url": "https://www.cyclingnews.com/rss/"},
        {"name": "ZwiftInsider", "url": "https://zwiftinsider.com/feed/"},
    ],
    "ai": [
        {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
        {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    ],
    "dev": [
        {"name": "HackerNews", "url": "https://hnrss.org/frontpage"},
        {"name": "GitHub Trending", "url": "https://github.com/polidisio/feed"},
    ],
    "gaming": [
        {"name": "GameSpot", "url": "https://www.gamespot.com/feeds/mashup/"},
    ],
}

MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"


def fetch_rss_feed(url: str, source_name: str) -> List[Dict]:
    """Fetch and parse RSS feed. Returns list of {title, description, link}."""
    items = []
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return items
        
        content = response.text
        
        # Check for CDATA format first
        cdata_items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL | re.IGNORECASE)
        if not cdata_items:
            cdata_items = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL | re.IGNORECASE)
        
        for item_xml in cdata_items:
            # Try CDATA title: <title><![CDATA[Title]]></title>
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item_xml, re.DOTALL)
            
            # Try regular title: <title>Title</title>
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item_xml, re.DOTALL)
            
            # Try CDATA description
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item_xml, re.DOTALL)
            if not desc_match:
                desc_match = re.search(r'<description>(.*?)</description>', item_xml, re.DOTALL)
            
            # Try content:encoded (common in WordPress feeds)
            if not desc_match:
                desc_match = re.search(r'<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>', item_xml, re.DOTALL)
            if not desc_match:
                desc_match = re.search(r'<content:encoded>(.*?)</content:encoded>', item_xml, re.DOTALL)
            
            # Link
            link_match = re.search(r'<link>(.*?)</link>', item_xml, re.DOTALL)
            if not link_match:
                link_match = re.search(r'<link>(.*?)</link>', item_xml)
            
            if title_match:
                title_text = title_match.group(1).strip()
                title_text = re.sub(r'<[^>]+>', '', title_text)
                
                desc_text = ""
                if desc_match:
                    desc_text = desc_match.group(1).strip()
                    desc_text = re.sub(r'<[^>]+>', '', desc_text)
                    desc_text = desc_text[:400].strip()
                
                link_text = link_match.group(1).strip() if link_match else ""
                
                if title_text and len(title_text) > 10:
                    items.append({
                        "title": title_text,
                        "description": desc_text,
                        "link": link_text,
                        "source": source_name
                    })
        
        return items[:6]
    
    except Exception as e:
        print(f"  ⚠ Error fetching {source_name}: {str(e)[:50]}")
        return items


def fetch_news_for_topic(topic: str) -> str:
    """Fetch news from all sources for a topic and format as text."""
    sources = NEWS_SOURCES.get(topic, [])
    all_items = []
    
    print(f"  📰 Fetching {topic} news...")
    for source in sources:
        items = fetch_rss_feed(source["url"], source["name"])
        if items:
            print(f"    - {source['name']}: {len(items)} items")
        all_items.extend(items)
    
    if not all_items:
        return ""
    
    # Format as text for AI
    news_text = f"Noticias de {topic.upper()}:\n\n"
    for i, item in enumerate(all_items[:8], 1):
        news_text += f"{i}. {item['title']}\n"
        if item['description']:
            news_text += f"   {item['description'][:300]}\n"
        if item['link']:
            news_text += f"   🔗 {item['link']}\n"
        news_text += "\n"
    
    return news_text


def call_nvidia(prompt: str, max_tokens: int = 2000) -> str:
    """Call NVIDIA Nemotron model."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Eres un editor de newsletter experto. Transformas noticias en contenido atractivo y fácil de leer. Usas español natural, emojis discretos y eres conciso."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": max_tokens,
        "stream": False,
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 8192
        }
    }
    
    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=90)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠ NVIDIA error: {str(e)[:50]}")
    return ""


def generate_topic_content(topic: str, topic_emoji: str) -> str:
    """Generate newsletter section for a topic using real news + AI."""
    
    # Step 1: Fetch real news
    news_text = fetch_news_for_topic(topic)
    
    if not news_text:
        return f"<h2>{topic_emoji} {topic.upper()}</h2><p>No se han encontrado noticias esta semana.</p>"
    
    # Step 2: Ask AI to write the section
    prompt = f"""Transforma estas noticias en una sección de newsletter atractivo:

{news_text}

Requisitos:
- 2-3 noticias destacadas (no todas)
- Titulares cortos y descriptivos
- Descripción de 1-2 líneas
- Incluye el enlace cuando sea relevante
- Un dato o reflexión al final
- Usa 1-2 emojis máximo
- Máximo 300 palabras
- Formato HTML: <h3> para titulares, <p> para texto
- No inventes información"""

    result = call_nvidia(prompt)
    
    if result and len(result) > 30:
        result = result.strip()
        if not result.startswith(f"<h"):
            result = f"<h3>{topic.upper()}</h3>\n{result}"
        return result
    else:
        # Fallback: show raw news
        fallback = f"<h3>{topic_emoji} {topic.upper()}</h3>\n"
        fallback += "<p>Noticias encontradas:</p>\n"
        for item in all_items[:5]:
            fallback += f"<p><strong>{item['title']}</strong></p>\n"
        return fallback


def send_email(subject: str, html_content: str) -> bool:
    """Send email via Resend API."""
    payload = {
        "from": "Aria Agent <aria.agent@saraiba.eu>",
        "to": ["aspontes@saraiba.eu"],
        "subject": subject,
        "html": html_content
    }
    
    try:
        response = requests.post(RESEND_URL, headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=30)
        return response.status_code == 200
    except:
        return False


def generate_newsletter():
    """Main: Fetch all news, generate content, send email."""
    print("=" * 60)
    print("📬 NVIDIA AI NEWSLETTER v2 - With Real News")
    print("=" * 60)
    
    date = datetime.now().strftime("%A, %d de %B de %Y")
    
    # Fetch all news first
    print("\n📰 Fetching news from all sources...")
    all_news = {}
    topics = ["cycling", "ai", "dev", "gaming"]
    topic_emojis = {"cycling": "🚴", "ai": "🤖", "dev": "💻", "gaming": "🎮"}
    
    for topic in topics:
        print(f"\n📝 Processing {topic}...")
        news_text = fetch_news_for_topic(topic)
        all_news[topic] = news_text
        print(f"    → {len(news_text)} chars")
    
    # Generate content with AI
    print("\n🤖 Generating AI content...")
    sections = []
    for topic in topics:
        news_text = all_news[topic]
        
        if not news_text:
            sections.append(f"<h3>{topic_emojis[topic]} {topic.upper()}</h3><p>Sin noticias esta semana.</p>")
            continue
        
        prompt = f"""Transforma estas noticias en una sección de newsletter atractivo:

{news_text}

Requisitos:
- 2-3 noticias destacadas
- Titulares cortos y descriptivos  
- Descripción de 1-2 líneas
- Incluye el enlace cuando sea relevante
- Un dato o reflexión al final
- Usa 1-2 emojis máximo
- Máximo 300 palabras
- Formato HTML: <h3> para titulares, <p> para texto
- No inventes información"""

        result = call_nvidia(prompt)
        
        if result and len(result) > 30:
            sections.append(f"<div style='margin-bottom: 20px;'>{result}</div>")
        else:
            sections.append(f"<h3>{topic_emojis[topic]} {topic.upper()}</h3><p>No se pudo generar contenido.</p>")
    
    # Build HTML
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
        <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h1 style="color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 10px; margin: 0 0 5px 0;">
                📬 Saraiba Newsletter
            </h1>
            <p style="color: #666; font-size: 12px; margin: 0 0 20px 0;">
                {date} | NVIDIA AI + Noticias Reales
            </p>
            {"".join(sections)}
        </div>
        <div style="text-align: center; padding: 15px; color: #999; font-size: 11px;">
            <hr style="border: none; border-top: 1px solid #ddd; margin: 15px 0;">
            <p>Aria Agent 🧠 | NVIDIA Nemotron | Fuentes RSS</p>
        </div>
    </div>
    """
    
    subject = f"📬 Saraiba Newsletter - {date}"
    
    print("\n📧 Sending email...")
    if send_email(subject, html):
        print("✅ Newsletter sent!")
    else:
        print("❌ Failed to send")


if __name__ == "__main__":
    generate_newsletter()