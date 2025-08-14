"""
MinuteMate User Profile Manager
Manages user preferences and learning from document comparisons.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class UserProfile:
    """Represents a user's preferences and settings"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.preferences = {
            'content_style': 'balanced',  # concise, balanced, detailed
            'formatting_style': 'roberts_rules',  # roberts_rules, informal, corporate
            'language': 'en',
            'include_timestamps': False,
            'include_speaker_names': True,
            'motion_detail_level': 'standard',  # minimal, standard, detailed
            'discussion_detail_level': 'standard',
            'auto_format_names': True,
            'custom_templates': {}
        }
        self.learning_data = {
            'document_comparisons': [],
            'common_edits': {},
            'style_patterns': {},
            'confidence_score': 0.0
        }
        self.statistics = {
            'documents_processed': 0,
            'documents_edited': 0,
            'total_processing_time': 0.0,
            'average_satisfaction': 0.0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for JSON serialization"""
        return {
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'preferences': self.preferences,
            'learning_data': self.learning_data,
            'statistics': self.statistics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile from dictionary"""
        profile = cls(data['user_id'])
        profile.created_at = data.get('created_at', profile.created_at)
        profile.updated_at = data.get('updated_at', profile.updated_at)
        profile.preferences.update(data.get('preferences', {}))
        profile.learning_data.update(data.get('learning_data', {}))
        profile.statistics.update(data.get('statistics', {}))
        return profile
    
    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        self.preferences.update(new_preferences)
        self.updated_at = datetime.now().isoformat()
        logger.info(f"Updated preferences for user {self.user_id}")
    
    def add_comparison_data(self, comparison_result: Dict[str, Any]) -> None:
        """Add document comparison data for learning"""
        self.learning_data['document_comparisons'].append({
            'timestamp': datetime.now().isoformat(),
            'similarity_score': comparison_result.get('similarity_score', 0.0),
            'change_categories': comparison_result.get('change_categories', {}),
            'total_changes': comparison_result.get('total_changes', 0)
        })
        
        # Update statistics
        self.statistics['documents_edited'] += 1
        self.updated_at = datetime.now().isoformat()
        
        # Analyze patterns and update preferences
        self._analyze_learning_patterns()
    
    def _analyze_learning_patterns(self) -> None:
        """Analyze learning patterns and update preferences"""
        comparisons = self.learning_data['document_comparisons']
        if len(comparisons) < 2:
            return
        
        # Analyze content style preferences
        expansion_count = 0
        condensation_count = 0
        
        for comp in comparisons:
            categories = comp.get('change_categories', {})
            expansion_count += categories.get('content_expansion', 0)
            condensation_count += categories.get('content_condensation', 0)
        
        # Update content style preference
        if expansion_count > condensation_count * 1.5:
            self.preferences['content_style'] = 'detailed'
        elif condensation_count > expansion_count * 1.5:
            self.preferences['content_style'] = 'concise'
        else:
            self.preferences['content_style'] = 'balanced'
        
        # Update confidence score
        self.learning_data['confidence_score'] = min(len(comparisons) / 5.0, 1.0)
        
        logger.info(f"Updated learning patterns for user {self.user_id}: {self.preferences['content_style']} style")

class UserProfileManager:
    """Manages user profiles and preferences"""
    
    def __init__(self, profiles_dir: str = "user_profiles"):
        """
        Initialize the profile manager
        
        Args:
            profiles_dir: Directory to store user profiles
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self._profiles_cache = {}
        logger.info(f"UserProfileManager initialized with directory: {profiles_dir}")
    
    def _get_profile_path(self, user_id: str) -> Path:
        """Get the file path for a user profile"""
        return self.profiles_dir / f"{user_id}.json"
    
    def create_profile(self, user_id: str) -> UserProfile:
        """
        Create a new user profile
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserProfile: New user profile
        """
        if self.profile_exists(user_id):
            logger.warning(f"Profile already exists for user {user_id}")
            return self.load_profile(user_id)
        
        profile = UserProfile(user_id)
        self.save_profile(profile)
        self._profiles_cache[user_id] = profile
        
        logger.info(f"Created new profile for user {user_id}")
        return profile
    
    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Load a user profile
        
        Args:
            user_id: User identifier
            
        Returns:
            UserProfile or None if not found
        """
        # Check cache first
        if user_id in self._profiles_cache:
            return self._profiles_cache[user_id]
        
        profile_path = self._get_profile_path(user_id)
        
        if not profile_path.exists():
            logger.info(f"Profile not found for user {user_id}")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = UserProfile.from_dict(data)
            self._profiles_cache[user_id] = profile
            
            logger.info(f"Loaded profile for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load profile for user {user_id}: {e}")
            return None
    
    def save_profile(self, profile: UserProfile) -> bool:
        """
        Save a user profile
        
        Args:
            profile: UserProfile to save
            
        Returns:
            bool: True if saved successfully
        """
        try:
            profile_path = self._get_profile_path(profile.user_id)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Update cache
            self._profiles_cache[profile.user_id] = profile
            
            logger.info(f"Saved profile for user {profile.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save profile for user {profile.user_id}: {e}")
            return False
    
    def profile_exists(self, user_id: str) -> bool:
        """
        Check if a profile exists for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: True if profile exists
        """
        return self._get_profile_path(user_id).exists()
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """
        Get existing profile or create new one
        
        Args:
            user_id: User identifier
            
        Returns:
            UserProfile: Existing or new profile
        """
        profile = self.load_profile(user_id)
        if profile is None:
            profile = self.create_profile(user_id)
        return profile
    
    def update_profile_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences
        
        Args:
            user_id: User identifier
            preferences: New preferences to update
            
        Returns:
            bool: True if updated successfully
        """
        profile = self.get_or_create_profile(user_id)
        profile.update_preferences(preferences)
        return self.save_profile(profile)
    
    def add_learning_data(self, user_id: str, comparison_result: Dict[str, Any]) -> bool:
        """
        Add learning data from document comparison
        
        Args:
            user_id: User identifier
            comparison_result: Results from document comparison
            
        Returns:
            bool: True if added successfully
        """
        profile = self.get_or_create_profile(user_id)
        profile.add_comparison_data(comparison_result)
        return self.save_profile(profile)
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of user preferences
        """
        profile = self.get_or_create_profile(user_id)
        return profile.preferences.copy()
    
    def get_formatting_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        Get formatting recommendations based on user's learning data
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with formatting recommendations
        """
        profile = self.load_profile(user_id)
        if not profile:
            return {'style': 'roberts_rules', 'confidence': 0.0}
        
        recommendations = {
            'content_style': profile.preferences['content_style'],
            'formatting_style': profile.preferences['formatting_style'],
            'confidence': profile.learning_data['confidence_score'],
            'suggestions': []
        }
        
        # Add specific suggestions based on learning data
        if profile.learning_data['confidence_score'] > 0.5:
            recommendations['suggestions'].append(f"Use {profile.preferences['content_style']} content style")
            
        if profile.statistics['documents_edited'] > 3:
            recommendations['suggestions'].append("Consider user's established editing patterns")
        
        return recommendations
    
    def list_all_profiles(self) -> List[str]:
        """
        List all user profile IDs
        
        Returns:
            List of user IDs
        """
        profile_files = self.profiles_dir.glob("*.json")
        return [f.stem for f in profile_files]
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Delete a user profile
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            profile_path = self._get_profile_path(user_id)
            if profile_path.exists():
                profile_path.unlink()
            
            # Remove from cache
            if user_id in self._profiles_cache:
                del self._profiles_cache[user_id]
            
            logger.info(f"Deleted profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete profile for user {user_id}: {e}")
            return False
