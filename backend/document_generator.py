"""
Enhanced Document Generator for Meeting Minutes
Converts JSON meeting minutes to professional user-friendly formats (DOCX, HTML, PDF)
Supports multiple templates and customizable formatting styles
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from docx import Document
    from docx.shared import Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.shared import OxmlElement, qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from weasyprint import HTML, CSS
    PDF_AVAILABLE = True
except (ImportError, OSError) as e:
    PDF_AVAILABLE = False
    # OSError can occur on macOS if system libraries are missing

logger = logging.getLogger(__name__)

class DocumentGenerator:
    """Generate user-friendly documents from meeting minutes JSON"""

    def __init__(self, output_dir: str):
        """
        Initialize document generator

        Args:
            output_dir: Directory to save generated documents
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Available templates
        self.templates = {
            'professional': 'Professional Corporate Template',
            'formal': 'Formal Government/Board Template',
            'casual': 'Casual Team Meeting Template',
            'academic': 'Academic Committee Template'
        }

        logger.info(f"DocumentGenerator initialized with output_dir: {output_dir}")
        logger.info(f"DOCX support: {DOCX_AVAILABLE}")
        logger.info(f"PDF support: {PDF_AVAILABLE}")
        logger.info(f"Available templates: {list(self.templates.keys())}")
    
    def generate_documents(self, meeting_minutes: Dict[str, Any], job_id: str) -> Dict[str, str]:
        """
        Generate multiple document formats from meeting minutes
        
        Args:
            meeting_minutes: JSON meeting minutes data
            job_id: Job ID for filename generation
            
        Returns:
            Dictionary with format -> file_path mappings
        """
        results = {}
        
        try:
            # Generate HTML (always available)
            html_path = self.generate_html(meeting_minutes, job_id)
            results['html'] = html_path
            
            # Generate DOCX if available
            if DOCX_AVAILABLE:
                docx_path = self.generate_docx(meeting_minutes, job_id)
                if docx_path:
                    results['docx'] = docx_path

            # Generate PDF if available
            if PDF_AVAILABLE and 'html' in results:
                pdf_path = self.generate_pdf_from_html(results['html'], job_id)
                if pdf_path:
                    results['pdf'] = pdf_path

            # Always keep JSON as backup
            json_path = self.generate_json(meeting_minutes, job_id)
            results['json'] = json_path
            
            logger.info(f"Generated documents for job {job_id}: {list(results.keys())}")
            return results
            
        except Exception as e:
            logger.error(f"Document generation failed for job {job_id}: {str(e)}")
            # Fallback to JSON only
            json_path = self.generate_json(meeting_minutes, job_id)
            return {'json': json_path}
    
    def generate_html(self, meeting_minutes: Dict[str, Any], job_id: str) -> str:
        """Generate HTML document"""
        
        meeting_info = meeting_minutes.get('meeting_info', {})
        attendees = meeting_minutes.get('attendees', [])
        agenda_items = meeting_minutes.get('agenda_items', [])
        motions = meeting_minutes.get('motions', [])
        action_items = meeting_minutes.get('action_items', [])
        key_decisions = meeting_minutes.get('key_decisions', [])
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Meeting Minutes - {meeting_info.get('title', 'Meeting')}</title>
            <style>
                /* Professional Meeting Minutes Stylesheet */
                @media print {{
                    body {{ margin: 0; }}
                    .no-print {{ display: none; }}
                }}

                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 40px auto;
                    max-width: 1000px;
                    line-height: 1.6;
                    color: #333;
                    background: #fff;
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding: 30px 0;
                    border-bottom: 3px solid #2c3e50;
                }}

                .header h1 {{
                    color: #2c3e50;
                    margin: 0 0 15px 0;
                    font-size: 2.2em;
                    font-weight: 300;
                }}

                .header p {{
                    color: #7f8c8d;
                    font-size: 1.1em;
                    margin: 0;
                }}

                .meeting-info {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 25px;
                    border-radius: 8px;
                    margin-bottom: 35px;
                    border-left: 5px solid #3498db;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}

                .meeting-info p {{
                    margin: 8px 0;
                    font-weight: 500;
                }}

                .section {{
                    margin-bottom: 35px;
                    page-break-inside: avoid;
                }}

                .section h2 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 8px;
                    margin-bottom: 20px;
                    font-size: 1.4em;
                    font-weight: 600;
                }}

                .attendee-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 15px;
                    margin-top: 15px;
                }}

                .attendee {{
                    background: #fff;
                    padding: 12px 15px;
                    border-radius: 6px;
                    border-left: 4px solid #27ae60;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}

                .attendee strong {{
                    color: #2c3e50;
                    display: block;
                    margin-bottom: 4px;
                }}

                .attendee em {{
                    color: #7f8c8d;
                    font-style: normal;
                    font-size: 0.9em;
                }}

                .motion {{
                    background: linear-gradient(135deg, #e3f2fd 0%, #f8f9fa 100%);
                    padding: 20px;
                    margin-bottom: 20px;
                    border-left: 5px solid #2196f3;
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}

                .motion h3 {{
                    color: #1976d2;
                    margin-top: 0;
                    margin-bottom: 15px;
                }}

                .action-item {{
                    background: linear-gradient(135deg, #fff8e1 0%, #f8f9fa 100%);
                    padding: 20px;
                    margin-bottom: 20px;
                    border-left: 5px solid #ff9800;
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}

                .action-item h3 {{
                    color: #f57c00;
                    margin-top: 0;
                    margin-bottom: 15px;
                }}

                .agenda-item {{
                    margin-bottom: 25px;
                    padding: 15px 0;
                    border-bottom: 1px solid #ecf0f1;
                }}

                .agenda-item h3 {{
                    color: #34495e;
                    margin-bottom: 12px;
                }}

                .agenda-item p {{
                    margin: 8px 0;
                    padding-left: 15px;
                }}

                .key-decisions ul {{
                    list-style: none;
                    padding: 0;
                }}

                .key-decisions li {{
                    background: #e8f5e8;
                    margin: 10px 0;
                    padding: 12px 15px;
                    border-left: 4px solid #4caf50;
                    border-radius: 4px;
                }}

                .footer {{
                    margin-top: 50px;
                    text-align: center;
                    color: #95a5a6;
                    font-size: 0.9em;
                    border-top: 1px solid #ecf0f1;
                    padding-top: 20px;
                }}

                /* Responsive design */
                @media (max-width: 768px) {{
                    body {{ margin: 20px; }}
                    .attendee-list {{ grid-template-columns: 1fr; }}
                    .header h1 {{ font-size: 1.8em; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{meeting_info.get('title', 'Meeting Minutes')}</h1>
                <p><strong>Date:</strong> {meeting_info.get('date', 'N/A')} | 
                   <strong>Time:</strong> {meeting_info.get('time', 'N/A')} | 
                   <strong>Location:</strong> {meeting_info.get('location', 'N/A')}</p>
            </div>
            
            <div class="section">
                <h2>Meeting Information</h2>
                <div class="meeting-info">
                    <p><strong>Meeting Type:</strong> {meeting_info.get('meeting_type', 'N/A')}</p>
                    <p><strong>Secretary:</strong> {meeting_minutes.get('secretary', 'N/A')}</p>
                    <p><strong>Chairperson:</strong> {meeting_minutes.get('chairperson', 'N/A')}</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Attendees ({len(attendees)})</h2>
                <div class="attendee-list">
        """
        
        for attendee in attendees:
            status = "✓ Present" if attendee.get('present', True) else "✗ Absent"
            html_content += f"""
                    <div class="attendee">
                        <strong>{attendee.get('name', 'Unknown')}</strong><br>
                        <em>{attendee.get('role', 'Participant')}</em> - {status}
                    </div>
            """
        
        html_content += """
                </div>
            </div>
        """
        
        if agenda_items:
            html_content += """
            <div class="section">
                <h2>Agenda Items</h2>
            """
            for item in agenda_items:
                html_content += f"""
                <div class="agenda-item">
                    <h3>{item.get('item_number', '')}. {item.get('title', 'Agenda Item')}</h3>
                    <p><strong>Discussion:</strong> {item.get('discussion', 'No discussion recorded.')}</p>
                    <p><strong>Outcome:</strong> {item.get('outcome', 'No outcome recorded.')}</p>
                </div>
                """
            html_content += "</div>"
        
        if motions:
            html_content += """
            <div class="section">
                <h2>Motions</h2>
            """
            for motion in motions:
                html_content += f"""
                <div class="motion">
                    <h3>Motion {motion.get('motion_number', '')}</h3>
                    <p><strong>Description:</strong> {motion.get('description', 'No description')}</p>
                    <p><strong>Moved by:</strong> {motion.get('moved_by', 'Unknown')}</p>
                    <p><strong>Seconded by:</strong> {motion.get('seconded_by', 'Unknown')}</p>
                    <p><strong>Result:</strong> {motion.get('result', 'Unknown')}</p>
                </div>
                """
            html_content += "</div>"
        
        if key_decisions:
            html_content += """
            <div class="section key-decisions">
                <h2>Key Decisions</h2>
                <ul>
            """
            for decision in key_decisions:
                html_content += f"<li>{decision}</li>"
            html_content += """
                </ul>
            </div>
            """
        
        html_content += """
            <div class="footer">
                <p><em>Generated by MinuteMate on """ + datetime.now().strftime('%Y-%m-%d at %H:%M') + """</em></p>
            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"meeting_minutes_{job_id}_{timestamp}.html"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML document: {file_path}")
        return str(file_path)
    
    def generate_json(self, meeting_minutes: Dict[str, Any], job_id: str) -> str:
        """Generate JSON document (backup format)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"meeting_minutes_{job_id}_{timestamp}.json"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(meeting_minutes, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated JSON document: {file_path}")
        return str(file_path)
    
    def generate_docx(self, meeting_minutes: Dict[str, Any], job_id: str) -> Optional[str]:
        """Generate DOCX document"""
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not available, skipping DOCX generation")
            return None
        
        try:
            doc = Document()
            
            # Add title
            meeting_info = meeting_minutes.get('meeting_info', {})
            title = doc.add_heading(meeting_info.get('title', 'Meeting Minutes'), 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add meeting info
            info_para = doc.add_paragraph()
            info_para.add_run(f"Date: {meeting_info.get('date', 'N/A')} | ")
            info_para.add_run(f"Time: {meeting_info.get('time', 'N/A')} | ")
            info_para.add_run(f"Location: {meeting_info.get('location', 'N/A')}")
            info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_paragraph()  # Spacing
            
            # Add attendees
            attendees = meeting_minutes.get('attendees', [])
            if attendees:
                doc.add_heading('Attendees', level=1)
                for attendee in attendees:
                    status = "Present" if attendee.get('present', True) else "Absent"
                    doc.add_paragraph(f"• {attendee.get('name', 'Unknown')} - {attendee.get('role', 'Participant')} ({status})")
            
            # Add agenda items
            agenda_items = meeting_minutes.get('agenda_items', [])
            if agenda_items:
                doc.add_heading('Agenda Items', level=1)
                for item in agenda_items:
                    doc.add_heading(f"{item.get('item_number', '')}. {item.get('title', 'Agenda Item')}", level=2)
                    doc.add_paragraph(f"Discussion: {item.get('discussion', 'No discussion recorded.')}")
                    doc.add_paragraph(f"Outcome: {item.get('outcome', 'No outcome recorded.')}")
            
            # Add motions
            motions = meeting_minutes.get('motions', [])
            if motions:
                doc.add_heading('Motions', level=1)
                for motion in motions:
                    doc.add_heading(f"Motion {motion.get('motion_number', '')}", level=2)
                    doc.add_paragraph(f"Description: {motion.get('description', 'No description')}")
                    doc.add_paragraph(f"Moved by: {motion.get('moved_by', 'Unknown')}")
                    doc.add_paragraph(f"Seconded by: {motion.get('seconded_by', 'Unknown')}")
                    doc.add_paragraph(f"Result: {motion.get('result', 'Unknown')}")
            
            # Add key decisions
            key_decisions = meeting_minutes.get('key_decisions', [])
            if key_decisions:
                doc.add_heading('Key Decisions', level=1)
                for decision in key_decisions:
                    doc.add_paragraph(f"• {decision}")
            
            # Save DOCX file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"meeting_minutes_{job_id}_{timestamp}.docx"
            file_path = self.output_dir / filename
            
            doc.save(str(file_path))
            
            logger.info(f"Generated DOCX document: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"DOCX generation failed: {str(e)}")
            return None

    def generate_pdf_from_html(self, html_path: str, job_id: str) -> Optional[str]:
        """Generate PDF from HTML"""
        if not PDF_AVAILABLE:
            logger.warning("weasyprint not available, skipping PDF generation")
            return None

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"meeting_minutes_{job_id}_{timestamp}.pdf"
            pdf_path = self.output_dir / filename

            # Generate PDF from HTML file
            HTML(filename=html_path).write_pdf(str(pdf_path))

            logger.info(f"Generated PDF document: {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return None
