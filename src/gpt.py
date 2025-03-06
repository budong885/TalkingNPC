
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
                "text": "扮演原神中雷电将军的角色，并用其语气回答用户的问题，同时尽量简短。\n\n# 角色设定与语气\n- 雷电将军的语气：庄重、简练、威严、带有审慎的语感。\n- 回答应符合雷电将军人物设定，避免过于现代化或随意的语言表达。\n- 偏好行动和决策导向的回答，言语中体现对永恒秩序的追求。\n\n# 输出格式\n- 简短的单段回答，最多2到3句话，保持庄重风格。\n\n# 示例\n**用户问题：** 为什么你追求永恒？  \n**雷电将军回答：** 永恒，是抵抗消逝的唯一方式。时代更迭，但心中的雷光永不熄灭。\n\n**用户问题：** 你喜欢什么样的食物？  \n**雷电将军回答：** 武士当心无旁骛，食物不过是维持行动的必需。\n\n**用户问题：** 如何才能强大起来？  \n**雷电将军回答：** 保持专注，磨练心志。在领悟自己的道路前，切勿分心。\n\n# 注意事项\n- 避免使用口语化或者违背角色气质的语言。\n- 可引用游戏中的经典设定或台词，增加角色代入感。\n- 若问题模糊或涉及角色“不可能知晓”的内容，可用雷电将军风格的语言进行委婉回答。"
            }
        ]
    }
] 
    
# Include speech result if speech is enabled  
messages = chat_prompt  
    
# Function to handle multi-turn conversation
def handle_conversation(user_input, queue):

    messages.append({
        "role": "user",
        "content": user_input
    })  
    
    response = ""
    completion = client.chat.completions.create(  
        model=deployment,
        messages=messages,
        max_tokens=800,  
        temperature=0.7,  
        top_p=0.95,  
        frequency_penalty=0,  
        presence_penalty=0,
        stop=None,  
        stream=True
    )
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content or ''
            queue.put(chunk.choices[0].delta.content or '')



    messages.append({
        "role": "assistant",
        "content": response
    })

    print(response)
    
    queue.put(None)

if __name__ == "__main__":
    queue = queue.Queue()
    handle_conversation("你好啊", queue)
    