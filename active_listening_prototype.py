import streamlit as st
from openai import OpenAI
from pathlib import Path
import os

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def generate_scenario(industry):
    prompt = f"Create a detailed role-playing scenario for a project team meeting in the {industry} industry. Provide background information about the project and list the team members and their roles."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    scenario = response.choices[0].message.content
    return scenario

def generate_conversation(context):
    prompt = f"Using {context}, create a scenario and character. You will play this character in a conversation."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a bot focused on generating a fluid, human-like conversation between yourself and a human user. You will be helping a learner focus on building their listening skills. You are also an expert in creating a scenario to frame your conversation."},
            {"role": "user", "content": prompt}
        ]
    )
    conversation = response.choices[0].message.content
    return conversation

# Function to generate audio from text
def generate_audio(text, voice):
    speech_file_path = Path(__file__).parent / f"{voice}_speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    response.stream_to_file(speech_file_path)
    return speech_file_path

# Function to provide feedback
def provide_feedback(response):
    # Placeholder for detailed feedback logic
    feedback = f"Feedback based on your response: {response}"
    return feedback

if 'scenario' in st.session_state:
    st.header("Scenario Background")
    st.write(st.session_state.scenario)

    if 'conversation' in st.session_state:
        if st.session_state.current_step < len(st.session_state.conversation):
            dialogue = st.session_state.conversation[st.session_state.current_step]
            speaker, text = dialogue.split(": ", 1)
            voice = "onyx" if speaker == "Bob" else "alloy"  # Example logic for voice selection

            st.subheader(f"Scene {st.session_state.current_step + 1}: {speaker} speaking")

            # Generate and play audio
            audio_path = generate_audio(text, voice)
            audio_file = open(audio_path, "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")

            # Reveal and close text functionality
            if st.button(f"Reveal text for Scene {st.session_state.current_step + 1}"):
                st.write(text)

            # User input for response
            user_input = st.text_input(f"Your response to {speaker}:", key=f"input_{st.session_state.current_step}")

            if user_input:
                # Provide feedback
                feedback = provide_feedback(user_input)
                st.write(feedback)
                if st.button("Next Scene"):
                    st.session_state.current_step += 1

        else:
            st.write("You have completed the scenario. Well done!")

            # Follow-up questions
            st.header("Follow-Up Questions")
            follow_up_questions = [
                "What was the main issue discussed in the conversation?",
                "Can you summarize the feedback provided by the team members?",
                "How did the context of the project influence the conversation?",
                "What were the key points raised by each team member?",
                "What actions were decided upon at the end of the meeting?"
            ]

            for i, question in enumerate(follow_up_questions):
                user_answer = st.text_input(f"Follow-Up Question {i + 1}: {question}", key=f"follow_up_{i}")
                if user_answer:
                    follow_up_feedback = provide_feedback(user_answer)
                    st.write(follow_up_feedback)
