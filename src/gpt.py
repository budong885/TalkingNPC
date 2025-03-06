from openai import AzureOpenAI  
import config
import queue
import json
from datetime import datetime, timedelta
import win32com.client
import os

endpoint = config.ENDPOINT_URL
deployment = config.DEPLOYMENT_NAME
subscription_key = config.AZURE_OPENAI_API_KEY 

# Initialize Azure OpenAI Service client with key-based authentication    
client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)

# Define available functions
available_functions = {
    "get_weather": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature to use"
                }
            },
            "required": ["location"]
        }
    },
    "schedule_meeting": {
        "name": "schedule_meeting",
        "description": "Schedule a meeting in Outlook calendar",
        "parameters": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "The subject/title of the meeting"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time in format 'YYYY-MM-DD HH:MM'"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration of the meeting in minutes"
                },
                "attendees": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of attendee email addresses"
                },
                "body": {
                    "type": "string",
                    "description": "Meeting description/body"
                }
            },
            "required": ["subject", "start_time", "duration_minutes"]
        }
    }
}

def get_weather(location, unit="celsius"):
    """Mock function to get weather"""
    return f"The weather in {location} is currently 22°{unit[0].upper()}"

def schedule_meeting(subject, start_time, duration_minutes, attendees=None, body=""):
    """Schedule a meeting in Outlook calendar"""
    try:
        # Create Outlook application object
        outlook = win32com.client.Dispatch("Outlook.Application")
        
        # Create a new appointment
        appointment = outlook.CreateItem(1)  # 1 represents an appointment
        
        # Set meeting properties
        appointment.Subject = subject
        appointment.Start = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        appointment.Duration = duration_minutes
        appointment.Body = body
        
        # Add attendees if provided
        if attendees:
            for attendee in attendees:
                appointment.Recipients.Add(attendee)
        
        # Save and send
        appointment.Save()
        appointment.Send()
        
        return f"Meeting '{subject}' has been scheduled successfully for {start_time}"
    except Exception as e:
        return f"Failed to schedule meeting: {str(e)}"

# Function to handle function calls
def handle_function_call(function_name, arguments):
    if function_name == "get_weather":
        args = json.loads(arguments)
        return get_weather(args.get("location"), args.get("unit", "celsius"))
    elif function_name == "schedule_meeting":
        args = json.loads(arguments)
        return schedule_meeting(
            args.get("subject"),
            args.get("start_time"),
            args.get("duration_minutes"),
            args.get("attendees"),
            args.get("body", "")
        )
    return "Function not found"

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
    while True:
        completion = client.chat.completions.create(  
            model=deployment,
            messages=messages,
            functions=list(available_functions.values()),
            function_call="auto",
            max_tokens=800,  
            temperature=0.7,  
            top_p=0.95,  
            frequency_penalty=0,  
            presence_penalty=0,
            stop=None,  
            stream=True
        )
        
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta:
                if chunk.choices[0].delta.content:
                    response += chunk.choices[0].delta.content or ''
                    queue.put(chunk.choices[0].delta.content or '')
                elif chunk.choices[0].delta.function_call:
                    function_call = chunk.choices[0].delta.function_call
                    if function_call.name:
                        function_name = function_call.name
                        function_args = function_call.arguments
                        function_response = handle_function_call(function_name, function_args)
                        messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": function_response
                        })
                        continue

        if not any(chunk.choices and chunk.choices[0].delta.function_call for chunk in completion):
            break

    messages.append({
        "role": "assistant",
        "content": response
    })

    print(response)
    queue.put(None)

if __name__ == "__main__":
    queue = queue.Queue()
    handle_conversation("你好啊", queue)
    