import audioop
import struct
import wave

path = "pat_mic_test.wav"

with wave.open(path, "rb") as wav:
    frames = wav.readframes(wav.getnframes())
    width = wav.getsampwidth()
    samples = struct.unpack("<" + "h" * (len(frames) // 2), frames)

    print("Duration:", round(wav.getnframes() / wav.getframerate(), 2))
    print("RMS:", audioop.rms(frames, width))
    print("Peak amplitude:", max(abs(x) for x in samples))
    print("Silent samples:", sum(x == 0 for x in samples))
    print("Total samples:", len(samples))