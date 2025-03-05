import queue
import audio
import gpt
import asr
import kws
import tts
import time
from threading import Thread
from playsound import playsound
import re
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")  # 屏蔽所有警告


audio_queue = queue.Queue()

input_path = './temp/'

pre_message = ''

def split_sentences(text):
    """
    根据标点分割句子，并保留最后一句未完成的语句
    """
    # 防小数点被切分 但如果是英语句子且以数字结尾会有句子粘连的问题
    parts = re.split(r'([。！？\!\?]|(?<!\d)\.(?!\d))', text)
    spilts = [parts[i].strip() + parts[i+1] for i in range(0, len(parts) - 1, 2) if parts[i].strip()]
    spilts.append(parts[-1].strip())
    return spilts

def audio_player():
    '''
    顺序播放队列中的音频
    '''
    while True:
        task = audio_queue.get()
        # None 表示结束信号
        if task is None:
            audio_queue.queue.clear()
            break

        try:
            playsound(task)
            # 让每句话之间有间隔
            time.sleep(0.5)
        except Exception as e:
            print(f'无法播放: {e}')

while True:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    input_speech = input_path + timestamp + '.wav'

    audio.microphone_thread(input_speech)
    try:
        # 语音识别
        input_text = asr.recognize_speech_from_wav(input_speech)
        print('you: ' + input_text)
    except Exception as e:
        print(f'无法识别语音: {e}')
        continue
    #print("please input:")
    #input_text = input()

    # 开启后台音频播放线程
    player_thread = Thread(target=audio_player)
    player_thread.start()

    # 调用大模型对话
    message_queue = queue.Queue()
    chat_thread = Thread(target=gpt.handle_conversation, args=(input_text, message_queue))
    chat_thread.start()
    sentence_buffer = ''
    print('pc: ', end='')
    while True:
        content = message_queue.get()
        if content == None:
            print("break")
            break
        print(content, end='')
        sentence_buffer += content

        # 检测并处理完整句子
        # 不要一次性整段做TTS 会很慢 发现一句就生成一句
        # sentences = split_sentences(sentence_buffer)
        # if sentences:
        #     for sentence in sentences[:-1]:
        #         if sentence:
        #             print(sentence)
        #             speech_file = tts.to_speech_wav(sentence, "zh")
        #             audio_queue.put(speech_file)
        #     # 保留未完成的句子
        #     sentence_buffer = sentences[-1]

    # 处理剩余缓冲区内容
    rest = sentence_buffer.strip()
    if rest:
        print(rest)
        speech_file = tts.to_speech_wav(rest, "zh")
        audio_queue.put(speech_file)
        pre_message += rest
    
    # 等待对话结束
    chat_thread.join()

    # 等待音频播放结束
    audio_queue.put(None)
    player_thread.join()
    print()
    print()

