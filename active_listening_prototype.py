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
    return "Detailed feedback based on the response."

# Function to generate team members and dialogues based on industry
def generate_scenario(industry):
    prompt = f"Create a detailed role-playing scenario for a project team meeting in the {industry} industry. List team members and their roles, and provide dialogue for a meeting discussing performance issues."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    scenario = completion.choices[0].message.content
    return scenario

# Streamlit app layout
st.title("Active Listening Practice App")

# Industry selection dropdown
industries = ["Finance", "Healthcare", "Technology", "Education", "Consulting"]
selected_industry = st.selectbox("Select your industry:", industries)

if selected_industry:
    st.write(f"You have selected: {selected_industry} industry")

    if st.button("Generate Scenario"):
        scenario = generate_scenario(selected_industry)
        st.session_state.scenario = scenario.split("\n\n")  # Split the scenario into parts for each dialogue
        st.session_state.current_step = 0

if 'scenario' in st.session_state:
    current_step = st.session_state.current_step
    if current_step < len(st.session_state.scenario):
        dialogue = st.session_state.scenario[current_step]
        speaker, text = dialogue.split(": ", 1)
        voice = "onyx" if speaker == "Bob" else "alloy"  # Example logic for voice selection

        st.subheader(f"Scene {current_step + 1}: {speaker} speaking")

        # Generate and play audio
        audio_path = generate_audio(text, voice)
        audio_file = open(audio_path, "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")

        # Reveal and close text functionality
        if st.button(f"Reveal text for Scene {current_step + 1}"):
            st.write(text)

        # User input for response
        user_input = st.text_input(f"Your response to {speaker}:", key=f"input_{current_step}")

        if user_input:
            # Provide feedback
            feedback = provide_feedback(user_input)
            st.write(feedback)
            if st.button("Next Scene"):
                st.session_state.current_step += 1

    else:
        st.write("You have completed the scenario. Well done!")

# Additional code to handle the full dialogue flow, feedback, and follow-up questions...
