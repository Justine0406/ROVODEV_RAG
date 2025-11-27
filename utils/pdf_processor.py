"""
PDF processing utilities for text extraction and chunking.
"""

import fitz  # PyMuPDF
import re
from typing import Dict, List, Tuple


def validate_pdf(pdf_bytes: bytes) -> Tuple[bool, str]:
    """
    Check if PDF is valid and within limits.
    
    Args:
        pdf_bytes: PDF file as bytes
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    try:
        # Check file size (10MB limit)
        size_mb = len(pdf_bytes) / (1024 * 1024)
        if size_mb > 10:
            return False, f"File too large ({size_mb:.1f}MB). Maximum 10MB allowed."
        
        # Try to open PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Check page count
        page_count = doc.page_count
        if page_count > 50:
            doc.close()
            return False, f"Too many pages ({page_count}). Recommended maximum is 50 pages for optimal performance."
        
        if page_count == 0:
            doc.close()
            return False, "PDF appears to be empty."
        
        doc.close()
        return True, ""
        
    except Exception as e:
        return False, f"Invalid or corrupted PDF file: {str(e)}"


def extract_text_with_metadata(pdf_bytes: bytes) -> Dict:
    """
    Extract text from PDF with page numbers and coordinates.
    
    Args:
        pdf_bytes: PDF file as bytes
    
    Returns:
        {
            'full_text': str,
            'pages': [
                {
                    'page_num': int,
                    'text': str,
                    'blocks': [{'bbox': tuple, 'text': str}]
                }
            ],
            'total_pages': int,
            'total_chars': int
        }
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    pages_data = []
    full_text = []
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Extract text blocks with coordinates
        blocks = []
        text_blocks = page.get_text("blocks")  # Returns list of (x0, y0, x1, y1, text, block_no, block_type)
        
        page_text_parts = []
        for block in text_blocks:
            if len(block) >= 5:  # Valid text block
                bbox = block[:4]
                text = block[4]
                
                # Clean text
                text = text.strip()
                if text:
                    blocks.append({
                        'bbox': bbox,
                        'text': text
                    })
                    page_text_parts.append(text)
        
        # Combine page text
        page_text = "\n".join(page_text_parts)
        
        pages_data.append({
            'page_num': page_num + 1,  # 1-indexed
            'text': page_text,
            'blocks': blocks
        })
        
        full_text.append(page_text)
    
    doc.close()
    
    combined_text = "\n\n".join(full_text)
    
    return {
        'full_text': combined_text,
        'pages': pages_data,
        'total_pages': len(pages_data),
        'total_chars': len(combined_text)
    }


def chunk_text(pages_data: List[Dict], chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
    """
    Split text into overlapping chunks with metadata.
    
    Args:
        pages_data: List of page dictionaries from extract_text_with_metadata
        chunk_size: Target chunk size in characters
        overlap: Overlap size in characters
    
    Returns:
        List of chunk dictionaries with metadata:
        [
            {
                'text': str,
                'chunk_id': int,
                'page_num': int,
                'start_char': int,
                'end_char': int
            }
        ]
    """
    chunks = []
    chunk_id = 0
    
    for page_data in pages_data:
        page_num = page_data['page_num']
        page_text = page_data['text']
        
        # Skip empty pages
        if not page_text.strip():
            continue
        
        # Split into sentences to avoid breaking mid-sentence
        sentences = re.split(r'(?<=[.!?])\s+', page_text)
        
        current_chunk = ""
        start_char = 0
        
        for sentence in sentences:
            # If adding this sentence exceeds chunk_size, save current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'chunk_id': chunk_id,
                    'page_num': page_num,
                    'start_char': start_char,
                    'end_char': start_char + len(current_chunk)
                })
                
                chunk_id += 1
                
                # Start new chunk with overlap
                # Take last 'overlap' characters from current chunk
                if len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + " " + sentence
                    start_char = start_char + len(current_chunk) - len(overlap_text) - len(sentence) - 1
                else:
                    current_chunk = sentence
                    start_char = start_char + len(current_chunk) - len(sentence)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add remaining text as final chunk for this page
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_id': chunk_id,
                'page_num': page_num,
                'start_char': start_char,
                'end_char': start_char + len(current_chunk)
            })
            chunk_id += 1
    
    return chunks
