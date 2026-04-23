import re


def extract_qa_pairs(text):
    """
    Extracts (question_label, answer) pairs from text.
    Handles formats like:
      Q1 <answer>
      Q1. <answer>
      Q1\n<answer>
    Also handles sheets that embed "Student Answer: ..." feedback blobs.
    """

    if not text:
        return []

    # Match optional Q/q and number followed by its content up to the next number or end
    pattern = r"(?m)^\s*[Qq]?(\d+)[\.\)]?\s*(.*?)(?=\n\s*[Qq]?\d+[\.\)]?\s*|\Z)"

    matches = re.findall(
        pattern,
        text,
        re.DOTALL | re.IGNORECASE
    )

    qa_pairs = []

    for q_num, raw_content in matches:

        answer = raw_content.strip()

        # If the content contains "Student Answer:" context (feedback blobs),
        # extract only the actual student answer text that follows it.
        student_answer_match = re.search(
            r"Student Answer:\s*(.+?)(?:\n\n|\n(?:Missing Concepts|Concepts needing|Correct Concepts|Teacher Feedback|Important ideas|$))",
            answer,
            flags=re.IGNORECASE | re.DOTALL
        )

        if student_answer_match:
            answer = student_answer_match.group(1).strip()
        else:
            # Remove a leading "answer:" prefix if present
            answer = re.sub(
                r"^answer\s*:\s*",
                "",
                answer,
                flags=re.IGNORECASE
            ).strip()

        if answer:
            qa_pairs.append((f"Q{q_num}", answer))

    return qa_pairs