"""
Enhanced PDF annotation utilities with professional-grade features.
"""

import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional
import io


# Enhanced color scheme for severity levels
HIGHLIGHT_COLORS = {
    'critical': (1, 0, 0, 0.3),         # Red - Critical issues
    'major': (1, 0.5, 0, 0.3),          # Orange - Major issues
    'minor': (1, 1, 0, 0.3),            # Yellow - Minor issues
    'suggestion': (0, 0.5, 1, 0.3),     # Blue - Suggestions
    'strength': (0, 1, 0, 0.3),         # Green - Well-written sections
    # Legacy mapping
    'high': (1, 0, 0, 0.3),             # Maps to critical
    'medium': (1, 0.5, 0, 0.3),         # Maps to major
    'low': (1, 1, 0, 0.3)               # Maps to minor
}

# Icons for different annotation types
ANNOTATION_ICONS = {
    'grammar': '✏️',
    'logic': '⚠️',
    'methodology': '🔍',
    'clarity': '💡',
    'suggestion': '💡',
    'strength': '✅',
    'critical': '⚠️',
    'general': '📝'
}

# Section names for summary boxes
SECTION_NAMES = [
    'abstract', 'introduction', 'literature review',
    'methodology', 'results', 'discussion', 'conclusion'
]


def create_annotated_pdf(
    original_pdf_bytes: bytes,
    issues: List[Dict],
    section_summaries: Optional[List[Dict]] = None,
    rewrites: Optional[List[Dict]] = None,
    include_legend: bool = True
) -> bytes:
    """
    Create professionally annotated PDF with advanced features.

    Args:
        original_pdf_bytes: Original PDF as bytes
        issues: List of issues with severity, type, text_snippet, suggestion
        section_summaries: Optional list of section-level summaries
        rewrites: Optional list of inline rewrite suggestions
        include_legend: Whether to add color legend on first page

    Returns:
        Annotated PDF as bytes
    """
    # Open PDF
    doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")

    # Track annotations
    highlighted_texts = set()
    comment_counter = 1

    # Add annotation legend to first page
    if include_legend and doc.page_count > 0:
        add_annotation_legend(doc[0])

    # Process main issues
    for issue in issues:
        result = add_issue_annotation(
            doc,
            issue,
            highlighted_texts,
            comment_counter
        )
        if result:
            comment_counter = result

    # Add section summaries if provided
    if section_summaries:
        for summary in section_summaries:
            add_section_summary_box(doc, summary)

    # Add inline rewrites if provided
    if rewrites:
        for rewrite in rewrites:
            add_inline_rewrite(doc, rewrite)

    # Save to bytes
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    doc.close()

    annotated_pdf_bytes = output_buffer.getvalue()
    output_buffer.close()

    return annotated_pdf_bytes


def add_issue_annotation(
    doc: fitz.Document,
    issue: Dict,
    highlighted_texts: set,
    comment_counter: int
) -> Optional[int]:
    """
    Add a single issue annotation to the PDF.

    Args:
        doc: PyMuPDF document
        issue: Issue dictionary
        highlighted_texts: Set of already highlighted text
        comment_counter: Current comment number

    Returns:
        Updated comment counter, or None if not added
    """
    text_snippet = issue.get('text_snippet', '')
    severity = issue.get('severity', 'medium')
    suggestion = issue.get('suggestion', 'Review this section')
    issue_type = issue.get('type', 'general')
    page_hint = issue.get('page_hint')

    # Skip if already highlighted
    if text_snippet in highlighted_texts:
        return comment_counter

    # Determine pages to search
    if page_hint:
        pages_to_search = range(
            max(0, page_hint - 2),
            min(doc.page_count, page_hint + 1)
        )
    else:
        pages_to_search = range(min(20, doc.page_count))

    # Try to find and highlight the text
    for page_num in pages_to_search:
        page = doc[page_num]

        # Search for text (try first 50 chars)
        search_text = text_snippet[:50]
        text_instances = page.search_for(search_text)

        if text_instances:
            rect = text_instances[0]

            # Add highlight
            add_highlight(page, rect, severity)

            # Add margin comment
            add_margin_comment(
                page,
                rect,
                comment_counter,
                issue_type,
                suggestion,
                severity
            )

            highlighted_texts.add(text_snippet)
            return comment_counter + 1

    # If not found but have page hint, add general note
    if page_hint and 0 <= page_hint - 1 < doc.page_count:
        page = doc[page_hint - 1]
        rect = fitz.Rect(50, 50, 150, 100)
        add_sticky_note(
            page,
            rect,
            f"[{comment_counter}] {issue_type.upper()}\n\n{suggestion}",
            icon="Help"
        )
        return comment_counter + 1

    return comment_counter


def add_highlight(
    page: fitz.Page,
    rect: fitz.Rect,
    severity: str = 'medium'
):
    """
    Add color-coded highlight to text.

    Args:
        page: PyMuPDF page object
        rect: Rectangle to highlight
        severity: Severity level (critical, major, minor, suggestion, strength)
    """
    try:
        color_rgba = HIGHLIGHT_COLORS.get(severity, HIGHLIGHT_COLORS['medium'])
        color_rgb = color_rgba[:3]  # Get RGB without alpha

        highlight = page.add_highlight_annot(rect)
        highlight.set_colors(stroke=color_rgb)
        highlight.set_opacity(color_rgba[3])
        highlight.update()
    except Exception:
        pass


def add_margin_comment(
    page: fitz.Page,
    text_rect: fitz.Rect,
    comment_num: int,
    issue_type: str,
    suggestion: str,
    severity: str = 'medium'
):
    """
    Add numbered comment in margin with connector line.

    Args:
        page: PyMuPDF page object
        text_rect: Rectangle of highlighted text
        comment_num: Sequential comment number
        issue_type: Type of issue (grammar, logic, etc.)
        suggestion: Suggestion text
        severity: Severity level
    """
    try:
        # Get page dimensions
        page_rect = page.rect
        margin_x = page_rect.width - 180  # Right margin

        # Position comment in right margin
        comment_y = text_rect.y0
        comment_rect = fitz.Rect(
            margin_x,
            comment_y,
            page_rect.width - 10,
            comment_y + 80
        )

        # Get icon for issue type
        icon = ANNOTATION_ICONS.get(issue_type, '📝')

        # Format comment text
        comment_text = f"{icon} [{comment_num}] {issue_type.upper()}\n\n{suggestion[:120]}"

        # Add comment box with background
        add_comment_box(page, comment_rect, comment_text, severity)

        # Add connector line from text to comment
        add_connector_line(page, text_rect, comment_rect)

    except Exception:
        # Fallback to simple sticky note
        add_sticky_note(
            page,
            text_rect,
            f"[{comment_num}] {suggestion}",
            icon="Note"
        )


def add_comment_box(
    page: fitz.Page,
    rect: fitz.Rect,
    text: str,
    severity: str = 'medium'
):
    """
    Add a styled comment box with background color.

    Args:
        page: PyMuPDF page object
        rect: Rectangle for comment box
        text: Comment text
        severity: Severity level for color coding
    """
    try:
        # Get color based on severity
        color_rgba = HIGHLIGHT_COLORS.get(severity, HIGHLIGHT_COLORS['medium'])
        bg_color = (color_rgba[0], color_rgba[1], color_rgba[2])

        # Draw rectangle background
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(
            color=bg_color,
            fill=bg_color,
            width=0.5,
            fill_opacity=0.1
        )
        shape.commit()

        # Add text using insert_text to avoid mirroring (split into lines)
        lines = text.split('\n')
        y_pos = rect.y0 + 10
        for line in lines[:8]:  # Limit to 8 lines
            if line.strip():
                text_point = fitz.Point(rect.x0 + 3, y_pos)
                page.insert_text(
                    text_point,
                    line[:35],  # Truncate long lines
                    fontsize=7,
                    fontname="helv",
                    color=(0, 0, 0)
                )
            y_pos += 9

    except Exception:
        pass


def add_connector_line(
    page: fitz.Page,
    from_rect: fitz.Rect,
    to_rect: fitz.Rect,
    color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
):
    """
    Draw a line connecting highlighted text to margin comment.

    Args:
        page: PyMuPDF page object
        from_rect: Source rectangle (highlighted text)
        to_rect: Target rectangle (comment box)
        color: Line color RGB tuple
    """
    try:
        # Calculate connection points
        start_point = fitz.Point(from_rect.x1, from_rect.y0 + from_rect.height / 2)
        end_point = fitz.Point(to_rect.x0, to_rect.y0 + to_rect.height / 2)

        # Draw line
        shape = page.new_shape()
        shape.draw_line(start_point, end_point)
        shape.finish(
            color=color,
            width=0.5,
            dashes="[2 2]"  # Dashed line
        )
        shape.commit()

    except Exception:
        pass


def add_inline_rewrite(doc: fitz.Document, rewrite: Dict):
    """
    Add rewrite suggestion with strikethrough and margin comment.

    Args:
        doc: PyMuPDF document
        rewrite: Dictionary with 'original', 'suggested', 'page_num', 'explanation'
    """
    try:
        original_text = rewrite.get('original', '')
        suggested_text = rewrite.get('suggested', '')
        page_num = rewrite.get('page_num', 1) - 1  # Convert to 0-indexed
        explanation = rewrite.get('explanation', '')

        if page_num < 0 or page_num >= doc.page_count:
            return

        page = doc[page_num]
        page_rect = page.rect

        # Find original text
        text_instances = page.search_for(original_text[:50])

        if text_instances:
            rect = text_instances[0]

            # Add underline annotation (more visible than strikethrough)
            underline = page.add_underline_annot(rect)
            underline.set_colors(stroke=(0, 0.5, 1))  # Blue underline
            underline.set_info(content=f"REWRITE: {suggested_text}")
            underline.update()

            # Create prominent margin comment box for the rewrite
            margin_x = page_rect.width - 200
            comment_y = rect.y0

            # Make sure it doesn't go off page
            if comment_y + 100 > page_rect.height:
                comment_y = page_rect.height - 110

            comment_rect = fitz.Rect(
                margin_x,
                comment_y,
                page_rect.width - 10,
                comment_y + 100
            )

            # Create comment text with clear formatting
            comment_text = f"✏️ REWRITE SUGGESTION\n\nOriginal:\n{original_text[:60]}...\n\nSuggested:\n{suggested_text[:60]}..."

            # Draw comment box with blue background (for rewrites)
            shape = page.new_shape()
            shape.draw_rect(comment_rect)
            shape.finish(
                color=(0, 0.5, 1),  # Blue border
                fill=(0.9, 0.95, 1),  # Light blue fill
                width=1.5,
                fill_opacity=0.3
            )
            shape.commit()

            # Add comment text using insert_text (split into lines to avoid mirroring)
            lines = comment_text.split('\n')
            y_pos = comment_rect.y0 + 10
            for line in lines[:10]:  # Limit to 10 lines
                if line.strip():
                    text_point = fitz.Point(comment_rect.x0 + 3, y_pos)
                    page.insert_text(
                        text_point,
                        line[:40],  # Truncate long lines to fit in margin
                        fontsize=7,
                        fontname="helv",
                        color=(0, 0, 0)
                    )
                y_pos += 9

            # Draw connector line from underlined text to comment
            start_point = fitz.Point(rect.x1, rect.y0 + rect.height / 2)
            end_point = fitz.Point(comment_rect.x0, comment_rect.y0 + comment_rect.height / 2)

            line_shape = page.new_shape()
            line_shape.draw_line(start_point, end_point)
            line_shape.finish(
                color=(0, 0.5, 1),
                width=1,
                dashes="[2 2]"
            )
            line_shape.commit()

            # Add clickable sticky note for full details
            note_pos = fitz.Point(rect.x1 + 2, rect.y0)
            annot = page.add_text_annot(
                note_pos,
                f"REWRITE SUGGESTION\n\n=== ORIGINAL ===\n{original_text}\n\n=== SUGGESTED ===\n{suggested_text}\n\n=== REASON ===\n{explanation}",
                icon="Note"
            )
            annot.set_colors(stroke=(0, 0.5, 1))  # Blue icon
            annot.set_opacity(0.9)
            annot.update()

    except Exception as e:
        # Fallback: Just add a sticky note
        try:
            if page_num >= 0 and page_num < doc.page_count:
                page = doc[page_num]
                note_pos = fitz.Point(50, 50)
                annot = page.add_text_annot(
                    note_pos,
                    f"REWRITE:\n'{original_text}'\n\n→ '{suggested_text}'\n\n{explanation}",
                    icon="Insert"
                )
                annot.set_opacity(0.9)
                annot.update()
        except:
            pass


def add_section_summary_box(doc: fitz.Document, summary: Dict):
    """
    Add a summary box at the top/bottom of a section.

    Args:
        doc: PyMuPDF document
        summary: Dictionary with 'section', 'page_num', 'strengths', 'issues', 'suggestions', 'score'
    """
    try:
        section_name = summary.get('section', 'Section')
        page_num = summary.get('page_num', 1) - 1
        strengths = summary.get('strengths', [])
        issues = summary.get('issues', [])
        suggestions = summary.get('suggestions', [])
        score = summary.get('score', 0)

        if page_num < 0 or page_num >= doc.page_count:
            return

        page = doc[page_num]
        page_rect = page.rect

        # Create summary box at top of page
        box_height = min(200, page_rect.height * 0.25)
        summary_rect = fitz.Rect(
            50,
            50,
            page_rect.width - 50,
            50 + box_height
        )

        # Build summary text
        summary_text = f"📊 {section_name.upper()} REVIEW (Score: {score}/10)\n\n"

        if strengths:
            summary_text += "✅ Strengths:\n"
            for strength in strengths[:2]:
                summary_text += f"  • {strength[:60]}\n"
            summary_text += "\n"

        if issues:
            summary_text += "⚠️ Issues:\n"
            for issue in issues[:2]:
                summary_text += f"  • {issue[:60]}\n"
            summary_text += "\n"

        if suggestions:
            summary_text += "💡 Suggestions:\n"
            for suggestion in suggestions[:2]:
                summary_text += f"  • {suggestion[:60]}\n"

        # Draw box with border
        shape = page.new_shape()
        shape.draw_rect(summary_rect)
        shape.finish(
            color=(0, 0.5, 1),
            fill=(0.9, 0.95, 1),
            width=1,
            fill_opacity=0.3
        )
        shape.commit()

        # Add text using insert_text (split into lines to avoid mirroring)
        lines = summary_text.split('\n')
        y_pos = summary_rect.y0 + 15
        for line in lines[:20]:  # Limit to 20 lines
            if y_pos > summary_rect.y1 - 10:
                break
            if line.strip():
                text_point = fitz.Point(summary_rect.x0 + 8, y_pos)
                page.insert_text(
                    text_point,
                    line[:80],  # Truncate very long lines
                    fontsize=8,
                    fontname="helv",
                    color=(0, 0, 0)
                )
            y_pos += 10

    except Exception:
        pass


def add_annotation_legend(page: fitz.Page):
    """
    Add a color legend explaining the annotation system.

    Args:
        page: PyMuPDF page object (typically first page)
    """
    try:
        page_rect = page.rect

        # Position legend in top-right corner
        legend_width = 200
        legend_height = 120
        legend_rect = fitz.Rect(
            page_rect.width - legend_width - 10,
            10,
            page_rect.width - 10,
            10 + legend_height
        )

        # Draw legend box
        shape = page.new_shape()
        shape.draw_rect(legend_rect)
        shape.finish(
            color=(0, 0, 0),
            fill=(1, 1, 1),
            width=1,
            fill_opacity=0.9
        )
        shape.commit()

        # Add title using insert_text (not insert_textbox to avoid mirroring)
        title_point = fitz.Point(legend_rect.x0 + legend_width / 2 - 50, legend_rect.y0 + 15)
        page.insert_text(
            title_point,
            "ANNOTATION LEGEND",
            fontsize=9,
            fontname="helv",
            color=(0, 0, 0)
        )

        # Add color samples
        y_offset = 25
        items = [
            ("Critical Issues", HIGHLIGHT_COLORS['critical']),
            ("Major Issues", HIGHLIGHT_COLORS['major']),
            ("Minor Issues", HIGHLIGHT_COLORS['minor']),
            ("Suggestions", HIGHLIGHT_COLORS['suggestion']),
            ("Strengths", HIGHLIGHT_COLORS['strength'])
        ]

        for label, color in items:
            # Draw color sample
            sample_rect = fitz.Rect(
                legend_rect.x0 + 10,
                legend_rect.y0 + y_offset,
                legend_rect.x0 + 30,
                legend_rect.y0 + y_offset + 12
            )

            sample_shape = page.new_shape()
            sample_shape.draw_rect(sample_rect)
            sample_shape.finish(
                color=color[:3],
                fill=color[:3],
                width=0.5,
                fill_opacity=color[3]
            )
            sample_shape.commit()

            # Add label using insert_text
            label_point = fitz.Point(legend_rect.x0 + 35, legend_rect.y0 + y_offset + 9)
            page.insert_text(
                label_point,
                label,
                fontsize=7,
                fontname="helv",
                color=(0, 0, 0)
            )

            y_offset += 16

    except Exception:
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
        # Create icon position
        icon_rect = fitz.Rect(
            rect.x1 - 20,
            rect.y0,
            rect.x1,
            rect.y0 + 20
        )

        # Add text annotation
        annot = page.add_text_annot(
            icon_rect.top_left,
            note_text,
            icon=icon
        )
        annot.set_opacity(0.8)
        annot.update()
    except Exception:
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

    # Add title using insert_text
    title_point = fitz.Point(200, 70)
    new_page.insert_text(
        title_point,
        "Thesis Review Summary",
        fontsize=18,
        fontname="helv",
        color=(0, 0, 0)
    )

    # Add issue count
    count_point = fitz.Point(50, 130)
    new_page.insert_text(
        count_point,
        f"Total Issues Found: {issue_count}",
        fontsize=12,
        fontname="helv",
        color=(0, 0, 0)
    )

    # Add summary (truncate if too long and split into lines)
    summary_text = critique_summary[:1000] + "..." if len(critique_summary) > 1000 else critique_summary
    lines = summary_text.split('\n')
    y_pos = 170
    for line in lines[:50]:  # Limit to 50 lines
        if y_pos > 750:
            break
        if line.strip():
            text_point = fitz.Point(50, y_pos)
            new_page.insert_text(
                text_point,
                line[:100],  # Truncate very long lines
                fontsize=10,
                fontname="helv",
                color=(0, 0, 0)
            )
        y_pos += 12

    # Save to bytes
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    doc.close()

    result_bytes = output_buffer.getvalue()
    output_buffer.close()

    return result_bytes
