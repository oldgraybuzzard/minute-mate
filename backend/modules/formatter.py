"""
MinuteMate Meeting Formatter
Formats parsed meeting data into formal meeting minutes following Robert's Rules of Order.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .parser import MeetingStructure, Motion, Speaker

logger = logging.getLogger(__name__)

class MinutesFormatter:
    """Formats meeting data into formal minutes"""
    
    def __init__(self, style: str = "roberts_rules"):
        """
        Initialize the formatter
        
        Args:
            style: Formatting style (roberts_rules, informal, corporate)
        """
        self.style = style
        self.templates = self._load_templates()
        logger.info(f"MinutesFormatter initialized with style: {style}")
    
    def _load_templates(self) -> Dict[str, str]:
        """Load formatting templates for different styles"""
        templates = {
            'roberts_rules': {
                'header': """MEETING MINUTES
{title}
{date}

ATTENDEES:
{attendees}

""",
                'call_to_order': """CALL TO ORDER
The meeting was called to order at {time}.

""",
                'approval_minutes': """APPROVAL OF MINUTES
{approval_text}

""",
                'motion': """MOTION #{motion_num}
Moved by: {mover}
Seconded by: {seconder}
Motion: {motion_text}

{discussion}

VOTE: {outcome}
{vote_details}

""",
                'discussion': """DISCUSSION: {topic}
{content}

""",
                'adjournment': """ADJOURNMENT
{adjournment_text}

Meeting adjourned at {time}.

""",
                'footer': """
Minutes prepared by: [Secretary Name]
Date prepared: {date_prepared}
"""
            },
            'informal': {
                'header': """{title} - Meeting Notes
Date: {date}
Attendees: {attendees}

""",
                'motion': """• Motion: {motion_text}
  Proposed by: {mover}
  Seconded by: {seconder}
  Result: {outcome}

""",
                'discussion': """• Discussion: {topic}
  {content}

"""
            }
        }
        return templates.get(self.style, templates['roberts_rules'])
    
    def _format_attendees(self, attendees: List[str]) -> str:
        """Format attendees list"""
        if not attendees:
            return "No attendees recorded"
        
        if self.style == "roberts_rules":
            return "\n".join(f"• {name}" for name in sorted(attendees))
        else:
            return ", ".join(sorted(attendees))
    
    def _format_motion(self, motion: Motion, motion_num: int) -> str:
        """Format a single motion"""
        template = self.templates.get('motion', '')
        
        # Format discussion
        discussion_text = ""
        if motion.discussion:
            discussion_text = "DISCUSSION:\n" + "\n".join(f"• {item}" for item in motion.discussion)
        else:
            discussion_text = "No discussion recorded."
        
        # Format vote details
        vote_details = ""
        if motion.vote_count:
            vote_details = f"For: {motion.vote_count.get('for', 0)}, Against: {motion.vote_count.get('against', 0)}, Abstentions: {motion.vote_count.get('abstentions', 0)}"
        
        return template.format(
            motion_num=motion_num,
            mover=motion.mover or "Unknown",
            seconder=motion.seconder or "Unknown",
            motion_text=motion.text,
            discussion=discussion_text,
            outcome=motion.outcome or "Unknown",
            vote_details=vote_details
        )
    
    def _format_discussions(self, discussions: List[Dict[str, Any]]) -> str:
        """Format general discussions"""
        if not discussions:
            return ""
        
        formatted = []
        for i, discussion in enumerate(discussions, 1):
            topic = discussion.get('topic', f'Discussion Item {i}')
            content = discussion.get('content', 'No details recorded.')
            
            template = self.templates.get('discussion', '')
            formatted.append(template.format(topic=topic, content=content))
        
        return "\n".join(formatted)
    
    def _extract_time_from_text(self, text: str) -> str:
        """Extract time from text, return placeholder if not found"""
        import re
        
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
            r'(\d{1,2}:\d{2})',
            r'at\s+(\d{1,2}:\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "[Time not specified]"
    
    def format_minutes(self, structure: MeetingStructure, 
                      include_timestamps: bool = False,
                      secretary_name: Optional[str] = None) -> str:
        """
        Format meeting structure into formal minutes
        
        Args:
            structure: Parsed meeting structure
            include_timestamps: Whether to include timestamps
            secretary_name: Name of the secretary preparing minutes
            
        Returns:
            Formatted minutes as string
        """
        logger.info("Formatting meeting minutes")
        
        formatted_minutes = []
        
        # Header
        header_template = self.templates.get('header', '')
        attendees_formatted = self._format_attendees(structure.attendees)
        
        header = header_template.format(
            title=structure.title or "Meeting Minutes",
            date=structure.date or datetime.now().strftime("%B %d, %Y"),
            attendees=attendees_formatted
        )
        formatted_minutes.append(header)
        
        # Call to Order
        if structure.call_to_order:
            call_template = self.templates.get('call_to_order', '')
            time = self._extract_time_from_text(structure.call_to_order)
            call_section = call_template.format(time=time)
            formatted_minutes.append(call_section)
        
        # Approval of Previous Minutes
        if structure.approval_of_minutes:
            approval_template = self.templates.get('approval_minutes', '')
            approval_section = approval_template.format(
                approval_text=structure.approval_of_minutes
            )
            formatted_minutes.append(approval_section)
        
        # Motions
        if structure.motions:
            formatted_minutes.append("BUSINESS\n")
            for i, motion in enumerate(structure.motions, 1):
                motion_section = self._format_motion(motion, i)
                formatted_minutes.append(motion_section)
        
        # General Discussions
        discussions_section = self._format_discussions(structure.discussions)
        if discussions_section:
            formatted_minutes.append("ADDITIONAL DISCUSSIONS\n")
            formatted_minutes.append(discussions_section)
        
        # Adjournment
        if structure.adjournment:
            adjournment_template = self.templates.get('adjournment', '')
            time = self._extract_time_from_text(structure.adjournment)
            adjournment_section = adjournment_template.format(
                adjournment_text=structure.adjournment,
                time=time
            )
            formatted_minutes.append(adjournment_section)
        
        # Footer
        footer_template = self.templates.get('footer', '')
        if footer_template:
            footer = footer_template.format(
                date_prepared=datetime.now().strftime("%B %d, %Y")
            )
            if secretary_name:
                footer = footer.replace("[Secretary Name]", secretary_name)
            formatted_minutes.append(footer)
        
        result = "\n".join(formatted_minutes)
        logger.info(f"Minutes formatting completed. Length: {len(result)} characters")
        
        return result
    
    def format_summary(self, structure: MeetingStructure) -> Dict[str, Any]:
        """
        Create a summary of the meeting
        
        Args:
            structure: Parsed meeting structure
            
        Returns:
            Dictionary with meeting summary
        """
        summary = {
            'title': structure.title or "Meeting",
            'date': structure.date,
            'attendee_count': len(structure.attendees),
            'attendees': structure.attendees,
            'motion_count': len(structure.motions),
            'motions_summary': [],
            'key_decisions': [],
            'action_items': []
        }
        
        # Summarize motions
        for motion in structure.motions:
            motion_summary = {
                'text': motion.text,
                'mover': motion.mover,
                'outcome': motion.outcome,
                'status': 'Passed' if motion.outcome == 'passed' else 'Failed' if motion.outcome == 'failed' else 'Unknown'
            }
            summary['motions_summary'].append(motion_summary)
            
            # Add to key decisions if passed
            if motion.outcome == 'passed':
                summary['key_decisions'].append(motion.text)
        
        return summary
    
    def get_available_styles(self) -> List[str]:
        """Get list of available formatting styles"""
        return ['roberts_rules', 'informal', 'corporate']
    
    def set_style(self, style: str) -> bool:
        """
        Change formatting style
        
        Args:
            style: New style to use
            
        Returns:
            bool: True if style was changed successfully
        """
        if style in self.get_available_styles():
            self.style = style
            self.templates = self._load_templates()
            logger.info(f"Formatting style changed to: {style}")
            return True
        else:
            logger.warning(f"Unknown formatting style: {style}")
            return False
