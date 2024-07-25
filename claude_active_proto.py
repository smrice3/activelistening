from openai import OpenAI
import streamlit as st
import json
import re
from pathlib import Path
import os

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# List of white-collar industries
INDUSTRIES = ["Finance", "Technology", "Healthcare", "Marketing", "Law"]


def create_scenario(industry: str):
    prompt = f"""Create a detailed workplace scenario in the {industry} industry. Include:
    1. The name and function of the company
    2. The name and role of the person the user will be talking to
    3. The reason for the discussion
    Format the response strictly as a JSON object with the following keys: company_name, company_function, person_name, person_role, discussion_reason"""
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates workplace scenarios. Always respond in valid JSON format without any additional text."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Debug: Print the entire response object to check its structure
    st.write("Full API Response:", response)

    if response.choices and response.choices[0].message and response.choices[0].message.content:
        content = response.choices[0].message.content.strip()
        st.write("API Response Content:", content)
        
        # Ensure the content is a valid JSON string
        try:
            scenario = json.loads(content)
            return scenario
        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON: {e}")
            st.write("Raw content:", content)
            return None
    else:
        st.error("The response content is empty or malformed.")
        return None


create_scenario('Finance')
