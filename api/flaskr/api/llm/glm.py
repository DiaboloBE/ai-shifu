from typing import Generator
import requests
from flask import Flask
import jwt
import time 
import json
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
API_KEY = "40c6f6bbdcd16b6458b1f6c3e72fea68.hkUiwx5S0GR9Jueu"


# # MINIMAX_URL=""
# MINIMAX_KEY="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLokZvkupHpo54iLCJVc2VyTmFtZSI6IuiRm-S6kemjniIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzI5MzM5MjE0NTM5MDAyNDU0IiwiUGhvbmUiOiIxODYxMjMxMjMyNiIsIkdyb3VwSUQiOiIxNzI5MzM5MjE0NTM0ODA4MDg1IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDMtMjYgMTU6Mzc6MDIiLCJpc3MiOiJtaW5pbWF4In0.NsMbB91gDqdtb8M688qn5JaFdQj3Ac2qtCboj5hQHtO7tmFnGNaHIVFM9Q3RnEO-eaSPdixWoEUcjAUO_rKEbAaW9XLD5Dnfr3eEzEgu4T2BJTHPLfxwkJMrQAoWQR2x0xKdoVG3E5ucUGafvCbmPFQeacztMeW-JzikAkA1RoJCq1SfKvfuU-BtRCDfDZ_hT6Jb3ibTrwTPAOBOTB8jUhwoWf_DcmU3_lumGarv0dqMYBOAFGGwtuogTqr_QelnmlBbPHOjozNrx4-IiKWnnK7GNdBdJRwZN2txSxAFvyb4tNAFOzfuqUIyb1rqmST5TGb7Jz0JqhUFdzB1-0NKTg"
# MINIMAX_URL="https://api.minimax.chat/v1/text/chatcompletion_v2"


URLS = {
    "glm-4-0520":"https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "glm-4":"https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "glm-4-air":"https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "glm-4-airx":"https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "glm-4-flash":"https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "glm-4v":"https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "glm-3-turbo":"https://open.bigmodel.cn/api/paas/v4/chat/completions"
}
class ChatResponse:
    def __init__(self, id,created,model,choices,usage=None,object=None):
        self.id:str = id
        self.created: int = created
        self.model:str = model
        self.choices:list[Choice] = [Choice(**choice) for choice in choices] 
        self.usage:Usage = Usage(**usage) if usage else None
        self.object:str = object if object else None

class FunctionCall:
    def __init__(self, name=None,arguments=None):
        self.name:str = name
        self.arguments:str = arguments
class ToolCall:
    def __init__(self, id,type,index=None,function=None):
        self.id:str = id
        self.type:str = type
        self.index:int = index if index else None
        self.function:FunctionCall = FunctionCall(**function) if function else None
class Choice:
    def __init__(self,index,delta,finish_reason=None):
        self.index:int = index
        self.delta:Delta = Delta(**delta)
        self.finish_reason:str = finish_reason if finish_reason else None
      
class Delta:
    def __init__(self,role,content=None,tool_calls=None):
        self.role = role
        self.content = content
        self.tool_calls:list[ToolCall] = [ToolCall(**tool_call) for tool_call in tool_calls] if tool_calls else None

class Usage:
    def __init__(self,prompt_tokens,completion_tokens,total_tokens):
        self.prompt_tokens:int = prompt_tokens
        self.completion_tokens:int = completion_tokens
        self.total_tokens:int = total_tokens
    def __str__(self):
        return f"prompt_tokens:{self.prompt_tokens},completion_tokens:{self.completion_tokens},total_tokens:{self.total_tokens}"

def get_token(app:Flask)->str:
    try:
        id, secret = API_KEY.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)
 
    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) +  10 * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }
    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )
def get_chat_response(app:Flask, msg:str)->Generator[ChatResponse,None,None]:
    data = {
        "messages": [{"content": msg,"role": "user"}],
    }
    for res in invoke_glm(app, **data):
        yield res


def invoke_glm(app:Flask,model,message,system=None,**args)->Generator[ChatResponse,None,None]:

    app.logger.info("input data: model:{},message:{},system:{}".format(model,message,system))

    messages = []

    if system:
        message.append({"content":system,"role":"system"})
    messages.append({"content":message,"role":"user"})
    data = {
        "model": model,
        "messages": messages,
        "stream": True
    }

    data = {**data,**args}
    
    headers = {"Authorization": "Bearer "+API_KEY}
    response = requests.post(URLS[model], json=data, headers=headers,stream=True)
    app.logger.info('request data: {}'.format(json.dumps(data)))
    for res in response.iter_lines():
        res = res.decode('utf-8')
        app.logger.info('zhipu response data: {}'.format(res))
        if res.startswith('data:'):
            # 提取 'data:' 后面的内容
            json_data = res[5:].strip()
            # 尝试解析 JSON 数据
            if(json_data.replace(' ','') == '[DONE]'):
                return
            parsed_data = json.loads(json_data)
            yield ChatResponse(**parsed_data)


def get_zhipu_models(app:Flask)->list[str]:
    return list(URLS.keys())