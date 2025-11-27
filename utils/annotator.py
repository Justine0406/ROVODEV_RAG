"""
PDF annotation utilities for highlighting and adding comments.
"""

import fitz  # PyMuPDF
from typing import List, Dict
import io


def create_annotated_pdf(original_pdf_bytes: bytes, issues: List[Dict]) -> bytes:
    """
    Create PDF with highlights and annotations.
    
    Args:
        original_pdf_bytes: Original PDF as bytes
        issues: List of issues from parse_critique_for_issues()
    
    Returns:
        Annotated PDF as bytes
    """
    # Open PDF
    doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
    
    # Color mapping based on severity
    color_map = {
        'high': (1, 0.2, 0.2),      # Red
        'medium': (1, 0.6, 0),       # Orange
        'low': (1, 1, 0)             # Yellow
    }
    
    # Track what we've highlighted to avoid duplicates
    highlighted_texts = set()
    
    for issue in issues:
        text_snippet = issue['text_snippet']
        severity = issue.get('severity', 'medium')
        suggestion = issue.get('suggestion', 'Review this section')
        page_hint = issue.get('page_hint')
        
        # Skip if already highlighted
        if text_snippet in highlighted_texts:
            continue
        
        # Determine which pages to search
        if page_hint:
            # Search specific page (and adjacent pages)
            pages_to_search = range(
                max(0, page_hint - 2),
                min(doc.page_count, page_hint + 1)
            )
        else:
            # Search all pages (limit to first 20 for performance)
            pages_to_search = range(min(20, doc.page_count))
        
        # Try to find and highlight the text
        found = False
        for page_num in pages_to_search:
            page = doc[page_num]
            
            # Search for the text (try first 50 chars for better matching)
            search_text = text_snippet[:50]
            text_instances = page.search_for(search_text)
            
            if text_instances:
                # Highlight first instance
                rect = text_instances[0]
                
                # Add highlight
                highlight_text_on_page(
                    page,
                    rect,
                    color=color_map.get(severity, (1, 1, 0)),
                    opacity=0.3
                )
                
                # Add sticky note with suggestion
                add_sticky_note(
                    page,
                    rect,
                    note_text=f"Issue: {issue['type']}\n\n{suggestion}",
                    icon="Note"
                )
                
                highlighted_texts.add(text_snippet)
                found = True
                break
        
        # If text not found but we have a page hint, add a general note
        if not found and page_hint and 0 <= page_hint - 1 < doc.page_count:
            page = doc[page_hint - 1]
            # Add note at top of page
            rect = fitz.Rect(50, 50, 150, 100)
            add_sticky_note(
                page,
                rect,
                note_text=f"Issue on this page ({issue['type']})\n\n{suggestion}",
                icon="Help"
            )
    
    # Save to bytes
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    doc.close()
    
    annotated_pdf_bytes = output_buffer.getvalue()
    output_buffer.close()
    
    return annotated_pdf_bytes


def highlight_text_on_page(
    page: fitz.Page,
    rect: fitz.Rect,
    color: tuple = (1, 1, 0),
    opacity: float = 0.3
):
    """
    Highlight specific text area on a PDF page.
    
    Args:
        page: PyMuPDF page object
        rect: Rectangle coordinates to highlight
        color: RGB tuple (0-1 range)
        opacity: Highlight transparency
    """
    try:
        # Add highlight annotation
        highlight = page.add_highlight_annot(rect)
        highlight.set_colors(stroke=color)
        highlight.set_opacity(opacity)
        highlight.update()
    except Exception as e:
        # Silently fail if highlighting doesn't work
        pass


def add_sticky_note(
    page: fitz.Page,
    rect: fitz.Rect,
    note_text: str,
    icon: str = "Note"
):
    """
    Add sticky note annotation to PDF.
    
    Args:
        page: PyMuPDF page object
        rect: Position for the note icon
        note_text: Annotation content
        icon: Icon type - "Note", "Comment", "Help", "Insert", "Key", etc.
    """
    try:
        # Create a small rect for the icon (top-right of highlight)
        icon_rect = fitz.Rect(
            rect.x1 - 20,  # 20 points from right edge
            rect.y0,
            rect.x1,
            rect.y0 + 20
        )
        
        # Add text annotation (sticky note)
        annot = page.add_text_annot(
            icon_rect.top_left,
            note_text,
            icon=icon
        )
        annot.set_opacity(0.8)
        annot.update()
    except Exception as e:
        # Silently fail if annotation doesn't work
        pass


def add_summary_page(pdf_bytes: bytes, critique_summary: str, issue_count: int) -> bytes:
    """
    Add a summary page at the beginning of the PDF.
    
    Args:
        pdf_bytes: Original PDF bytes
        critique_summary: Summary text to add
        issue_count: Number of issues found
    
    Returns:
        PDF with summary page prepended
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Insert blank page at the beginning
    new_page = doc.new_page(0, width=595, height=842)  # A4 size
    
    # Add title
    title_rect = fitz.Rect(50, 50, 545, 100)
    new_page.insert_textbox(
        title_rect,
        "Thesis Review Summary",
        fontsize=18,
        fontname="helv",
        fontfile=None,
        bold=True,
        align=fitz.TEXT_ALIGN_CENTER
    )
    
    # Add issue count
    count_rect = fitz.Rect(50, 120, 545, 150)
    new_page.insert_textbox(
        count_rect,
        f"Total Issues Found: {issue_count}",
        fontsize=12,
        fontname="helv",
        align=fitz.TEXT_ALIGN_LEFT
    )
    
    # Add summary (truncate if too long)
    summary_text = critique_summary[:1000] + "..." if len(critique_summary) > 1000 else critique_summary
    summary_rect = fitz.Rect(50, 170, 545, 750)
    new_page.insert_textbox(
        summary_rect,
        summary_text,
        fontsize=10,
        fontname="helv",
        align=fitz.TEXT_ALIGN_LEFT
    )
    
    # Save to bytes
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    doc.close()
    
    result_bytes = output_buffer.getvalue()
    output_buffer.close()
    
    return result_bytes
