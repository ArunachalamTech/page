# Link formatting utilities for Telegram captions
# Copyright 2021 To 2024-present, Author: MrAKTech

import re
from typing import Optional

def format_links_in_text(text: str, parse_mode: str = "HTML") -> str:
    """
    Format links in text for Telegram captions
    Supports both Markdown and HTML link formats
    
    Args:
        text: The text containing links
        parse_mode: Either "HTML" or "MARKDOWN" 
        
    Returns:
        Formatted text with proper link syntax
    """
    if not text:
        return text
    
    # Markdown link pattern: [text](url) - now handles spaces between ] and (
    markdown_pattern = r'\[([^\]]+)\]\s*\(([^)]+)\)'
    
    if parse_mode.upper() == "HTML":
        # Convert Markdown links to HTML format
        def markdown_to_html(match):
            link_text = match.group(1)
            url = match.group(2)
            return f'<a href="{url}">{link_text}</a>'
        
        text = re.sub(markdown_pattern, markdown_to_html, text)
        
    elif parse_mode.upper() == "MARKDOWN":
        # Keep Markdown format or convert HTML to Markdown
        html_pattern = r'<a href="([^"]+)">([^<]+)</a>'
        
        def html_to_markdown(match):
            url = match.group(1)
            link_text = match.group(2)
            return f'[{link_text}]({url})'
        
        text = re.sub(html_pattern, html_to_markdown, text)
    
    return text

def validate_links_in_text(text: str) -> tuple[bool, list[str]]:
    """
    Validate that all links in text are properly formatted
    
    Args:
        text: Text to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if not text:
        return True, []
    
    errors = []
    
    # Check for common link formatting issues
    
    # 1. Check for unmatched brackets in markdown links
    markdown_pattern = r'\[([^\]]*)\]\s*\(([^)]*)\)'
    markdown_matches = re.findall(markdown_pattern, text)
    
    # Check for empty link text or URLs
    for link_text, url in markdown_matches:
        if not link_text.strip():
            errors.append("Found link with empty text")
        if not url.strip():
            errors.append("Found link with empty URL")
        if not url.startswith(('http://', 'https://', 'tg://', 'telegram.me', 't.me')):
            errors.append(f"Invalid URL format: {url}")
    
    # 2. Check for unmatched HTML tags
    html_pattern = r'<a href="([^"]*)"[^>]*>([^<]*)</a>'
    html_matches = re.findall(html_pattern, text)
    
    for url, link_text in html_matches:
        if not link_text.strip():
            errors.append("Found HTML link with empty text")
        if not url.strip():
            errors.append("Found HTML link with empty URL")
        if not url.startswith(('http://', 'https://', 'tg://', 'telegram.me', 't.me')):
            errors.append(f"Invalid URL format: {url}")
    
    # 3. Check for malformed links
    malformed_patterns = [
        r'\[[^\]]*\s*\([^)]*\]',  # [text (url] or [text(url]
        r'\([^\)]*\]\s*[^)]*\)',  # (text] url) or (text]url)
        r'\[[^\]]*\)\s*\([^)]*',  # [text) (url or [text)(url
    ]
    
    for pattern in malformed_patterns:
        if re.search(pattern, text):
            errors.append("Found malformed link syntax")
            break
    
    return len(errors) == 0, errors

def extract_links_from_text(text: str) -> list[dict]:
    """
    Extract all links from text
    
    Args:
        text: Text containing links
        
    Returns:
        List of dictionaries with 'text' and 'url' keys
    """
    if not text:
        return []
    
    links = []
    
    # Extract Markdown links
    markdown_pattern = r'\[([^\]]+)\]\s*\(([^)]+)\)'
    for match in re.finditer(markdown_pattern, text):
        links.append({
            'text': match.group(1),
            'url': match.group(2),
            'format': 'markdown'
        })
    
    # Extract HTML links
    html_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
    for match in re.finditer(html_pattern, text):
        links.append({
            'text': match.group(2),
            'url': match.group(1),
            'format': 'html'
        })
    
    return links

def create_link(text: str, url: str, format_type: str = "HTML") -> str:
    """
    Create a formatted link
    
    Args:
        text: Link text to display
        url: URL to link to
        format_type: "HTML" or "MARKDOWN"
        
    Returns:
        Formatted link string
    """
    if format_type.upper() == "HTML":
        return f'<a href="{url}">{text}</a>'
    else:
        return f'[{text}]({url})'

def sanitize_link_text(text: str) -> str:
    """
    Sanitize text to be safe for use in links
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove potentially problematic characters
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace('&', '&amp;')
    return text

def get_link_examples() -> dict:
    """
    Get example link formats for user reference
    
    Returns:
        Dictionary with example formats
    """
    return {
        "markdown_examples": [
            "[Click Here](https://example.com)",
            "[Join Channel](https://t.me/your_channel)",
            "[Download](https://your-shortener.com/abc123)",
            "[How to Open](https://t.me/shotner_solution/6)"
        ],
        "html_examples": [
            '<a href="https://example.com">Click Here</a>',
            '<a href="https://t.me/your_channel">Join Channel</a>',
            '<a href="https://your-shortener.com/abc123">Download</a>',
            '<a href="https://t.me/shotner_solution/6">How to Open</a>'
        ],
        "telegram_links": [
            "[User Profile](tg://user?id=123456789)",
            "[Channel](https://t.me/channel_name)",
            "[Group](https://t.me/group_name)",
            "[Bot](https://t.me/bot_username)"
        ]
    }
