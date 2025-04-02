from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import openai
import os


# Get OpenAI API key from environment variables
openai.api_key = "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"
# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for frontend-backend communication

# Ensure 'uploads' directory exists
if not os.path.exists('uploads'):
    os.mkdir('uploads')

# Function to extract text from a text-based PDF
def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            return text.strip() if text else None
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# Function to extract text from an image-based PDF using OCR
def extract_text_from_image_pdf(pdf_file):
    try:
        images = convert_from_path(pdf_file)
        text = "\n".join([pytesseract.image_to_string(image) for image in images])
        return text.strip() if text else None
    except Exception as e:
        print(f"Error extracting text from image-based PDF: {e}")
        return None

# Function to get predefined job descriptions based on categories
def get_predefined_job_description(job_category):
    job_descriptions = {
        "Software Engineer": "Develop and maintain software applications, write efficient code...",
        "Data Scientist": "Analyze large datasets, build machine learning models...",
        "Web Developer": "Develop and maintain websites, ensure front-end and back-end efficiency...",
        "DevOps Engineer": "Manage CI/CD pipelines, monitor cloud infrastructure..."
    }
    return job_descriptions.get(job_category, None)

# Route to serve the frontend
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle file upload and resume analysis
@app.route('/analyze', methods=['POST'])
def analyze():
    job_description = request.form.get('jobDescription', '').strip()
    # job_category = request.form.get('jobCategory', '').strip()
    resume_file = request.files.get('resumeUpload')

    if not resume_file:
        return jsonify({"error": "Resume file is missing"}), 400

    if not job_description and job_category:
        job_description = get_predefined_job_description(job_category)
    
    if not job_description:
        return jsonify({"error": "Provide either a job description or a job category."}), 400

    if resume_file.filename.split(".")[-1].lower() != "pdf":
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    unique_filename = f"{os.urandom(16).hex()}_{resume_file.filename}"
    resume_file_path = os.path.join("uploads", unique_filename)

    try:
        resume_file.save(resume_file_path)
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({"error": "Failed to save the resume file."}), 500

    resume_text = extract_text_from_pdf(resume_file_path) or extract_text_from_image_pdf(resume_file_path)
    
    if not resume_text:
        os.remove(resume_file_path)
        return jsonify({"error": "Failed to extract text from the resume."}), 500

    feedback = analyze_resume_with_ai(resume_text, job_description)
    
    os.remove(resume_file_path)  # Clean up uploaded file

    return jsonify({"feedback": feedback, "status": "success"})

# Function to analyze resume with OpenAI API
def analyze_resume_with_ai(resume_text, job_description):
    prompt = f"""
    Given the job description and resume, analyze the resume in bullet points under the following categories:

    **1. Skills Match:**   
    - Missing  skills:  

    **2. Experience Relevance:**  
    - Evaluate if the candidate’s experience aligns with the job role.  
    - Highlight experience gaps.  

    **3. Content Optimization:**  
    - Suggest improvements for clarity and impact.  
    - Recommend modifications for readability.  

    **4. ATS Optimization:**  
    - Assess ATS-friendliness (keywords, formatting).  
    - Suggest improvements for ATS compatibility.  

    **5. Strengths & Weaknesses:**  
    - Highlight strong points.  
    - List major weaknesses with fixes.  

    Job Description:  
    {job_description}  

    Resume:  
    {resume_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume analyzer. Provide structured feedback using bullet points."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.5
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "Error analyzing the resume. Please try again later."

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)