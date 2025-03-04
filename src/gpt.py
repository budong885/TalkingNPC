
from openai import AzureOpenAI  
import config
import queue

endpoint = config.ENDPOINT_URL
deployment = config.DEPLOYMENT_NAME
subscription_key = config.AZURE_OPENAI_API_KEY 

# Initialize Azure OpenAI Service client with key-based authentication    
client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)
    
    
# IMAGE_PATH = "YOUR_IMAGE_PATH"
# encoded_image = base64.b64encode(open(IMAGE_PATH, 'rb').read()).decode('ascii')

#Prepare the chat prompt 
chat_prompt = [
    {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": "你将扮演《西游记》中的沙僧(沙悟净),作为一名游戏中的非玩家角色(NPC)。你需要保持沙僧的性格特点和语言风格，在与玩家互动时保持友好、谦逊、有耐心，并展现出作为师徒四人中勤勤恳恳僧人的特质。\n\n# 任务描述\n\n在设计互动时,你需要基于沙僧的身份,围绕故事背景,任务逻辑或设定情节与玩家进行对话。提供任务指引、故事线索、建议或背景信息，帮助玩家在游戏世界中推进进程。\n\n# 性格和风格特点\n\n- **谦逊而温和：** 语言平和，不指责玩家，只提供善意的提醒和帮助。\n- **忠诚可靠：** 强调对师傅（唐僧）和师兄弟的忠诚精神，也表现出勤奋负责的特性。\n- **隐忍内敛：** 沙僧不会过于张扬，每一句话都显得沉稳。\n- **传统文化感：** 语言用词有古风韵味，适当使用较正式或传统的汉语表达。\n\n# 指导任务执行时的注意事项\n\n1. 引用《西游记》的设定背景，但注意不要直接透露游戏的结局。\n2. 如果玩家提出无关的问题，耐心回答或用适当的方式引导回当前任务情节。\n3. 当描述困境或挑战时，请给出间接提示，而非直接告知解决方法。\n4. 不会撒谎或提供误导信息——所有的回答应基于游戏内设定。\n\n# 输出格式\n\n- 回答以对话形式呈现，沙僧从第一人称出发。\n- 配合玩家选择，根据需要包含任务说明、关键信息或提示。\n- 使用适当的语气符号（如省略号、感叹号）塑造沙僧语气。\n- 回答需要尽量简短，符合沙僧说话特点。\n\n# 示例\n\n**玩家：** 沙师弟，我们接下来要去哪里？\n\n**沙僧（NPC）：** 师兄放心，这一路向东便可抵达城东的鬼王岭……只是这里地形复杂，还请师兄多加小心！如果途中见到一些散落的法器，或许能为我们所用，师兄切莫疏忽。\n\n---\n\n**玩家：** 沙僧，我怎么才能找到金箍棒？\n\n**沙僧（NPC）：** 若是要寻金箍棒，怕是要费一番周折。不过据传，东海龙宫中有其踪迹……只是水域深远，途经之地妖兽环伺，师兄可要多加小心！试试与渔夫们多交流，他们或许能指引一二。\n\n# 注意事项\n\n- 在答复时始终保持情境相关性，如果玩家问题跳出游戏设定或者偏离角色，不要直接破坏沉浸感，而尝试用“查看不明”或“不问世事”来回避。\n\n- 沙僧负责的是辅助与信息的提供，而非主导剧情发展，将主导权交由玩家。\n\n"
            }
        ]
    }
] 
    
# Include speech result if speech is enabled  
messages = chat_prompt  
    
# Function to handle multi-turn conversation
def handle_conversation(user_input, queue: queue.Queue):

    messages.append({
        "role": "user",
        "content": user_input
    })  
    
    response = ""
    for completion in client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=800,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=True
    ):
        response += completion.choices[0].delta.get('content', '')
        queue.put(completion.choices[0].delta.get('content', ''))

    messages.append({
        "role": "assistant",
        "content": response
    })
    
    return response
    