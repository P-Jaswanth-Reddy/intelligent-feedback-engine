import streamlit as st
from engine import run_engine, generate_class_report
from parser import parse_file
from batch_engine import evaluate_exam
from report_generator import generate_report
from qa_extractor import extract_qa_pairs
from answer_key_gen import generate_answer_key
import re

st.set_page_config(page_title="Intelligent Feedback Engine")

st.title("Intelligent Feedback Engine")

mode = st.sidebar.selectbox(

    "Select Mode",

    ["Student Mode","Teacher Mode"]

)


# STUDENT MODE

if mode=="Student Mode":

    st.header("Student Evaluation")

    st.subheader("Question")

    question_text=st.text_area("Enter Question")

    question_file=st.file_uploader(

        "Or Upload Question File",

        type=["pdf","docx","png","jpg","jpeg","txt"]

    )

    st.subheader("Student Answer")

    student_text=st.text_area("Enter Student Answer")

    student_file=st.file_uploader(

        "Or Upload Student Answer",

        type=["pdf","docx","png","jpg","jpeg","txt"]

    )

    st.subheader("Answer Key (Optional)")

    model_text=st.text_area("Enter Model Answer")

    model_file=st.file_uploader(

        "Or Upload Answer Key",

        type=["pdf","docx","png","jpg","jpeg","txt"]

    )

    if st.button("Evaluate Answer"):

        # Resolve Question
        if question_file:

            question=parse_file(question_file)

        else:

            question=question_text

        # Resolve Student Answer
        if student_file:

            student_answer=parse_file(student_file)

        else:

            student_answer=student_text

        # Resolve Model Answer
        if model_file:

            answer_key_text=parse_file(model_file)

        else:

            answer_key_text=model_text

        question_pairs = dict(extract_qa_pairs(question)) if question else {}

        if student_answer:

            student_pairs=extract_qa_pairs(student_answer)

            answer_pairs={}

            if answer_key_text:

                answer_pairs=dict(

                    extract_qa_pairs(answer_key_text)

                )
            
            if not student_pairs:
                
                # Fallback to single question evaluation
                student_pairs = [(question, student_answer)]
                
                if answer_key_text and not answer_pairs:
                    
                    answer_pairs = {question: answer_key_text}

            results=[]

            for q,student_ans in student_pairs:

                model_answer = answer_pairs.get(q,"")
                actual_question_text = question_pairs.get(q, q) if question_pairs else q

                # AUTO GENERATION if missing
                if not model_answer:
                    model_answer=generate_answer_key(actual_question_text)

                coverage,score,teacher_feedback,enhanced,graded=run_engine(

                    actual_question_text,

                    student_ans,

                    model_answer

                )

                results.append({

                    "question":actual_question_text,

                    "coverage":coverage,

                    "score":score,

                    "feedback":teacher_feedback,

                    "enhanced":enhanced

                })

            st.success("Evaluation Complete")

            for r in results:

                st.subheader(r["question"])

                st.write("Coverage Score:",r["coverage"])

                st.write("Marks:",r["score"])

                st.write("Teacher Feedback")

                st.markdown(r["feedback"])

                st.write("Enhanced AI Feedback")

                st.markdown(r["enhanced"])

        else:

            st.error("Please provide student answer")


# TEACHER MODE


elif mode=="Teacher Mode":

    st.header("Class Evaluation")

    st.subheader("Question Paper ")

    question_text=st.text_area(

        "Enter Question Paper"

    )

    question_file=st.file_uploader(

        "Or Upload Question Paper",

        type=["pdf","docx","png","jpg","jpeg","txt"]

    )

    st.subheader("Answer Key")

    answer_text=st.text_area(

        "Enter Answer Key"

    )

    answer_file=st.file_uploader(

        "Or Upload Answer Key",

        type=["pdf","docx","png","jpg","jpeg","txt"]

    )

    st.subheader("Student Answer Sheets")

    student_text_input=st.text_area(

        "Enter Student Answers"

    )

    student_files=st.file_uploader(

        "Or Upload Student Answer Sheets",

        type=["pdf","docx","png","jpg","jpeg","txt"],

        accept_multiple_files=True

    )

    if st.button("Evaluate Class"):

        results=[]

        answer_key_dict={}

        question_dict = {}
        if question_file:
            q_text = parse_file(question_file)
        else:
            q_text = question_text
        if q_text:
            question_dict = dict(extract_qa_pairs(q_text))

        # Resolve Answer Key
        if answer_file:

            answer_key_text=parse_file(answer_file)

        else:

            answer_key_text=answer_text

        if answer_key_text:

            qa_pairs=extract_qa_pairs(

                answer_key_text

            )

            answer_key_dict={

                q:a for q,a in qa_pairs

            }

        # Evaluate uploaded files
        if student_files:

            for file in student_files:

                student_text=parse_file(file)

                student_results=evaluate_exam(

                    student_text,

                    answer_key_dict,
                    
                    question_dict

                )

                results.extend(student_results)

        elif student_text_input:

            student_results=evaluate_exam(

                student_text_input,

                answer_key_dict,
                
                question_dict

            )

            results.extend(student_results)

        if results:

            df=generate_report(results)

            st.success("Evaluation Complete")

            st.subheader("Class Insights & Analysis")
            
            with st.spinner("Generating class report..."):
                report_text = generate_class_report(results)
                st.markdown(report_text)

            st.dataframe(df)

            st.download_button(

                "Download Results",

                df.to_csv(index=False),

                file_name="class_results.csv"

            )

        else:

            st.error("No student answers found")