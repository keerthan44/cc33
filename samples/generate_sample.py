"""Generate a 3-second silent WAV at 16 kHz mono for endpoint testing."""
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 16_000
DURATION_S = 3
OUTPUT = Path(__file__).parent / "sample.wav"


def main() -> None:
    num_frames = SAMPLE_RATE * DURATION_S
    with wave.open(str(OUTPUT), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(struct.pack(f"<{num_frames}h", *([0] * num_frames)))
    print(f"Created {OUTPUT}  ({DURATION_S}s silent WAV, 16 kHz mono)")


if __name__ == "__main__":
    main()
