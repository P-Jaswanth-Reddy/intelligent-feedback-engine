from qa_extractor import extract_qa_pairs
from engine import run_engine
from answer_key_gen import generate_answer_key

def evaluate_exam(text, answer_key=None, question_dict=None):

    qa_pairs = extract_qa_pairs(text)

    results = []

    for q, a in qa_pairs:

        model_answer = ""
        if answer_key:
            model_answer = answer_key.get(q,"")
            
        actual_q = q
        if question_dict and q in question_dict:
            actual_q = question_dict[q]

        if not model_answer:
            # fallback
            model_answer = generate_answer_key(actual_q)
            if answer_key is not None:
                answer_key[q] = model_answer

        coverage, score, teacher_feedback, enhanced, graded_concepts = run_engine(
            actual_q,
            a,
            model_answer,
            skip_enhancement=True
        )
        
        strong = [c["concept"] for c in graded_concepts if c["level"]=="Strong"]
        partial = [c["concept"] for c in graded_concepts if c["level"]=="Partial"]
        weak = [c["concept"] for c in graded_concepts if c["level"]=="Weak"]

        results.append({

        "question": actual_q,
        "student_answer": a,
        "coverage": coverage,
        "score": score,
        "feedback": teacher_feedback,
        "enhanced_feedback": enhanced,
        "strong": "\n".join(strong),
        "partial": "\n".join(partial),
        "weak": "\n".join(weak)

    })

    return results