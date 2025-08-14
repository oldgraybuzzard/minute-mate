"""
MinuteMate Backend Modules
Core processing modules for the MinuteMate application.
"""

__version__ = "1.0.0"
__author__ = "MinuteMate Team"

# Import all processing modules
from .transcriber import AudioTranscriber, TranscriptionResult
from .parser import MinutesParser, MeetingStructure, Motion, Speaker
from .formatter import MinutesFormatter
from .exporter import DocxExporter
from .comparator import DocumentComparator, DocumentChange
from .user_profiles import UserProfileManager, UserProfile

# Define what gets imported with "from modules import *"
__all__ = [
    'AudioTranscriber',
    'TranscriptionResult',
    'MinutesParser',
    'MeetingStructure',
    'Motion',
    'Speaker',
    'MinutesFormatter',
    'DocxExporter',
    'DocumentComparator',
    'DocumentChange',
    'UserProfileManager',
    'UserProfile'
]
