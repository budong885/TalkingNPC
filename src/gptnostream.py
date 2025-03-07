from openai import AzureOpenAI  
import config
import queue
import json
from datetime import datetime, timedelta
import os
import requests

endpoint = config.ENDPOINT_URL
deployment = config.DEPLOYMENT_NAME
subscription_key = config.AZURE_OPENAI_API_KEY 

# Initialize Azure OpenAI Service client with key-based authentication    
client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)
# Define the function to query weather
def query_weather(location):
    """Query weather information using a weather API"""
    try:
        url = f"https://wttr.in/{location}?format=j1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data["current_condition"][0]
        return f"{location}的当前温度为{current['temp_C']}度。"
    except Exception as e:
        return {"error": str(e)}
    
# Define available functions
available_functions = {
    "schedule_meeting": {
        "name": "schedule_meeting",
        "description": "安排一个会议，参数可为空",
        "parameters": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "会议主题，例如 '团队会议'"
                },
                "start_time": {
                    "type": "string",
                    "description": "开始时间，可为空"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "持续时间，可为空"
                },
                "attendees": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "参与者姓名，由提问者给出，需要判断"
                },
            },
            "required": ["attendees"]
        }
    },
    "query_weather": {
        "name": "query_weather",
        "description": "查询指定地点的天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "地点名称"
                }
            },
            "required": ["location"]
        }
    }
}

def schedule_meeting(subject = "special meeting", start_time = "", duration_minutes = 30, attendees=["handong"]):
    """Schedule a meeting using Microsoft Graph API"""
    try:
        # Find attendees' email addresses using Microsoft Graph API
        try:
            start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
            if start_time < datetime.utcnow():
                start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            print(f"Failed to parse start time: {str(e)}")
            start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        attendee_emails = []
        if attendees:
            for attendee in attendees:
                search_url = f"https://graph.microsoft.com/v1.0/me/people/?$search={attendee}&$select=scoredEmailAddresses&$top=1"
                search_headers = {
                    "Authorization": f"Bearer {config.MS_GRAPH_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                search_response = requests.get(search_url, headers=search_headers)
                print(f"Search Response: {search_response.json()}")
                try:

                    if search_response.status_code == 200:
                        search_results = search_response.json().get('value', [])
                        if search_results and len(search_results) > 0:
                            user = search_results[0]
                            if "scoredEmailAddresses" in user and len(user["scoredEmailAddresses"]) > 0:
                                email = user["scoredEmailAddresses"][0]["address"]
                                attendee_emails.append(email)
                                print(f"User's Email: {email}")
                            else:
                                print("No email found.")
                        else:
                            print(f"Failed to find email for attendee: {attendee}")
                            return f"Failed to find email for attendee: {attendee}"
                    else:
                        print(f"Failed to search for attendee: {attendee}, Error: {search_response.json().get('error', {}).get('message', 'Unknown error')}")
                        return f"Failed to search for attendee: {attendee}, Error: {search_response.json().get('error', {}).get('message', 'Unknown error')}"
                except Exception as e:
                    print(f"Failed to search for attendee: {attendee}, Error: {str(e)}")

        attendees = attendee_emails
        print(f"Attendees: {attendees}")
        # Set up the API endpoint and headers
        url = f"https://graph.microsoft.com/v1.0/me/events"
        headers = {
            "Authorization": f"Bearer {config.MS_GRAPH_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Calculate end time
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Create the event payload
        event_payload = {
            "subject": subject,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "UTC"
            },
            "attendees": [{"emailAddress": {"address": attendee, "name": attendee}, "type": "required"} for attendee in attendees] if attendees else []
        }
        
        # Make the API request to create the event
        response = requests.post(url, headers=headers, json=event_payload)
        
        if response.status_code == 201:
            return f"会议已经成功预定！"
        else:
            return f"Failed to schedule3 meeting: {response.json().get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        return f"Failed to schedule meeting: {str(e)}"

# Function to handle function calls
def handle_function_call(function_name, arguments):
    if function_name == "schedule_meeting":
        if arguments:
            args = json.loads(arguments)
            print(f"Function Arguments: {args}")
            return schedule_meeting(
            args.get("subject", "special meeting"),
            args.get("start_time", datetime.now().strftime("%Y-%m-%d %H:%M")),
            args.get("duration_minutes", 30),
            args.get("attendees", ["ares"]),
            )
        else:
            return schedule_meeting()
    elif function_name == "query_weather":
        if arguments:
            args = json.loads(arguments)
            print(f"Function Arguments: {args}")
            return query_weather(args.get("location", "Beijing"))
        else:
            return query_weather("Beijing")
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

    try:
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
        stream=False
        )
        final_tool_calls = {}

        if completion.choices and completion.choices[0].message:
            if completion.choices[0].message.content:
                response += completion.choices[0].message.content or ''
                queue.put(completion.choices[0].message.content or '')
            if completion.choices[0].message.function_call:
                function_call = completion.choices[0].message.function_call
                if function_call.name:
                    if function_call.name not in final_tool_calls:
                        final_tool_calls[function_call.name] = function_call
                        final_tool_calls[function_call.name].arguments = function_call.arguments

        if len(final_tool_calls) > 0:
            for tool_call in final_tool_calls.values():
                print(f"Tool Call: {tool_call.arguments}")
                response += handle_function_call(tool_call.name, tool_call.arguments)
                queue.put(response)

        messages.append({
            "role": "assistant",
            "content": response
        })
    except Exception as e:
        print(f"Failed to handle conversation: {str(e)}")
        response = "Failed to handle conversation."
    
    messages.append({
        "role": "assistant",
        "content": response
    })
    queue.put(None)

if __name__ == "__main__":
    queue = queue.Queue()
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        handle_conversation(user_input, queue)
        while True:
            response = queue.get()
            if response is None:
                break
            print(response, end='')
        print()
    