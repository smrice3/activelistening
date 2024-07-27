import streamlit as st
from openai import OpenAI
import json
import random

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Constants
HURIER_ELEMENTS = ["Hear", "Understand", "Remember", "Interpret", "Evaluate", "Respond"]
HURIER_QUESTIONS = {
    "Hear": "What did you hear in the message?",
    "Understand": "What do you understand from this message?",
    "Remember": "What key points do you remember from the message?",
    "Interpret": "How do you interpret the meaning behind this message?",
    "Evaluate": "How would you evaluate the importance or relevance of this message?",
    "Respond": "How would you respond to this message?"
}

def create_scenario(industry):
    prompt = f"""Create a unique and detailed workplace scenario in the {industry} industry. Be creative and include unexpected elements. Include:
    1. The name and function of the company (make this inventive and memorable)
    2. The name and role of the person the user will be talking to (give them an interesting backstory)
    3. The reason for the discussion (make this compelling and slightly unusual)
    Format the response as a JSON object with the following keys: company_name, company_function, person_name, person_role, discussion_reason"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a creative assistant designed to generate unique and engaging scenarios. Output your response as JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        scenario = json.loads(response.choices[0].message.content)
        return scenario
    except Exception as e:
        st.error(f"An error occurred while creating the scenario: {str(e)}")
        return None

def clean_up_scenario(scenario):
    if not scenario:
        return None

    prompt = f"""
    Take the following scenario and make it more readable and engaging for a user:
    
    Company: {scenario['company_name']}
    Company Function: {scenario['company_function']}
    Person: {scenario['person_name']}
    Role: {scenario['person_role']}
    Discussion Reason: {scenario['discussion_reason']}
    
    Create a brief narrative that introduces the scenario in a conversational tone. 
    Then, clearly state who the user will be talking to and why.
    Return the result as a JSON object with two keys: 'context' (the narrative) and 'person' (who they're talking to).
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates engaging scenario descriptions."},
                {"role": "user", "content": prompt}
            ]
        )

        clean_scenario = json.loads(response.choices[0].message.content)
        return clean_scenario
    except Exception as e:
        st.error(f"An error occurred while cleaning up the scenario: {str(e)}")
        return None

def conversation_engine(character, context):
    st.write("Starting conversation engine...")
    try:
        prompt = f"""You are roleplaying as {character} in the following context: {context}. 
        Generate an opening statement to start the conversation as this character would.
        This statement should relate to the scenario and invite a response from the other person.
        Do not introduce yourself or ask how you can assist. Instead, speak as if you're already in the middle of a workplace interaction."""

        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" if gpt-4 is not available
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Start the conversation."}
            ]
        )

        initial_message = response.choices[0].message.content
        st.write("Initial message generated successfully.")

        return {
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "assistant", "content": initial_message}
            ],
            "initial_message": initial_message
        }

    except Exception as e:
        st.error(f"An error occurred in the conversation engine: {str(e)}")
        return None

def continue_conversation(messages, user_message):
    try:
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" if gpt-4 is not available
            messages=messages
        )

        assistant_response = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response, messages

    except Exception as e:
        st.error(f"An error occurred while continuing the conversation: {str(e)}")
        return None, messages

def analyze_response(element, user_response, assistant_message):
    prompt = f"""
    Analyze the learner's response for the '{element}' element of the HURIER model.
    
    Assistant's message: "{assistant_message}"
    Learner's response: "{user_response}"
    
    Evaluate if the learner's response accurately reflects the quality of the '{element}' element.
    Provide constructive feedback that is positive, clear, and concrete.
    
    Return your analysis as a JSON object with two keys:
    1. "Evaluation": Either "passed" or "failed"
    2. "Feedback": Your constructive feedback for the learner
    
    The response should be marked as "passed" if the learner demonstrated a good understanding of the '{element}' element, and "failed" if their response needs improvement.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an expert in active listening and the HURIER model."},
                {"role": "user", "content": prompt}
            ]
        )
        
        feedback = json.loads(response.choices[0].message.content)
        return feedback
    except Exception as e:
        st.error(f"An error occurred while analyzing the response: {str(e)}")
        return {"Evaluation": "failed", "Feedback": "Unable to analyze response due to an error."}

def listening_skill_coach(assistant_message):
    st.subheader("Listening Skill Coach")
    st.write("Let's analyze your listening skills using the HURIER model.")
    
    for element in HURIER_ELEMENTS:
        st.write(f"\n--- {element.upper()} ---")
        st.write(HURIER_QUESTIONS[element])
        
        user_response = st.text_input(f"Your answer for {element}:", key=f"input_{element}")
        
        if st.button(f"Submit {element}", key=f"submit_{element}"):
            feedback = analyze_response(element, user_response, assistant_message)
            st.write(feedback['Feedback'])
            
            if feedback['Evaluation'] == 'failed':
                st.write("Let's try again. Please provide a more detailed answer.")
            else:
                st.write("Great job! Let's move on to the next element.")

def main():
    st.title("Active Listening Skills Trainer")

    # Industry selection
    industry = st.selectbox("Select an industry:", ["Technology", "Healthcare", "Finance", "Education", "Retail"])

    if st.button("Generate Scenario"):
        st.write("Generating scenario...")
        scenario = create_scenario(industry)
        if scenario:
            st.write("Cleaning up scenario...")
            clean_scenario = clean_up_scenario(scenario)
            if clean_scenario:
                st.session_state.clean_scenario = clean_scenario
                st.session_state.conversation = None  # Reset conversation when new scenario is generated
                st.write("Scenario generated successfully!")
            else:
                st.error("Failed to clean up the scenario.")
        else:
            st.error("Failed to create a scenario.")

    if 'clean_scenario' in st.session_state:
        st.subheader("Scenario:")
        st.write(st.session_state.clean_scenario['context'])
        st.write(f"You will be talking to: {st.session_state.clean_scenario['person']}")

        if 'conversation' not in st.session_state:
            st.write("Initializing conversation...")
            with st.spinner('Please wait while the conversation is being initialized...'):
                try:
                    st.session_state.conversation = conversation_engine(
                        st.session_state.clean_scenario['person'], 
                        st.session_state.clean_scenario['context']
                    )
                    if not st.session_state.conversation:
                        st.error("Failed to initialize conversation.")
                except Exception as e:
                    st.error(f"An error occurred while initializing the conversation: {str(e)}")

        if st.session_state.conversation:
            st.subheader("Conversation:")
            st.write("Character:", st.session_state.conversation['initial_message'])

            user_response = st.text_input("Your response:")

            if st.button("Submit Response"):
                st.write("Processing your response...")
                try:
                    assistant_response, st.session_state.conversation['messages'] = continue_conversation(
                        st.session_state.conversation['messages'],
                        user_response
                    )
                    if assistant_response:
                        st.write("Character:", assistant_response)
                        listening_skill_coach(assistant_response)
                    else:
                        st.error("Failed to get a response from the character.")
                except Exception as e:
                    st.error(f"An error occurred during the conversation: {str(e)}")
        else:
            st.write("Waiting for conversation to initialize...")
    else:
        st.write("Please generate a scenario to start.")

if __name__ == "__main__":
    main()
