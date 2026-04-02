from groq import Groq
from dotenv import load_dotenv
import pymupdf
import os
import json

load_dotenv(override=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def analyze_resume(resume_text, job_description):
    prompt = f"""
You are an expert ATS (Applicant Tracking System) analyzer and career coach.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Analyze the resume against the job description and respond with ONLY a valid JSON object, no extra text, no markdown, no backticks:
{{
    "ats_score": 85,
    "matching_keywords": ["Python", "REST API", "SQL"],
    "missing_keywords": ["Docker", "AWS", "Kubernetes"],
    "suggestions": [
        "Add Docker experience to your skills section",
        "Mention any cloud platforms you have used",
        "Quantify achievements with numbers and metrics"
    ],
    "cover_letter": "Dear Hiring Manager, I am excited to apply..."
}}

IMPORTANT: Return ONLY the JSON object. No explanation. No markdown. No backticks.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()
    # Clean any markdown formatting
    raw = raw.replace("```json", "").replace("```", "").strip()
    # Find JSON object
    start = raw.find("{")
    end = raw.rfind("}") + 1
    raw = raw[start:end]
    return json.loads(raw)

def print_results(results):
    print("\n" + "="*50)
    print(f"📊 ATS MATCH SCORE: {results['ats_score']}/100")
    print("="*50)

    print("\n✅ MATCHING KEYWORDS:")
    for kw in results['matching_keywords']:
        print(f"   • {kw}")

    print("\n❌ MISSING KEYWORDS:")
    for kw in results['missing_keywords']:
        print(f"   • {kw}")

    print("\n💡 SUGGESTIONS:")
    for i, s in enumerate(results['suggestions'], 1):
        print(f"   {i}. {s}")

    print("\n📝 COVER LETTER:")
    print("-"*50)
    print(results['cover_letter'])
    print("="*50)

if __name__ == "__main__":
    # ← Put your resume PDF path here
    resume_path = input("Enter your resume PDF path: ")
    
    print("\nPaste the job description below.")
    print("When done, type 'END' on a new line and press Enter:\n")
    
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    job_description = "\n".join(lines)

    print("\n⏳ Analyzing your resume...")
    
    resume_text = extract_text_from_pdf(resume_path)
    results = analyze_resume(resume_text, job_description)
    print_results(results)