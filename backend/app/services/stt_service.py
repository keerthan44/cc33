import asyncio
import logging
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class STTService:
    _model: WhisperModel | None = None

    def get_model(self) -> WhisperModel:
        if STTService._model is None:
            STTService._model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
            )
        return STTService._model

    async def transcribe(self, audio_bytes: bytes, vad_filter: bool = True) -> str:
        src = tempfile.NamedTemporaryFile(delete=False, suffix=".audio")
        dst_path = src.name + ".wav"
        try:
            src.write(audio_bytes)
            src.close()

            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", src.name,
                "-ar", "16000", "-ac", "1", dst_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("ffmpeg conversion failed: %s", stderr.decode())
                return ""

            segments, _ = await asyncio.to_thread(
                self.get_model().transcribe, dst_path, vad_filter=vad_filter
            )
            return " ".join(seg.text.strip() for seg in segments if seg.text.strip())
        except Exception as exc:
            logger.error("STT transcription error: %s", exc)
            return ""
        finally:
            Path(src.name).unlink(missing_ok=True)
            Path(dst_path).unlink(missing_ok=True)
