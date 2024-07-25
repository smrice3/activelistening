import openai
from openai import OpenAI
import streamlit as st
import json

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def create_scenario(industry: str):
    prompt = f"""Create a detailed workplace scenario in the {industry} industry. Include:
    1. The name and function of the company
    2. The name and role of the person the user will be talking to
    3. The reason for the discussion
    Format the response as a JSON object with the following keys: company_name, company_function, person_name, person_role, discussion_reason"""
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content

    # Debug: Print the content to check the response
    st.write("API Response Content:", content)

    # Directly parse JSON from the content
    scenario = json.loads(content)
    return scenario

# Main Streamlit app
if __name__ == "__main__":
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
        st.experimental_rerun()

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
                st.experimental_rerun()

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
