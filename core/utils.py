# core/utils.py

import re
import requests
from django.conf import settings
from PyPDF2 import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """
    Verilen PDF dosyasından sayfa sayfa metin çıkarır
    ve birleştirip döner.
    """
    reader = PdfReader(file_path)
    texts = []
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            texts.append(txt)
    return "\n".join(texts)


def generate_summary(
    text: str,
    max_length: int = 300,
    min_length: int = 80
) -> str:
    """
    Uzun metinler için Hugging Face summarization API’sini çağırır.
    HF_API_TOKEN ve HF_SUMMARY_API_URL .env içinde tanımlı olmalı.
    """
    api_token = getattr(settings, "HF_API_TOKEN", None)
    api_url   = getattr(settings, "HF_SUMMARY_API_URL", None)

    if not api_token or not api_url:
        raise RuntimeError(
            "HF_API_TOKEN veya HF_SUMMARY_API_URL ayarlı değil. "
            "Lütfen .env dosyanıza ekleyin."
        )

    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {
        # Bu API doğrudan metinden özet çıkarır, ek instruction koymaya gerek yok
        "inputs": text,
        "parameters": {"max_length": max_length, "min_length": min_length}
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data[0].get("summary_text", "")


def generate_explanation(
    text: str,
    max_length: int = 200,
    min_length: int = 50
) -> str:
    """
    Kısa kavram/metinler için 'explain' API’sini çağırır.
    Aşağıdaki prompt ile modelden yalnızca verilen bilgiyi
    kullanarak açıklama yapması istenir—ek URL veya bilgi eklemez.
    HF_API_TOKEN ve HF_EXPLAIN_API_URL .env içinde tanımlı olmalı.
    """
    api_token   = getattr(settings, "HF_API_TOKEN", None)
    explain_url = getattr(settings, "HF_EXPLAIN_API_URL", None)

    if not api_token or not explain_url:
        raise RuntimeError(
            "HF_API_TOKEN veya HF_EXPLAIN_API_URL ayarlı değil. "
            "Lütfen .env dosyanıza ekleyin."
        )

    headers = {"Authorization": f"Bearer {api_token}"}
    # Prompt'u sıkılaştırıyoruz:
    instruction = (
        "Explain the following in simple terms using only the information given. "
        "Do NOT add any URLs or external facts:\n\n"
    )
    payload = {
        "inputs": instruction + text,
        "parameters": {"max_length": max_length, "min_length": min_length}
    }

    resp = requests.post(explain_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Bazı modeller "generated_text", bazısı "summary_text" dönebilir:
    return data[0].get("generated_text", data[0].get("summary_text", ""))


def chunk_text(text: str, max_chars: int = 8000) -> list[str]:
    """
    Çok uzun metinleri, maksimum max_chars karakterlik
    cümle-sonu kırılımlarıyla parçalara böler.
    """
    sentences = re.split(r'(?<=[\.\?\!])\s+', text)
    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) + 1 <= max_chars:
            current += sent + " "
        else:
            if current:
                chunks.append(current.strip())
            current = sent + " "
    if current:
        chunks.append(current.strip())
    return chunks
