"""
MinuteMate Audio Transcriber
Handles audio/video transcription using OpenAI Whisper.
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import whisper
import torch
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class TranscriptionResult:
    """Container for transcription results"""
    
    def __init__(self, text: str, segments: list, language: str, 
                 confidence: float = 0.0, duration: float = 0.0):
        self.text = text
        self.segments = segments
        self.language = language
        self.confidence = confidence
        self.duration = duration
        self.timestamp_created = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'segments': self.segments,
            'language': self.language,
            'confidence': self.confidence,
            'duration': self.duration,
            'timestamp_created': self.timestamp_created
        }

class AudioTranscriber:
    """Audio transcription service using OpenAI Whisper"""
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        """
        Initialize the transcriber
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cuda, cpu, or auto-detect)
        """
        self.model_size = model_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self._supported_formats = {
            'audio': ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        }
        
        logger.info(f"AudioTranscriber initialized with model: {model_size}, device: {self.device}")
    
    def _load_model(self) -> None:
        """Load the Whisper model if not already loaded"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            try:
                self.model = whisper.load_model(self.model_size, device=self.device)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
    
    def _extract_audio_from_video(self, video_path: str, output_path: str) -> bool:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            output_path: Path for extracted audio file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Extracting audio from video: {video_path}")
            
            # Use pydub to extract audio
            audio = AudioSegment.from_file(video_path)
            audio.export(output_path, format="wav")
            
            logger.info(f"Audio extracted successfully to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract audio from video: {e}")
            return False
    
    def _preprocess_audio(self, file_path: str) -> str:
        """
        Preprocess audio file for optimal transcription
        
        Args:
            file_path: Path to audio file
            
        Returns:
            str: Path to preprocessed audio file
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # If it's a video file, extract audio first
            if file_ext in self._supported_formats['video']:
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_audio.close()
                
                if self._extract_audio_from_video(file_path, temp_audio.name):
                    return temp_audio.name
                else:
                    os.unlink(temp_audio.name)
                    raise Exception("Failed to extract audio from video")
            
            # For audio files, convert to WAV if needed for consistency
            if file_ext != '.wav':
                logger.info(f"Converting audio file to WAV: {file_path}")
                audio = AudioSegment.from_file(file_path)
                
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_audio.close()
                
                audio.export(temp_audio.name, format="wav")
                return temp_audio.name
            
            # Already a WAV file
            return file_path
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise
    
    def transcribe(self, file_path: str, language: Optional[str] = None,
                  progress_callback: Optional[Callable[[int], None]] = None) -> TranscriptionResult:
        """
        Transcribe audio/video file
        
        Args:
            file_path: Path to audio/video file
            language: Language code (e.g., 'en', 'es') or None for auto-detection
            progress_callback: Optional callback function for progress updates
            
        Returns:
            TranscriptionResult: Transcription results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load model if needed
        self._load_model()
        
        temp_file = None
        try:
            # Update progress
            if progress_callback:
                progress_callback(10)
            
            # Preprocess audio
            logger.info(f"Starting transcription of: {file_path}")
            processed_file = self._preprocess_audio(file_path)
            
            # Keep track of temp file for cleanup
            if processed_file != file_path:
                temp_file = processed_file
            
            if progress_callback:
                progress_callback(25)
            
            # Transcribe using Whisper
            logger.info("Running Whisper transcription...")
            result = self.model.transcribe(
                processed_file,
                language=language,
                verbose=False
            )
            
            if progress_callback:
                progress_callback(90)
            
            # Extract results
            text = result.get('text', '').strip()
            segments = result.get('segments', [])
            detected_language = result.get('language', 'unknown')
            
            # Calculate average confidence if available
            confidence = 0.0
            if segments:
                confidences = [seg.get('avg_logprob', 0.0) for seg in segments]
                confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Get audio duration
            duration = 0.0
            if segments:
                duration = max(seg.get('end', 0.0) for seg in segments)
            
            if progress_callback:
                progress_callback(100)
            
            logger.info(f"Transcription completed. Language: {detected_language}, Duration: {duration:.2f}s")
            
            return TranscriptionResult(
                text=text,
                segments=segments,
                language=detected_language,
                confidence=confidence,
                duration=duration
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
        finally:
            # Clean up temporary file
            if temp_file and temp_file != file_path:
                try:
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get supported file formats"""
        return self._supported_formats.copy()
    
    def estimate_processing_time(self, file_path: str) -> float:
        """
        Estimate processing time based on file size and model
        
        Args:
            file_path: Path to audio/video file
            
        Returns:
            float: Estimated processing time in seconds
        """
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Rough estimates based on model size and file size
            time_multipliers = {
                'tiny': 0.1,
                'base': 0.2,
                'small': 0.3,
                'medium': 0.5,
                'large': 0.8
            }
            
            multiplier = time_multipliers.get(self.model_size, 0.3)
            estimated_time = file_size_mb * multiplier
            
            return max(estimated_time, 5.0)  # Minimum 5 seconds
            
        except Exception:
            return 60.0  # Default estimate
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Transcriber resources cleaned up")
