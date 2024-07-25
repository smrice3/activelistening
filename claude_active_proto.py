import streamlit as st
from openai import OpenAI
from pathlib import Path
import time
import json
import re

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# List of white-collar industries
INDUSTRIES = ["Finance", "Technology", "Healthcare", "Marketing", "Law"]

import re

def create_scenario(industry: str):
    prompt = f"""Create a detailed workplace scenario in the {industry} industry. Include:
    1. The name and function of the company
    2. The name and role of the person the user will be talking to
    3. The reason for the discussion
    Format the response as JSON with keys: company_name, company_function, person_name, person_role, discussion_reason"""
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates workplace scenarios. Always respond in valid JSON format."},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content
    
    # Try to extract JSON from the content
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # If JSON parsing fails, extract information manually
    scenario = {}
    patterns = {
        'company_name': r'company_name"?\s*:\s*"?([^",\}]+)',
        'company_function': r'company_function"?\s*:\s*"?([^",\}]+)',
        'person_name': r'person_name"?\s*:\s*"?([^",\}]+)',
        'person_role': r'person_role"?\s*:\s*"?([^",\}]+)',
        'discussion_reason': r'discussion_reason"?\s*:\s*"?([^",\}]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            scenario[key] = match.group(1).strip()
        else:
            scenario[key] = f"[{key.replace('_', ' ').title()}]"
    
    return scenario

def create_assistant(industry: str, scenario: dict):
    assistant = client.beta.assistants.create(
        name=f"{scenario['person_name']} - {scenario['person_role']}",
        instructions=f"""You are {scenario['person_name']}, the {scenario['person_role']} at {scenario['company_name']}. 
        You're in a meeting to discuss {scenario['discussion_reason']}. 
        Engage in a realistic conversation as this character, maintaining their perspective and role.""",
        model="gpt-4-turbo-preview",
        tools=[{"type": "code_interpreter"}]
    )
    return assistant

def create_thread():
    return client.beta.threads.create()

def add_message_to_thread(thread_id, role, content):
    return client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )

def run_assistant(thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    while run.status not in ["completed", "failed"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    return run

def get_messages(thread_id):
    return client.beta.threads.messages.list(thread_id=thread_id)

def text_to_speech(text: str) -> bytes:
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    
    speech_file_path = Path("temp_speech.mp3")
    response.stream_to_file(speech_file_path)
    
    with open(speech_file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    
    speech_file_path.unlink()
    
    return audio_bytes

def ask_hurier_question(stage: str) -> str:
    questions = {
        "Hearing": "What was the main point of the message?",
        "Understanding": "Can you summarize the key ideas presented?",
        "Remembering": "What specific details do you recall from the conversation?",
        "Interpreting": "How would you interpret the speaker's tone and intent?",
        "Evaluating": "What is your assessment of the information provided?",
        "Responding": "How would you respond to this message?"
    }
    return questions.get(stage, "Invalid stage")

def main():
    st.title("Active Listening Prototype")

    if 'scenario' not in st.session_state:
        industry = st.selectbox("Select an industry:", INDUSTRIES)
        if st.button("Create Scenario"):
            st.session_state.scenario = create_scenario(industry)
            st.session_state.assistant = create_assistant(industry, st.session_state.scenario)
            st.session_state.thread = create_thread()
            st.success("Scenario created and assistant ready!")

    if 'scenario' in st.session_state:
        scenario = st.session_state.scenario
        st.write(f"""You work for {scenario['company_name']}, {scenario['company_function']}. 
        You are in a meeting with {scenario['person_name']}, {scenario['person_role']}, 
        to discuss {scenario['discussion_reason']}.""")

        if 'conversation_started' not in st.session_state:
            st.session_state.conversation_started = True
            add_message_to_thread(st.session_state.thread.id, "user", "Hello, let's start our meeting.")
            run = run_assistant(st.session_state.thread.id, st.session_state.assistant.id)
            
            messages = get_messages(st.session_state.thread.id)
            for message in reversed(list(messages)):
                if message.role == "assistant":
                    response = message.content[0].text.value
                    break
            
            audio_data = text_to_speech(response)
            st.audio(audio_data, format="audio/mp3")
            st.write(f"{scenario['person_name']}: {response}")

            for stage in ["Hearing", "Understanding", "Remembering", "Interpreting", "Evaluating", "Responding"]:
                question = ask_hurier_question(stage)
                st.text_input(f"{stage} question: {question}")

        user_input = st.text_input("Your response:")
        if st.button("Send"):
            add_message_to_thread(st.session_state.thread.id, "user", user_input)
            run = run_assistant(st.session_state.thread.id, st.session_state.assistant.id)
            
            messages = get_messages(st.session_state.thread.id)
            for message in reversed(list(messages)):
                if message.role == "assistant":
                    response = message.content[0].text.value
                    break
            
            audio_data = text_to_speech(response)
            st.audio(audio_data, format="audio/mp3")
            st.write(f"{scenario['person_name']}: {response}")

            for stage in ["Hearing", "Understanding", "Remembering", "Interpreting", "Evaluating", "Responding"]:
                question = ask_hurier_question(stage)
                st.text_input(f"{stage} question: {question}")

        if st.button("View Conversation History"):
            messages = get_messages(st.session_state.thread.id)
            for message in reversed(list(messages)):
                if message.role == "user":
                    st.write(f"You: {message.content[0].text.value}")
                else:
                    st.write(f"{scenario['person_name']}: {message.content[0].text.value}")

if __name__ == "__main__":
    main()
