import queue

audio_queue = queue.Queue()
is_audio_working = False
is_audio_recording = False

def set_audio_working(working):
    global is_audio_working
    is_audio_working = working

def set_audio_recording(recording):
    global is_audio_recording
    is_audio_recording = recording