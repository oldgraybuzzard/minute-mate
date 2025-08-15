"""
AI-powered meeting transcript processor using OpenAI GPT models
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIProcessor:
    """AI-powered transcript processor using OpenAI"""
    
    def __init__(self):
        """Initialize the AI processor"""
        self.client = None
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 4000
        self.temperature = 0.1  # Low temperature for consistent, factual output
        
        if OPENAI_AVAILABLE:
            self._initialize_openai()
        else:
            logger.warning("OpenAI package not available. AI processing will be disabled.")
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not found in environment variables")
                return
            
            # Check for placeholder or invalid API keys
            if api_key in ['openai_api_key', 'your-openai-api-key-here', 'sk-...']:
                logger.warning("Using placeholder API key. AI processing will be disabled.")
                return

            # Validate API key format (should start with sk- and be at least 40 characters)
            if not api_key.startswith('sk-') or len(api_key) < 40:
                logger.warning("Invalid OpenAI API key format. AI processing will be disabled.")
                return
            
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if AI processing is available"""
        return OPENAI_AVAILABLE and self.client is not None
    
    def process_transcript(self, transcript_text: str, filename: str = "") -> Dict[str, Any]:
        """
        Process meeting transcript using AI
        
        Args:
            transcript_text: The meeting transcript text
            filename: Original filename for context
            
        Returns:
            Dictionary containing structured meeting minutes
        """
        if not self.is_available():
            logger.warning("AI processing not available, falling back to mock processing")
            return self._create_fallback_response(transcript_text, filename)
        
        try:
            # Truncate transcript if too long
            max_chars = 12000  # Conservative limit for GPT-3.5-turbo
            if len(transcript_text) > max_chars:
                logger.warning(f"Transcript too long ({len(transcript_text)} chars), truncating to {max_chars}")
                transcript_text = transcript_text[:max_chars] + "\n\n[TRANSCRIPT TRUNCATED]"
            
            # Create the prompt
            prompt = self._create_analysis_prompt(transcript_text)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert meeting secretary who creates professional meeting minutes from transcripts. Always respond with valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"AI response received: {len(ai_response)} characters")
            
            # Try to parse as JSON
            try:
                meeting_minutes = json.loads(ai_response)
                logger.info("Successfully parsed AI response as JSON")
                return meeting_minutes
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                logger.debug(f"AI response content: {ai_response[:500]}...")
                return self._create_fallback_response(transcript_text, filename)
                
        except Exception as e:
            logger.error(f"AI processing failed: {str(e)}")
            return self._create_fallback_response(transcript_text, filename)
    
    def _create_analysis_prompt(self, transcript_text: str) -> str:
        """Create the analysis prompt for OpenAI"""
        
        prompt = f"""
Please analyze this meeting transcript and extract structured meeting minutes in JSON format.

TRANSCRIPT:
{transcript_text}

Please provide a JSON response with the following structure:
{{
  "meeting_info": {{
    "title": "Meeting title (infer from content)",
    "date": "YYYY-MM-DD (today's date if not mentioned)",
    "time": "HH:MM (start time if mentioned)",
    "location": "Meeting location or 'Virtual' if not specified",
    "meeting_type": "Type of meeting (e.g., 'Regular Meeting', 'Board Meeting')"
  }},
  "attendees": [
    {{
      "name": "Full name of attendee",
      "role": "Their role or title",
      "present": true
    }}
  ],
  "agenda_items": [
    {{
      "item_number": 1,
      "title": "Agenda item title",
      "discussion": "Summary of discussion",
      "outcome": "Result or decision"
    }}
  ],
  "motions": [
    {{
      "motion_number": 1,
      "description": "Motion description",
      "moved_by": "Name of person who made motion",
      "seconded_by": "Name of person who seconded",
      "result": "Approved/Rejected/Tabled",
      "vote_count": {{
        "in_favor": 0,
        "against": 0,
        "abstained": 0
      }}
    }}
  ],
  "action_items": [
    {{
      "item_number": 1,
      "description": "Action item description",
      "assigned_to": "Person responsible",
      "due_date": "YYYY-MM-DD or 'Not specified'",
      "status": "Pending"
    }}
  ],
  "key_decisions": [
    "List of key decisions made"
  ],
  "next_meeting": {{
    "date": "YYYY-MM-DD or 'Not mentioned'",
    "time": "HH:MM or 'TBD'",
    "location": "Location or 'TBD'"
  }},
  "meeting_end_time": "HH:MM (if mentioned)",
  "secretary": "Name of secretary/note taker",
  "chairperson": "Name of meeting chair/president"
}}

IMPORTANT INSTRUCTIONS:
1. Extract actual names and roles from the transcript - don't use generic placeholders
2. If information is not available, use appropriate defaults like "Not mentioned" or "TBD"
3. For attendees, try to identify roles from context (President, Secretary, etc.)
4. For motions, extract the actual motion text and voting details if available
5. Use today's date ({datetime.now().strftime('%Y-%m-%d')}) if meeting date not specified
6. Respond ONLY with valid JSON - no additional text or formatting
"""
        
        return prompt
    
    def _create_fallback_response(self, transcript_text: str, filename: str) -> Dict[str, Any]:
        """Create a basic fallback response when AI is not available"""
        
        # Try to extract some basic info from the transcript
        lines = transcript_text.split('\n')
        potential_names = []
        
        # Simple name extraction (look for patterns like "Speaker:" or capitalized words)
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if ':' in line:
                speaker = line.split(':')[0].strip()
                if speaker and len(speaker.split()) <= 3 and speaker[0].isupper():
                    potential_names.append(speaker)
        
        # Remove duplicates and common non-names
        unique_names = []
        common_words = {'Speaker', 'Moderator', 'Host', 'Participant', 'Unknown'}
        for name in set(potential_names):
            if name not in common_words and len(name) > 1:
                unique_names.append(name)
        
        # Create attendees list
        attendees = []
        for i, name in enumerate(unique_names[:20]):  # Limit to 20 attendees
            attendees.append({
                "name": name,
                "role": "Participant",
                "present": True
            })
        
        return {
            "meeting_info": {
                "title": f"Meeting - {filename}" if filename else "Meeting Minutes",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "time": datetime.now().strftime('%H:%M'),
                "location": "Not specified",
                "meeting_type": "Meeting"
            },
            "attendees": attendees,
            "agenda_items": [
                {
                    "item_number": 1,
                    "title": "Meeting Discussion",
                    "discussion": "Meeting transcript processed without AI analysis.",
                    "outcome": "Please review transcript for details."
                }
            ],
            "motions": [],
            "action_items": [],
            "key_decisions": ["Meeting transcript processed - manual review recommended"],
            "next_meeting": {
                "date": "Not mentioned",
                "time": "TBD", 
                "location": "TBD"
            },
            "meeting_end_time": "Not specified",
            "secretary": "Not specified",
            "chairperson": "Not specified"
        }
