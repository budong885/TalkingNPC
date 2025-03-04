import requests

url = "http://localhost:9872"
response = requests.get(url)

print(response.text)  # 打印 API 响应
