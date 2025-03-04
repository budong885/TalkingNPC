import pyaudio
import numpy as np
import pvporcupine as porcupine
import config

# Initialize the Porcupine keyword detector
porcupine = porcupine.create(access_key=config.PICO_KEY, keyword_paths=["./resources/こんにちは_ja_windows_v3_0_0.ppn"], model_path="./resources/porcupine_params_ja.pv")

# Audio stream parameters
SAMPLE_RATE = 16000  # 16kHz sample rate
FRAME_LENGTH = porcupine.frame_length  # The number of audio samples per frame

# Initialize the audio stream
p = pyaudio.PyAudio()

def get_next_audio_frame(stream):
    # Read a frame of audio data from the microphone
    audio_frame = stream.read(FRAME_LENGTH)
    # Convert the byte data to numpy array (16-bit PCM)
    audio_frame = np.frombuffer(audio_frame, dtype=np.int16)
    return audio_frame

def keyword_detect():
    # Open the microphone stream
    stream = p.open(format=pyaudio.paInt16,  # 16-bit PCM format
                    channels=1,  # Mono audio
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=FRAME_LENGTH)

    print("Listening for keywords...")

    # Continuously process audio for keyword detection
    try:
        while True:
            audio_frame = get_next_audio_frame(stream)
            keyword_index = porcupine.process(audio_frame)
            
            if keyword_index >= 0:
                print("Detected key words!")

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Close the audio stream and cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        porcupine.delete()
