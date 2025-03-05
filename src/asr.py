import azure.cognitiveservices.speech as speechsdk
import time
import config
import os

def recognize_speech_from_wav(wav_file_path):

    # 配置 Azure Speech 识别
    speech_config = speechsdk.SpeechConfig(subscription=config.SPEECH_KEY, region=config.SPEECH_REGION)
    speech_config.speech_recognition_language="zh-CN"
    audio_config = speechsdk.audio.AudioConfig(filename=wav_file_path)

    # 创建语音识别器
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # 运行语音识别
    result = speech_recognizer.recognize_once()

    # 处理结果
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"识别结果: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("未能识别出语音")
        return None
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("语音识别被取消:", cancellation_details.reason)
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("错误详情:", cancellation_details.error_details)
        return None

# 示例调用
if __name__ == "__main__":

    wav_file = "./resources/split.wav"  # 这里换成你的 WAV 文件路径

    if not os.path.exists(wav_file):
        print(f"错误: 文件 '{wav_file}' 不存在！请检查路径。")
    else:
        recognize_speech_from_wav(wav_file)
