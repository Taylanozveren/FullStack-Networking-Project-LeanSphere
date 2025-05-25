# core/utils.py

import re
import requests
import logging
from django.conf import settings
from PyPDF2 import PdfReader
from datetime import datetime

# Cursor: Logging ekleyerek hata ayıklamayı kolaylaştırma
logger = logging.getLogger(__name__)

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
    Uzun metinler için Hugging Face summarization API'sini çağırır.
    HF_API_TOKEN ve HF_SUMMARY_API_URL .env içinde tanımlı olmalı.
    """
    api_token = getattr(settings, "HF_API_TOKEN", None)
    api_url   = getattr(settings, "HF_SUMMARY_API_URL", None)

    # Cursor: Daha kapsamlı hata kontrolü ve hata mesajı
    if not api_token:
        logger.error("HF_API_TOKEN tanımlı değil.")
        raise RuntimeError(
            "HF_API_TOKEN ayarlı değil. "
            "Lütfen .env dosyanıza ekleyin."
        )
    
    if not api_url:
        logger.error("HF_SUMMARY_API_URL tanımlı değil.")
        raise RuntimeError(
            "HF_SUMMARY_API_URL ayarlı değil. "
            "Lütfen .env dosyanıza ekleyin."
        )

    try:
        headers = {"Authorization": f"Bearer {api_token}"}
        payload = {
            # Bu API doğrudan metinden özet çıkarır, ek instruction koymaya gerek yok
            "inputs": text,
            "parameters": {"max_length": max_length, "min_length": min_length}
        }

        logger.info(f"Hugging Face API isteği gönderiliyor: {api_url[:30]}...")
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        # Cursor: API yanıtını log'a kaydet (hassas bilgileri filtrele)
        logger.info(f"API yanıtı alındı: Status {resp.status_code}")
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.error(f"Geçersiz API yanıtı: {data}")
            raise RuntimeError("Hugging Face API geçersiz yanıt döndü.")
        
        return data[0].get("summary_text", "")
    except requests.RequestException as e:
        logger.error(f"API isteği başarısız: {str(e)}")
        raise RuntimeError(f"Hugging Face API isteği başarısız: {str(e)}")
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"API yanıtı işlenirken hata: {str(e)}")
        raise RuntimeError(f"API yanıtı işlenirken hata: {str(e)}")


def test_api_connection():
    """
    API bağlantısını test eder.
    """
    api_token = getattr(settings, "HF_API_TOKEN", None)
    explain_url = getattr(settings, "HF_EXPLAIN_API_URL", None)

    if not api_token:
        return False, "HF_API_TOKEN is missing"
    if not explain_url:
        return False, "HF_EXPLAIN_API_URL is missing"

    try:
        headers = {"Authorization": f"Bearer {api_token}"}
        test_payload = {
            "inputs": "Test API connection",
            "parameters": {
                "max_length": 50,
                "min_length": 10,
                "do_sample": False
            }
        }
        
        resp = requests.post(explain_url, headers=headers, json=test_payload, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        if not data or not isinstance(data, list) or len(data) == 0:
            return False, f"Invalid API response structure: {data}"
            
        return True, "API connection successful"
        
    except requests.exceptions.RequestException as e:
        return False, f"API connection error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def clean_explanation(text: str, concept: str = "") -> str:
    """
    AI yanıtını 3-4 cümleye çıkarır, linkleri ve alakasız cümleleri temizler, anahtar kelimelerle ilgili bilgi ekler.
    """
    # Tüm cümlelere ayır
    sentences = re.split(r'(?<=[.!?]) +', text)
    filtered = []
    for s in sentences:
        s = s.strip()
        # Link, reklam, destek, click here, www, telefon, e-posta, "for more information" gibi şeyleri at
        if re.search(r'(http[s]?://|www\.|click here|for more information|support|call|visit|details|gallery|confidential|samaritans|email|\d{3,})', s, re.I):
            continue
        # Çok kısa veya çok anlamsız cümleleri at
        if len(s) < 15:
            continue
        filtered.append(s)
        if len(filtered) == 4:
            break
    summary = " ".join(filtered).strip()

    # Eğer hala çok kısa ise, concept ile ilgili otomatik bilgi ekle
    if len(summary.split()) < 12 and concept:
        summary = f"{concept.capitalize()} is an important concept in computer science. It refers to the use, design, or understanding of {concept.lower()} in various applications."

    # Cümle başı büyük, sonu noktalı
    if summary and not summary.endswith('.'):
        summary += '.'

    # Başına kavramı ekle (gerekiyorsa)
    if concept and not summary.lower().startswith(concept.lower()):
        summary = f'{concept.capitalize()}: {summary}'

    return summary

def generate_explanation(text: str) -> str:
    api_token = getattr(settings, "HF_API_TOKEN", None)
    explain_url = getattr(settings, "HF_EXPLAIN_API_URL", None)

    if not api_token or not explain_url:
        logger.error("API configuration missing")
        return "API configuration is missing"

    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        concept = text.strip()
        if len(concept) > 100:
            concept = concept[:97] + "..."
        payload = {
            "inputs": concept,
            "options": {
                "wait_for_model": True
            }
        }
        logger.debug(f"Sending request to API with concept: {concept}")
        resp = requests.post(explain_url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            error_msg = f"API error {resp.status_code}: {resp.text}"
            logger.error(error_msg)
            return error_msg
        data = resp.json()
        logger.debug(f"Raw API response: {data}")
        if isinstance(data, list) and len(data) > 0:
            result = data[0].get("summary_text", "") or data[0].get("generated_text", "")
            if result:
                return clean_explanation(result, concept=concept)
        logger.error(f"Unexpected API response format: {data}")
        return "Unexpected API response format"
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return "API request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return f"API request failed: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"


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

def extract_key_terms(text: str, max_terms: int = 3) -> list[str]:
    """
    Metinden anahtar terimleri çıkarır.
    Bu terimler açıklamayı zenginleştirmek için kullanılabilir.
    """
    # Basit bir terim çıkarma yaklaşımı
    words = text.lower().split()
    # Stop words ve gereksiz kelimeleri kaldır
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were'}
    terms = [w for w in words if w not in stop_words and len(w) > 3]
    # Frekansa göre sırala
    from collections import Counter
    return [term for term, _ in Counter(terms).most_common(max_terms)]

def generate_related_questions(text: str, key_terms: list[str]) -> list[str]:
    """
    Verilen metin ve anahtar terimlere göre ilgili sorular üretir.
    Bu sorular öğrenmeyi derinleştirmek için kullanılabilir.
    """
    questions = [
        f"What are the main benefits of {text.strip()}?",
        f"How is {text.strip()} used in practice?",
        f"What skills are needed for {text.strip()}?"
    ]
    return questions[:2]  # En alakalı 2 soruyu döndür
