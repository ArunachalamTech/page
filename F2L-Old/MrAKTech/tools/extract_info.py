"""
File information extraction utilities for quality, season, and episode detection
Based on Auto-Rename-Bot patterns
"""
import re

# Episode number patterns - improved to avoid quality numbers
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)', re.IGNORECASE)
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)', re.IGNORECASE)
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)\s*(\d{1,3})\s*[)\]>}]?)', re.IGNORECASE)  # Limit to 3 digits max
pattern3_2 = re.compile(r'(?:\s*-\s*(\d{1,2})\s*)', re.IGNORECASE)  # Limit to 2 digits max
pattern4 = re.compile(r'S(\d+)[^\d]*(\d{1,3})', re.IGNORECASE)  # Limit to 3 digits max
patternX = re.compile(r'(\d{1,2})', re.IGNORECASE)  # Limit to 2 digits max

# Season patterns
season_pattern1 = re.compile(r'S(\d+)', re.IGNORECASE)
season_pattern2 = re.compile(r'Season\s*(\d+)', re.IGNORECASE)
season_pattern3 = re.compile(r'(?:[([<{]?\s*S(\d+)\s*[)\]>}]?)', re.IGNORECASE)

# Quality patterns - improved to be more specific and capture standard resolutions
pattern5 = re.compile(r'\b(144p|240p|360p|480p|540p|720p|1080p|1440p|2160p)\b', re.IGNORECASE)
pattern6 = re.compile(r'\b4k\b', re.IGNORECASE)
pattern7 = re.compile(r'\b2k\b', re.IGNORECASE)
pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)\]>}]?', re.IGNORECASE)
pattern11 = re.compile(r'[([<{]?\s*BluRay\s*[)\]>}]?|\bBluRay\b', re.IGNORECASE)
pattern12 = re.compile(r'[([<{]?\s*WEB-DL\s*[)\]>}]?|\bWEB-DL\b', re.IGNORECASE)
pattern13 = re.compile(r'[([<{]?\s*HDTV\s*[)\]>}]?|\bHDTV\b', re.IGNORECASE)

def extract_quality(filename):
    """Extract video quality from filename and standardize to specific values with brackets"""
    if not filename:
        return ""  # Return empty string instead of space
    
    # Define allowed quality values and their mappings (with brackets)
    quality_mappings = {
        '144p': '(144p)',
        '240p': '(240p)', 
        '360p': '(360p)',
        '480p': '(480p)',
        '540p': '(540p)',
        '720p': '(720p)',
        '1080p': '(1080p)',
        '1440p': '(1440p)',
        '2160p': '(4K)',  # 2160p maps to (4K)
    }
    
    # Try to find standard resolution patterns (144p, 240p, 360p, 480p, 720p, 1080p, 2160p)
    match5 = re.search(pattern5, filename)
    if match5:
        quality_found = match5.group(1).lower()
        return quality_mappings.get(quality_found, f"({quality_found})")
    
    # Check for 4K specifically
    match6 = re.search(pattern6, filename)
    if match6:
        return "(4K)"
    
    # Check for 2K specifically  
    match7 = re.search(pattern7, filename)
    if match7:
        return "(2K)"
    
    # If no standard quality found, return empty string
    return ""

def extract_episode_number(filename):
    """Extract episode number from filename, avoiding quality numbers and years"""
    if not filename:
        return " "
    
    # Avoid common quality numbers and years
    avoid_numbers = ['144', '240', '360', '480', '720', '1080', '2160', '2025', '2024', '2023', '2022', '2021', '2020']
    
    # Try Pattern 1: S01E02 or S01EP02 (most reliable)
    match = re.search(pattern1, filename)
    if match:
        episode = match.group(2)
        if episode not in avoid_numbers:
            return episode.zfill(2)  # Pad with zero if needed (e.g., "1" -> "01")
    
    # Try Pattern 2: S01 E02 or S01 EP02 or S01 - E01 or S01 - EP02
    match = re.search(pattern2, filename)
    if match:
        episode = match.group(2)
        if episode not in avoid_numbers:
            return episode.zfill(2)

    # Try Pattern 3: Episode Number After "E" or "EP" (only if very clear)
    match = re.search(pattern3, filename)
    if match:
        episode = match.group(1)
        # Only accept if it's clearly an episode (1-2 digits, not quality/year)
        if episode not in avoid_numbers and len(episode) <= 2 and int(episode) <= 50:
            return episode.zfill(2)

    # Skip other patterns as they're too ambiguous
    return " "

def extract_season_number(filename):
    """Extract season number from filename"""
    if not filename:
        return " "
    
    # Try Season Pattern 1: S01
    match = re.search(season_pattern1, filename)
    if match:
        season = match.group(1)
        # Only accept reasonable season numbers (1-2 digits, not years)
        if len(season) <= 2 and int(season) <= 50:
            return season.zfill(2)  # Pad with zero if needed
    
    # Try Season Pattern 2: Season 1
    match = re.search(season_pattern2, filename)
    if match:
        season = match.group(1)
        if len(season) <= 2 and int(season) <= 50:
            return season.zfill(2)
        
    # Try Season Pattern 3: [S1] or (S1)
    match = re.search(season_pattern3, filename)
    if match:
        season = match.group(1)
        if len(season) <= 2 and int(season) <= 50:
            return season.zfill(2)
        
    return " "

def format_extracted_info(filename, quality=None, season=None, episode=None):
    """Format extracted information for display"""
    info = []
    
    if quality and quality != "Unknown":
        info.append(f"Quality: {quality}")
    
    if season:
        info.append(f"Season: {season}")
        
    if episode:
        info.append(f"Episode: {episode}")
    
    return " | ".join(info) if info else ""

def replace_placeholders_in_caption(caption, filename, quality=None, season=None, episode=None):
    """Replace quality, season, and episode placeholders in caption"""
    if not caption:
        return caption
    
    # Extract info if not provided
    if quality is None:
        quality = extract_quality(filename)
    if season is None:
        season = extract_season_number(filename)
    if episode is None:
        episode = extract_episode_number(filename)
    
    # Replace quality placeholders
    quality_placeholders = ["{quality}", "{Quality}", "{QUALITY}", "quality", "Quality", "QUALITY"]
    for placeholder in quality_placeholders:
        if placeholder in caption:
            caption = caption.replace(placeholder, quality or "Unknown")
    
    # Replace season placeholders
    season_placeholders = ["{season}", "{Season}", "{SEASON}", "season", "Season", "SEASON"]
    for placeholder in season_placeholders:
        if placeholder in caption:
            caption = caption.replace(placeholder, season or "Unknown")
    
    # Replace episode placeholders
    episode_placeholders = ["{episode}", "{Episode}", "{EPISODE}", "episode", "Episode", "EPISODE"]
    for placeholder in episode_placeholders:
        if placeholder in caption:
            caption = caption.replace(placeholder, episode or "Unknown")
    
    return caption

def extract_combined_info(filename, original_caption=None):
    """
    Extract quality, season, and episode from both filename and original caption.
    Combines the best available information from both sources.
    Returns spaces for missing values instead of None.
    """
    # Extract from filename
    filename_quality = extract_quality(filename)
    filename_season = extract_season_number(filename)
    filename_episode = extract_episode_number(filename)
    
    # Extract from original caption if provided
    caption_quality = None
    caption_season = None
    caption_episode = None
    
    if original_caption:
        caption_quality = extract_quality(original_caption)
        caption_season = extract_season_number(original_caption)
        caption_episode = extract_episode_number(original_caption)
    
    # Combine results - prefer filename but fallback to caption if filename is empty/space
    final_quality = filename_quality if filename_quality and filename_quality.strip() else (caption_quality if caption_quality and caption_quality.strip() else "")
    final_season = filename_season if filename_season else (caption_season if caption_season else " ")
    final_episode = filename_episode if filename_episode else (caption_episode if caption_episode else " ")
    
    return {
        'quality': final_quality,
        'season': final_season,
        'episode': final_episode,
        'sources': {
            'filename': {
                'quality': filename_quality,
                'season': filename_season,
                'episode': filename_episode
            },
            'caption': {
                'quality': caption_quality,
                'season': caption_season,
                'episode': caption_episode
            }
        }
    }


def smart_replace_placeholders_in_caption(caption, filename, original_caption=None):
    """
    Smart replacement that extracts from both filename and original caption
    to get the most complete information possible.
    """
    if not caption:
        return caption
    
    # Get combined extraction results
    extracted_info = extract_combined_info(filename, original_caption)
    
    quality = extracted_info['quality']
    season = extracted_info['season'] 
    episode = extracted_info['episode']
    
    # Replace quality placeholders
    if "{quality}" in caption:
        caption = caption.replace("{quality}", quality or "Unknown")
    if "{Quality}" in caption:
        caption = caption.replace("{Quality}", quality or "Unknown")
    if "{QUALITY}" in caption:
        caption = caption.replace("{QUALITY}", quality or "Unknown")
    
    # Replace season placeholders
    if "{season}" in caption:
        caption = caption.replace("{season}", season or "Unknown")
    if "{Season}" in caption:
        caption = caption.replace("{Season}", season or "Unknown")
    if "{SEASON}" in caption:
        caption = caption.replace("{SEASON}", season or "Unknown")
    
    # Replace episode placeholders
    if "{episode}" in caption:
        caption = caption.replace("{episode}", episode or "Unknown")
    if "{Episode}" in caption:
        caption = caption.replace("{Episode}", episode or "Unknown")
    if "{EPISODE}" in caption:
        caption = caption.replace("{EPISODE}", episode or "Unknown")
    
    return caption

def create_safe_format_dict(basic_dict, filename, caption):
    """
    Create a safe format dictionary that includes all possible placeholders
    to prevent KeyError when using .format()
    
    Args:
        basic_dict: Dictionary with basic placeholders (file_name, caption, file_size, etc.)
        filename: Original filename for extraction
        caption: Original caption for extraction
    
    Returns:
        Complete dictionary with all possible placeholders
    """
    # Start with the basic dictionary
    safe_dict = basic_dict.copy()
    
    # Extract info from filename and caption
    info = extract_combined_info(filename, caption)
      # Add extraction placeholders with default spaces for missing values
    safe_dict.update({
        'quality': info.get('quality', ' '),
        'Quality': info.get('quality', ' '),
        'QUALITY': info.get('quality', ' '),
        'season': info.get('season', ' '),
        'Season': info.get('season', ' '),
        'SEASON': info.get('season', ' '),
        'episode': info.get('episode', ' '),
        'Episode': info.get('episode', ' '),
        'EPISODE': info.get('episode', ' '),
    })
    
    return safe_dict
