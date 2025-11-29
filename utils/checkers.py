"""
Advanced checkers for thesis analysis: citations, consistency, and alignment.
"""

import re
from typing import List, Dict, Tuple, Set
from collections import Counter


# Thesis sections for analysis
THESIS_SECTIONS = [
    'abstract', 'introduction', 'literature review', 'related work',
    'methodology', 'methods', 'results', 'findings',
    'discussion', 'conclusion', 'references'
]


def check_citations(full_text: str, pdf_pages: List[Dict]) -> Dict:
    """
    Comprehensive citation and reference integrity check.

    Args:
        full_text: Complete thesis text
        pdf_pages: List of page dictionaries with text

    Returns:
        Dictionary with citation analysis:
        {
            'in_text_citations': [str],
            'reference_list': [str],
            'missing_references': [str],
            'unused_references': [str],
            'citation_count': int,
            'reference_count': int,
            'format_issues': [str],
            'outdated_sources': [str]
        }
    """
    results = {
        'in_text_citations': [],
        'reference_list': [],
        'missing_references': [],
        'unused_references': [],
        'citation_count': 0,
        'reference_count': 0,
        'format_issues': [],
        'outdated_sources': []
    }

    # Extract in-text citations (various formats)
    # APA style: (Author, Year) or (Author et al., Year)
    apa_pattern = r'\(([A-Z][a-z]+(?:\s+et al\.)?),?\s+(\d{4})\)'
    apa_citations = re.findall(apa_pattern, full_text)

    # Author-year: Author (Year)
    author_year_pattern = r'([A-Z][a-z]+(?:\s+et al\.)?)\s+\((\d{4})\)'
    author_year_citations = re.findall(author_year_pattern, full_text)

    # Bracketed: [1], [2], etc.
    bracketed_pattern = r'\[(\d+)\]'
    bracketed_citations = re.findall(bracketed_pattern, full_text)

    # Combine all citations
    all_citations = set()
    for author, year in apa_citations + author_year_citations:
        all_citations.add(f"{author} ({year})")

    results['in_text_citations'] = sorted(list(all_citations))
    results['citation_count'] = len(all_citations) + len(bracketed_citations)

    # Try to find references section
    references_section = extract_references_section(full_text)

    if references_section:
        # Extract individual references
        # Split by newlines or common patterns
        ref_lines = references_section.split('\n')
        references = []

        for line in ref_lines:
            line = line.strip()
            # Look for lines that start with author names or numbers
            if line and (line[0].isupper() or line[0].isdigit()):
                # Extract year if present
                year_match = re.search(r'\((\d{4})\)', line)
                if year_match:
                    references.append(line[:100])  # First 100 chars

        results['reference_list'] = references
        results['reference_count'] = len(references)

        # Check for outdated sources (>10 years old)
        current_year = 2024
        for ref in references:
            year_match = re.search(r'\((\d{4})\)', ref)
            if year_match:
                year = int(year_match.group(1))
                if current_year - year > 10:
                    results['outdated_sources'].append(f"{ref[:60]}... ({year})")

    # Cross-check citations and references
    cited_authors = set()
    for citation in all_citations:
        # Extract author name
        author_match = re.match(r'([A-Za-z\s]+)', citation)
        if author_match:
            cited_authors.add(author_match.group(1).strip())

    referenced_authors = set()
    for ref in results['reference_list']:
        # Extract first author name (before comma or parenthesis)
        parts = re.split(r'[,(]', ref)
        if parts:
            referenced_authors.add(parts[0].strip())

    # Find discrepancies (simplified - in real implementation, needs fuzzy matching)
    results['missing_references'] = [
        f"{author} - cited but not in reference list"
        for author in list(cited_authors - referenced_authors)[:5]
    ]

    results['unused_references'] = [
        f"{author} - in reference list but not cited"
        for author in list(referenced_authors - cited_authors)[:5]
    ]

    return results


def extract_references_section(text: str) -> str:
    """Extract the references/bibliography section from text."""
    # Look for common reference section headers
    patterns = [
        r'(?i)\n\s*REFERENCES\s*\n(.*?)(?:\n\s*APPENDIX|\Z)',
        r'(?i)\n\s*BIBLIOGRAPHY\s*\n(.*?)(?:\n\s*APPENDIX|\Z)',
        r'(?i)\n\s*WORKS CITED\s*\n(.*?)(?:\n\s*APPENDIX|\Z)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)

    return ""


def check_consistency(full_text: str, pdf_pages: List[Dict]) -> Dict:
    """
    Check for consistency issues in terminology, tenses, formatting.

    Args:
        full_text: Complete thesis text
        pdf_pages: List of page dictionaries

    Returns:
        Dictionary with consistency analysis
    """
    results = {
        'terminology_issues': [],
        'tense_issues': [],
        'number_format_issues': [],
        'acronym_issues': [],
        'heading_issues': []
    }

    # Check for terminology consistency
    terminology_variants = [
        (['participants', 'respondents', 'subjects'], 'Use consistent term for study participants'),
        (['questionnaire', 'survey', 'instrument'], 'Use consistent term for data collection tool'),
        (['data', 'datas'], 'Data is uncountable - use "data" not "datas"'),
        (['analyze', 'analyse'], 'Use consistent spelling (American vs British)'),
        (['per cent', 'percent', '%'], 'Use consistent percentage format')
    ]

    for variants, suggestion in terminology_variants:
        found_variants = []
        for variant in variants:
            if re.search(r'\b' + re.escape(variant) + r'\b', full_text, re.IGNORECASE):
                found_variants.append(variant)

        if len(found_variants) > 1:
            results['terminology_issues'].append({
                'variants': found_variants,
                'suggestion': suggestion
            })

    # Check for acronym definitions
    # Find all acronyms (2-6 uppercase letters)
    acronyms = re.findall(r'\b([A-Z]{2,6})\b', full_text)
    acronym_counts = Counter(acronyms)

    # Common acronyms that don't need definition
    common_acronyms = {'USA', 'UK', 'PhD', 'MSc', 'BSc', 'IBM', 'PDF', 'URL', 'HTML', 'CSS', 'API'}

    for acronym, count in acronym_counts.most_common(10):
        if acronym not in common_acronyms and count > 2:
            # Check if it's defined (look for pattern: "Full Name (ACRONYM)")
            definition_pattern = rf'\([^)]*\b{re.escape(acronym)}\b\)'
            if not re.search(definition_pattern, full_text):
                results['acronym_issues'].append(
                    f"'{acronym}' used {count} times but never defined"
                )

    # Check number formatting consistency
    # Numbers written as words vs digits
    number_words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
    found_word_numbers = []
    found_digit_numbers = []

    for word in number_words[1:11]:  # 1-10
        if re.search(r'\b' + word + r'\b', full_text, re.IGNORECASE):
            found_word_numbers.append(word)

    # Check for digits 1-10 at start of sentences or standalone
    if re.search(r'(?:^|\.\s+)([1-9]|10)\s', full_text, re.MULTILINE):
        found_digit_numbers.append('digits')

    if found_word_numbers and found_digit_numbers:
        results['number_format_issues'].append(
            "Inconsistent number format: Some numbers written as words, others as digits. " +
            "Typically write 1-10 as words, 11+ as digits."
        )

    return results


def check_research_alignment(full_text: str, pdf_pages: List[Dict]) -> Dict:
    """
    Check alignment between research components.

    Args:
        full_text: Complete thesis text
        pdf_pages: List of page dictionaries

    Returns:
        Dictionary with alignment analysis
    """
    results = {
        'components': {},
        'alignment_issues': [],
        'alignment_score': 0,
        'recommendations': []
    }

    # Extract key research components
    components = extract_research_components(full_text)
    results['components'] = components

    # Check alignments
    alignment_checks = []

    # 1. Research questions vs methodology
    if components['research_questions'] and components['methodology']:
        if len(components['research_questions']) > 0:
            alignment_checks.append({
                'check': 'Research Questions ↔ Methodology',
                'status': 'aligned',
                'note': f"Found {len(components['research_questions'])} RQ(s) with methodology section"
            })
        else:
            results['alignment_issues'].append(
                "No clear research questions found. Ensure objectives are stated as specific questions."
            )

    # 2. Variables mentioned vs methodology
    if components['variables']:
        alignment_checks.append({
            'check': 'Variables ↔ Methodology',
            'status': 'aligned',
            'note': f"Found {len(components['variables'])} variable(s) mentioned"
        })
    else:
        results['alignment_issues'].append(
            "No variables clearly identified. Specify independent and dependent variables."
        )

    # 3. Problem statement vs conclusion
    if components['problem_statement'] and components['conclusion']:
        alignment_checks.append({
            'check': 'Problem ↔ Conclusion',
            'status': 'check_needed',
            'note': "Verify conclusion addresses the stated problem"
        })

    # Calculate alignment score
    total_checks = len(alignment_checks)
    aligned = sum(1 for check in alignment_checks if check['status'] == 'aligned')
    results['alignment_score'] = int((aligned / total_checks * 10) if total_checks > 0 else 5)

    # Recommendations
    if results['alignment_score'] < 7:
        results['recommendations'].append(
            "Review research design: Ensure all components (problem, RQs, methodology, conclusions) are logically connected"
        )

    if not components['research_questions']:
        results['recommendations'].append(
            "Add explicit research questions in the introduction or methodology section"
        )

    if not components['variables']:
        results['recommendations'].append(
            "Clearly define and operationalize your variables in the methodology section"
        )

    return results


def extract_research_components(text: str) -> Dict:
    """Extract key research components from thesis text."""
    components = {
        'problem_statement': None,
        'research_questions': [],
        'objectives': [],
        'hypotheses': [],
        'variables': [],
        'methodology': None,
        'conclusion': None
    }

    # Extract research questions
    rq_patterns = [
        r'(?i)research question[s]?:?\s*(.{0,200})\?',
        r'(?i)RQ\d+:?\s*(.{0,200})\?',
        r'(?i)this study (?:asks|addresses|explores):?\s*(.{0,200})\?'
    ]

    for pattern in rq_patterns:
        matches = re.findall(pattern, text)
        components['research_questions'].extend(matches[:3])

    # Extract objectives
    obj_patterns = [
        r'(?i)objective[s]?:?\s*\n\s*(?:1\.|•|-)\s*(.{0,150})',
        r'(?i)this study aims to\s+(.{0,150})',
        r'(?i)the goal (?:of this research )?is to\s+(.{0,150})'
    ]

    for pattern in obj_patterns:
        matches = re.findall(pattern, text)
        components['objectives'].extend(matches[:3])

    # Extract variables (look for common patterns)
    var_patterns = [
        r'(?i)independent variable[s]?:?\s*(.{0,100})',
        r'(?i)dependent variable[s]?:?\s*(.{0,100})',
        r'(?i)variable[s]?\s+(?:include|are|measured):?\s*(.{0,100})'
    ]

    for pattern in var_patterns:
        matches = re.findall(pattern, text)
        components['variables'].extend(matches[:5])

    # Check for methodology section
    if re.search(r'(?i)\n\s*(?:METHODOLOGY|METHODS)\s*\n', text):
        components['methodology'] = True

    # Check for conclusion section
    if re.search(r'(?i)\n\s*CONCLUSION\s*\n', text):
        components['conclusion'] = True

    # Check for problem statement
    problem_patterns = [
        r'(?i)(?:the )?problem (?:is|addressed):?\s*(.{0,200})',
        r'(?i)(?:the )?(?:research )?gap:?\s*(.{0,200})',
        r'(?i)this study (?:addresses|tackles):?\s*(.{0,200})'
    ]

    for pattern in problem_patterns:
        match = re.search(pattern, text)
        if match:
            components['problem_statement'] = match.group(1)
            break

    return components


def analyze_section(
    section_name: str,
    section_text: str,
    retrieved_chunks: List[Dict]
) -> Dict:
    """
    Analyze a specific thesis section with specialized criteria.

    Args:
        section_name: Name of the section (abstract, introduction, etc.)
        section_text: Text content of the section
        retrieved_chunks: Related chunks from vector search

    Returns:
        Dictionary with section analysis
    """
    # Section-specific criteria
    criteria = {
        'abstract': {
            'word_count_range': (150, 300),
            'must_include': ['problem', 'method', 'results', 'conclusion'],
            'tense': 'past'
        },
        'introduction': {
            'must_include': ['background', 'problem', 'gap', 'objectives'],
            'flow': 'general_to_specific'
        },
        'literature review': {
            'must_include': ['themes', 'synthesis', 'gap'],
            'citation_density': 'high'
        },
        'methodology': {
            'must_include': ['design', 'participants', 'instruments', 'procedures', 'analysis'],
            'tense': 'past'
        },
        'results': {
            'must_include': ['findings', 'statistics'],
            'tense': 'past'
        },
        'discussion': {
            'must_include': ['interpretation', 'implications', 'limitations'],
            'comparison': 'with_literature'
        },
        'conclusion': {
            'must_include': ['summary', 'contributions', 'recommendations'],
            'no_new_info': True
        }
    }

    section_key = section_name.lower()
    section_criteria = criteria.get(section_key, {})

    analysis = {
        'section': section_name,
        'word_count': len(section_text.split()),
        'meets_criteria': [],
        'issues': [],
        'score': 7  # Default score
    }

    # Check word count for abstract
    if section_key == 'abstract' and 'word_count_range' in section_criteria:
        min_words, max_words = section_criteria['word_count_range']
        if analysis['word_count'] < min_words:
            analysis['issues'].append(f"Abstract too short ({analysis['word_count']} words, recommended {min_words}-{max_words})")
        elif analysis['word_count'] > max_words:
            analysis['issues'].append(f"Abstract too long ({analysis['word_count']} words, recommended {min_words}-{max_words})")
        else:
            analysis['meets_criteria'].append(f"Appropriate length ({analysis['word_count']} words)")

    # Check for required elements
    if 'must_include' in section_criteria:
        for element in section_criteria['must_include']:
            if re.search(r'\b' + element + r'\b', section_text, re.IGNORECASE):
                analysis['meets_criteria'].append(f"Includes {element}")
            else:
                analysis['issues'].append(f"Missing or unclear: {element}")

    # Adjust score based on issues
    analysis['score'] = max(1, 10 - len(analysis['issues']))

    return analysis
