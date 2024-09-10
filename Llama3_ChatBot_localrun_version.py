import streamlit as st
import os
import requests
import json
import speech_recognition as sr  # 新增的語音辨識庫
from Llama3_Backend_API_Url import SFT_LLAMA3_8B_MODEL_PATH, SFT_LLAMA2_7B_MODEL_PATH, META_LLAMA2_7B_MODEL_PATH

# Load the entire model on the GPU 0 or Auto #
device_map = "auto" #{"": 0}

global chat_model, tokenizer, voice_prompt

temperature = 0.1
top_p = 0.9
max_length = 200
voice_prompt = " "

# App title
st.set_page_config(page_title="🦙💬 Llama Chatbot-靈動智伴")


#system_prompt = st.sidebar.text_input('System prompt', "你是一個有幫助的問答機器人，請用繁體中文回覆。")
system_prompt = "你是一個具有勞工知識及很有智慧與幫助的問答機器人，請用繁體中文回答。"

def response_api(prompt, url, system_prompt):
    # payload = json.dumps({
    #   "messages": [
    #     {
    #       "role": "system",
    #       "content": system_prompt
    #     },
    #     {
    #       "role": "user",
    #       "content": prompt
    #     }
    #   ]
    # })

    payload = json.dumps({
      "messages": system_prompt + prompt,
      "temperature": temperature,
      "maxlength": max_length
    })
    headers = {
       'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print("JSON:", response.json())  # Steven test 2023/10/14 #

    #return response.json()["choices"][0]["message"]['content']
    return response.json()

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

st.header("<My Great ChatBot 🤗>")

# Replicate Credentials
with st.sidebar:
    st.title('🦙🦙💬 靈動智伴\n(Llama 3.1 Chatbot)')

    st.subheader('Models and parameters')
    selected_model = st.sidebar.selectbox('Choose a Llama model', ['SFT_Llama3-8B', 'SFT_Llama2-7B', 'Meta_Llama2-7B'], key='selected_model')   
    if selected_model == 'SFT_Llama3-8B':
        api_url = SFT_LLAMA3_8B_MODEL_PATH  # [Backend URL] Change here... #
    elif selected_model == 'SFT_Llama2-7B':
        api_url = SFT_LLAMA2_7B_MODEL_PATH  # [Backend URL] Change here... #
    elif selected_model == 'Meta_Llama2-7B':
        api_url = META_LLAMA2_7B_MODEL_PATH  # [Backend URL] Change here... #

    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    temperature = st.sidebar.slider('溫度係數(temperature)', min_value=0.0, max_value=3.0, value=0.3, step=0.1)
    top_p = st.sidebar.slider('核取樣(top_p)', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('回覆長度(max_length)', min_value=128, max_value=512, value=300, step=8)
    st.sidebar.button('清除對話記錄\n(Clear Chat History)', on_click=clear_chat_history)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')
    

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "哈囉！今天又是一個學習AI的好日子。"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
prompt = st.chat_input("請輸入訊息...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Add a button for speech recognition
if st.button("語音辨識輸入"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("請開始說話...")
        with st.spinner("Listening ..."):
            audio = recognizer.listen(source, timeout=2)

    try:
        # 使用Google Web語音辨識服務進行語音轉文字
        recognized_text = recognizer.recognize_google(audio, language="zh-TW")
        # 將語音辨識的內容設定為文本輸入框的內容
        #st.session_state.messages.append({"role": "user", "content": recognized_text})
        #with st.chat_message("user"):
        #    st.write(recognized_text)
        voice_prompt = recognized_text
    except sr.WaitTimeoutError:
        st.write("語音辨識超時，請再試一次。")
    except sr.UnknownValueError:
        st.write("無法識別語音。")
    except sr.RequestError as e:
        st.write("語音辨識服務錯誤： {0}".format(e))

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = response_api(prompt, api_url, system_prompt)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)

# Voice-Text auto-filled solution - Steven 2023/10/13 #
#default_chat_input_value = "Default Value"
default_chat_input_value = voice_prompt
js = f"""
    <script>
        function insertText(dummy_var_to_force_repeat_execution) {{
            var chatInput = parent.document.querySelector('textarea[data-testid="stChatInput"]');
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            nativeInputValueSetter.call(chatInput, "{default_chat_input_value}");
            var event = new Event('input', {{ bubbles: true}});
            chatInput.dispatchEvent(event);
        }}
        insertText({len(st.session_state.messages)});
    </script>
    """
st.components.v1.html(js)    
