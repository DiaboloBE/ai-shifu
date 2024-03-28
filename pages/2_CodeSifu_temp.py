import json
import logging
import random

from streamlit_chatbox import *
from langchain_openai import ChatOpenAI

from tools.utils import *
# from prompt import trial, agent
from script import *


# ========== 基础初始化工作 ==========
# 日志级别设置
logging.basicConfig(level=logging.DEBUG)  # 如需要更细致的观察run状态时可以将 `level` 的值改为 `logging.DEBUG`

chat_box = ChatBox(
    assistant_avatar=ICON_SIFU,
)


# llm = ChatOpenAI(model='gpt-4', organization='org-fC5Q2f4MQIEaTOa3k8vTQu6G')

# ========== Streamlit 初始化 ==========
# 设置页面标题和图标
st.set_page_config(
    page_title="CodeSifu",
    page_icon="🧙‍♂️",  # 👨‍🏫
)

'# Code Sifu ⌨️🧙‍♂️⌨️'  # 📚
st.caption('📚 你的专属AI编程私教')


# 初始化进展ID
if 'progress' not in st.session_state:
    st.session_state['progress'] = 0
    
if 'script_has_output' not in st.session_state:
    st.session_state['script_has_output'] = set()

# 初始化侧边栏
with st.sidebar:
    st.subheader('CodeSifu Configuration')
    st.write(f'当前进度：{st.session_state["progress"]}')


chat_box.init_session()
chat_box.output_messages()


# 根据剧本的进度，展示不同的对话
# 根据当前进度ID，获取对应的剧本
script = SCRIPT_LIST[st.session_state['progress']]
logging.debug(f'当前剧本：\n{script}')

if script['type'] == Type.FIXED:
    # 先输出内容
    if script['format'] == Format.MARKDOWN and script['id'] not in st.session_state['script_has_output']:
        full_result = simulate_streaming(chat_box, script['template'], script['template_vars'])
        logging.debug(f'scrip id: {script["id"]}, 输出固定剧本：{full_result}')
        # 标记该进展ID的fixed内容已输出过
        st.session_state['script_has_output'].add(script['id'])  
    elif 1:
        pass  # TODO: 其他格式的固定剧本（代码块、图片、视频、音频等）
    
    # 再根据是否需要输入，展示输入框
    if script['show_input']:
        if user_input := st.chat_input(script['input_placeholder']):
            chat_box.user_say(user_input)
            
            full_result = streaming_from_template(chat_box, script['check_input'], {'input': user_input},
                                                  input_done_with=script['input_done_with'],
                                                  parse_keys=script['parse_keys'])
            logging.debug(f'scrip id: {script["id"]}, chat result: {full_result}')
            
            if full_result.startswith(script['input_done_with']):
                if script['input_for'] == InputFor.SAVE_PROFILE:
                    st.session_state[script['save_key']] = user_input
                    logging.debug(f'保存用户输入：{script["save_key"]} = {user_input}')
                
                st.session_state['progress'] += 1
                st.rerun()
    elif script['show_btn']:
        if st.button(script['btn_label'], type=script['btn_type'], use_container_width=script['use_container_width']):
            if script['btn_for'] == BtnFor.CONTINUE:
                st.session_state['progress'] += 1
                st.rerun()
            elif 1:
                pass  # TODO 其他可能的按钮操作
    else:
        st.session_state['progress'] += 1
        st.rerun()

    
elif script['type'] == Type.PROMPT:
    if script['id'] not in st.session_state['script_has_output']:
        # 拼装 variables 字典
        variables = {}
        for v in script['template_vars']:
            variables[v] = st.session_state[v]
        
        full_result = streaming_from_template(chat_box, script['template'], variables)
        logging.debug(f'scrip id: {script["id"]}, chat result: {full_result}')
        st.session_state['script_has_output'].add(script['id'])
    
    if script['show_input']:
        pass  # TODO 其他可能的输入操作
    elif script['show_btn']:
        if st.button(script['btn_label'], type=script['btn_type'], use_container_width=script['use_container_width']):
            if script['btn_for'] == BtnFor.CONTINUE:
                st.session_state['progress'] += 1
                st.rerun()
            elif 1:
                pass  # TODO 其他可能的按钮操作
    else:
        st.session_state['progress'] += 1
        st.rerun()
    


