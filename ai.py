'''

from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def analyse_resume(resume_text, user_goal):
    prompt = f"""
You are a senior software engineer and hiring manager.
Evaluate the resume based on user's goal.
User goal : "{user_goal}"

STRICT RULES
-Extract only relevant skills for this goal
-Remove irrelevant tools [excel for backend, etc]
-Identify real gaps
-Generate roadmap only for missing fields
-Make output different based on goal

Return only JSON:
{{
"skills":[],
"missing_skills":[],
"roadmap":[],
"interview_questions":[]
}}

Resume:
{resume_text}

"""
    
    try:
        response = client.chat.completions.create(
            model = "gpt-4.1-mini",
            response_format={"type": "json_object"},
            temperature=0.3,
            messages=[
                {"role":"system", "content":"You're a strict hiring manager"},
                {"role":"user", "content":prompt}
            ]
        )

        content = response.choices[0].message.content

        return json.loads(content)
    
    except Exception as e:
        return {
            "skills":[],
            "missing_skills":[],
            "roadmap":[],
            "interview_questions":[],
            "error":str(e)
        }

'''

import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyse_resume(resume_text, user_goal):

    prompt = f"""
You are a senior software engineer and hiring manager.

Evaluate the resume based on the user's goal.

User Goal:
{user_goal}

STRICT RULES

- Extract only relevant skills.
- Remove irrelevant tools.
- Identify real missing skills.
- Generate a roadmap.
- Generate interview questions.

Return ONLY JSON.

{{
    "skills": [],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}

Resume:

{resume_text}
"""

    try:

        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )

        content = response.text

        start = content.find("{")
        end = content.rfind("}") + 1

        return json.loads(content[start:end])

    except Exception as e:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }