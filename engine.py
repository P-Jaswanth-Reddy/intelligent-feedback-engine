import os
import re
import numpy as np
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import sent_tokenize
import wikipedia
from groq import Groq
from models import model

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# CONCEPT EXTRACTION 


def split_concepts(text):

    if not text:
        return []

    text = text.lower().strip()

    sentences = sent_tokenize(text)

    concepts=[]

    for s in sentences:

        s=s.strip()

        # remove markdown
        s = re.sub(r"\*\*","",s)

        # remove numbering
        s = re.sub(r"\d+\.","",s)

        # remove answer prefix
        s = re.sub(r"answer\s*:","",s)

        # REMOVE QUESTION LINES 
        if s.startswith((
            "what",
            "define",
            "name",
            "explain",
            "difference"
        )):
            continue

        if len(s.split())>=1:

            concepts.append(s)

    return concepts



# SIMILARITY ANALYSIS 


def concept_similarity(student_answer, model_concepts):

    if not student_answer:

        return [(c,0.0) for c in model_concepts]

    student_answer = student_answer.lower().strip()

    student_parts = sent_tokenize(student_answer)

    student_parts=[

        s.strip()

        for s in student_parts

        if len(s.split())>=1

    ]

    if len(student_parts)==0:

        return [(c,0.0) for c in model_concepts]

    student_embeddings = model.encode(student_parts)

    results=[]

    for concept in model_concepts:

        concept_embedding = model.encode([concept])

        sims = cosine_similarity(

            student_embeddings,

            concept_embedding

        ).flatten()

        c_len = len(concept.split())
        best = 0.0
        
        for i, s_part in enumerate(student_parts):
            sim = float(sims[i])
            s_len = len(s_part.split())
            
            # Apply brevity penalty only if student part is much shorter AND difference is huge (> 5 words)
            if s_len < c_len * 0.4 and (c_len - s_len) > 5:
                penalty = s_len / max(1.0, c_len * 0.4)
                sim *= penalty
                
            if sim > best:
                best = sim

        results.append((concept,best))

    return results



# CONCEPT CLASSIFICATION 


def classify_concepts(concepts):

    graded=[]

    for concept,score in concepts:

        if score>=0.60:

            level="Strong"

        elif score>=0.30:

            level="Partial"

        else:

            level="Weak"

        graded.append({

            "concept":concept,
            "similarity":round(score,3),
            "level":level

        })

    return graded



# COVERAGE SCORING 


def compute_coverage(concepts):

    strong=sum(1 for c in concepts if c["level"]=="Strong")

    partial=sum(1 for c in concepts if c["level"]=="Partial")

    total=len(concepts)

    if total==0:

        return 0,0

    coverage=(strong+0.5*partial)/total

    score=round(coverage*10,2)

    return round(coverage,3),score



# TEACHER FEEDBACK 


def generate_teacher_feedback(

    student_answer,
    concept_grading,
    coverage

):

    strong=[]
    partial=[]
    weak=[]

    for c in concept_grading:

        if c["level"]=="Strong":

            strong.append(c["concept"])

        elif c["level"]=="Partial":

            partial.append(c["concept"])

        else:

            weak.append(c["concept"])


    feedback=""

    if coverage>=0.8:

        feedback+="Excellent answer. Strong conceptual understanding.\n"

    elif coverage>=0.6:

        feedback+="Good answer but some concepts need improvement.\n"

    elif coverage>=0.4:

        feedback+="Basic understanding present but important ideas missing.\n"

    else:

        feedback+="Important ideas are missing.\n"


    feedback+=f"\nStudent Answer:\n{student_answer}\n"


    if strong:

        feedback+="\nCorrect Concepts:\n"

        for s in strong:

            feedback+=f"- {s}\n"


    if partial:

        feedback+="\nConcepts needing improvement:\n"

        for p in partial:

            feedback+=f"- {p}\n"


    if weak:

        feedback+="\nMissing Concepts:\n"

        for w in weak:

            feedback+=f"- {w}\n"


    return feedback



# WIKIPEDIA RESOURCE 


def get_wikipedia_resource(text):

    try:

        if not text:
            return None

        results=wikipedia.search(text)

        if len(results)==0:
            return None

        page=wikipedia.page(results[0], auto_suggest=False)

        return{

            "title":page.title,
            "url":page.url,
            "summary":wikipedia.summary(
                page.title,
                sentences=2,
                auto_suggest=False
            )

        }

    except:

        return None



# FEEDBACK ENHANCEMENT 


def enhance_feedback(

    question,
    student_answer,
    teacher_feedback,
    wiki

):

    wiki_text = ""

    if wiki:

        wiki_text = f"""\nReference Resource:\nTitle: {wiki['title']}\nSummary: {wiki['summary']}\nLink: {wiki['url']}\n"""

    # Guard: if question is empty or just a label, skip enhancement
    if not question or not question.strip() or len(question.strip()) < 5:
        return teacher_feedback

    prompt = f"""You are reviewing a student's answer to the following question.

QUESTION: {question.strip()}

STUDENT ANSWER: {student_answer.strip()}

TEACHER FEEDBACK (based on concept coverage analysis):
{teacher_feedback.strip()}
{wiki_text}
Your task:
1. Improve and expand the teacher feedback above — stay focused on the QUESTION topic.
2. Highlight what the student did well and what is missing. Do NOT repeat or quote the original Teacher Feedback or Student Answer.
3. Recommend 2-3 specific learning resources relevant to this QUESTION topic. YOU MUST FORMAT URLs USING STRICT MARKDOWN LINK SYNTAX. Example: [Resource Name](https://example.com). Do NOT output plain text URLs.

IMPORTANT:
- Do NOT answer a different question.
- Do NOT invent a new question.
- Do NOT discuss unrelated topics.
- Keep your response focused only on the QUESTION provided above."""

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[

            {
                "role": "system",
                "content": (
                    f"You are an expert tutor specialised in the subject area of: '{question.strip()}'. "
                    "Your sole task is to give focused, accurate feedback on the student's answer "
                    "to that exact question. You must never go off-topic or discuss unrelated subjects."
                )
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0.3

    )

    return response.choices[0].message.content.strip()



# MAIN ENGINE 


def run_engine(

    question,
    student_answer,
    model_answer,
    skip_enhancement=False

):

    concepts=split_concepts(model_answer)

    analysis=concept_similarity(

        student_answer,
        concepts

    )

    graded=classify_concepts(analysis)

    coverage,score=compute_coverage(graded)

    teacher_feedback=generate_teacher_feedback(

        student_answer,
        graded,
        coverage

    )

    if skip_enhancement:
        enhanced = ""
    else:
        # FIX: use question to search Wikipedia instead of full model answer
        wiki=get_wikipedia_resource(question)

        enhanced=enhance_feedback(

            question,
            student_answer,
            teacher_feedback,
            wiki

        )

    return coverage,score,teacher_feedback,enhanced,graded


# CLASS REPORT GENERATION

def generate_class_report(results):
    if not results:
        return "No data available."
        
    q_stats = {}
    for r in results:
        q = r["question"]
        if q not in q_stats:
            q_stats[q] = {"total_score": 0, "count": 0, "weak_concepts": set()}
        q_stats[q]["total_score"] += r["score"]
        q_stats[q]["count"] += 1
        if "weak" in r and r["weak"]:
            for wc in r["weak"].split("\n"):
                if wc.strip():
                    q_stats[q]["weak_concepts"].add(wc.strip())

    summary = []
    for q, stats in q_stats.items():
        avg = stats["total_score"] / stats["count"]
        weaks = ", ".join(list(stats["weak_concepts"])[:3])
        if not weaks:
            weaks = "None"
        summary.append(f"Q: {q} | Avg Score: {avg:.1f}/10.0 | Concepts Missing: {weaks}")
        
    prompt = f"""You are an educational data analyst. Read the following class test summary:
    
{chr(10).join(summary)}

Provide a concise 2-3 paragraph report for the teacher. 
Highlight what topics the majority of students understood well, and where the major knowledge gaps or weak areas are.
Format your response cleanly using markdown."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a concise data analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()