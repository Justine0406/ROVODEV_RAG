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
    Extract structured issues from critique text.
    
    Args:
        critique_text: Generated critique text
    
    Returns:
        List of issue dictionaries:
        [
            {
                'type': 'grammar' | 'logic' | 'methodology' | 'clarity',
                'severity': 'high' | 'medium' | 'low',
                'text_snippet': str,
                'suggestion': str,
                'page_hint': int or None
            }
        ]
    """
    issues = []
    
    # Look for quoted text (likely citations from the critique)
    # Pattern: text in quotes followed by suggestions
    quote_pattern = r'"([^"]{20,200})"'
    quotes = re.findall(quote_pattern, critique_text)
    
    # Look for page references
    page_pattern = r'(?:page|pg\.?|p\.)\s*(\d+)'
    
    # Categorize issues based on section headers
    current_type = 'general'
    current_severity = 'medium'
    
    lines = critique_text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Detect section type
        if 'major issue' in line_lower or 'critical' in line_lower:
            current_type = 'methodology'
            current_severity = 'high'
        elif 'methodology' in line_lower:
            current_type = 'methodology'
            current_severity = 'high'
        elif 'grammar' in line_lower or 'spelling' in line_lower:
            current_type = 'grammar'
            current_severity = 'low'
        elif 'writing' in line_lower or 'clarity' in line_lower:
            current_type = 'clarity'
            current_severity = 'medium'
        elif 'logic' in line_lower or 'argument' in line_lower:
            current_type = 'logic'
            current_severity = 'high'
        
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
                    'suggestion': suggestion[:200].strip(),
                    'page_hint': page_hint
                })
    
    # If no issues found through parsing, create general issues from quotes
    if not issues and quotes:
        for quote in quotes[:5]:  # Limit to 5
            issues.append({
                'type': 'general',
                'severity': 'medium',
                'text_snippet': quote[:150],
                'suggestion': 'Review and revise this section',
                'page_hint': None
            })
    
    return issues


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

