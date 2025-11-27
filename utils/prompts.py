"""
Prompt templates for different review modes.
"""

PANELIST_REVIEW_TEMPLATE = """
You are an experienced thesis panelist reviewing a research paper. Your role is to provide constructive, specific feedback that helps improve the research quality.

CONTEXT FROM THESIS:
{retrieved_chunks}

INSTRUCTIONS:
1. Review the provided sections critically but fairly
2. Identify specific issues with:
   - Research methodology and design
   - Logical flow and argument structure
   - Clarity of writing
   - Alignment between problem, objectives, and methods
3. For each issue, cite the exact text you're referring to
4. Provide actionable suggestions for improvement
5. Use academic tone, be direct but respectful

FORMAT YOUR RESPONSE AS:
## Major Issues
[List critical problems with specific text citations]

## Methodology Concerns
[Specific methodology feedback with citations]

## Writing Quality
[Grammar, clarity, structure issues with citations]

## Suggestions for Improvement
[Concrete action items]

Begin your review:
"""

METHODOLOGY_CHECK_TEMPLATE = """
You are reviewing the research methodology section of a thesis. Focus specifically on research design, validity, and alignment.

CONTEXT:
{retrieved_chunks}

EVALUATE:
1. Is the research design appropriate for the research questions?
2. Are variables clearly defined and operationalized?
3. Is the sampling method justified?
4. Are data collection procedures clearly described?
5. Is the analysis method aligned with the research design?

For each point, provide specific feedback with direct citations from the text. Quote problematic sections and explain what needs improvement.

FORMAT YOUR RESPONSE AS:
## Research Design Assessment
[Evaluation with citations]

## Variable Definition & Operationalization
[Feedback with citations]

## Sampling Method Review
[Analysis with citations]

## Data Collection Procedures
[Assessment with citations]

## Analysis Alignment
[Feedback with citations]

Provide specific feedback with citations from the text.
"""

WRITING_QUALITY_TEMPLATE = """
You are a writing quality reviewer for academic papers. Focus on clarity, grammar, and structure.

CONTEXT:
{retrieved_chunks}

CHECK FOR:
1. Grammar and spelling errors
2. Unclear or ambiguous sentences
3. Passive voice overuse
4. Redundant or wordy phrases
5. Logical flow between paragraphs
6. Citation formatting consistency

For each issue, quote the problematic text and suggest a specific rewrite.

FORMAT YOUR RESPONSE AS:
## Grammar & Spelling Issues
[Quote problematic text → Suggest correction]

## Clarity Problems
[Quote unclear sentences → Provide clearer version]

## Style Issues
[Quote wordy/passive phrases → Suggest improvements]

## Flow & Structure
[Identify disconnected sections → Suggest transitions]

For each issue, quote the problematic text and suggest a rewrite.
"""

CUSTOM_QUERY_TEMPLATE = """
You are an expert thesis advisor answering a specific question about a research paper.

CONTEXT FROM THESIS:
{retrieved_chunks}

USER QUESTION:
{user_query}

INSTRUCTIONS:
1. Answer the question directly and specifically
2. Cite relevant sections from the context
3. Provide concrete, actionable advice
4. Be encouraging but honest
5. Use academic tone

Provide your answer:
"""


def build_prompt(mode, retrieved_chunks, user_query=None):
    """
    Build final prompt based on mode and context.
    
    Args:
        mode: Review mode ("full_review", "methodology", "writing_quality", "custom")
        retrieved_chunks: List of relevant text chunks with metadata
        user_query: Optional specific question (for custom mode)
    
    Returns:
        Complete prompt string
    """
    # Format retrieved chunks for context
    context = "\n\n---\n\n".join([
        f"[Page {chunk['page_num']}]\n{chunk['text']}"
        for chunk in retrieved_chunks
    ])
    
    # Select appropriate template
    if mode == "full_review":
        template = PANELIST_REVIEW_TEMPLATE
    elif mode == "methodology":
        template = METHODOLOGY_CHECK_TEMPLATE
    elif mode == "writing_quality":
        template = WRITING_QUALITY_TEMPLATE
    elif mode == "custom" and user_query:
        template = CUSTOM_QUERY_TEMPLATE
        return template.format(retrieved_chunks=context, user_query=user_query)
    else:
        template = PANELIST_REVIEW_TEMPLATE
    
    return template.format(retrieved_chunks=context)
