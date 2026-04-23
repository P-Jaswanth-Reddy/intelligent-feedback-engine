from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_answer_key(question):
    """
    Generate a model answer for the given question text.
    The question must be the actual question string, not a label like 'Q1'.
    """

    if not question or not question.strip():
        return ""

    prompt = f"""You are an expert teacher preparing an answer key.

Write a clear, accurate, and concise model answer ONLY for the question below.
Do NOT invent or answer a different question.
Do NOT include any preamble, introduction, or explanation about the question.
Just write the model answer directly.

Question: {question.strip()}

Model Answer:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert teacher. "
                    "Your task is to write a correct, concise model answer "
                    "for the exact question provided. "
                    "Never answer a different question. "
                    "Never fabricate or assume the question."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()