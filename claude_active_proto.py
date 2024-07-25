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
    Format the response as JSON with keys: company_name, company_function, person_name, person_role, discussion_reason"""
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates workplace scenarios. Always respond in valid JSON format."},
            {"role": "user", "content": prompt}
        ]
    )
    content = response.choices[0].message.content

    # Debug: Print the content to check the response
    st.print("API Response Content:", content)

    # Directly parse JSON from the content
    scenario = json.loads(content)
    return scenario

create.scenario(Finance)
