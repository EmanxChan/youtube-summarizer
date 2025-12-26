#!/usr/bin/env python3
"""
Export format converters for content summaries.
Supports Markdown, PDF, Plain Text, and JSON exports.
"""

import json
import re
from datetime import datetime
from typing import Dict, Optional
from io import BytesIO


def markdown_to_plain_text(markdown_content: str) -> str:
    """
    Convert markdown content to plain text.

    Args:
        markdown_content: Markdown formatted string

    Returns:
        Plain text string
    """
    text = markdown_content

    # Remove markdown headers (keep text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove highlight/mark tags
    text = re.sub(r'<mark>(.+?)</mark>', r'\1', text)
    text = re.sub(r'</?mark>', '', text)

    # Remove inline code
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Convert links to plain text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove horizontal rules
    text = re.sub(r'^[-─]{3,}$', '\n', text, flags=re.MULTILINE)

    # Convert bullet points to simple dashes
    text = re.sub(r'^[\*\-]\s+', '- ', text, flags=re.MULTILINE)

    # Convert numbered lists
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)

    # Convert checkboxes
    text = re.sub(r'- \[ \]', '- [ ]', text)
    text = re.sub(r'- \[x\]', '- [x]', text)

    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def markdown_to_json(markdown_content: str, metadata: Optional[Dict] = None) -> str:
    """
    Convert markdown content to structured JSON.

    Args:
        markdown_content: Markdown formatted string
        metadata: Optional metadata dict (title, url, etc.)

    Returns:
        JSON string
    """
    # Parse sections from markdown
    sections = {}
    current_section = "content"
    current_content = []

    lines = markdown_content.split('\n')

    title = None
    source_url = None

    for line in lines:
        # Extract title (first H1)
        if line.startswith('# ') and title is None:
            title = line[2:].strip()
            continue

        # Extract source URL
        if line.startswith('**Source:**'):
            match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
            if match:
                source_url = match.group(2)
            continue

        # Detect section headers
        if line.startswith('## '):
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()

            # Start new section
            section_title = line[3:].strip()
            # Clean emoji and normalize
            section_key = re.sub(r'[^\w\s]', '', section_title).strip().lower().replace(' ', '_')
            current_section = section_key
            current_content = []
            continue

        # Skip horizontal rules
        if re.match(r'^[-─]{3,}$', line):
            continue

        current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    # Extract key insights as list
    key_insights = []
    if 'key_insights' in sections:
        insights_text = sections['key_insights']
        for line in insights_text.split('\n'):
            line = line.strip()
            if line and re.match(r'^\d+\.', line):
                # Remove number prefix
                insight = re.sub(r'^\d+\.\s*', '', line)
                key_insights.append(insight)

    # Extract highlights as list
    highlights = []
    if 'highlights' in sections:
        for line in sections['highlights'].split('\n'):
            line = line.strip()
            if line.startswith('- '):
                highlights.append(line[2:])

    # Extract next steps as list
    next_steps = []
    if 'next_steps' in sections:
        for line in sections['next_steps'].split('\n'):
            line = line.strip()
            if line.startswith('- [ ]'):
                next_steps.append(line[6:].strip())

    # Build structured output
    output = {
        "title": title or metadata.get('title', 'Untitled') if metadata else 'Untitled',
        "source_url": source_url or (metadata.get('url') if metadata else None),
        "exported_at": datetime.now().isoformat(),
        "key_insights": key_insights,
        "highlights": highlights,
        "executive_summary": sections.get('executive_summary', ''),
        "next_steps": next_steps,
        "full_content": sections.get('full_transcript', sections.get('full_article', '')),
    }

    # Add any extra metadata
    if metadata:
        output["metadata"] = {
            k: v for k, v in metadata.items()
            if k not in ['title', 'url', 'content']
        }

    return json.dumps(output, indent=2, ensure_ascii=False)


def _markdown_to_pdf_reportlab(markdown_content: str, title: str = "Summary") -> bytes:
    """Fallback PDF generation using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Heading1'],
                             fontSize=18, spaceAfter=12))
    styles.add(ParagraphStyle(name='CustomHeading', parent=styles['Heading2'],
                             fontSize=14, spaceAfter=8, spaceBefore=12))
    styles.add(ParagraphStyle(name='CustomBody', parent=styles['Normal'],
                             fontSize=10, spaceAfter=6))
    styles.add(ParagraphStyle(name='CustomBullet', parent=styles['Normal'],
                             fontSize=10, leftIndent=20, spaceAfter=4))

    story = []
    lines = markdown_content.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue

        # Clean markdown formatting for PDF
        clean_line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
        clean_line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', clean_line)
        clean_line = re.sub(r'<mark>(.+?)</mark>', r'<font backColor="yellow">\1</font>', clean_line)  # Highlights
        clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_line)

        if line.startswith('# '):
            text = clean_line[2:]
            story.append(Paragraph(text, styles['CustomTitle']))
        elif line.startswith('## '):
            text = clean_line[3:]
            story.append(Paragraph(text, styles['CustomHeading']))
        elif line.startswith('### '):
            text = clean_line[4:]
            story.append(Paragraph(text, styles['Heading3']))
        elif line.startswith('- ') or line.startswith('* '):
            text = '• ' + clean_line[2:]
            story.append(Paragraph(text, styles['CustomBullet']))
        elif re.match(r'^\d+\.', line):
            story.append(Paragraph(clean_line, styles['CustomBullet']))
        elif re.match(r'^[-─]{3,}$', line):
            story.append(Spacer(1, 12))
        else:
            story.append(Paragraph(clean_line, styles['CustomBody']))

    doc.build(story)
    return buffer.getvalue()


def markdown_to_pdf(markdown_content: str, title: str = "Summary") -> bytes:
    """
    Convert markdown content to PDF.

    Args:
        markdown_content: Markdown formatted string
        title: Document title for PDF metadata

    Returns:
        PDF file as bytes
    """
    # Try reportlab first (more reliable across environments)
    try:
        return _markdown_to_pdf_reportlab(markdown_content, title)
    except ImportError:
        pass
    except Exception as e:
        # reportlab failed, try fpdf2
        pass

    # Try fpdf2 as fallback
    try:
        from fpdf import FPDF
    except (ImportError, Exception) as e:
        raise ImportError(
            "PDF export requires reportlab or fpdf2. "
            "Install with: pip install reportlab"
        )

    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.set_auto_page_break(auto=True, margin=15)

        def header(self):
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, 'Content Summary', align='R')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Page {self.page_no()}', align='C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # Process markdown line by line
    lines = markdown_content.split('\n')

    for line in lines:
        line = line.rstrip()

        # Skip empty lines (add small space)
        if not line:
            pdf.ln(3)
            continue

        # Handle headers
        if line.startswith('# '):
            pdf.set_font('Helvetica', 'B', 18)
            pdf.set_text_color(0, 0, 0)
            text = line[2:].strip()
            pdf.multi_cell(0, 10, text)
            pdf.ln(2)
            continue

        if line.startswith('## '):
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            text = line[3:].strip()
            pdf.multi_cell(0, 8, text)
            pdf.ln(2)
            continue

        if line.startswith('### '):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(52, 73, 94)
            text = line[4:].strip()
            pdf.multi_cell(0, 7, text)
            pdf.ln(1)
            continue

        # Handle horizontal rules
        if re.match(r'^[-─]{3,}$', line):
            pdf.set_draw_color(200, 200, 200)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(5)
            continue

        # Handle bullet points
        if line.startswith('- ') or line.startswith('* '):
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            text = '  • ' + line[2:].strip()
            # Clean markdown formatting
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'<mark>(.+?)</mark>', r'[\1]', text)  # Convert highlights to brackets
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            pdf.multi_cell(0, 6, text)
            continue

        # Handle numbered lists
        if re.match(r'^\d+\.\s', line):
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            text = '  ' + line.strip()
            # Clean markdown formatting
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'<mark>(.+?)</mark>', r'[\1]', text)  # Convert highlights to brackets
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            pdf.multi_cell(0, 6, text)
            continue

        # Handle checkboxes
        if line.startswith('- [ ]') or line.startswith('- [x]'):
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            checkbox = '☐' if '[ ]' in line else '☑'
            text = f'  {checkbox} ' + line[6:].strip()
            pdf.multi_cell(0, 6, text)
            continue

        # Handle bold text in metadata lines
        if line.startswith('**') and ':**' in line:
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(80, 80, 80)
            # Clean markdown
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            text = re.sub(r'<mark>(.+?)</mark>', r'[\1]', text)  # Convert highlights to brackets
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            pdf.multi_cell(0, 6, text)
            continue

        # Regular paragraph text
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        # Clean markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        text = re.sub(r'\*(.+?)\*', r'\1', line)
        text = re.sub(r'<mark>(.+?)</mark>', r'[\1]', text)  # Convert highlights to brackets
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        pdf.multi_cell(0, 6, text)

    # Return as bytes
    return pdf.output()


def markdown_to_html(markdown_content: str, title: str = "Summary") -> str:
    """
    Convert markdown to standalone HTML document.

    Args:
        markdown_content: Markdown formatted string
        title: HTML page title

    Returns:
        HTML string
    """
    # Convert markdown to HTML
    html_body = markdown_content

    # Convert headers
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)

    # Convert bold/italic
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_body)

    # Convert links
    html_body = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_body)

    # Convert inline code
    html_body = re.sub(r'`(.+?)`', r'<code>\1</code>', html_body)

    # Convert horizontal rules
    html_body = re.sub(r'^[-─]{3,}$', '<hr>', html_body, flags=re.MULTILINE)

    # Convert bullet lists (simple approach)
    lines = html_body.split('\n')
    in_list = False
    new_lines = []

    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            item_content = line.strip()[2:]
            # Handle checkboxes
            if item_content.startswith('[ ]'):
                item_content = '☐ ' + item_content[4:]
            elif item_content.startswith('[x]'):
                item_content = '☑ ' + item_content[4:]
            new_lines.append(f'<li>{item_content}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)

    if in_list:
        new_lines.append('</ul>')

    html_body = '\n'.join(new_lines)

    # Convert numbered lists
    html_body = re.sub(r'^(\d+)\.\s+(.+)$', r'<p><strong>\1.</strong> \2</p>', html_body, flags=re.MULTILINE)

    # Wrap paragraphs (simple approach - non-tagged lines)
    lines = html_body.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('<') and not stripped.endswith('>'):
            new_lines.append(f'<p>{stripped}</p>')
        else:
            new_lines.append(line)
    html_body = '\n'.join(new_lines)

    # Build full HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        h3 {{ color: #34495e; }}
        a {{ color: #3498db; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 5px 0; }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background: #f9f9f9;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    return html


# Export format registry
EXPORT_FORMATS = {
    'markdown': {
        'label': 'Markdown (.md)',
        'extension': '.md',
        'mime': 'text/markdown',
        'converter': lambda content, meta: content,  # Already markdown
    },
    'pdf': {
        'label': 'PDF (.pdf)',
        'extension': '.pdf',
        'mime': 'application/pdf',
        'converter': lambda content, meta: markdown_to_pdf(content, meta.get('title', 'Summary')),
    },
    'txt': {
        'label': 'Plain Text (.txt)',
        'extension': '.txt',
        'mime': 'text/plain',
        'converter': lambda content, meta: markdown_to_plain_text(content),
    },
    'json': {
        'label': 'JSON (.json)',
        'extension': '.json',
        'mime': 'application/json',
        'converter': lambda content, meta: markdown_to_json(content, meta),
    },
    'html': {
        'label': 'HTML (.html)',
        'extension': '.html',
        'mime': 'text/html',
        'converter': lambda content, meta: markdown_to_html(content, meta.get('title', 'Summary')),
    },
}


def convert_for_export(markdown_content: str, format_key: str, metadata: Optional[Dict] = None) -> tuple:
    """
    Convert markdown content to specified export format.

    Args:
        markdown_content: Markdown formatted string
        format_key: Export format key (markdown, pdf, txt, json, html)
        metadata: Optional metadata dict

    Returns:
        tuple: (converted_content, mime_type, file_extension)
    """
    if format_key not in EXPORT_FORMATS:
        raise ValueError(f"Unknown export format: {format_key}")

    fmt = EXPORT_FORMATS[format_key]
    metadata = metadata or {}

    converted = fmt['converter'](markdown_content, metadata)

    return converted, fmt['mime'], fmt['extension']
