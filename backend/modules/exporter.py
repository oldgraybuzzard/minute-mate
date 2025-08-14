"""
MinuteMate Document Exporter
Exports formatted meeting minutes to DOCX documents.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

logger = logging.getLogger(__name__)

class DocxExporter:
    """Exports meeting minutes to DOCX format"""
    
    def __init__(self):
        """Initialize the DOCX exporter"""
        self.document = None
        logger.info("DocxExporter initialized")
    
    def _create_document(self) -> Document:
        """Create a new document with proper styling"""
        doc = Document()
        
        # Set up document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Create custom styles
        self._create_styles(doc)
        
        return doc
    
    def _create_styles(self, doc: Document) -> None:
        """Create custom styles for the document"""
        styles = doc.styles
        
        # Title style
        try:
            title_style = styles['Title']
        except KeyError:
            title_style = styles.add_style('Title', WD_STYLE_TYPE.PARAGRAPH)
        
        title_font = title_style.font
        title_font.name = 'Arial'
        title_font.size = Pt(16)
        title_font.bold = True
        title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_style.paragraph_format.space_after = Pt(12)
        
        # Heading 1 style
        try:
            heading1_style = styles['Heading 1']
        except KeyError:
            heading1_style = styles.add_style('Heading 1', WD_STYLE_TYPE.PARAGRAPH)
        
        heading1_font = heading1_style.font
        heading1_font.name = 'Arial'
        heading1_font.size = Pt(14)
        heading1_font.bold = True
        heading1_style.paragraph_format.space_before = Pt(12)
        heading1_style.paragraph_format.space_after = Pt(6)
        
        # Normal style
        normal_style = styles['Normal']
        normal_font = normal_style.font
        normal_font.name = 'Arial'
        normal_font.size = Pt(11)
        normal_style.paragraph_format.space_after = Pt(6)
    
    def _add_header(self, doc: Document, title: str, date: str) -> None:
        """Add document header"""
        # Add title
        title_para = doc.add_paragraph(title, style='Title')
        
        # Add date
        if date:
            date_para = doc.add_paragraph(f"Date: {date}")
            date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            date_para.add_run().add_break()
    
    def _parse_formatted_text(self, doc: Document, formatted_text: str) -> None:
        """Parse formatted text and add to document with proper styling"""
        lines = formatted_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            if line.upper() in ['ATTENDEES:', 'CALL TO ORDER', 'BUSINESS', 'ADJOURNMENT']:
                doc.add_heading(line.replace(':', ''), level=1)
            elif line.startswith('MOTION #'):
                doc.add_heading(line, level=2)
            elif line.startswith('•'):
                # Bullet point
                para = doc.add_paragraph(style='List Bullet')
                para.add_run(line[1:].strip())
            elif ':' in line and len(line.split(':')) == 2:
                # Key-value pair
                key, value = line.split(':', 1)
                para = doc.add_paragraph()
                para.add_run(f'{key.strip()}: ').bold = True
                para.add_run(value.strip())
            else:
                # Regular paragraph
                doc.add_paragraph(line)
    
    def export_to_docx(self, formatted_minutes: str, output_path: str,
                      title: Optional[str] = None, date: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Export formatted minutes to DOCX file
        
        Args:
            formatted_minutes: Formatted minutes text
            output_path: Path for output file
            title: Document title
            date: Meeting date
            metadata: Additional metadata
            
        Returns:
            str: Path to created file
        """
        logger.info(f"Exporting minutes to DOCX: {output_path}")
        
        try:
            # Create document
            doc = self._create_document()
            
            # Add header
            doc_title = title or "Meeting Minutes"
            doc_date = date or datetime.now().strftime("%B %d, %Y")
            self._add_header(doc, doc_title, doc_date)
            
            # Parse and add formatted text
            self._parse_formatted_text(doc, formatted_minutes)
            
            # Add footer with metadata
            if metadata:
                doc.add_page_break()
                doc.add_heading('Document Information', level=1)
                
                info_para = doc.add_paragraph()
                info_para.add_run('Generated by: ').bold = True
                info_para.add_run('MinuteMate AI\n')
                info_para.add_run('Generated on: ').bold = True
                info_para.add_run(datetime.now().strftime("%B %d, %Y at %I:%M %p"))
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save document
            doc.save(output_path)
            
            logger.info(f"DOCX export completed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"DOCX export failed: {e}")
            raise
    
    def create_template_document(self, output_path: str) -> str:
        """
        Create a template DOCX document for reference
        
        Args:
            output_path: Path for template file
            
        Returns:
            str: Path to created template
        """
        logger.info(f"Creating template document: {output_path}")
        
        doc = self._create_document()
        
        # Add sample content
        self._add_header(doc, "Sample Meeting Minutes Template", "Month Day, Year")
        
        # Sample attendees
        doc.add_heading('Attendees', level=1)
        sample_attendees = ["John Smith (Chair)", "Jane Doe (Secretary)", "Bob Johnson"]
        for attendee in sample_attendees:
            para = doc.add_paragraph(style='List Bullet')
            para.add_run(attendee)
        
        # Sample call to order
        doc.add_heading('Call to Order', level=1)
        doc.add_paragraph("The meeting was called to order at [Time] by [Chair Name].")
        
        # Sample motion
        doc.add_heading('Business', level=1)
        doc.add_heading('Motion #1', level=2)
        
        motion_para = doc.add_paragraph()
        motion_para.add_run('Moved by: ').bold = True
        motion_para.add_run('John Smith\n')
        motion_para.add_run('Motion: ').bold = True
        motion_para.add_run('To approve the budget.\n\n')
        motion_para.add_run('Vote: ').bold = True
        motion_para.add_run('PASSED')
        
        # Save template
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        
        logger.info(f"Template document created: {output_path}")
        return output_path
