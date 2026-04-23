import pandas as pd

def generate_report(results):

    rows = []

    for r in results:

        rows.append({

            "Question": r.get("question",""),
            "Student Answer": r.get("student_answer",""),
            "Coverage Score": r.get("coverage",""),
            "Teacher Feedback": r.get("feedback",""),
            "Marks": r.get("score",""),
            "Strong Concepts": r.get("strong",""),
            "Partial Concepts": r.get("partial",""),
            "Weak Concepts": r.get("weak","")

        })

    df = pd.DataFrame(rows)

    return df