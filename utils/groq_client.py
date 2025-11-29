"""
Groq API integration for generating critiques.
"""

from groq import Groq
from typing import List, Dict, Generator, Optional
import re


def get_groq_client(api_key: str) -> Groq:
    """
    Initialize Groq client with API key.
    
    Args:
        api_key: Groq API key
    
    Returns:
        Groq client instance
    """
    return Groq(api_key=api_key)


def generate_critique(
    client: Groq,
    prompt: str,
    stream: bool = True,
    model: str = "llama-3.3-70b-versatile"
) -> Generator[str, None, None] | str:
    """
    Generate critique using Groq API.
    
    Args:
        client: Groq client
        prompt: Complete prompt with context
        stream: Enable streaming response
        model: Groq model to use
    
    Returns:
        Generator yielding response chunks (if stream=True)
        or complete response string (if stream=False)
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert thesis panelist with years of experience reviewing academic research. Provide constructive, specific, and actionable feedback."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
            stream=stream
        )
        
        if stream:
            # Return generator for streaming
            def stream_generator():
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return stream_generator()
        else:
            # Return complete response
            return response.choices[0].message.content
            
    except Exception as e:
        raise Exception(f"Groq API Error: {str(e)}")


def parse_critique_for_issues(critique_text: str) -> List[Dict]:
    """
    Extract structured issues from critique text with enhanced severity classification.

    Args:
        critique_text: Generated critique text

    Returns:
        List of issue dictionaries:
        [
            {
                'type': 'grammar' | 'logic' | 'methodology' | 'clarity' | 'strength',
                'severity': 'critical' | 'major' | 'minor' | 'suggestion' | 'strength',
                'text_snippet': str,
                'suggestion': str,
                'page_hint': int or None
            }
        ]
    """
    issues = []

    # Look for quoted text (likely citations from the critique)
    quote_pattern = r'"([^"]{20,200})"'
    quotes = re.findall(quote_pattern, critique_text)

    # Look for page references
    page_pattern = r'(?:page|pg\.?|p\.)\s*(\d+)'

    # Categorize issues based on section headers
    current_type = 'general'
    current_severity = 'major'  # Default to major

    lines = critique_text.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Detect severity level (enhanced)
        if any(word in line_lower for word in ['critical', 'major issue', 'serious', 'fatal', 'fundamental']):
            current_severity = 'critical'
        elif any(word in line_lower for word in ['major', 'significant', 'important']):
            current_severity = 'major'
        elif any(word in line_lower for word in ['minor', 'small', 'typo', 'grammar']):
            current_severity = 'minor'
        elif any(word in line_lower for word in ['suggest', 'could', 'might', 'consider', 'recommendation']):
            current_severity = 'suggestion'
        elif any(word in line_lower for word in ['strength', 'well-written', 'excellent', 'good', 'clear']):
            current_severity = 'strength'
            current_type = 'strength'

        # Detect issue type
        if 'methodology' in line_lower or 'research design' in line_lower:
            current_type = 'methodology'
            if current_severity not in ['critical', 'strength']:
                current_severity = 'major'  # Methodology issues are typically major
        elif 'grammar' in line_lower or 'spelling' in line_lower or 'typo' in line_lower:
            current_type = 'grammar'
            if current_severity not in ['critical', 'major']:
                current_severity = 'minor'
        elif 'writing' in line_lower or 'clarity' in line_lower or 'style' in line_lower:
            current_type = 'clarity'
        elif 'logic' in line_lower or 'argument' in line_lower or 'reasoning' in line_lower:
            current_type = 'logic'
            if current_severity == 'minor':
                current_severity = 'major'  # Logic issues are at least major

        # Extract quoted text and suggestions
        if '"' in line and i + 1 < len(lines):
            snippet_match = re.search(quote_pattern, line)
            if snippet_match:
                text_snippet = snippet_match.group(1)

                # Look for suggestion in next few lines
                suggestion = ""
                for j in range(i + 1, min(i + 4, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        suggestion += lines[j].strip() + " "

                # Extract page number if present
                page_hint = None
                page_match = re.search(page_pattern, line, re.IGNORECASE)
                if page_match:
                    page_hint = int(page_match.group(1))

                issues.append({
                    'type': current_type,
                    'severity': current_severity,
                    'text_snippet': text_snippet[:150],  # Limit length
                    'suggestion': suggestion[:200].strip() if suggestion.strip() else 'Review and improve this section',
                    'page_hint': page_hint
                })

    # If no issues found through parsing, create general issues from quotes
    if not issues and quotes:
        for quote in quotes[:5]:  # Limit to 5
            issues.append({
                'type': 'general',
                'severity': 'major',
                'text_snippet': quote[:150],
                'suggestion': 'Review and revise this section',
                'page_hint': None
            })

    return issues


def parse_rewrite_suggestions(critique_text: str) -> List[Dict]:
    """
    Extract inline rewrite suggestions from critique text.

    Args:
        critique_text: Generated critique text

    Returns:
        List of rewrite dictionaries:
        [
            {
                'original': str,
                'suggested': str,
                'explanation': str,
                'page_num': int or None
            }
        ]
    """
    rewrites = []

    # Pattern for "X → Y" or "X should be Y" suggestions
    arrow_pattern = r'"([^"]+)"\s*(?:→|->|should be|could be|replace with)\s*"([^"]+)"'
    matches = re.findall(arrow_pattern, critique_text, re.IGNORECASE)

    # Look for page references
    page_pattern = r'(?:page|pg\.?|p\.)\s*(\d+)'

    for original, suggested in matches:
        # Find page number (search nearby text)
        page_num = None
        # Simple approach: look for page number in the same paragraph
        context_start = max(0, critique_text.find(original) - 100)
        context_end = min(len(critique_text), critique_text.find(original) + 100)
        context = critique_text[context_start:context_end]

        page_match = re.search(page_pattern, context, re.IGNORECASE)
        if page_match:
            page_num = int(page_match.group(1))

        rewrites.append({
            'original': original[:100],
            'suggested': suggested[:100],
            'explanation': 'Improves clarity and correctness',
            'page_num': page_num
        })

    return rewrites[:10]  # Limit to 10 rewrites


def parse_section_summaries(critique_text: str) -> List[Dict]:
    """
    Extract section-level summaries from critique text.

    Args:
        critique_text: Generated critique text

    Returns:
        List of section summary dictionaries:
        [
            {
                'section': str,
                'page_num': int or None,
                'strengths': [str],
                'issues': [str],
                'suggestions': [str],
                'score': int (1-10)
            }
        ]
    """
    summaries = []

    # Define section keywords
    sections = [
        'abstract', 'introduction', 'literature review',
        'methodology', 'results', 'discussion', 'conclusion'
    ]

    # Try to find section-specific content
    for section in sections:
        section_pattern = rf'##\s*{section}[^#]*'
        section_match = re.search(section_pattern, critique_text, re.IGNORECASE)

        if section_match:
            section_content = section_match.group(0)

            # Extract strengths
            strengths = []
            strength_patterns = [
                r'strength[s]?:?\s*[-•]\s*([^\n]+)',
                r'good:?\s*[-•]\s*([^\n]+)',
                r'well[- ](?:written|done):?\s*[-•]\s*([^\n]+)'
            ]
            for pattern in strength_patterns:
                strengths.extend(re.findall(pattern, section_content, re.IGNORECASE))

            # Extract issues
            issues = []
            issue_patterns = [
                r'issue[s]?:?\s*[-•]\s*([^\n]+)',
                r'problem[s]?:?\s*[-•]\s*([^\n]+)',
                r'concern[s]?:?\s*[-•]\s*([^\n]+)',
                r'weakness[es]*:?\s*[-•]\s*([^\n]+)'
            ]
            for pattern in issue_patterns:
                issues.extend(re.findall(pattern, section_content, re.IGNORECASE))

            # Extract suggestions
            suggestions = []
            suggestion_patterns = [
                r'suggest[ion]*[s]?:?\s*[-•]\s*([^\n]+)',
                r'recommend[ation]*[s]?:?\s*[-•]\s*([^\n]+)',
                r'should:?\s*[-•]\s*([^\n]+)'
            ]
            for pattern in suggestion_patterns:
                suggestions.extend(re.findall(pattern, section_content, re.IGNORECASE))

            # Extract score if present (e.g., "Score: 7/10")
            score = 7  # Default
            score_match = re.search(r'score:?\s*(\d+)(?:/10)?', section_content, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))

            # Try to find page number
            page_num = None
            page_match = re.search(r'(?:page|pg\.?|p\.)\s*(\d+)', section_content, re.IGNORECASE)
            if page_match:
                page_num = int(page_match.group(1))

            if strengths or issues or suggestions:
                summaries.append({
                    'section': section.title(),
                    'page_num': page_num,
                    'strengths': strengths[:3],
                    'issues': issues[:3],
                    'suggestions': suggestions[:3],
                    'score': min(10, max(1, score))
                })

    return summaries


def test_groq_connection(api_key: str) -> tuple[bool, str]:
    """
    Test if Groq API key is valid.
    
    Args:
        api_key: Groq API key to test
    
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    try:
        client = get_groq_client(api_key)
        
        # Make a minimal test call
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=10
        )
        
        return True, "API key is valid!"
        
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return False, "Invalid API key. Please check your key."
        elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
            return False, "Rate limit reached. Please try again in a moment."
        else:
            return False, f"Connection error: {error_msg}"

