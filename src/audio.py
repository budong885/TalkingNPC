import pyaudio
import queue
import wave
import threading
import numpy as np
import time
import config
import pvporcupine as porcupine

# ========== 配置音频参数 ==========
porcupine = porcupine.create(access_key=config.PICO_KEY, keyword_paths=["./resources/こんにちは_ja_windows_v3_0_0.ppn"], model_path="./resources/porcupine_params_ja.pv")
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # 采样率 16kHz
CHUNK = porcupine.frame_length  # 每帧数据大小

# 阈值设置（用于检测静音）
SILENCE_THRESHOLD = 500  # 小于该值认为是静音
SILENCE_DURATION = 1  # 静音超过多少秒停止录音

# 创建队列存储音频数据
audio_queue = queue.Queue()

recording = False  # 是否在录音状态
last_audio_time = time.time()  # 记录最后有声音的时间


# ========== 录音线程 ==========
def microphone_thread(speech_file_path):
    global recording, last_audio_time

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("麦克风输入线程启动...")

    try:
        while True:
            audio_data = stream.read(CHUNK)
            audio_frame = np.frombuffer(audio_data, dtype=np.int16)
            audio_queue.put(audio_data)

            # 关键词检测
            keyword_index = porcupine.process(audio_frame)
            if keyword_index == 0:  # 检测到关键词
                print("检测到 'porcupine' 关键词! 开始录音...")
                recording = True
                last_audio_time = time.time()  # 记录开始录音的时间

            # 如果正在录音，检测静音
            if recording:
                amplitude = np.frombuffer(audio_data, dtype=np.int16).max()  # 计算最大音量
                if amplitude > SILENCE_THRESHOLD:
                    last_audio_time = time.time()  # 重置静音计时
                elif time.time() - last_audio_time > SILENCE_DURATION:  # 静音超过 X 秒
                    print("检测到静音, 停止录音...")
                    recording = False
                    save_queue_to_wav(speech_file_path)
                    clear_queue()

    except KeyboardInterrupt:
        print("录音线程结束...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


# ========== 保存队列中的音频数据到 WAV 文件 ==========
def save_queue_to_wav(filename):
    print(f"正在保存音频到 {filename}...")
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)

        while not audio_queue.empty():
            wf.writeframes(audio_queue.get())

    print(f"音频已保存为 {filename}")


# ========== 清空队列 ==========
def clear_queue():
    while not audio_queue.empty():
        audio_queue.get()


if __name__ == "__main__":
    output_filename = "./temp/output.wav"
    microphone_thread(output_filename)
