"""
MinuteMate Meeting Parser
Parses transcribed text to extract meeting structure according to Robert's Rules of Order.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import spacy

logger = logging.getLogger(__name__)

@dataclass
class Motion:
    """Represents a motion in the meeting"""
    text: str
    mover: Optional[str] = None
    seconder: Optional[str] = None
    discussion: List[str] = None
    outcome: Optional[str] = None  # passed, failed, tabled, withdrawn
    vote_count: Optional[Dict[str, int]] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.discussion is None:
            self.discussion = []
        if self.vote_count is None:
            self.vote_count = {}

@dataclass
class Speaker:
    """Represents a speaker in the meeting"""
    name: str
    statements: List[str] = None
    
    def __post_init__(self):
        if self.statements is None:
            self.statements = []

@dataclass
class MeetingStructure:
    """Represents the parsed meeting structure"""
    title: Optional[str] = None
    date: Optional[str] = None
    attendees: List[str] = None
    call_to_order: Optional[str] = None
    approval_of_minutes: Optional[str] = None
    motions: List[Motion] = None
    discussions: List[Dict[str, Any]] = None
    adjournment: Optional[str] = None
    speakers: List[Speaker] = None
    
    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []
        if self.motions is None:
            self.motions = []
        if self.discussions is None:
            self.discussions = []
        if self.speakers is None:
            self.speakers = []

class MinutesParser:
    """Parser for extracting meeting structure from transcripts"""
    
    def __init__(self, language: str = "en"):
        """
        Initialize the parser
        
        Args:
            language: Language code for spaCy model
        """
        self.language = language
        self.nlp = None
        self._load_nlp_model()
        
        # Patterns for identifying meeting elements
        self._patterns = {
            'call_to_order': [
                r'(?i)call(?:ing)?\s+(?:the\s+)?meeting\s+to\s+order',
                r'(?i)meeting\s+(?:is\s+)?(?:now\s+)?called\s+to\s+order',
                r'(?i)(?:let\'s\s+)?(?:begin|start)\s+(?:the\s+)?meeting'
            ],
            'motion': [
                r'(?i)i\s+move\s+(?:that\s+)?(.+?)(?:\.|$)',
                r'(?i)motion\s+to\s+(.+?)(?:\.|$)',
                r'(?i)i\s+propose\s+(?:that\s+)?(.+?)(?:\.|$)'
            ],
            'second': [
                r'(?i)i\s+second\s+(?:the\s+motion|that)',
                r'(?i)seconded',
                r'(?i)second'
            ],
            'vote': [
                r'(?i)all\s+(?:those\s+)?in\s+favor',
                r'(?i)(?:those\s+)?opposed',
                r'(?i)(?:any\s+)?abstentions',
                r'(?i)motion\s+(?:passes|fails|carried|defeated)',
                r'(?i)vote\s+(?:passes|fails)'
            ],
            'adjournment': [
                r'(?i)meeting\s+(?:is\s+)?adjourned',
                r'(?i)adjourn\s+(?:the\s+)?meeting',
                r'(?i)motion\s+to\s+adjourn'
            ]
        }
        
        logger.info(f"MinutesParser initialized for language: {language}")
    
    def _load_nlp_model(self) -> None:
        """Load spaCy NLP model"""
        try:
            model_name = f"{self.language}_core_web_sm"
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"spaCy model for {self.language} not found, using basic processing")
            self.nlp = None
    
    def _extract_speakers(self, text: str) -> List[str]:
        """
        Extract speaker names from the transcript
        
        Args:
            text: Transcript text
            
        Returns:
            List of speaker names
        """
        speakers = set()
        
        if self.nlp:
            doc = self.nlp(text)
            # Extract person names using NER
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    speakers.add(ent.text.strip())
        
        # Also look for common speaker patterns
        speaker_patterns = [
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):',  # "John Smith:"
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+said',  # "John Smith said"
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+stated',  # "John Smith stated"
        ]
        
        for pattern in speaker_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            speakers.update(matches)
        
        return list(speakers)
    
    def _extract_motions(self, text: str) -> List[Motion]:
        """
        Extract motions from the transcript
        
        Args:
            text: Transcript text
            
        Returns:
            List of Motion objects
        """
        motions = []
        
        for pattern in self._patterns['motion']:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                motion_text = match.group(1).strip()
                
                # Try to find who made the motion
                context_start = max(0, match.start() - 100)
                context = text[context_start:match.start()]
                
                mover = None
                speaker_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:said|stated)?[:\s]*$', context)
                if speaker_match:
                    mover = speaker_match.group(1)
                
                motion = Motion(
                    text=motion_text,
                    mover=mover,
                    timestamp=None  # Could be extracted from segments if available
                )
                motions.append(motion)
        
        return motions
    
    def _find_seconds_and_votes(self, text: str, motions: List[Motion]) -> None:
        """
        Find seconds and vote outcomes for motions
        
        Args:
            text: Transcript text
            motions: List of motions to update
        """
        lines = text.split('\n')
        
        for i, motion in enumerate(motions):
            # Look for seconds after the motion
            motion_line_idx = None
            for j, line in enumerate(lines):
                if motion.text.lower() in line.lower():
                    motion_line_idx = j
                    break
            
            if motion_line_idx is not None:
                # Look for second in next few lines
                for j in range(motion_line_idx + 1, min(motion_line_idx + 5, len(lines))):
                    line = lines[j]
                    for pattern in self._patterns['second']:
                        if re.search(pattern, line):
                            # Try to extract who seconded
                            seconder_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line)
                            if seconder_match:
                                motion.seconder = seconder_match.group(1)
                            break
                
                # Look for vote outcome
                for j in range(motion_line_idx + 1, min(motion_line_idx + 20, len(lines))):
                    line = lines[j]
                    for pattern in self._patterns['vote']:
                        if re.search(pattern, line):
                            if re.search(r'(?i)(?:passes|passed|carried)', line):
                                motion.outcome = 'passed'
                            elif re.search(r'(?i)(?:fails|failed|defeated)', line):
                                motion.outcome = 'failed'
                            break
    
    def _extract_meeting_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract meeting metadata (title, date, etc.)
        
        Args:
            text: Transcript text
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Look for date patterns
        date_patterns = [
            r'(?i)(?:meeting\s+)?(?:date|held\s+on)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?i)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?i)([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text[:500])  # Look in first 500 chars
            if match:
                metadata['date'] = match.group(1)
                break
        
        # Look for meeting title
        title_patterns = [
            r'(?i)^(.+?)\s+meeting',
            r'(?i)meeting\s+of\s+(.+?)(?:\n|$)',
            r'(?i)(.+?)\s+board\s+meeting'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text[:200], re.MULTILINE)
            if match:
                metadata['title'] = match.group(1).strip()
                break
        
        return metadata
    
    def parse(self, transcript_text: str, segments: Optional[List[Dict]] = None) -> MeetingStructure:
        """
        Parse transcript text into structured meeting data
        
        Args:
            transcript_text: The transcribed text
            segments: Optional segment data with timestamps
            
        Returns:
            MeetingStructure object
        """
        logger.info("Starting meeting structure parsing")
        
        # Extract metadata
        metadata = self._extract_meeting_metadata(transcript_text)
        
        # Extract speakers
        speakers = self._extract_speakers(transcript_text)
        speaker_objects = [Speaker(name=name) for name in speakers]
        
        # Extract motions
        motions = self._extract_motions(transcript_text)
        
        # Find seconds and votes for motions
        self._find_seconds_and_votes(transcript_text, motions)
        
        # Look for call to order
        call_to_order = None
        for pattern in self._patterns['call_to_order']:
            match = re.search(pattern, transcript_text[:1000])  # Look in first 1000 chars
            if match:
                call_to_order = match.group(0)
                break
        
        # Look for adjournment
        adjournment = None
        for pattern in self._patterns['adjournment']:
            match = re.search(pattern, transcript_text[-1000:])  # Look in last 1000 chars
            if match:
                adjournment = match.group(0)
                break
        
        # Create meeting structure
        structure = MeetingStructure(
            title=metadata.get('title'),
            date=metadata.get('date'),
            attendees=speakers,
            call_to_order=call_to_order,
            motions=motions,
            adjournment=adjournment,
            speakers=speaker_objects
        )
        
        logger.info(f"Parsing completed. Found {len(motions)} motions, {len(speakers)} speakers")
        
        return structure
    
    def to_dict(self, structure: MeetingStructure) -> Dict[str, Any]:
        """
        Convert MeetingStructure to dictionary for JSON serialization
        
        Args:
            structure: MeetingStructure object
            
        Returns:
            Dictionary representation
        """
        return {
            'title': structure.title,
            'date': structure.date,
            'attendees': structure.attendees,
            'call_to_order': structure.call_to_order,
            'approval_of_minutes': structure.approval_of_minutes,
            'motions': [
                {
                    'text': motion.text,
                    'mover': motion.mover,
                    'seconder': motion.seconder,
                    'discussion': motion.discussion,
                    'outcome': motion.outcome,
                    'vote_count': motion.vote_count,
                    'timestamp': motion.timestamp
                }
                for motion in structure.motions
            ],
            'discussions': structure.discussions,
            'adjournment': structure.adjournment,
            'speakers': [
                {
                    'name': speaker.name,
                    'statements': speaker.statements
                }
                for speaker in structure.speakers
            ]
        }
