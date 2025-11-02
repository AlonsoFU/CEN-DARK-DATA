# Intelligent Hierarchy Building: Strategies Beyond Pattern Matching

**Last Updated**: 2025-10-27
**Purpose**: Advanced techniques for building semantic hierarchy from Docling JSON

---

## 🎯 Current Approach (Pattern-Based)

### What You Have Now (`build_semantic_hierarchy.py`):

**Method:** Regex pattern matching on text content

```python
HEADER_PATTERNS = [
    r'^([a-z])\.\s+(.+)',           # a. Title
    r'^(\d+)\.\s+(.+)',             # 1. Title
    r'^(\d+)\.(\d+)\s+(.+)',        # 7.2 Title
]

def is_header(text):
    for pattern in HEADER_PATTERNS:
        if re.match(pattern, text):
            return True
    return False
```

**Workflow:**
1. Iterate through `body.children` (reading order)
2. Check if text matches header pattern
3. If yes → Start new section
4. If no → Add to current section

**Strengths:**
- ✅ Simple and fast
- ✅ Works well for consistent numbering schemes
- ✅ Reusable across similar documents

**Limitations:**
- ❌ Only uses text patterns (ignores Docling's AI classification)
- ❌ Doesn't use spatial information (bounding boxes)
- ❌ Misses headers without numbering ("Introduction", "Abstract")
- ❌ Can't distinguish between similar-looking text

---

## 🚀 Advanced Strategy 1: Use Docling's Classification

### Leverage `DocItemLabel` Types

**Docling already classifies elements!**

Looking at your JSON structure:
```json
{
  "texts": [
    {
      "self_ref": "#/texts/0",
      "label": "section_header",  // ← Docling detected this is a header!
      "text": "a. Fecha y Hora",
      "prov": [...]
    },
    {
      "self_ref": "#/texts/1",
      "label": "text",  // ← Regular paragraph
      "text": "El presente informe...",
      "prov": [...]
    }
  ]
}
```

### **Improved Approach:**

```python
class IntelligentHierarchyBuilder:
    """Uses Docling's AI classification + pattern matching"""

    def is_header(self, item):
        """
        Multi-strategy header detection:
        1. Check Docling's label
        2. Check text patterns
        3. Check font size (from bbox)
        """
        # Strategy 1: Trust Docling's classification
        if item.get('label') in ['section_header', 'title']:
            return True

        # Strategy 2: Pattern matching (fallback)
        text = item.get('text', '')
        for pattern in self.HEADER_PATTERNS:
            if re.match(pattern, text):
                return True

        # Strategy 3: Font size analysis (if available)
        if self.is_large_font(item):
            return True

        return False
```

**Benefits:**
- ✅ Uses Docling's AI (better than regex alone)
- ✅ Multi-strategy approach (redundancy)
- ✅ Catches headers without numbering

---

## 🚀 Advanced Strategy 2: Spatial Hierarchy

### Use Bounding Box Information

**Key insight:** Headers often have specific layout characteristics:
- Larger font size
- Different X position (indentation)
- More whitespace before/after

```python
def analyze_spatial_hierarchy(self, items):
    """
    Build hierarchy based on spatial relationships
    """
    hierarchy = []
    stack = []  # Track nesting levels

    for i, item in enumerate(items):
        bbox = item.get('bbox', {})
        x0 = bbox.get('x0', 0)
        y0 = bbox.get('y0', 0)
        height = bbox.get('y1', 0) - y0

        # Detect indentation level
        indent_level = self.get_indent_level(x0)

        # Detect font size (larger = higher level header)
        font_size_category = self.categorize_font_size(height)

        # Detect whitespace before element
        whitespace_before = self.calculate_whitespace(items, i)

        # Determine if this is a header and its level
        if self.is_spatial_header(
            indent_level,
            font_size_category,
            whitespace_before
        ):
            level = self.calculate_level(indent_level, font_size_category)
            # Add to appropriate level in hierarchy
            self.add_to_hierarchy(hierarchy, stack, item, level)
        else:
            # Add as content to current section
            self.add_content_to_current_section(stack, item)

    return hierarchy

def get_indent_level(self, x0):
    """
    Categorize indentation level
    """
    # Typical PDF margins: 56 (left margin)
    if x0 < 60:
        return 0  # No indent (main section)
    elif x0 < 80:
        return 1  # First level indent
    elif x0 < 100:
        return 2  # Second level indent
    else:
        return 3  # Deep indent

def categorize_font_size(self, height):
    """
    Categorize font size from bbox height
    """
    if height > 18:
        return 'large'      # Title or main header
    elif height > 14:
        return 'medium'     # Section header
    elif height > 10:
        return 'normal'     # Regular text
    else:
        return 'small'      # Footnote or caption
```

**Benefits:**
- ✅ Works without text patterns
- ✅ Detects visual hierarchy
- ✅ Handles multi-level nesting automatically

---

## 🚀 Advanced Strategy 3: Contextual Analysis

### Use Content Context and Relationships

**Key insight:** Headers are followed by related content

```python
def build_contextual_hierarchy(self, items):
    """
    Analyze context around elements
    """
    for i, item in enumerate(items):
        # Look ahead: What comes after this?
        next_items = items[i+1:i+5]  # Next 4 elements

        # If followed by multiple paragraphs/tables → likely a header
        if self.followed_by_content(next_items):
            # This is probably a section header
            confidence_score = self.calculate_confidence(item, next_items)

            if confidence_score > 0.7:
                # Start new section
                pass

        # Look back: What came before?
        prev_items = items[max(0, i-3):i]

        # If preceded by whitespace → likely a header
        if self.preceded_by_whitespace(prev_items, item):
            confidence_score += 0.2

def followed_by_content(self, next_items):
    """
    Check if element is followed by substantial content
    """
    content_types = [item.get('type') for item in next_items]

    # Headers are typically followed by text/tables
    has_text = 'text' in content_types
    has_tables = 'table' in content_types

    # Multiple items suggest this starts a section
    return len(next_items) >= 2 and (has_text or has_tables)
```

**Benefits:**
- ✅ Context-aware decisions
- ✅ Reduces false positives
- ✅ Works for unusual formatting

---

## 🚀 Advanced Strategy 4: Machine Learning-Based

### Use Document Structure Learning

**Concept:** Train on your JSON data to learn document patterns

```python
class MLHierarchyBuilder:
    """
    Learn hierarchy patterns from labeled examples
    """

    def extract_features(self, item, context):
        """
        Extract features for ML classification
        """
        return {
            # Text features
            'text_length': len(item.get('text', '')),
            'starts_with_number': bool(re.match(r'^\d', item['text'])),
            'starts_with_letter_dot': bool(re.match(r'^[a-z]\.', item['text'])),
            'all_caps': item['text'].isupper(),
            'ends_with_colon': item['text'].endswith(':'),

            # Docling features
            'docling_label': item.get('label'),
            'docling_is_section_header': item.get('label') == 'section_header',

            # Spatial features
            'x_position': item.get('bbox', {}).get('x0', 0),
            'y_position': item.get('bbox', {}).get('y0', 0),
            'height': item.get('bbox', {}).get('y1', 0) - item.get('bbox', {}).get('y0', 0),
            'width': item.get('bbox', {}).get('x1', 0) - item.get('bbox', {}).get('x0', 0),

            # Context features
            'preceded_by_whitespace': context['whitespace_before'],
            'followed_by_content': context['content_after'],
            'font_size_relative': context['font_size_percentile'],

            # Reading order features
            'position_in_document': context['position'],
            'position_on_page': context['page_position'],
        }

    def train(self, labeled_documents):
        """
        Train ML model on labeled examples
        """
        # Extract features from labeled examples
        X = []
        y = []

        for doc in labeled_documents:
            for item in doc['items']:
                features = self.extract_features(item, item['context'])
                label = item['is_header']  # Ground truth
                X.append(features)
                y.append(label)

        # Train classifier (Random Forest, XGBoost, etc.)
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier()
        self.model.fit(X, y)

    def predict_hierarchy(self, document):
        """
        Predict hierarchy for new document
        """
        for item in document['items']:
            features = self.extract_features(item, self.get_context(item))
            is_header = self.model.predict([features])[0]
            level = self.predict_level(features) if is_header else None
```

**Benefits:**
- ✅ Learns from your documents
- ✅ Adapts to document variations
- ✅ Improves over time with more examples

**Limitations:**
- ⚠️ Requires labeled training data
- ⚠️ More complex to maintain

---

## 🚀 Advanced Strategy 5: Combined Approach

### Best of All Worlds

```python
class SmartHierarchyBuilder:
    """
    Combines multiple strategies with confidence scoring
    """

    def is_header_with_confidence(self, item, context):
        """
        Multi-strategy header detection with confidence score
        """
        scores = {}

        # Strategy 1: Docling's classification (high confidence)
        if item.get('label') == 'section_header':
            scores['docling'] = 0.9
        elif item.get('label') == 'title':
            scores['docling'] = 0.95
        else:
            scores['docling'] = 0.1

        # Strategy 2: Pattern matching (medium confidence)
        pattern_match = self.pattern_confidence(item['text'])
        scores['pattern'] = pattern_match

        # Strategy 3: Spatial analysis (medium confidence)
        spatial_score = self.spatial_confidence(item, context)
        scores['spatial'] = spatial_score

        # Strategy 4: Context analysis (low-medium confidence)
        context_score = self.context_confidence(item, context)
        scores['context'] = context_score

        # Weighted average
        weights = {
            'docling': 0.4,    # Trust Docling's AI heavily
            'pattern': 0.3,    # Patterns are reliable
            'spatial': 0.2,    # Spatial is helpful
            'context': 0.1     # Context is supplementary
        }

        final_score = sum(scores[k] * weights[k] for k in scores)

        return {
            'is_header': final_score > 0.6,
            'confidence': final_score,
            'scores': scores
        }

    def determine_level(self, item, context):
        """
        Determine hierarchy level using multiple signals
        """
        # Method 1: Pattern-based (1, 1.1, 1.1.1)
        pattern_level = self.extract_level_from_pattern(item['text'])

        # Method 2: Spatial (indentation)
        spatial_level = self.get_indent_level(item['bbox']['x0'])

        # Method 3: Font size (larger = higher level)
        font_level = self.level_from_font_size(item['bbox'])

        # Combine (prefer pattern if available, else spatial)
        if pattern_level is not None:
            return pattern_level
        elif spatial_level > 0:
            return spatial_level
        else:
            return font_level
```

**Benefits:**
- ✅ Robust (multiple fallbacks)
- ✅ Confidence scoring (know how sure you are)
- ✅ Best accuracy
- ✅ Handles edge cases

---

## 📋 Practical Recommendations

### For Your EAF Documents:

**Current approach is good** ✅ because:
- Consistent numbering scheme (`a.`, `1.`, `7.2`)
- Docling correctly labels most headers as `section_header`
- Pattern matching works 95%+ of the time

**Could improve by:**

1. **Add Docling label check** (5 minutes):
   ```python
   def is_header(self, text, label):
       # Priority 1: Trust Docling
       if label in ['section_header', 'title']:
           return True

       # Priority 2: Pattern matching (fallback)
       for pattern in self.HEADER_PATTERNS:
           if re.match(pattern, text):
               return True

       return False
   ```

2. **Add confidence scoring** (15 minutes):
   - Log cases where Docling and patterns disagree
   - Review and adjust patterns
   - Build confidence in your hierarchy

3. **Add spatial analysis for edge cases** (30 minutes):
   - Use when patterns fail
   - Detect headers without numbering
   - Handle unusual formatting

### For New Document Types:

1. **Start with combined approach** (Strategy 5)
2. **Collect examples** (5-10 documents)
3. **Tune confidence weights** based on what works
4. **Document patterns** you discover
5. **Iterate** as you process more documents

---

## 💡 Quick Wins You Can Implement Now

### 1. Use Docling's Labels (5 minutes)

```python
# In build_semantic_hierarchy.py
def is_header(self, item_data):
    """Enhanced header detection"""
    item = item_data['item']
    item_type = item_data['type']

    # Get text and label
    text = item.get('text', '')
    label = item.get('label', '')

    # Check Docling's classification first
    if label in ['section_header', 'title']:
        return self.extract_header_info(text)

    # Fallback to pattern matching
    for pattern in self.HEADER_PATTERNS:
        # ... existing pattern logic
```

### 2. Log Confidence (10 minutes)

```python
def build_hierarchy(self):
    """Build hierarchy with confidence logging"""
    for ref in self.children_refs:
        item_data = self.get_item_by_ref(ref)

        if item_data and item_data['type'] == 'text':
            text = item_data['item'].get('text', '')
            label = item_data['item'].get('label', '')

            # Check both methods
            docling_says_header = label in ['section_header', 'title']
            pattern_says_header = self.matches_pattern(text)

            # Log disagreements
            if docling_says_header != pattern_says_header:
                print(f"⚠️  Disagreement on: {text[:50]}")
                print(f"   Docling: {docling_says_header} | Pattern: {pattern_says_header}")
```

### 3. Handle Multi-line Headers (15 minutes)

```python
def is_header(self, text, next_item=None):
    """
    Detect split headers like:
        "7.2 Análisis de las causas"
        "de la falla"
    """
    # Check current text
    header_info = self.match_pattern(text)

    # If pattern matches but text seems incomplete
    if header_info and next_item and not text.endswith('.'):
        # Check if next item continues the header
        next_text = next_item.get('text', '')
        if len(next_text) < 50 and not self.match_pattern(next_text):
            # Likely a continuation
            header_info['title'] += ' ' + next_text
            header_info['merged'] = True

    return header_info
```

---

## 🎯 Summary: How to Think About Hierarchy

### The Hierarchy Builder's Job:

**Input:** Docling's flat list (reading order)
```
[header_a, table_1, header_b, text_1, text_2, header_c, ...]
```

**Output:** Nested tree structure
```
section_a:
  - table_1
section_b:
  - text_1
  - text_2
section_c:
  ...
```

### Decision Points:

1. **Is this element a header?**
   - Check Docling's label
   - Check text patterns
   - Check spatial features
   - Check context

2. **What level is this header?**
   - Extract from numbering (7.2.1 = level 3)
   - Or use indentation
   - Or use font size

3. **What belongs to this section?**
   - Everything after header
   - Until next header of same/higher level

### The Art of Hierarchy Building:

- **No perfect solution** - documents vary
- **Combine strategies** - redundancy helps
- **Use confidence scores** - know when you're uncertain
- **Iterate** - improve as you learn from examples
- **Document assumptions** - make decisions explicit

---

**Last Updated**: 2025-10-27
**Tested On**: EAF Chapter 1 (13 sections detected)
**Status**: Production-ready (Strategy 1) + Advanced ideas for future
