"""
mapper.py
---------
This is the actual "Parsing into ontology" piece for Task 14.

Takes whatever the resume/JD parser (Task 12) spits out and converts each
raw skill string into a standardized skill from data/ontology.csv.

Two lookup strategies are used, in order:
  1. exact / normalized match  -> alias found (after lowercasing, stripping
     punctuation, collapsing whitespace) directly in the ontology
  2. fuzzy match               -> nothing exact, so we fall back to
     difflib to see if it's a near-miss (typos, minor wording differences)

If neither works the skill is passed through unchanged and flagged as
"unmapped" so a human can add it to the ontology later instead of silently
losing it.

Every mapping returned includes a `method` and a short `reason` so the
system stays explainable (see Section 4 of the study guide - that was a
hard requirement, not a nice-to-have).
"""

import csv
import difflib
import re
from pathlib import Path

DEFAULT_ONTOLOGY_PATH = Path(__file__).resolve().parent.parent / "data" / "ontology.csv"

# Below this similarity score we don't trust a fuzzy match enough to auto-map it.
FUZZY_THRESHOLD = 0.82


def normalize(text):
    """Lowercase, strip punctuation/extra spaces so 'Power-BI' and 'Power BI'
    end up looking the same. Keeps letters, digits, +, # and . (so C++, C#,
    Node.js etc don't get mangled)."""
    text = text.strip().lower()
    text = re.sub(r"[_/-]", " ", text)
    text = re.sub(r"[^a-z0-9+#. ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class SkillOntologyMapper:
    def __init__(self, ontology_path=None, fuzzy_threshold=FUZZY_THRESHOLD, use_fuzzy=True):
        self.ontology_path = Path(ontology_path) if ontology_path else DEFAULT_ONTOLOGY_PATH
        self.fuzzy_threshold = fuzzy_threshold
        self.use_fuzzy = use_fuzzy

        # normalized_alias -> standard skill name
        self.alias_lookup = {}
        # normalized_alias -> category (just for reporting, not used in matching)
        self.category_lookup = {}
        # the set of all standard skill names, used for fuzzy fallback
        self.standard_skills = set()

        self._load_ontology()

    def _load_ontology(self):
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Ontology file not found at {self.ontology_path}")

        with open(self.ontology_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                alias = row["alias"].strip()
                standard = row["standard_skill"].strip()
                category = row.get("category", "").strip()

                norm_alias = normalize(alias)
                self.alias_lookup[norm_alias] = standard
                self.category_lookup[norm_alias] = category
                self.standard_skills.add(standard)

    def reload(self):
        """Handy if the ontology CSV gets edited while the app is running."""
        self.alias_lookup.clear()
        self.category_lookup.clear()
        self.standard_skills.clear()
        self._load_ontology()

    def _fuzzy_lookup(self, norm_skill):
        """Try to find the closest known alias using sequence matching.
        Returns (standard_skill, score) or (None, 0) if nothing is close enough."""
        candidates = difflib.get_close_matches(
            norm_skill, self.alias_lookup.keys(), n=1, cutoff=self.fuzzy_threshold
        )
        if not candidates:
            return None, 0.0
        best = candidates[0]
        score = difflib.SequenceMatcher(None, norm_skill, best).ratio()
        return self.alias_lookup[best], score

    def map_skill(self, raw_skill):
        """Map a single raw skill string to its standardized form.

        Returns a dict:
            original      - the raw string exactly as it came in
            standard      - the standardized skill (falls back to the
                             original, title-cased, if nothing matched)
            method         - 'exact' | 'fuzzy' | 'unmapped'
            confidence     - 1.0 for exact, similarity score for fuzzy, 0 for unmapped
            reason         - plain English explanation (see Step 7 of the guide)
        """
        if raw_skill is None or not str(raw_skill).strip():
            return None

        raw_skill = str(raw_skill).strip()
        norm = normalize(raw_skill)

        # 1. exact / normalized match
        if norm in self.alias_lookup:
            standard = self.alias_lookup[norm]
            return {
                "original": raw_skill,
                "standard": standard,
                "method": "exact",
                "confidence": 1.0,
                "reason": f"'{raw_skill}' is a known alias for '{standard}' in the ontology.",
            }

        # 2. fuzzy fallback
        if self.use_fuzzy:
            fuzzy_standard, score = self._fuzzy_lookup(norm)
            if fuzzy_standard:
                return {
                    "original": raw_skill,
                    "standard": fuzzy_standard,
                    "method": "fuzzy",
                    "confidence": round(score, 3),
                    "reason": (
                        f"'{raw_skill}' closely matched an existing ontology alias "
                        f"for '{fuzzy_standard}' (similarity {score:.2f}), likely a "
                        f"typo or minor wording difference."
                    ),
                }

        # 3. nothing found - pass through, flagged, don't silently drop it
        fallback = raw_skill.strip().title()
        return {
            "original": raw_skill,
            "standard": fallback,
            "method": "unmapped",
            "confidence": 0.0,
            "reason": (
                f"No ontology entry matched '{raw_skill}'. Kept as-is so it isn't "
                f"silently dropped - consider adding it to ontology.csv."
            ),
        }

    def map_skill_list(self, raw_skills):
        """Map a list of raw skills, de-duping the standardized output while
        keeping the individual explanations for every original string."""
        mappings = []
        seen_standard = []
        for skill in raw_skills:
            mapped = self.map_skill(skill)
            if mapped is None:
                continue
            mappings.append(mapped)
            if mapped["standard"] not in seen_standard:
                seen_standard.append(mapped["standard"])

        return {
            "original_skills": [m["original"] for m in mappings],
            "standard_skills": seen_standard,
            "mappings": mappings,
        }

    def is_known_skill(self, raw_skill):
        """True if the skill exactly or fuzzily resolves to something in the
        ontology (used by evaluate.py to score precision/recall)."""
        norm = normalize(raw_skill)
        if norm in self.alias_lookup:
            return True
        if self.use_fuzzy:
            match, _ = self._fuzzy_lookup(norm)
            return match is not None
        return False


if __name__ == "__main__":
    # quick manual smoke test - run `python mapper.py`
    mapper = SkillOntologyMapper()
    sample = ["Py", "ML", "Power BI", "Structured Query Language", "Machinee Learning", "Photoshop"]
    for skill in sample:
        result = mapper.map_skill(skill)
        print(f"{skill!r:35} -> {result['standard']:20} ({result['method']}, conf={result['confidence']})")
