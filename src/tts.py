from gradio_client import Client, file

client = Client("http://localhost:9872/")

def to_speech_wav(text, language):

    text_language = "中文"
    if language == "zh":
        text_language = "中文"
    elif language == "en":
        text_language = "英文"

    with open('./resources/ref.txt', 'r', encoding='utf-8') as text_file:
        prompt_text = text_file.read()

    # gradio api
    result = client.predict(
		text=text,
		text_lang=text_language,
		ref_audio_path=file('./resources/split.wav'),
		aux_ref_audio_paths=[],
		prompt_text=prompt_text,
		prompt_lang="中文",
		top_k=15,
		top_p=1,
		temperature=1,
		text_split_method="凑四句一切",
		batch_size=20,
		speed_factor=1,
		ref_text_free=False,
		split_bucket=True,
		fragment_interval=0.3,
		seed=-1,
		keep_random=True,
		parallel_infer=True,
		repetition_penalty=1.35,
		api_name="/inference"
)
    print(result)
    return result[0]

if __name__ == "__main__":
    speech_wav = to_speech_wav('我们大家一起努力，再创辉煌！', 'zh')
    print(speech_wav)
