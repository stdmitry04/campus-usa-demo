# server/core/document_validators.py
import os
from django.core.exceptions import ValidationError
import filetype


def validate_file_size(file):
    """check if uploaded file isn't too big"""
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        raise ValidationError(f'File size cannot exceed {max_size // (1024 * 1024)}MB')


def validate_file_extension(file):
    """make sure file has an allowed extension"""
    allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.txt']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'File extension {ext} is not allowed. Allowed: {", ".join(allowed_extensions)}')


def validate_file_mimetype(file):
    """verify the actual file type matches what we expect"""
    # allowed mime types
    allowed_mimes = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }

    # reset file pointer to beginning
    file.seek(0)

    # guess the file type from content
    kind = filetype.guess(file.read(1024))  # read first 1KB to determine type

    # reset file pointer again for other processes
    file.seek(0)

    if kind is None:
        # couldn't determine file type, maybe it's plain text
        if file.name.lower().endswith('.txt'):
            return  # allow txt files even if filetype can't detect them
        raise ValidationError('Could not determine file type')

    if kind.mime not in allowed_mimes:
        raise ValidationError(f'File type {kind.mime} is not allowed')


def validate_filename(file):
    """ensure filename doesn't contain problematic characters"""
    filename = file.name

    # basic filename validation
    if not filename:
        raise ValidationError('Filename cannot be empty')

    # check for dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    for char in dangerous_chars:
        if char in filename:
            raise ValidationError(f'Filename contains invalid character: {char}')

    # check filename length
    if len(filename) > 255:
        raise ValidationError('Filename is too long (max 255 characters)')


def sanitize_title(title):
    """sanitize document title removing dangerous characters"""
    if not title:
        return 'untitled'

    # remove html tags and dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\\', '/', '\x00', '\n', '\r', '\t']

    sanitized = title
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    # replace multiple spaces with single space
    sanitized = ' '.join(sanitized.split())

    # limit length
    sanitized = sanitized[:100].strip()

    return sanitized or 'untitled'


def validate_document_file(file):
    """comprehensive document file validation (same as before)"""
    validate_file_size(file)
    validate_file_extension(file)
    validate_file_mimetype(file)
    validate_filename(file)
