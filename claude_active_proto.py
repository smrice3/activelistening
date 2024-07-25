import streamlit as st
from openai import OpenAI
from pathlib import Path
import time

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# List of white-collar industries
INDUSTRIES = ["Finance", "Technology", "Healthcare", "Marketing", "Law"]

def create_assistant(industry: str):
    assistant = client.beta.assistants.create(
        name=f"{industry} Workplace Assistant",
        instructions=f"You are a helpful assistant in the {industry} industry. You engage in workplace scenarios and respond accordingly.",
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

    if 'assistant' not in st.session_state:
        industry = st.selectbox("Select an industry:", INDUSTRIES)
        if st.button("Create Assistant"):
            st.session_state.assistant = create_assistant(industry)
            st.session_state.thread = create_thread()
            st.success("Assistant created and conversation started!")

    if 'assistant' in st.session_state:
        user_input = st.text_input("Your message:")
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

            with st.expander("Conversation"):
                for message in reversed(list(messages)):
                    st.write(f"{message.role.capitalize()}: {message.content[0].text.value}")

            for stage in ["Hearing", "Understanding", "Remembering", "Interpreting", "Evaluating", "Responding"]:
                question = ask_hurier_question(stage)
                st.write(f"{stage} question: {question}")
                st.text_input(f"Your answer for {stage}:")

if __name__ == "__main__":
    main()
