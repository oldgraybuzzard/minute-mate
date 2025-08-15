"""
Comprehensive validation utilities for MinuteMate
Provides input validation, sanitization, and data integrity checks
"""

import re
import logging
import mimetypes
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable
from werkzeug.datastructures import FileStorage
from email_validator import validate_email, EmailNotValidError
import bleach
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None, code: str = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.code = code or 'VALIDATION_ERROR'

class Validator:
    """Base validator class"""
    
    def __init__(self, required: bool = False, allow_none: bool = True):
        self.required = required
        self.allow_none = allow_none
    
    def validate(self, value: Any, field_name: str = None) -> Any:
        """Validate a value"""
        if value is None:
            if self.required:
                raise ValidationError(f"Field '{field_name}' is required", field_name, 'REQUIRED')
            if self.allow_none:
                return None
        
        return self._validate_value(value, field_name)
    
    def _validate_value(self, value: Any, field_name: str = None) -> Any:
        """Override in subclasses"""
        return value

class StringValidator(Validator):
    """String validation with length and pattern constraints"""
    
    def __init__(self, min_length: int = None, max_length: int = None, 
                 pattern: str = None, choices: List[str] = None, 
                 strip: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.choices = choices
        self.strip = strip
    
    def _validate_value(self, value: Any, field_name: str = None) -> str:
        if not isinstance(value, str):
            raise ValidationError(f"Field '{field_name}' must be a string", field_name, 'TYPE_ERROR')
        
        if self.strip:
            value = value.strip()
        
        # Length validation
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                f"Field '{field_name}' must be at least {self.min_length} characters long",
                field_name, 'MIN_LENGTH'
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                f"Field '{field_name}' must be at most {self.max_length} characters long",
                field_name, 'MAX_LENGTH'
            )
        
        # Pattern validation
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(
                f"Field '{field_name}' has invalid format",
                field_name, 'PATTERN_MISMATCH'
            )
        
        # Choices validation
        if self.choices and value not in self.choices:
            raise ValidationError(
                f"Field '{field_name}' must be one of: {', '.join(self.choices)}",
                field_name, 'INVALID_CHOICE'
            )
        
        return value

class EmailValidator(StringValidator):
    """Email validation"""
    
    def __init__(self, **kwargs):
        super().__init__(max_length=255, **kwargs)
    
    def _validate_value(self, value: Any, field_name: str = None) -> str:
        value = super()._validate_value(value, field_name)
        
        try:
            # Use email-validator library for comprehensive validation
            validated_email = validate_email(value)
            return validated_email.email
        except EmailNotValidError as e:
            raise ValidationError(
                f"Field '{field_name}' must be a valid email address",
                field_name, 'INVALID_EMAIL'
            )

class IntegerValidator(Validator):
    """Integer validation with range constraints"""
    
    def __init__(self, min_value: int = None, max_value: int = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Any, field_name: str = None) -> int:
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise ValidationError(f"Field '{field_name}' must be an integer", field_name, 'TYPE_ERROR')
        
        if not isinstance(value, int):
            raise ValidationError(f"Field '{field_name}' must be an integer", field_name, 'TYPE_ERROR')
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"Field '{field_name}' must be at least {self.min_value}",
                field_name, 'MIN_VALUE'
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"Field '{field_name}' must be at most {self.max_value}",
                field_name, 'MAX_VALUE'
            )
        
        return value

class FloatValidator(Validator):
    """Float validation with range constraints"""
    
    def __init__(self, min_value: float = None, max_value: float = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Any, field_name: str = None) -> float:
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise ValidationError(f"Field '{field_name}' must be a number", field_name, 'TYPE_ERROR')
        
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Field '{field_name}' must be a number", field_name, 'TYPE_ERROR')
        
        value = float(value)
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"Field '{field_name}' must be at least {self.min_value}",
                field_name, 'MIN_VALUE'
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"Field '{field_name}' must be at most {self.max_value}",
                field_name, 'MAX_VALUE'
            )
        
        return value

class BooleanValidator(Validator):
    """Boolean validation"""
    
    def _validate_value(self, value: Any, field_name: str = None) -> bool:
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ('true', '1', 'yes', 'on'):
                return True
            elif value_lower in ('false', '0', 'no', 'off'):
                return False
            else:
                raise ValidationError(f"Field '{field_name}' must be a boolean", field_name, 'TYPE_ERROR')
        
        if not isinstance(value, bool):
            raise ValidationError(f"Field '{field_name}' must be a boolean", field_name, 'TYPE_ERROR')
        
        return value

class ListValidator(Validator):
    """List validation with item validation"""
    
    def __init__(self, item_validator: Validator = None, min_items: int = None, 
                 max_items: int = None, **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_items = min_items
        self.max_items = max_items
    
    def _validate_value(self, value: Any, field_name: str = None) -> List[Any]:
        if not isinstance(value, list):
            raise ValidationError(f"Field '{field_name}' must be a list", field_name, 'TYPE_ERROR')
        
        if self.min_items is not None and len(value) < self.min_items:
            raise ValidationError(
                f"Field '{field_name}' must have at least {self.min_items} items",
                field_name, 'MIN_ITEMS'
            )
        
        if self.max_items is not None and len(value) > self.max_items:
            raise ValidationError(
                f"Field '{field_name}' must have at most {self.max_items} items",
                field_name, 'MAX_ITEMS'
            )
        
        if self.item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = self.item_validator.validate(item, f"{field_name}[{i}]")
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(
                        f"Field '{field_name}[{i}]': {e.message}",
                        f"{field_name}[{i}]", e.code
                    )
            return validated_items
        
        return value

class DateTimeValidator(Validator):
    """DateTime validation"""
    
    def __init__(self, format: str = None, **kwargs):
        super().__init__(**kwargs)
        self.format = format or '%Y-%m-%dT%H:%M:%S'
    
    def _validate_value(self, value: Any, field_name: str = None) -> datetime:
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                # Try ISO format first
                if 'T' in value:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    return datetime.strptime(value, self.format)
            except ValueError:
                raise ValidationError(
                    f"Field '{field_name}' must be a valid datetime",
                    field_name, 'INVALID_DATETIME'
                )
        
        raise ValidationError(f"Field '{field_name}' must be a datetime", field_name, 'TYPE_ERROR')

class FileValidator(Validator):
    """File upload validation"""
    
    def __init__(self, allowed_extensions: List[str] = None, max_size: int = None,
                 allowed_mimetypes: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_extensions = [ext.lower() for ext in (allowed_extensions or [])]
        self.max_size = max_size
        self.allowed_mimetypes = allowed_mimetypes or []
    
    def _validate_value(self, value: Any, field_name: str = None) -> FileStorage:
        if not isinstance(value, FileStorage):
            raise ValidationError(f"Field '{field_name}' must be a file", field_name, 'TYPE_ERROR')
        
        if not value.filename:
            raise ValidationError(f"Field '{field_name}' requires a filename", field_name, 'NO_FILENAME')
        
        # Extension validation
        if self.allowed_extensions:
            file_ext = value.filename.rsplit('.', 1)[1].lower() if '.' in value.filename else ''
            if file_ext not in self.allowed_extensions:
                raise ValidationError(
                    f"Field '{field_name}' must have one of these extensions: {', '.join(self.allowed_extensions)}",
                    field_name, 'INVALID_EXTENSION'
                )
        
        # MIME type validation
        if self.allowed_mimetypes:
            mimetype = value.mimetype or mimetypes.guess_type(value.filename)[0]
            if mimetype not in self.allowed_mimetypes:
                raise ValidationError(
                    f"Field '{field_name}' must be one of these file types: {', '.join(self.allowed_mimetypes)}",
                    field_name, 'INVALID_MIMETYPE'
                )
        
        # Size validation
        if self.max_size:
            # Get file size
            value.seek(0, 2)  # Seek to end
            file_size = value.tell()
            value.seek(0)  # Reset to beginning
            
            if file_size > self.max_size:
                max_size_mb = self.max_size / (1024 * 1024)
                raise ValidationError(
                    f"Field '{field_name}' must be smaller than {max_size_mb:.1f}MB",
                    field_name, 'FILE_TOO_LARGE'
                )
        
        return value

class URLValidator(StringValidator):
    """URL validation"""
    
    def __init__(self, schemes: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.schemes = schemes or ['http', 'https']
    
    def _validate_value(self, value: Any, field_name: str = None) -> str:
        value = super()._validate_value(value, field_name)
        
        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError(
                    f"Field '{field_name}' must be a valid URL",
                    field_name, 'INVALID_URL'
                )
            
            if self.schemes and parsed.scheme not in self.schemes:
                raise ValidationError(
                    f"Field '{field_name}' must use one of these schemes: {', '.join(self.schemes)}",
                    field_name, 'INVALID_SCHEME'
                )
            
            return value
        except Exception:
            raise ValidationError(
                f"Field '{field_name}' must be a valid URL",
                field_name, 'INVALID_URL'
            )

class Schema:
    """Schema for validating complex data structures"""
    
    def __init__(self, fields: Dict[str, Validator]):
        self.fields = fields
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema"""
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary", code='TYPE_ERROR')
        
        validated_data = {}
        errors = {}
        
        # Validate each field
        for field_name, validator in self.fields.items():
            try:
                value = data.get(field_name)
                validated_value = validator.validate(value, field_name)
                if validated_value is not None or not validator.allow_none:
                    validated_data[field_name] = validated_value
            except ValidationError as e:
                errors[field_name] = {
                    'message': e.message,
                    'code': e.code
                }
        
        if errors:
            raise ValidationError("Validation failed", code='VALIDATION_FAILED')
        
        return validated_data

def sanitize_html(html_content: str, allowed_tags: List[str] = None) -> str:
    """Sanitize HTML content to prevent XSS"""
    if not html_content:
        return html_content
    
    allowed_tags = allowed_tags or [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]
    
    allowed_attributes = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    return bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    issues = []
    score = 0
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    else:
        score += 1
    
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    else:
        score += 1
    
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    else:
        score += 1
    
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one number")
    else:
        score += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    else:
        score += 1
    
    strength_levels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
    strength = strength_levels[min(score, 4)]
    
    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'strength': strength,
        'score': score
    }
