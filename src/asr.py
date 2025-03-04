import azure.cognitiveservices.speech as speechsdk
import time
import config

# create service client
speech_config = speechsdk.SpeechConfig(subscription=config.SPEECH_KEY, region=config.SPEECH_REGION)
speech_config.speech_recognition_language="en-US"
audio_config = speechsdk.AudioConfig(use_default_microphone=True)
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# Track the last time speech was detected
last_speech_time = time.time()

def recognized_callback(evt):
    """ Callback function triggered when speech is recognized """
    global last_speech_time
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Recognized text: {evt.result.text}")
        last_speech_time = time.time()  # Reset timer

def session_stopped_callback(evt):
    """ Callback triggered when the session stops """
    print("Session stopped")
    stop_continuous_recognition()

def stop_continuous_recognition():
    """ Stop speech recognition if there is no input for 5 seconds """
    print("No speech detected for 5 seconds. Terminating process.")
    speech_recognizer.stop_continuous_recognition()
    exit(0)  # Exit the script

# Bind event handlers
speech_recognizer.recognized.connect(recognized_callback)
speech_recognizer.session_stopped.connect(session_stopped_callback)

# Start continuous speech recognition
print("Listening for speech (terminates if silent for 5 seconds)...")
speech_recognizer.start_continuous_recognition()

# Monitor for silence
while True:
    time.sleep(1)
    if time.time() - last_speech_time > 5:
        stop_continuous_recognition()
