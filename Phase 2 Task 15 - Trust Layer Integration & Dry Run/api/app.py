"""
Task 15 FastAPI Application
Endpoints for AI Trust pipeline:
- Resume parsing
- Skill ontology mapping
- Job matching
- Assessment proctoring
- AI Trust reporting
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from pathlib import Path
import joblib
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from run_validations import SkillParser, SkillOntologyMapper, JobMatcher, ProctoringClassifier

app = FastAPI(
    title="PlaceMux AI Trust API",
    description="AI/ML pipeline for intelligent job matching and proctored assessments",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

# Load models and data
ontology_df = pd.read_csv(DATA_DIR / "ontology.csv")
proctoring_model = joblib.load(MODELS_DIR / "proctoring_model.pkl")

# Initialize components
parser = SkillParser(ontology_df)
mapper = SkillOntologyMapper(ontology_df)
matcher = JobMatcher(ontology_df)
classifier = ProctoringClassifier(proctoring_model)

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ResumeParseRequest(BaseModel):
    resume_text: str

class ResumeParseResponse(BaseModel):
    skills: list[str]
    count: int
    timestamp: str

class SkillMapRequest(BaseModel):
    raw_skill: str

class SkillMapResponse(BaseModel):
    raw_skill: str
    standard_skill: str | None
    match_type: str
    confidence: float

class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str

class MatchResponse(BaseModel):
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: str
    timestamp: str

class ProctoringRequest(BaseModel):
    assessment_duration_min: int
    tab_switches: int
    face_detections: int
    external_audio_detected: int
    copy_paste_events: int
    keystroke_velocity_variance: float
    mouse_speed_anomaly: int

class ProctoringResponse(BaseModel):
    classification: str
    confidence: float
    reasons: list[str]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    components: dict
    timestamp: str

class EndToEndRequest(BaseModel):
    resume_text: str
    jd_text: str
    assessment_features: dict

class EndToEndResponse(BaseModel):
    resume_skills: list[str]
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    proctoring_classification: str
    recommendation: str
    timestamp: str

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with model status"""
    return {
        "status": "healthy",
        "components": {
            "parser": "✓ loaded",
            "ontology": f"✓ loaded ({len(ontology_df)} mappings)",
            "matcher": "✓ loaded",
            "proctoring_model": "✓ loaded",
            "reports": "✓ available"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/parse/resume", response_model=ResumeParseResponse)
async def parse_resume(request: ResumeParseRequest):
    """Extract skills from resume text"""
    try:
        skills = parser.extract_skills(request.resume_text)
        return {
            "skills": sorted(skills),
            "count": len(skills),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/parse/jd")
async def parse_jd(request: ResumeParseRequest):
    """Extract required skills from job description"""
    try:
        skills = parser.extract_skills(request.resume_text)
        return {
            "skills": sorted(skills),
            "count": len(skills),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ontology/map", response_model=SkillMapResponse)
async def map_skill(request: SkillMapRequest):
    """Map raw skill to standard skill"""
    try:
        standard, match_type, confidence = mapper.map_skill(request.raw_skill)
        return {
            "raw_skill": request.raw_skill,
            "standard_skill": standard,
            "match_type": match_type,
            "confidence": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/match", response_model=MatchResponse)
async def match_resume_to_job(request: MatchRequest):
    """Match resume to job description"""
    try:
        result = matcher.match(request.resume_text, request.jd_text)
        return {
            "score": result['score'],
            "matched_skills": result['matched_skills'],
            "missing_skills": result['missing_skills'],
            "explanation": result['explanation'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/proctor/check", response_model=ProctoringResponse)
async def check_proctoring(request: ProctoringRequest):
    """Classify assessment session"""
    try:
        features_dict = request.dict()
        result = classifier.classify(features_dict)
        return {
            "classification": result['classification'],
            "confidence": result['confidence'],
            "reasons": result['reasons'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/trust/report")
async def get_trust_report():
    """Get the AI Trust Report"""
    try:
        report_path = REPORTS_DIR / "ai_trust_report.md"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="AI Trust Report not found. Run validations first.")
        
        with open(report_path) as f:
            report = f.read()
        
        return {
            "report": report,
            "format": "markdown",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trust/validate", response_model=EndToEndResponse)
async def validate_end_to_end(request: EndToEndRequest):
    """Run complete end-to-end validation"""
    try:
        # Parse resume
        resume_skills = parser.extract_skills(request.resume_text)
        
        # Match to job
        match_result = matcher.match(request.resume_text, request.jd_text)
        
        # Proctor assessment
        proctor_result = classifier.classify(request.assessment_features)
        
        # Make recommendation
        if match_result['score'] >= 0.6 and proctor_result['classification'] in ['SAFE', 'REVIEW']:
            recommendation = "PROCEED_TO_OFFER"
        elif match_result['score'] >= 0.4 and proctor_result['classification'] in ['SAFE', 'REVIEW']:
            recommendation = "REVIEW_FURTHER"
        else:
            recommendation = "PASS"
        
        return {
            "resume_skills": resume_skills,
            "match_score": match_result['score'],
            "matched_skills": match_result['matched_skills'],
            "missing_skills": match_result['missing_skills'],
            "proctoring_classification": proctor_result['classification'],
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "PlaceMux AI Trust API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "GET /health",
            "parse_resume": "POST /parse/resume",
            "parse_jd": "POST /parse/jd",
            "map_skill": "POST /ontology/map",
            "match": "POST /match",
            "proctor": "POST /proctor/check",
            "trust_report": "GET /trust/report",
            "validate": "POST /trust/validate",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)
