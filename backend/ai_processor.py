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

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIProcessor:
    """AI-powered transcript processor supporting multiple providers"""

    def __init__(self):
        """Initialize the AI processor"""
        self.provider = os.getenv('AI_PROVIDER', 'openai').lower()
        self.client = None
        self.gemini_client = None
        self.anthropic_client = None

        # Provider-specific configuration
        if self.provider == 'openai':
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
            self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
            self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
        elif self.provider == 'gemini':
            self.model = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
            self.max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '4000'))
            self.temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.1'))
        elif self.provider == 'anthropic':
            self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
            self.max_tokens = int(os.getenv('ANTHROPIC_MAX_TOKENS', '4000'))
            self.temperature = float(os.getenv('ANTHROPIC_TEMPERATURE', '0.1'))

        # Context window limits (in characters, approximate)
        self.model_limits = {
            # OpenAI models (adjusted for 30K TPM rate limit)
            'gpt-3.5-turbo': 12000,      # ~4K tokens
            'gpt-4': 24000,              # ~8K tokens
            'gpt-4-turbo': 75000,        # ~25K tokens (adjusted for 30K TPM limit)
            'gpt-4-turbo-preview': 75000, # ~25K tokens (adjusted for 30K TPM limit)
            'gpt-4o': 75000,             # ~25K tokens (adjusted for 30K TPM limit)

            # Gemini models (much higher limits)
            'gemini-1.5-pro': 4000000,   # ~1M tokens (4M characters)
            'gemini-1.5-flash': 4000000, # ~1M tokens (4M characters)

            # Claude models (high limits)
            'claude-3-5-sonnet-20241022': 800000,  # ~200K tokens (800K characters)
            'claude-3-haiku': 800000,    # ~200K tokens (800K characters)
        }

        # Get the context limit for current model
        self.max_context_chars = self.model_limits.get(self.model, 12000)

        # Rate limit aware processing - use chunking for large transcripts
        # Gemini can handle much larger transcripts without chunking
        if self.provider == 'gemini':
            self.use_chunking_threshold = 3000000  # 3M chars for Gemini
        elif self.provider == 'anthropic':
            self.use_chunking_threshold = 600000   # 600K chars for Claude
        else:
            self.use_chunking_threshold = 60000    # 60K chars for OpenAI
        
        # Initialize the appropriate AI client
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize AI clients based on provider"""
        if self.provider == 'openai':
            self._initialize_openai()
        elif self.provider == 'gemini':
            self._initialize_gemini()
        elif self.provider == 'anthropic':
            self._initialize_anthropic()
        else:
            logger.error(f"Unknown AI provider: {self.provider}")
    
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
            
            # Initialize OpenAI client - handle different versions gracefully
            logger.info(f"Attempting to initialize OpenAI client...")

            # Try different initialization methods for compatibility
            client_kwargs = {'api_key': api_key}

            try:
                # Try with timeout and max_retries (newer versions)
                self.client = OpenAI(
                    api_key=api_key,
                    timeout=60.0,
                    max_retries=3
                )
                logger.info("OpenAI client initialized with full configuration")
            except TypeError:
                try:
                    # Fallback: just API key (older versions)
                    self.client = OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized with basic configuration")
                except Exception as fallback_error:
                    logger.error(f"All OpenAI initialization methods failed: {fallback_error}")
                    self.client = None
                    return
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None

    def _initialize_gemini(self):
        """Initialize Google Gemini client"""
        if not GEMINI_AVAILABLE:
            logger.error("Google Generative AI package not available")
            return

        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.warning("GOOGLE_API_KEY not found in environment variables")
                return

            logger.info("Attempting to initialize Gemini client...")
            genai.configure(api_key=api_key)
            self.gemini_client = genai.GenerativeModel(self.model)
            logger.info(f"Gemini client initialized with model: {self.model}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            self.gemini_client = None

    def _initialize_anthropic(self):
        """Initialize Anthropic Claude client"""
        if not ANTHROPIC_AVAILABLE:
            logger.error("Anthropic package not available")
            return

        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not found in environment variables")
                return

            logger.info("Attempting to initialize Anthropic client...")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info(f"Anthropic client initialized with model: {self.model}")

        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {str(e)}")
            self.anthropic_client = None

    def is_available(self) -> bool:
        """Check if AI processing is available"""
        if self.provider == 'openai':
            return OPENAI_AVAILABLE and self.client is not None
        elif self.provider == 'gemini':
            return GEMINI_AVAILABLE and self.gemini_client is not None
        elif self.provider == 'anthropic':
            return ANTHROPIC_AVAILABLE and self.anthropic_client is not None
        return False

    def _call_ai_provider(self, prompt: str) -> str:
        """Call the appropriate AI provider with the given prompt"""
        if self.provider == 'openai':
            return self._call_openai(prompt)
        elif self.provider == 'gemini':
            return self._call_gemini(prompt)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
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
        return response.choices[0].message.content.strip()

    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        full_prompt = """You are an expert meeting secretary who creates professional meeting minutes from transcripts. Always respond with valid JSON.

""" + prompt

        response = self.gemini_client.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        )
        return response.text.strip()

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system="You are an expert meeting secretary who creates professional meeting minutes from transcripts. Always respond with valid JSON.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.content[0].text.strip()

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
            # Check if transcript should use chunking (rate limit aware)
            if len(transcript_text) > self.use_chunking_threshold:
                logger.warning(f"Transcript large ({len(transcript_text)} chars), using chunking to respect rate limits")
                logger.info("Using chunking strategy to stay within rate limits")
                return self._process_large_transcript_chunked(transcript_text, filename)
            elif len(transcript_text) > self.max_context_chars:
                logger.warning(f"Transcript too long ({len(transcript_text)} chars), max for {self.model} is {self.max_context_chars}")
                # For moderately large transcripts, truncate intelligently
                logger.info("Truncating transcript intelligently")
                transcript_text = self._truncate_intelligently(transcript_text)

            # Create the prompt
            prompt = self._create_analysis_prompt(transcript_text)

            # Call the appropriate AI provider
            ai_response = self._call_ai_provider(prompt)
            logger.info(f"AI response received: {len(ai_response)} characters")
            
            # Try to parse as JSON
            try:
                # First try direct JSON parsing
                meeting_minutes = json.loads(ai_response)
                logger.info("Successfully parsed AI response as JSON")
                return meeting_minutes

            except json.JSONDecodeError as e:
                # If direct parsing fails, try to extract JSON from markdown code blocks
                logger.warning(f"Direct JSON parsing failed: {str(e)}")
                logger.debug(f"AI response content: {ai_response[:500]}...")

                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    try:
                        json_content = json_match.group(1)
                        meeting_minutes = json.loads(json_content)
                        logger.info("Successfully extracted and parsed JSON from markdown")
                        return meeting_minutes
                    except json.JSONDecodeError as e2:
                        logger.error(f"Failed to parse extracted JSON: {str(e2)}")

                logger.error("Could not extract valid JSON from AI response")
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

    def _truncate_intelligently(self, transcript_text: str) -> str:
        """Intelligently truncate transcript to preserve important content"""
        lines = transcript_text.split('\n')
        total_chars = len(transcript_text)
        target_chars = self.max_context_chars - 2000  # Leave room for prompt

        if total_chars <= target_chars:
            return transcript_text

        # Strategy: Keep beginning (context) and end (conclusions), sample middle
        beginning_ratio = 0.3  # 30% from beginning
        ending_ratio = 0.3     # 30% from end
        middle_ratio = 0.4     # 40% from middle (sampled)

        beginning_chars = int(target_chars * beginning_ratio)
        ending_chars = int(target_chars * ending_ratio)
        middle_chars = target_chars - beginning_chars - ending_chars

        # Get beginning portion
        beginning_text = ""
        char_count = 0
        for line in lines:
            if char_count + len(line) > beginning_chars:
                break
            beginning_text += line + '\n'
            char_count += len(line) + 1

        # Get ending portion
        ending_text = ""
        char_count = 0
        for line in reversed(lines):
            if char_count + len(line) > ending_chars:
                break
            ending_text = line + '\n' + ending_text
            char_count += len(line) + 1

        # Sample middle portion (every nth line to get representative content)
        middle_lines = lines[len(beginning_text.split('\n')):-len(ending_text.split('\n'))]
        if middle_lines:
            # Calculate sampling rate to fit middle_chars
            total_middle_chars = sum(len(line) for line in middle_lines)
            if total_middle_chars > middle_chars:
                sample_rate = max(1, len(middle_lines) * middle_chars // total_middle_chars)
                sampled_middle = middle_lines[::sample_rate]
            else:
                sampled_middle = middle_lines

            middle_text = '\n'.join(sampled_middle)
        else:
            middle_text = ""

        # Combine all parts
        result = beginning_text + "\n\n[... MIDDLE CONTENT SAMPLED ...]\n\n" + middle_text + "\n\n[... CONTINUING TO END ...]\n\n" + ending_text

        logger.info(f"Intelligently truncated transcript from {total_chars} to {len(result)} characters")
        return result

    def _process_large_transcript_chunked(self, transcript_text: str, filename: str) -> Dict[str, Any]:
        """Process very large transcripts using chunking strategy"""
        logger.info(f"Processing large transcript ({len(transcript_text)} chars) using chunking")

        # Split transcript into logical chunks
        chunks = self._split_transcript_into_chunks(transcript_text)
        logger.info(f"Split transcript into {len(chunks)} chunks")

        # Process each chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            try:
                chunk_result = self._process_single_chunk(chunk, i+1, len(chunks))
                chunk_results.append(chunk_result)
            except Exception as e:
                logger.error(f"Failed to process chunk {i+1}: {str(e)}")
                continue

        # Merge chunk results into final meeting minutes
        if chunk_results:
            return self._merge_chunk_results(chunk_results, filename)
        else:
            logger.error("All chunks failed to process")
            return self._create_fallback_response(transcript_text, filename)

    def _split_transcript_into_chunks(self, transcript_text: str) -> List[str]:
        """Split transcript into logical chunks that fit within context limits"""
        lines = transcript_text.split('\n')
        chunks = []
        current_chunk = ""
        chunk_size_limit = self.max_context_chars - 3000  # Leave room for prompt

        for line in lines:
            # If adding this line would exceed limit, start new chunk
            if len(current_chunk) + len(line) > chunk_size_limit and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'

        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _process_single_chunk(self, chunk_text: str, chunk_num: int, total_chunks: int) -> Dict[str, Any]:
        """Process a single chunk of transcript"""
        prompt = f"""
Please analyze this portion ({chunk_num}/{total_chunks}) of a meeting transcript and extract key information in JSON format.

TRANSCRIPT CHUNK:
{chunk_text}

Please provide a JSON response focusing on what's discussed in this chunk:
{{
  "chunk_info": {{
    "chunk_number": {chunk_num},
    "total_chunks": {total_chunks}
  }},
  "attendees_mentioned": ["Names of people who spoke in this chunk"],
  "topics_discussed": ["Main topics covered in this chunk"],
  "agenda_items": [
    {{
      "title": "Topic title",
      "discussion": "Summary of discussion",
      "outcome": "Result or decision if any"
    }}
  ],
  "motions": [
    {{
      "description": "Motion description",
      "moved_by": "Name",
      "seconded_by": "Name",
      "result": "Approved/Rejected/Tabled"
    }}
  ],
  "action_items": [
    {{
      "description": "Action item",
      "assigned_to": "Person responsible",
      "due_date": "Date if mentioned"
    }}
  ],
  "key_decisions": ["Important decisions made in this chunk"],
  "important_quotes": ["Significant statements or quotes"]
}}

Respond ONLY with valid JSON.
"""

        # Use provider-agnostic AI calling
        ai_response = self._call_ai_provider(prompt)
        return json.loads(ai_response)

    def _merge_chunk_results(self, chunk_results: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """Merge results from multiple chunks into comprehensive meeting minutes"""
        logger.info(f"Merging results from {len(chunk_results)} chunks")

        # Collect all data from chunks
        all_attendees = set()
        all_agenda_items = []
        all_motions = []
        all_action_items = []
        all_decisions = []
        all_topics = []

        for chunk_result in chunk_results:
            # Collect attendees
            if 'attendees_mentioned' in chunk_result:
                all_attendees.update(chunk_result['attendees_mentioned'])

            # Collect agenda items
            if 'agenda_items' in chunk_result:
                all_agenda_items.extend(chunk_result['agenda_items'])

            # Collect motions
            if 'motions' in chunk_result:
                all_motions.extend(chunk_result['motions'])

            # Collect action items
            if 'action_items' in chunk_result:
                all_action_items.extend(chunk_result['action_items'])

            # Collect decisions
            if 'key_decisions' in chunk_result:
                all_decisions.extend(chunk_result['key_decisions'])

            # Collect topics
            if 'topics_discussed' in chunk_result:
                all_topics.extend(chunk_result['topics_discussed'])

        # Create comprehensive meeting minutes
        return {
            "meeting_info": {
                "title": f"Meeting - {filename}" if filename else "Large Meeting Minutes",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "time": datetime.now().strftime('%H:%M'),
                "location": "Not specified",
                "meeting_type": "Meeting",
                "processing_method": f"Chunked processing ({len(chunk_results)} chunks)"
            },
            "attendees": [
                {"name": name, "role": "Participant", "present": True}
                for name in sorted(all_attendees) if name and name.strip()
            ],
            "agenda_items": [
                {**item, "item_number": i+1}
                for i, item in enumerate(all_agenda_items)
            ],
            "motions": [
                {**motion, "motion_number": i+1}
                for i, motion in enumerate(all_motions)
            ],
            "action_items": [
                {**item, "item_number": i+1}
                for i, item in enumerate(all_action_items)
            ],
            "key_decisions": all_decisions,
            "topics_covered": list(set(all_topics)),  # Remove duplicates
            "next_meeting": {
                "date": "Not mentioned",
                "time": "TBD",
                "location": "TBD"
            },
            "meeting_end_time": "Not specified",
            "secretary": "Not specified",
            "chairperson": "Not specified",
            "processing_stats": {
                "total_chunks": len(chunk_results),
                "total_attendees": len(all_attendees),
                "total_agenda_items": len(all_agenda_items),
                "total_motions": len(all_motions),
                "total_action_items": len(all_action_items)
            }
        }

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
