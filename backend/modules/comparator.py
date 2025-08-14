"""
MinuteMate Document Comparator
Compares original AI-generated minutes with user-edited versions to learn preferences.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher
from docx import Document
import json

logger = logging.getLogger(__name__)

class DocumentChange:
    """Represents a change made to a document"""
    
    def __init__(self, change_type: str, original: str, modified: str, 
                 context: str = "", confidence: float = 1.0):
        self.change_type = change_type  # addition, deletion, modification, formatting
        self.original = original
        self.modified = modified
        self.context = context
        self.confidence = confidence
        self.category = self._categorize_change()
    
    def _categorize_change(self) -> str:
        """Categorize the type of change for learning purposes"""
        if self.change_type == "addition":
            if "motion" in self.modified.lower():
                return "motion_enhancement"
            elif "discussion" in self.modified.lower():
                return "discussion_addition"
            else:
                return "content_addition"
        elif self.change_type == "deletion":
            return "content_removal"
        elif self.change_type == "modification":
            if len(self.modified) > len(self.original) * 1.5:
                return "content_expansion"
            elif len(self.modified) < len(self.original) * 0.5:
                return "content_condensation"
            else:
                return "content_refinement"
        else:
            return "formatting_change"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'change_type': self.change_type,
            'original': self.original,
            'modified': self.modified,
            'context': self.context,
            'confidence': self.confidence,
            'category': self.category
        }

class DocumentComparator:
    """Compares documents to identify user preferences and changes"""
    
    def __init__(self):
        """Initialize the document comparator"""
        self.similarity_threshold = 0.6
        logger.info("DocumentComparator initialized")
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            str: Extracted text
        """
        try:
            doc = Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")
            raise
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison
        
        Args:
            text: Text to normalize
            
        Returns:
            str: Normalized text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common formatting artifacts
        text = re.sub(r'[•\-\*]\s*', '', text)  # Remove bullet points
        text = re.sub(r'\n+', '\n', text)  # Normalize line breaks
        
        return text.strip()
    
    def _find_text_differences(self, original: str, modified: str) -> List[DocumentChange]:
        """
        Find differences between two text documents
        
        Args:
            original: Original text
            modified: Modified text
            
        Returns:
            List of DocumentChange objects
        """
        changes = []
        
        # Normalize texts
        orig_normalized = self._normalize_text(original)
        mod_normalized = self._normalize_text(modified)
        
        # Split into lines for comparison
        orig_lines = orig_normalized.split('\n')
        mod_lines = mod_normalized.split('\n')
        
        # Use SequenceMatcher to find differences
        matcher = SequenceMatcher(None, orig_lines, mod_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            elif tag == 'delete':
                # Content was removed
                deleted_content = '\n'.join(orig_lines[i1:i2])
                context = self._get_context(orig_lines, i1, i2)
                changes.append(DocumentChange(
                    change_type="deletion",
                    original=deleted_content,
                    modified="",
                    context=context
                ))
            elif tag == 'insert':
                # Content was added
                inserted_content = '\n'.join(mod_lines[j1:j2])
                context = self._get_context(mod_lines, j1, j2)
                changes.append(DocumentChange(
                    change_type="addition",
                    original="",
                    modified=inserted_content,
                    context=context
                ))
            elif tag == 'replace':
                # Content was modified
                original_content = '\n'.join(orig_lines[i1:i2])
                modified_content = '\n'.join(mod_lines[j1:j2])
                context = self._get_context(orig_lines, i1, i2)
                changes.append(DocumentChange(
                    change_type="modification",
                    original=original_content,
                    modified=modified_content,
                    context=context
                ))
        
        return changes
    
    def _get_context(self, lines: List[str], start: int, end: int, 
                    context_size: int = 2) -> str:
        """
        Get context around changed lines
        
        Args:
            lines: List of text lines
            start: Start index of change
            end: End index of change
            context_size: Number of lines before/after to include
            
        Returns:
            str: Context text
        """
        context_start = max(0, start - context_size)
        context_end = min(len(lines), end + context_size)
        
        context_lines = lines[context_start:context_start] + ["[CHANGE]"] + lines[context_end:context_end]
        return '\n'.join(context_lines)
    
    def _analyze_formatting_changes(self, original_docx: str, modified_docx: str) -> List[DocumentChange]:
        """
        Analyze formatting changes between DOCX documents
        
        Args:
            original_docx: Path to original DOCX
            modified_docx: Path to modified DOCX
            
        Returns:
            List of formatting changes
        """
        changes = []
        
        try:
            orig_doc = Document(original_docx)
            mod_doc = Document(modified_docx)
            
            # Compare paragraph styles
            orig_styles = [p.style.name for p in orig_doc.paragraphs if p.text.strip()]
            mod_styles = [p.style.name for p in mod_doc.paragraphs if p.text.strip()]
            
            if orig_styles != mod_styles:
                changes.append(DocumentChange(
                    change_type="formatting",
                    original=f"Styles: {orig_styles[:5]}...",  # First 5 styles
                    modified=f"Styles: {mod_styles[:5]}...",
                    context="Document styling"
                ))
        
        except Exception as e:
            logger.warning(f"Could not analyze formatting changes: {e}")
        
        return changes
    
    def compare_documents(self, original_path: str, modified_path: str) -> Dict[str, Any]:
        """
        Compare original and modified documents
        
        Args:
            original_path: Path to original document
            modified_path: Path to modified document
            
        Returns:
            Dictionary with comparison results
        """
        logger.info(f"Comparing documents: {original_path} vs {modified_path}")
        
        try:
            # Extract text from both documents
            if original_path.endswith('.docx'):
                original_text = self._extract_text_from_docx(original_path)
            else:
                with open(original_path, 'r', encoding='utf-8') as f:
                    original_text = f.read()
            
            if modified_path.endswith('.docx'):
                modified_text = self._extract_text_from_docx(modified_path)
            else:
                with open(modified_path, 'r', encoding='utf-8') as f:
                    modified_text = f.read()
            
            # Find text differences
            text_changes = self._find_text_differences(original_text, modified_text)
            
            # Analyze formatting changes if both are DOCX
            formatting_changes = []
            if original_path.endswith('.docx') and modified_path.endswith('.docx'):
                formatting_changes = self._analyze_formatting_changes(original_path, modified_path)
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, original_text, modified_text).ratio()
            
            # Categorize changes
            change_categories = {}
            for change in text_changes + formatting_changes:
                category = change.category
                if category not in change_categories:
                    change_categories[category] = 0
                change_categories[category] += 1
            
            results = {
                'similarity_score': similarity,
                'total_changes': len(text_changes) + len(formatting_changes),
                'text_changes': [change.to_dict() for change in text_changes],
                'formatting_changes': [change.to_dict() for change in formatting_changes],
                'change_categories': change_categories,
                'analysis_summary': self._generate_analysis_summary(text_changes, formatting_changes, similarity)
            }
            
            logger.info(f"Document comparison completed. Similarity: {similarity:.2f}, Changes: {len(text_changes)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            raise
    
    def _generate_analysis_summary(self, text_changes: List[DocumentChange], 
                                 formatting_changes: List[DocumentChange], 
                                 similarity: float) -> Dict[str, Any]:
        """
        Generate a summary of the analysis
        
        Args:
            text_changes: List of text changes
            formatting_changes: List of formatting changes
            similarity: Similarity score
            
        Returns:
            Dictionary with analysis summary
        """
        summary = {
            'overall_assessment': '',
            'key_patterns': [],
            'recommendations': []
        }
        
        # Overall assessment
        if similarity > 0.9:
            summary['overall_assessment'] = 'Minor edits - mostly formatting or small content adjustments'
        elif similarity > 0.7:
            summary['overall_assessment'] = 'Moderate changes - some content restructuring'
        elif similarity > 0.5:
            summary['overall_assessment'] = 'Significant changes - substantial content modifications'
        else:
            summary['overall_assessment'] = 'Major rewrite - extensive changes throughout'
        
        # Identify patterns
        if len([c for c in text_changes if c.category == 'content_expansion']) > 2:
            summary['key_patterns'].append('User prefers more detailed content')
        
        if len([c for c in text_changes if c.category == 'content_condensation']) > 2:
            summary['key_patterns'].append('User prefers more concise content')
        
        if len([c for c in text_changes if c.category == 'motion_enhancement']) > 0:
            summary['key_patterns'].append('User enhances motion descriptions')
        
        # Generate recommendations
        if summary['key_patterns']:
            summary['recommendations'].append('Adjust content detail level based on user preferences')
        
        if len(formatting_changes) > 0:
            summary['recommendations'].append('Consider user formatting preferences in future documents')
        
        return summary
    
    def extract_user_preferences(self, comparison_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract user preferences from multiple comparison results
        
        Args:
            comparison_results: List of comparison result dictionaries
            
        Returns:
            Dictionary with extracted preferences
        """
        preferences = {
            'content_style': 'balanced',  # concise, balanced, detailed
            'formatting_preferences': {},
            'common_additions': [],
            'common_removals': [],
            'confidence_score': 0.0
        }
        
        if not comparison_results:
            return preferences
        
        # Analyze patterns across all comparisons
        all_changes = []
        for result in comparison_results:
            all_changes.extend(result.get('text_changes', []))
        
        # Determine content style preference
        expansions = len([c for c in all_changes if c.get('category') == 'content_expansion'])
        condensations = len([c for c in all_changes if c.get('category') == 'content_condensation'])
        
        if expansions > condensations * 1.5:
            preferences['content_style'] = 'detailed'
        elif condensations > expansions * 1.5:
            preferences['content_style'] = 'concise'
        
        # Calculate confidence based on number of comparisons
        preferences['confidence_score'] = min(len(comparison_results) / 5.0, 1.0)
        
        logger.info(f"Extracted user preferences: {preferences['content_style']} style, confidence: {preferences['confidence_score']:.2f}")
        
        return preferences
