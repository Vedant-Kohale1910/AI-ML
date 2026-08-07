# Data-Subject Rights — Task 23

## Right of Access (DPDP §12)

Fields in feature store: ['experience_summary', 'certifications', 'assessment_score', 'education', 'verified_skills', 'years_experience']
PII in feature store: [] (empty = compliant)

## Right to Delete (DPDP §17)

Feature store deleted immediately: True
Data store: within 90 days
Model note: Trained model reco-v2.0 was trained on this subject's features. Their influence cannot be removed without full retraining. Next scheduled retraining will exclude this subject. This is compliant with DPDP §17 and GDPR Recital 26 documented retention window.

## Automated-decision disclosure (DPDP §16)

Human review ticket: HRV-0002-0001
Reviewer: compliance-team@placemux.com
SLA: 5 business days
