# tts_service.py

import os
import io
import base64
import subprocess
from pathlib import Path
from fastapi import HTTPException
from pydub import AudioSegment
from pydub.utils import which

AudioSegment.converter = which("ffmpeg")


# Optional Google Cloud client (only needed if using GOOGLE_APPLICATION_CREDENTIALS)
# from google.cloud import texttospeech


# -------------------------------
# Helpers for chunking
# -------------------------------
def _chunk_text_by_chars(text: str, max_chars: int):
    """Split text into chunks not exceeding max_chars, preferring whitespace boundaries."""
    import re

    if len(text) <= max_chars:
        return [text]

    tokens = re.findall(r"\S+\s*", text)
    chunks, current = [], ""

    for token in tokens:
        if len(current) + len(token) <= max_chars:
            current += token
        else:
            if current:
                chunks.append(current.strip())
                current = ""
            if len(token) > max_chars:
                start = 0
                while start < len(token):
                    part = token[start:start + max_chars].strip()
                    if part:
                        chunks.append(part)
                    start += max_chars
            else:
                current = token

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if c]


# -------------------------------
# Provider-specific implementations
# -------------------------------

def _generate_gcp_tts(text: str, output_file: str, voice: str, lang="en-US"):
    """Google Cloud TTS via REST API or service account."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("TTS_API")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    try:
        if api_key:
            # REST API call
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
            body = {
                "input": {"text": text},
                "voice": {"languageCode": lang, "name": voice},
                "audioConfig": {"audioEncoding": "MP3"},
            }
            import requests
            r = requests.post(url, json=body, timeout=30)
            r.raise_for_status()
            audio_content = r.json().get("audioContent")
            if not audio_content:
                raise RuntimeError("Google TTS returned empty response.")
            with open(output_file, "wb") as f:
                f.write(base64.b64decode(audio_content))
        # else:
        #     # Service account client
        #     # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            # client = texttospeech.TextToSpeechClient()
            # input_text = texttospeech.SynthesisInput(text=text)
            # voice_params = texttospeech.VoiceSelectionParams(language_code=lang, name=voice)
            # audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            # response = client.synthesize_speech(input=input_text, voice=voice_params, audio_config=audio_config)
            # with open(output_file, "wb") as f:
            #     f.write(response.audio_content)

        return output_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCP TTS failed: {e}")


def _generate_azure_tts(text: str, output_file: str, voice: str):
    """Azure OpenAI TTS call."""
    api_key = os.getenv("AZURE_TTS_KEY")
    endpoint = os.getenv("AZURE_TTS_ENDPOINT")
    deployment = os.getenv("AZURE_TTS_DEPLOYMENT", "tts")
    api_version = os.getenv("AZURE_TTS_API_VERSION", "2025-03-01-preview")

    if not api_key or not endpoint:
        raise HTTPException(status_code=500, detail="Azure TTS credentials missing.")

    headers = {"api-key": api_key, "Content-Type": "application/json"}
    payload = {"model": deployment, "input": text, "voice": voice}

    import requests
    try:
        r = requests.post(
            f"{endpoint}/openai/deployments/{deployment}/audio/speech?api-version={api_version}",
            headers=headers, json=payload, timeout=30
        )
        r.raise_for_status()
        with open(output_file, "wb") as f:
            f.write(r.content)
        return output_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Azure TTS failed: {e}")


def _generate_local_tts(text: str, output_file: str, voice: str):
    """Local espeak-ng fallback."""
    temp_wav_file = output_file.replace(".mp3", ".wav")
    espeak_speed = os.getenv("ESPEAK_SPEED", "150")

    try:
        cmd = ["espeak-ng", "-v", voice, "-s", espeak_speed, "-w", temp_wav_file, text]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        audio = AudioSegment.from_wav(temp_wav_file)
        audio.export(output_file, format="mp3")
        os.remove(temp_wav_file)
        return output_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local TTS failed: {e}")


# -------------------------------
# Main Podcast Generation
# -------------------------------

def script_to_audio(script_text: str, output_path: Path, provider: str = "gcp"):
    """
    Convert a podcast script into audio with alternating voices.
    Supports: gcp, azure, local.
    """
    provider = provider.lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    voices = {
        "gcp": ["en-US-Wavenet-D", "en-US-Wavenet-F"],
        "azure": ["alloy", "shimmer"],
        "local": ["en+m1", "en+f3"],
    }

    if provider not in voices:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    lines = [l.strip() for l in script_text.splitlines() if l.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="Script text is empty.")

    podcast_audio = AudioSegment.silent(duration=500)

    for idx, line in enumerate(lines):
        voice = voices[provider][idx % 2]
        temp_file = output_path.parent / f".line_{idx}.mp3"

        # Handle chunking for long lines (esp. in GCP/Azure)
        max_chars = int(os.getenv("TTS_CLOUD_MAX_CHARS", "3000"))
        text_chunks = _chunk_text_by_chars(line, max_chars)

        combined_line_audio = AudioSegment.silent(duration=0)
        for chunk in text_chunks:
            if provider == "gcp":
                _generate_gcp_tts(chunk, str(temp_file), voice)
            elif provider == "azure":
                _generate_azure_tts(chunk, str(temp_file), voice)
            else:
                _generate_local_tts(chunk, str(temp_file), voice)

            segment = AudioSegment.from_file(temp_file, format="mp3")
            combined_line_audio += segment

        podcast_audio += combined_line_audio + AudioSegment.silent(duration=400)

        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass

    final_file = output_path.with_suffix(".mp3")
    podcast_audio.export(final_file, format="mp3")
    print(f"[PODCAST] Generated at {final_file}")
    return str(final_file)
