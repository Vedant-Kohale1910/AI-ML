"""
Generate synthetic data for Task 15 AI Trust Signoff
- 30 synthetic resumes with varied skills
- 15 synthetic job descriptions
- 60 labeled skill pairs for parser evaluation
- 1200 proctoring session records
"""

import pandas as pd
import csv
import json
from pathlib import Path
import random

# Set seed for reproducibility
random.seed(42)

DATA_DIR = "../data"
EVAL_DIR = "../data/eval"

def create_ontology():
    """Create skill ontology CSV"""
    ontology_data = {
        'raw_skill': [
            'python', 'py', 'python3', 'javascript', 'js', 'java', 'c++', 'cpp',
            'machine learning', 'ml', 'deep learning', 'dl', 'nlp', 'computer vision',
            'sql', 'mysql', 'postgres', 'nosql', 'mongodb',
            'data science', 'data analysis', 'analytics',
            'aws', 'gcp', 'azure', 'cloud',
            'react', 'vue', 'angular', 'frontend',
            'django', 'flask', 'fastapi', 'backend',
            'docker', 'kubernetes', 'devops', 'ci/cd',
            'git', 'version control', 'github',
            'agile', 'scrum', 'kanban', 'project management',
            'communication', 'leadership', 'teamwork',
            'tensorflow', 'torch', 'keras', 'pytorch',
            'pandas', 'numpy', 'scipy', 'scikit-learn',
            'tableau', 'powerbi', 'visualization', 'bi',
            'rest api', 'api design', 'microservices',
            'html', 'css', 'responsive design',
            'testing', 'pytest', 'unit testing',
            'linux', 'bash', 'shell scripting',
            'spark', 'hadoop', 'bigdata', 'big data'
        ],
        'standard_skill': [
            'Python', 'Python', 'Python', 'JavaScript', 'JavaScript', 'Java', 'C++', 'C++',
            'Machine Learning', 'Machine Learning', 'Deep Learning', 'Deep Learning', 'NLP', 'Computer Vision',
            'SQL', 'SQL', 'SQL', 'NoSQL', 'NoSQL',
            'Data Science', 'Data Science', 'Data Science',
            'AWS', 'GCP', 'Azure', 'Cloud',
            'React', 'Vue', 'Angular', 'Frontend Development',
            'Django', 'Flask', 'FastAPI', 'Backend Development',
            'Docker', 'Kubernetes', 'DevOps', 'CI/CD',
            'Git', 'Git', 'Git',
            'Agile', 'Agile', 'Agile', 'Project Management',
            'Communication', 'Leadership', 'Teamwork',
            'TensorFlow', 'PyTorch', 'Keras', 'PyTorch',
            'Pandas', 'NumPy', 'SciPy', 'Scikit-Learn',
            'Tableau', 'Power BI', 'Data Visualization', 'Business Intelligence',
            'REST API', 'API Design', 'Microservices',
            'HTML', 'CSS', 'Responsive Design',
            'Testing', 'Testing', 'Testing',
            'Linux', 'Bash', 'Bash',
            'Spark', 'Hadoop', 'Big Data', 'Big Data'
        ]
    }
    ontology_df = pd.DataFrame(ontology_data)
    ontology_df.to_csv(DATA_DIR/"ontology.csv", index=False)
    print(f"✓ Created ontology.csv with {len(ontology_df)} skill mappings")
    return ontology_df

def create_resumes():
    """Generate 30 synthetic resumes"""
    skill_pool = [
        'Python', 'JavaScript', 'Java', 'C++', 'SQL', 'Machine Learning', 'Deep Learning',
        'Data Science', 'AWS', 'Docker', 'React', 'Django', 'FastAPI', 'Git',
        'Agile', 'Leadership', 'Communication', 'TensorFlow', 'PyTorch', 'Pandas',
        'NumPy', 'Spark', 'Kubernetes', 'REST API', 'Linux', 'DevOps'
    ]
    
    resume_dir = DATA_DIR/"resumes"
    resume_dir.mkdir(exist_ok=True)
    
    for i in range(1, 31):
        num_skills = random.randint(4, 10)
        skills = random.sample(skill_pool, num_skills)
        years_exp = random.randint(1, 15)
        
        resume_text = f"""
CANDIDATE {i}
Email: candidate{i}@example.com | Phone: +1-555-{1000+i:04d}

SUMMARY
Experienced professional with {years_exp} years in software development and data science.

TECHNICAL SKILLS
{', '.join(skills)}

EXPERIENCE
- Senior Software Engineer (2021-2024): Built scalable systems using modern tech stacks
- Data Scientist (2019-2021): Developed ML models for business insights
- Software Developer (2017-2019): Full-stack development and APIs

EDUCATION
B.S. in Computer Science
"""
        
        with open(resume_dir / f"resume_{i:03d}.txt", "w") as f:
            f.write(resume_text)
    
    print(f"✓ Generated 30 synthetic resumes in {resume_dir}")

def create_job_descriptions():
    """Generate 15 synthetic job descriptions"""
    jd_templates = [
        {
            'title': 'Senior Backend Engineer',
            'skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'AWS', 'CI/CD'],
            'level': 'Senior'
        },
        {
            'title': 'ML Engineer',
            'skills': ['Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Data Science', 'SQL'],
            'level': 'Mid'
        },
        {
            'title': 'Frontend Developer',
            'skills': ['JavaScript', 'React', 'HTML', 'CSS', 'Responsive Design', 'Git'],
            'level': 'Mid'
        },
        {
            'title': 'Data Scientist',
            'skills': ['Python', 'Data Science', 'Machine Learning', 'Pandas', 'NumPy', 'SQL'],
            'level': 'Mid'
        },
        {
            'title': 'DevOps Engineer',
            'skills': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Linux', 'Bash'],
            'level': 'Senior'
        },
        {
            'title': 'Full Stack Developer',
            'skills': ['Python', 'JavaScript', 'React', 'Django', 'PostgreSQL', 'Docker'],
            'level': 'Mid'
        },
        {
            'title': 'Cloud Architect',
            'skills': ['AWS', 'Kubernetes', 'DevOps', 'Docker', 'Python', 'Linux'],
            'level': 'Senior'
        },
        {
            'title': 'Data Engineer',
            'skills': ['Python', 'SQL', 'Spark', 'Hadoop', 'AWS', 'Big Data'],
            'level': 'Mid'
        },
        {
            'title': 'Machine Learning Engineer',
            'skills': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Data Science'],
            'level': 'Senior'
        },
        {
            'title': 'Software Engineer - Backend',
            'skills': ['Java', 'C++', 'REST API', 'SQL', 'Microservices', 'Docker'],
            'level': 'Mid'
        },
        {
            'title': 'NLP Engineer',
            'skills': ['Python', 'NLP', 'Machine Learning', 'Deep Learning', 'TensorFlow'],
            'level': 'Senior'
        },
        {
            'title': 'Computer Vision Engineer',
            'skills': ['Python', 'Computer Vision', 'Deep Learning', 'PyTorch', 'OpenCV'],
            'level': 'Mid'
        },
        {
            'title': 'Junior Software Developer',
            'skills': ['Python', 'JavaScript', 'Git', 'SQL', 'React', 'Testing'],
            'level': 'Junior'
        },
        {
            'title': 'Analytics Engineer',
            'skills': ['SQL', 'Data Science', 'Tableau', 'Python', 'Data Visualization'],
            'level': 'Mid'
        },
        {
            'title': 'AI/ML Platform Engineer',
            'skills': ['Python', 'Machine Learning', 'Kubernetes', 'Docker', 'AWS', 'DevOps'],
            'level': 'Senior'
        }
    ]
    
    jd_dir = DATA_DIR / "job_descriptions"
    jd_dir.mkdir(exist_ok=True)
    
    for idx, template in enumerate(jd_templates, 1):
        jd_text = f"""
JOB ID: JD_{idx:03d}
TITLE: {template['title']}
LEVEL: {template['level']}

DESCRIPTION
We are looking for a talented professional to join our team. This is a {template['level']}-level position
requiring strong technical skills and the ability to work in a fast-paced environment.

REQUIRED SKILLS
{', '.join(template['skills'])}

RESPONSIBILITIES
- Develop and maintain production systems
- Collaborate with cross-functional teams
- Participate in code reviews and knowledge sharing
- Contribute to system design and architecture decisions

QUALIFICATIONS
- 3-8 years of professional experience
- Strong problem-solving skills
- Experience with modern development practices
- Excellent communication abilities
"""
        
        with open(jd_dir / f"jd_{idx:03d}.txt", "w") as f:
            f.write(jd_text)
    
    print(f"✓ Generated 15 synthetic job descriptions in {jd_dir}")

def create_parser_labeled_pairs():
    """Create 60 labeled skill extraction pairs for evaluation"""
    EVAL_DIR.mkdir(exist_ok=True)
    
    labeled_pairs = [
        # Clean aliases
        ('python', 'Python', 1),
        ('py', 'Python', 1),
        ('python3', 'Python', 1),
        ('javascript', 'JavaScript', 1),
        ('js', 'JavaScript', 1),
        ('java', 'Java', 1),
        ('c++', 'C++', 1),
        ('cpp', 'C++', 1),
        ('machine learning', 'Machine Learning', 1),
        ('ml', 'Machine Learning', 1),
        
        # Typos and variations
        ('pythno', 'Python', 1),
        ('javasript', 'JavaScript', 1),
        ('machne learning', 'Machine Learning', 1),
        ('deeplearning', 'Deep Learning', 1),
        ('sql', 'SQL', 1),
        ('SQL', 'SQL', 1),
        ('data science', 'Data Science', 1),
        ('aws', 'AWS', 1),
        ('docker', 'Docker', 1),
        ('kubernetes', 'Kubernetes', 1),
        
        # Case variations
        ('PYTHON', 'Python', 1),
        ('Python', 'Python', 1),
        ('JAVA', 'Java', 1),
        ('JavaScript', 'JavaScript', 1),
        
        # Genuine aliases
        ('react', 'React', 1),
        ('django', 'Django', 1),
        ('fastapi', 'FastAPI', 1),
        ('tensorflow', 'TensorFlow', 1),
        ('torch', 'PyTorch', 1),
        ('pytorch', 'PyTorch', 1),
        
        # Fuzzy matches
        ('pandas', 'Pandas', 1),
        ('numpy', 'NumPy', 1),
        ('sklearn', 'Scikit-Learn', 1),
        ('scikit-learn', 'Scikit-Learn', 1),
        
        # Unmapped but valid
        ('golang', 'Go', 0),  # Not in standard ontology
        ('rust', 'Rust', 0),
        ('kotlin', 'Kotlin', 0),
        ('scala', 'Scala', 0),
        ('haskell', 'Haskell', 0),
        
        # Additional clean mappings
        ('git', 'Git', 1),
        ('github', 'Git', 1),
        ('mysql', 'SQL', 1),
        ('postgres', 'SQL', 1),
        ('mongodb', 'NoSQL', 1),
        ('nosql', 'NoSQL', 1),
        ('tableau', 'Tableau', 1),
        ('powerbi', 'Power BI', 1),
        ('react.js', 'React', 1),
        ('vue.js', 'Vue', 1),
        
        # Typos and variations
        ('react js', 'React', 1),
        ('vue js', 'Vue', 1),
        ('docker compose', 'Docker', 1),
        ('kuberentes', 'Kubernetes', 1),  # Typo
        ('restapi', 'REST API', 1),
        ('rest-api', 'REST API', 1),
        ('devops', 'DevOps', 1),
        ('ci/cd', 'CI/CD', 1),
        ('cicd', 'CI/CD', 1),
        
        # Communication/Soft skills
        ('communication', 'Communication', 1),
        ('leadership', 'Leadership', 1),
        ('teamwork', 'Teamwork', 1),
        ('problem solving', 'Problem Solving', 0),
        ('analytical thinking', 'Analytical Thinking', 0),
    ]
    
    parser_df = pd.DataFrame(labeled_pairs, columns=['raw_text', 'expected_standard', 'is_mapped'])
    parser_df.to_csv(EVAL_DIR / "parser_labeled_pairs.csv", index=False)
    print(f"✓ Created parser_labeled_pairs.csv with {len(parser_df)} labeled examples")

def create_proctoring_sessions():
    """Create 1200 labeled proctoring session records"""
    EVAL_DIR.mkdir(exist_ok=True)
    
    sessions = []
    session_id = 1
    
    for _ in range(1200):
        # Simulate features from a proctoring session
        assessment_duration = random.randint(10, 120)  # minutes
        tab_switches = random.randint(0, 15)
        face_detections = random.randint(0, 30)
        external_audio = random.randint(0, 5)
        copy_paste_events = random.randint(0, 8)
        keystroke_velocity_variance = round(random.uniform(0.1, 2.5), 2)
        mouse_speed_anomaly = random.randint(0, 1)
        
        # Generate label based on feature patterns (ground truth)
        # SAFE: normal behavior
        # REVIEW: some suspicious activity
        # FLAGGED: clear cheating indicators
        
        risk_score = (
            tab_switches * 0.15 +
            copy_paste_events * 0.2 +
            external_audio * 0.25 +
            mouse_speed_anomaly * 0.15 +
            (keystroke_velocity_variance - 1.0) * 0.1
        )
        
        if risk_score > 2.0:
            label = 'FLAGGED'
        elif risk_score > 0.8:
            label = 'REVIEW'
        else:
            label = 'SAFE'
        
        # Add noise for some realistic variation
        if random.random() < 0.05:  # 5% mislabeling noise
            label = random.choice(['SAFE', 'REVIEW', 'FLAGGED'])
        
        session = {
            'session_id': session_id,
            'assessment_duration_min': assessment_duration,
            'tab_switches': tab_switches,
            'face_detections': face_detections,
            'external_audio_detected': external_audio,
            'copy_paste_events': copy_paste_events,
            'keystroke_velocity_variance': keystroke_velocity_variance,
            'mouse_speed_anomaly': mouse_speed_anomaly,
            'predicted_label': label,
            'split': random.choices(['train', 'val', 'test'], weights=[0.6, 0.2, 0.2])[0]
        }
        sessions.append(session)
        session_id += 1
    
    proctoring_df = pd.DataFrame(sessions)
    proctoring_df.to_csv(EVAL_DIR / "proctoring_sessions.csv", index=False)
    print(f"✓ Created proctoring_sessions.csv with {len(proctoring_df)} session records")
    print(f"  - SAFE: {len(proctoring_df[proctoring_df['predicted_label']=='SAFE'])}")
    print(f"  - REVIEW: {len(proctoring_df[proctoring_df['predicted_label']=='REVIEW'])}")
    print(f"  - FLAGGED: {len(proctoring_df[proctoring_df['predicted_label']=='FLAGGED'])}")

def main():
    print("\n" + "="*60)
    print("TASK 15 - DATA GENERATION")
    print("="*60 + "\n")
    
    create_ontology()
    create_resumes()
    create_job_descriptions()
    create_parser_labeled_pairs()
    create_proctoring_sessions()
    
    print("\n" + "="*60)
    print("✓ DATA GENERATION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
