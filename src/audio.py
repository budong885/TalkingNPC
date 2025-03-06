import pyaudio
import queue
import wave
import threading
import numpy as np
import time
import config
import workstate
import pvporcupine as porcupine
import playsound
import os

# ========== 配置音频参数 ==========
porcupine = porcupine.create(access_key=config.PICO_KEY, keyword_paths=["./resources/こんにちは_ja_windows_v3_0_0.ppn"], model_path="./resources/porcupine_params_ja.pv")
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # 采样率 16kHz
CHUNK = porcupine.frame_length  # 每帧数据大小

# 阈值设置（用于检测静音）
SILENCE_THRESHOLD = 500  # 小于该值认为是静音
SILENCE_DURATION = 2  # 静音超过多少秒停止录音


# 创建队列存储音频数据
audio_queue = queue.Queue()

high_count = 0  # 高音量计数
last_audio_time = time.time()  # 记录最后有声音的时间


# ========== 录音线程 ==========
def microphone_thread(speech_file_path):
    global recording, last_audio_time, working, high_count

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("麦克风输入线程启动...")

    try:
        # 计算系统白噪音的平均值
        noise_samples = []
        for _ in range(50):  # 采集50个样本
            audio_data = stream.read(CHUNK)
            audio_frame = np.frombuffer(audio_data, dtype=np.int16)
            noise_samples.append(np.abs(audio_frame).mean())
        noise_threshold = max(np.mean(noise_samples) * 1.5, 500)  # 设置阈值为白噪音平均值的1.5倍
        #print(f"系统白噪音平均值: {np.mean(noise_samples)}, 阈值设置为: {noise_threshold}")

        while True:
            audio_data = stream.read(CHUNK)
            audio_frame = np.frombuffer(audio_data, dtype=np.int16)

            # 关键词检测
            keyword_index = porcupine.process(audio_frame)
            if keyword_index == 0:  # 检测到关键词
                if not workstate.is_audio_working:
                    print("检测到唤醒词! 开始运行...")
                    workstate.audio_queue.put("./resources/wakeup.wav")
                    workstate.set_audio_working(True)
                else:
                    workstate.set_audio_working(False)
                    workstate.set_audio_recording(False)
                    clear_queue()
                    workstate.audio_queue.put("./resources/sleep.wav")
                    continue

            # 如果正在录音，检测静音
            if workstate.is_audio_working:
                if workstate.is_audio_recording:
                    audio_queue.put(audio_data)
                amplitude = np.frombuffer(audio_data, dtype=np.int16).max()  # 计算最大音量
                if amplitude > noise_threshold:
                    high_count += 1
                    if high_count > 2:
                        workstate.set_audio_recording(True)
                        high_count = 0
                        last_audio_time = time.time()  # 重置静音计时
                elif workstate.is_audio_recording and time.time() - last_audio_time > SILENCE_DURATION:  # 静音超过 X 秒
                    print("检测到静音, 停止录音...")
                    workstate.set_audio_recording(False)
                    save_queue_to_wav(speech_file_path)
                    clear_queue()
                    return

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
    sleep_wav_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sleep.wav")
    playsound.playsound(sleep_wav_path)
    while True:
        output_filename = "./temp/output.wav"
        microphone_thread(output_filename)

