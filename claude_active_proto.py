import streamlit as st
from openai import OpenAI
import time
import json
import re
from pathlib import Path
import os

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# List of white-collar industries
INDUSTRIES = ["Finance", "Technology", "Healthcare", "Marketing", "Law"]

def cleanup_audio_files():
    current_dir = Path(__file__).parent
    for file in current_dir.glob("speech_*.mp3"):
        if time.time() - file.stat().st_mtime > 300:  # Delete files older than 5 minutes
            os.remove(file)

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

def text_to_speech(text: str) -> str:
    speech_file_path = Path(__file__).parent / f"speech_{int(time.time())}.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response.stream_to_file(speech_file_path)
    return str(speech_file_path)

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

# Main Streamlit app
cleanup_audio_files()
st.title("Active Listening Prototype")

# Industry selection
if 'industry' not in st.session_state:
    st.session_state.industry = st.selectbox("Select an industry:", INDUSTRIES)

# Create scenario button
if 'scenario' not in st.session_state and st.button("Create Scenario"):
    st.session_state.scenario = create_scenario(st.session_state.industry)
    st.session_state.assistant = create_assistant(st.session_state.industry, st.session_state.scenario)
    st.session_state.thread = create_thread()
    st.success("Scenario created and assistant ready!")
    st.rerun()

if 'scenario' in st.session_state:
    scenario = st.session_state.scenario
    st.write(f"""You work for {scenario['company_name']}, {scenario['company_function']}. 
    You are in a meeting with {scenario['person_name']}, {scenario['person_role']}, 
    to discuss {scenario['discussion_reason']}.""")

    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = True
        
        # Initiate the conversation with the assistant speaking first
        run = run_assistant(st.session_state.thread.id, st.session_state.assistant.id)
        
        messages = get_messages(st.session_state.thread.id)
        for message in reversed(list(messages)):
            if message.role == "assistant":
                response = message.content[0].text.value
                break
        
        # Generate and play audio for the first dialogue
        audio_file_path = text_to_speech(response)
        st.audio(audio_file_path)
        st.write(f"{scenario['person_name']}: {response}")

        # HURIER questions after the first dialogue
        st.write("Please answer the following questions based on the dialogue:")
        for stage in ["Hearing", "Understanding", "Remembering", "Interpreting", "Evaluating", "Responding"]:
            question = ask_hurier_question(stage)
            st.text_input(f"{stage} question: {question}")

        st.session_state.waiting_for_hurier = True

    elif 'waiting_for_hurier' in st.session_state and st.session_state.waiting_for_hurier:
        st.write("Please answer the HURIER questions above before continuing.")
        if st.button("I've answered the questions"):
            st.session_state.waiting_for_hurier = False
            st.rerun()

    else:
        user_input = st.text_input("Your response:")
        if st.button("Send"):
            add_message_to_thread(st.session_state.thread.id, "user", user_input)
            run = run_assistant(st.session_state.thread.id, st.session_state.assistant.id)
            
            messages = get_messages(st.session_state.thread.id)
            for message in reversed(list(messages)):
                if message.role == "assistant":
                    response = message.content[0].text.value
                    break
            
            audio_file_path = text_to_speech(response)
            st.audio(audio_file_path)
            st.write(f"{scenario['person_name']}: {response}")

            # HURIER questions after each dialogue
            st.write("Please answer the following questions based on the dialogue:")
            for stage in ["Hearing", "Understanding", "Remembering", "Interpreting", "Evaluating", "Responding"]:
                question = ask_hurier_question(stage)
                st.text_input(f"{stage} question: {question}")

            st.session_state.waiting_for_hurier = True

    if st.button("View Conversation History"):
        messages = get_messages(st.session_state.thread.id)
        for message in reversed(list(messages)):
            if message.role == "user":
                st.write(f"You: {message.content[0].text.value}")
            else:
                st.write(f"{scenario['person_name']}: {message.content[0].text.value}")
