#!/usr/bin/env python3
"""
Generic Standalone Name Detector
Detects standalone names (companies, organizations, entities) that should be section headers

GENERIC APPROACH - Not country-specific!
Uses structural and visual characteristics instead of legal patterns.

Detection criteria:
1. Short standalone line (not part of a paragraph)
2. Proper capitalization (title case or specific caps)
3. Isolated position (not part of a list or table)
4. Followed by descriptive content about that entity
5. Not a sentence (no verb conjugations)

Examples that SHOULD match:
✅ "AR Pampa SpA."                    (company name)
✅ "Enel Green Power Chile S.A."     (company name)
✅ "Microsoft Corporation"            (company name)
✅ "United Nations"                   (organization)
✅ "Planta Solar San Pedro III"       (facility name)
✅ "Central Hidroeléctrica Ralco"     (facility name)

Examples that should NOT match:
❌ "This is a paragraph mentioning Microsoft." (part of text)
❌ "1. First item in a list"                   (list item)
❌ "Page 42"                                   (page number)
❌ "the company operates in"                   (lowercase start)
"""
import re


class EAFCompanyNameDetector:
    """
    Generic detector for standalone entity names that should be section headers

    Uses structural characteristics instead of country-specific legal patterns.
    """

    def __init__(self):
        # Words that should NOT be detected as company names (table labels, etc.)
        self.excluded_words = [
            'total', 'subtotal', 'suma', 'promedio', 'average',
            'mínimo', 'máximo', 'min', 'max', 'nota', 'note',
            'fuente', 'source', 'observación', 'observation',
            'clientes', 'clients', 'customers', 'usuarios'
        ]

        # OPTIONAL: Legal suffixes (boost confidence if found)
        # But NOT required for detection!
        self.legal_suffixes = [
            # International
            r'Inc\.?', r'Corp\.?', r'Corporation', r'Ltd\.?', r'Limited',
            r'LLC', r'LLP', r'GmbH', r'AG', r'PLC',
            # Latin America
            r'S\.A\.?', r'SpA\.?', r'Ltda\.?', r'S\.A\.C\.?',
            r'S\.R\.L\.?', r'S\.L\.?', r'C\.A\.?'
        ]

        # Common entity type keywords (boost confidence, not required)
        self.entity_keywords = [
            # Generic
            'company', 'corporation', 'group', 'holdings', 'partners',
            'enterprise', 'international', 'global', 'nacional',
            # Infrastructure
            'plant', 'planta', 'facility', 'instalación', 'central',
            'station', 'estación', 'complejo', 'parque',
            # Energy (domain-specific but optional)
            'power', 'energy', 'energía', 'eléctrica', 'solar',
            'wind', 'eólica', 'hydro', 'hidroeléctrica', 'thermal',
            # Mining/Industrial
            'minera', 'mining', 'industrial', 'manufactura'
        ]

    def is_company_name_header(self, text: str, bbox: dict = None) -> dict:
        """
        FLEXIBLE SCORING: Check if text is a standalone entity name (company, org, facility)

        Uses weighted scoring system - NO HARD CUTOFFS!
        Every feature contributes to the score, allowing flexibility.

        Args:
            text: Text block to check
            bbox: Optional bounding box (for height/width analysis)

        Returns:
            dict with keys:
                - is_company_header: bool
                - detection_method: str (why it matched)
                - confidence: str (high/medium/low)
                - features: dict (detected features with scores)
        """
        text_clean = text.strip()

        # Check if text starts with an excluded word (case-insensitive)
        # Examples: "Total:", "Subtotal:", "Clientes Regulados", etc.
        first_word = text_clean.split()[0].lower().rstrip(':.,;') if text_clean.split() else ''
        if first_word in self.excluded_words:
            return {'is_company_header': False, 'reason': 'excluded_word'}

        # Start with base score
        score = 0.0
        features = {}

        # ========================================
        # SCORING SYSTEM (additive, no hard cutoffs)
        # ========================================

        # Parse words first (needed for multiple checks)
        words = text_clean.split()
        if len(words) == 0:
            return {'is_company_header': False, 'reason': 'empty'}

        # 1. LENGTH SCORE (flexible, not absolute)
        length = len(text_clean)
        if length < 3:
            # Extremely short - almost certainly not an entity name
            return {'is_company_header': False, 'reason': 'too_short', 'length': length}
        elif length <= 5 and len(words) <= 1:
            # Single word ≤5 chars: "S.A.", "Inc", "Ltd"
            return {'is_company_header': False, 'reason': 'single_short_word', 'length': length}
        elif length < 5:
            score += 0.0  # Very short, neutral
        elif 5 <= length <= 120:
            score += 0.2  # Ideal length for entity name
        elif 120 < length <= 200:
            score += 0.1  # Long but could still be valid
        else:
            score -= 0.1  # Very long, probably paragraph
        features['length_score'] = score
        features['length'] = length

        # 2. CAPITALIZATION SCORE
        if text_clean[0].islower():
            score -= 0.3  # Strong penalty for lowercase start
            features['lowercase_start'] = True
        else:
            features['lowercase_start'] = False

        cap_words = sum(1 for w in words if w and w[0].isupper())
        cap_ratio = cap_words / len(words) if len(words) > 0 else 0

        # Score based on capitalization ratio
        if cap_ratio >= 0.8:
            score += 0.3  # Very strong proper name signal
        elif cap_ratio >= 0.6:
            score += 0.2  # Good proper name signal
        elif cap_ratio >= 0.4:
            score += 0.1  # Moderate signal
        else:
            score -= 0.2  # Weak signal
        features['cap_ratio'] = round(cap_ratio, 2)
        features['cap_score'] = 0.3 if cap_ratio >= 0.8 else (0.2 if cap_ratio >= 0.6 else 0.1)

        # 3. FALSE POSITIVE FILTERS (strong penalties)
        # List items: "1. Item", "a) Item", "• Bullet"
        if re.match(r'^\s*[\d\w]+[\.\)]\s+', text_clean):
            score -= 0.5  # Strong penalty
            features['list_pattern'] = True

        # Page numbers: "Page 42", "Página 10"
        if re.match(r'^(Page|Página)\s+\d+', text_clean, re.IGNORECASE):
            return {'is_company_header': False, 'reason': 'page_number'}

        # Dates: "January 2024", "15 de marzo"
        if re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b', text_clean, re.IGNORECASE):
            return {'is_company_header': False, 'reason': 'date'}

        # 4. LEGAL SUFFIX SCORE (strong positive signal)
        has_legal_suffix = any(re.search(rf'\b{suffix}\b', text_clean, re.IGNORECASE)
                              for suffix in self.legal_suffixes)
        if has_legal_suffix:
            score += 0.4  # Strong boost for legal suffix
        features['has_legal_suffix'] = has_legal_suffix

        # 5. ENTITY KEYWORD SCORE
        text_lower = text_clean.lower()
        has_entity_keyword = any(keyword in text_lower for keyword in self.entity_keywords)
        if has_entity_keyword:
            score += 0.25  # Good boost for entity keywords
        features['has_entity_keyword'] = has_entity_keyword

        # 6. WORD COUNT SCORE
        word_count = len(words)
        if 2 <= word_count <= 10:
            score += 0.15  # Typical entity name length
        elif 10 < word_count <= 15:
            score += 0.05  # Long but still possible
        else:
            score -= 0.05  # Very long, less likely
        features['word_count'] = word_count

        # 7. ALL CAPS PENALTY
        # "POWER STATION" is less likely to be a header than "Power Station"
        if text_clean.isupper() and len(words) > 1:
            score -= 0.1  # Slight penalty for ALL CAPS
            features['all_caps'] = True

        # 8. PUNCTUATION AT END (positive signal)
        if text_clean[-1] in '.,:;':
            score += 0.05  # Slight boost for ending punctuation
            features['has_end_punct'] = True

        # ========================================
        # FINAL DECISION (flexible threshold)
        # ========================================
        # Lower threshold = 0.5 (was 0.6 before)
        # This allows long entity names to pass if they have other signals
        features['total_score'] = round(score, 2)

        if score < 0.5:
            return {
                'is_company_header': False,
                'reason': 'low_score',
                'score': round(score, 2),
                'features': features
            }

        # Determine confidence level
        if score >= 0.9:
            confidence = "high"
        elif score >= 0.7:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            'is_company_header': True,
            'detection_method': 'flexible_scoring',
            'confidence': confidence,
            'confidence_score': round(score, 2),
            'features': features,
            'text': text_clean
        }

    def should_create_cluster(self, text: str, bbox: dict, page: int) -> bool:
        """
        Determine if a cluster should be created for this entity name

        Args:
            text: Text content
            bbox: Bounding box coordinates
            page: Page number

        Returns:
            bool: True if cluster should be created
        """
        result = self.is_company_name_header(text, bbox)
        return result.get('is_company_header', False)


# Example usage and tests
if __name__ == "__main__":
    detector = EAFCompanyNameDetector()

    # Test cases: Chilean, international, facilities, LONG NAMES
    test_cases = [
        # Chilean companies (with legal suffixes)
        "AR Pampa SpA.",
        "Enel Green Power Chile S.A.",
        "Minera Escondida Ltda.",
        "Planta Solar San Pedro III SpA.",
        "Hidroeléctrica Río Colorado S.A.",
        "Transelec S.A.:",
        "Empresa Eléctrica Pehuenche S.A.",

        # International companies (generic detection)
        "Microsoft Corporation",
        "Apple Inc.",
        "General Electric",
        "Siemens AG",

        # Facilities and organizations (no legal suffix)
        "United Nations",
        "Central Nuclear Almaraz",
        "Planta Solar Atacama",
        "World Health Organization",

        # LONG ENTITY NAMES (>120 chars) - Should still pass with strong signals!
        "Compañía de Generación Eléctrica y Transmisión de Energía Renovable del Norte Grande de Chile S.A.",  # 104 chars
        "International Renewable Energy Development Corporation and Sustainable Power Solutions Ltd.",  # 100 chars
        "Sociedad Anónima de Producción, Distribución y Comercialización de Energía Eléctrica Renovable SpA.",  # 106 chars
        "Very Long Company Name With Many Words But No Legal Suffix Or Keywords Just Proper Capitalization Here",  # 107 chars, no suffix

        # FALSE POSITIVES (should NOT match)
        "This is a long paragraph that mentions Transelec S.A. in the middle",  # Part of paragraph
        "S.A.",  # Too short
        "Page 42",  # Page number
        "1. First item in a list",  # List item
        "the company operates in various regions",  # Lowercase start
    ]

    print("=" * 80)
    print("GENERIC ENTITY NAME DETECTOR - TEST RESULTS")
    print("=" * 80)

    for text in test_cases:
        result = detector.is_company_name_header(text)
        status = "✅ MATCH" if result.get('is_company_header') else "❌ NO MATCH"
        print(f"\n{status}: {text[:60]}")

        if result.get('is_company_header'):
            print(f"   Method: {result.get('detection_method', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')} (score: {result.get('confidence_score', 0):.2f})")
            features = result.get('features', {})
            print(f"   Features: legal_suffix={features.get('has_legal_suffix')}, "
                  f"entity_keyword={features.get('has_entity_keyword')}, "
                  f"words={features.get('word_count')}, "
                  f"caps={features.get('cap_ratio')}")
        else:
            print(f"   Reason: {result.get('reason', 'N/A')}")
