import streamlit as st
import openai
import os

# Load API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Function to generate a response from OpenAI
def generate_response(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Initialize session state for conversation history
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

# Streamlit app layout
st.title("Active Listening Practice with ChatGPT")

# Introduction
st.header("Welcome to the Active Listening Practice App")
st.write("""
This app helps you practice and refine your active listening skills by interacting with ChatGPT.
Follow the steps below to improve your ability to listen actively in conversations.
""")

# Steps of Active Listening
st.header("Steps of Active Listening")
st.markdown("""
1. **Hear the message being delivered**: Actively feel the sound enter your head or see the words as they form in front of you.
2. **Understand the message**: Make sense of what you experience by recognizing who’s speaking and what’s being said.
3. **Remember what was said**: Make note of what you hear. Commit it to memory and allow it to be accessed for later situations.
4. **Interpret the message by applying context**: Consider the context in which the message is delivered.
5. **Evaluate the result using your context**: Your attitude and point of view become a lens for evaluating the message.
6. **Respond to the message**: Act on the message you’ve received, such as nodding your head in conversation.
""")

# Interactive chat section
st.header("Practice Active Listening")

user_input = st.text_input("Enter your message here:")

if st.button("Send"):
    if user_input:
        # Add user's message to conversation history
        st.session_state.conversation.append(("User", user_input))
        
        # Generate response from OpenAI
        response = generate_response(user_input)
        
        # Add OpenAI's response to conversation history
        st.session_state.conversation.append(("ChatGPT", response))
        
        # Clear the input field
        st.text_input("Enter your message here:", value="", key="input_clear")

# Display conversation history
st.subheader("Conversation History")
for speaker, message in st.session_state.conversation:
    if speaker == "User":
        st.write(f"**You:** {message}")
    else:
        st.write(f"**ChatGPT:** {message}")

# Feedback Section (Optional)
st.header("Feedback")
feedback = st.text_area("Provide your feedback on the response or your practice experience here:")
if st.button("Submit Feedback"):
    if feedback:
        st.write("Thank you for your feedback!")
    else:
        st.write("Please provide feedback before submitting.")