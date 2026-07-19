"""
Pytest test suite for Task 15 AI Trust Pipeline
Tests for all major components and end-to-end flow
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from run_validations import SkillParser, SkillOntologyMapper, JobMatcher, ProctoringClassifier

# Setup paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

@pytest.fixture
def ontology_df():
    """Load ontology for testing"""
    return pd.read_csv(DATA_DIR / "ontology.csv")

@pytest.fixture
def parser(ontology_df):
    """Create parser instance"""
    return SkillParser(ontology_df)

@pytest.fixture
def mapper(ontology_df):
    """Create ontology mapper instance"""
    return SkillOntologyMapper(ontology_df)

@pytest.fixture
def matcher(ontology_df):
    """Create job matcher instance"""
    return JobMatcher(ontology_df)

@pytest.fixture
def proctoring_model():
    """Load proctoring model"""
    import joblib
    return joblib.load(MODELS_DIR / "proctoring_model.pkl")

@pytest.fixture
def classifier(proctoring_model):
    """Create proctoring classifier instance"""
    return ProctoringClassifier(proctoring_model)

# ============================================================
# SKILL PARSER TESTS
# ============================================================

class TestSkillParser:
    """Tests for resume/JD skill extraction"""
    
    def test_parser_initializes(self, parser):
        """Test parser initializes correctly"""
        assert parser is not None
        assert len(parser.standard_skills) > 0
    
    def test_extract_skills_basic(self, parser):
        """Test basic skill extraction"""
        text = "I have experience with Python and JavaScript"
        skills = parser.extract_skills(text)
        
        assert len(skills) > 0
        assert 'Python' in skills or 'JavaScript' in skills
    
    def test_extract_skills_empty(self, parser):
        """Test extraction from text with no skills"""
        text = "This candidate has generic work experience"
        skills = parser.extract_skills(text)
        
        assert isinstance(skills, list)
    
    def test_extract_skills_multiple(self, parser):
        """Test extraction of multiple skills"""
        text = "Python, JavaScript, SQL, Docker, Kubernetes, AWS"
        skills = parser.extract_skills(text)
        
        assert len(skills) >= 1
    
    def test_extract_skills_case_insensitive(self, parser):
        """Test case-insensitive extraction"""
        text1 = "python and java"
        text2 = "PYTHON and JAVA"
        
        skills1 = parser.extract_skills(text1)
        skills2 = parser.extract_skills(text2)
        
        assert len(skills1) == len(skills2)

# ============================================================
# ONTOLOGY MAPPER TESTS
# ============================================================

class TestSkillOntologyMapper:
    """Tests for skill ontology mapping"""
    
    def test_mapper_initializes(self, mapper):
        """Test mapper initializes correctly"""
        assert mapper is not None
        assert len(mapper.raw_to_standard) > 0
    
    def test_exact_match(self, mapper):
        """Test exact skill mapping"""
        standard, match_type, confidence = mapper.map_skill('python')
        
        assert standard == 'Python'
        assert match_type == 'exact'
        assert confidence == 1.0
    
    def test_alias_mapping(self, mapper):
        """Test alias mapping"""
        standard, match_type, confidence = mapper.map_skill('py')
        
        assert standard == 'Python'
        assert match_type in ['exact', 'fuzzy']
    
    def test_fuzzy_matching(self, mapper):
        """Test fuzzy matching with typos"""
        standard, match_type, confidence = mapper.map_skill('pythno')
        
        assert standard is not None  # Should match despite typo
        assert match_type == 'fuzzy'
    
    def test_case_insensitive_mapping(self, mapper):
        """Test case-insensitive mapping"""
        standard1, _, _ = mapper.map_skill('python')
        standard2, _, _ = mapper.map_skill('PYTHON')
        
        assert standard1 == standard2
    
    def test_unmapped_skill(self, mapper):
        """Test handling of unmapped skills"""
        standard, match_type, confidence = mapper.map_skill('obscureskill123')
        
        assert standard is None
        assert match_type == 'unmapped'

# ============================================================
# JOB MATCHING TESTS
# ============================================================

class TestJobMatcher:
    """Tests for job-resume matching"""
    
    def test_matcher_initializes(self, matcher):
        """Test matcher initializes correctly"""
        assert matcher is not None
    
    def test_match_score_range(self, matcher):
        """Test that match scores are between 0 and 1"""
        resume_skills = ['Python', 'SQL', 'AWS']
        jd_skills = ['Python', 'Java', 'SQL']
        
        score, _, _ = matcher.compute_match_score(resume_skills, jd_skills)
        
        assert 0 <= score <= 1
    
    def test_match_perfect_overlap(self, matcher):
        """Test perfect skill overlap"""
        resume_skills = ['Python', 'SQL', 'AWS']
        jd_skills = ['Python', 'SQL', 'AWS']
        
        score, matched, missing = matcher.compute_match_score(resume_skills, jd_skills)
        
        assert score == 1.0
        assert len(matched) == 3
        assert len(missing) == 0
    
    def test_match_no_overlap(self, matcher):
        """Test no skill overlap"""
        resume_skills = ['Python', 'SQL']
        jd_skills = ['Java', 'C++']
        
        score, matched, missing = matcher.compute_match_score(resume_skills, jd_skills)
        
        assert score == 0.0
        assert len(matched) == 0
        assert len(missing) == 2
    
    def test_match_partial_overlap(self, matcher):
        """Test partial skill overlap"""
        resume_skills = ['Python', 'SQL', 'AWS']
        jd_skills = ['Python', 'Java', 'SQL', 'Docker']
        
        score, matched, missing = matcher.compute_match_score(resume_skills, jd_skills)
        
        assert 0 < score < 1
        assert len(matched) == 2  # Python and SQL
        assert len(missing) == 2  # Java and Docker
    
    def test_match_explanation_generated(self, matcher):
        """Test that match includes explanation"""
        sample_resume = "I know Python and SQL"
        sample_jd = "We need Python and Java"
        
        result = matcher.match(sample_resume, sample_jd)
        
        assert 'explanation' in result
        assert len(result['explanation']) > 0
        assert result['score'] >= 0

# ============================================================
# PROCTORING CLASSIFIER TESTS
# ============================================================

class TestProctoringClassifier:
    """Tests for assessment proctoring"""
    
    def test_classifier_initializes(self, classifier):
        """Test classifier initializes correctly"""
        assert classifier is not None
        assert len(classifier.classes) == 3
    
    def test_classify_safe_session(self, classifier):
        """Test classification of clean session"""
        features = {
            'assessment_duration_min': 60,
            'tab_switches': 0,
            'face_detections': 60,
            'external_audio_detected': 0,
            'copy_paste_events': 0,
            'keystroke_velocity_variance': 1.0,
            'mouse_speed_anomaly': 0
        }
        
        result = classifier.classify(features)
        
        assert result['classification'] in classifier.classes
        assert result['confidence'] > 0
        assert len(result['reasons']) > 0
    
    def test_classify_flagged_session(self, classifier):
        """Test classification of suspicious session"""
        features = {
            'assessment_duration_min': 10,
            'tab_switches': 20,
            'face_detections': 0,
            'external_audio_detected': 5,
            'copy_paste_events': 10,
            'keystroke_velocity_variance': 2.5,
            'mouse_speed_anomaly': 1
        }
        
        result = classifier.classify(features)
        
        assert result['classification'] in classifier.classes
        assert result['confidence'] > 0
        assert len(result['reasons']) > 0
    
    def test_classification_consistency(self, classifier):
        """Test that same features produce same classification"""
        features = {
            'assessment_duration_min': 45,
            'tab_switches': 2,
            'face_detections': 45,
            'external_audio_detected': 0,
            'copy_paste_events': 0,
            'keystroke_velocity_variance': 0.95,
            'mouse_speed_anomaly': 0
        }
        
        result1 = classifier.classify(features)
        result2 = classifier.classify(features)
        
        assert result1['classification'] == result2['classification']

# ============================================================
# END-TO-END TESTS
# ============================================================

class TestEndToEnd:
    """Tests for complete pipeline"""
    
    def test_pipeline_with_sample_resume(self, parser, matcher):
        """Test pipeline with sample resume"""
        resume_text = """
        Senior Software Engineer
        Skills: Python, JavaScript, AWS, Docker, PostgreSQL
        Experience: 5 years in full-stack development
        """
        
        jd_text = """
        Senior Backend Engineer
        Required: Python, Docker, PostgreSQL, Kubernetes
        """
        
        # Parse
        resume_skills = parser.extract_skills(resume_text)
        assert len(resume_skills) > 0
        
        # Match
        result = matcher.match(resume_text, jd_text)
        assert result['score'] >= 0
        assert result['score'] <= 1
    
    def test_pipeline_data_files_exist(self):
        """Test that required data files exist"""
        assert (DATA_DIR / "ontology.csv").exists()
        assert (DATA_DIR / "eval" / "parser_labeled_pairs.csv").exists()
        assert (DATA_DIR / "eval" / "proctoring_sessions.csv").exists()
    
    def test_pipeline_models_exist(self):
        """Test that trained models exist"""
        assert (MODELS_DIR / "proctoring_model.pkl").exists()
        assert (MODELS_DIR / "matching_model.pkl").exists()

# ============================================================
# METRICS TESTS
# ============================================================

class TestMetrics:
    """Tests for metrics and evaluation"""
    
    def test_parser_evaluation_data_exists(self):
        """Test that parser evaluation data is available"""
        parser_pairs = pd.read_csv(DATA_DIR / "eval" / "parser_labeled_pairs.csv")
        
        assert len(parser_pairs) > 0
        assert 'raw_text' in parser_pairs.columns
        assert 'expected_standard' in parser_pairs.columns
    
    def test_proctoring_evaluation_data_exists(self):
        """Test that proctoring evaluation data is available"""
        proctoring_df = pd.read_csv(DATA_DIR / "eval" / "proctoring_sessions.csv")
        
        assert len(proctoring_df) > 0
        assert 'predicted_label' in proctoring_df.columns
        assert 'split' in proctoring_df.columns
    
    def test_evaluation_data_splits(self):
        """Test that evaluation data has proper train/val/test splits"""
        proctoring_df = pd.read_csv(DATA_DIR / "eval" / "proctoring_sessions.csv")
        
        splits = proctoring_df['split'].unique()
        assert 'train' in splits
        assert 'val' in splits
        assert 'test' in splits

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
