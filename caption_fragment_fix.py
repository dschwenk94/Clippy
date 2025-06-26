#!/usr/bin/env python3
"""
Fix for fragmented caption updates
"""

def merge_fragmented_captions(captions):
    """
    Merge captions that have been incorrectly fragmented by the frontend
    Groups captions by speaker and combines those that are too short or incomplete
    """
    if not captions:
        return captions
    
    merged_captions = []
    current_group = []
    current_speaker = None
    
    for i, caption in enumerate(captions):
        speaker = caption.get('speaker', 'Speaker 1')
        text = caption.get('text', '').strip()
        
        # Skip empty captions
        if not text:
            continue
        
        # More conservative fragment detection - only merge VERY short fragments
        is_fragment = (
            len(text) <= 3 or  # Single letters or very short ("I", "Oh", etc)
            (len(text) < 8 and text.endswith(',')) or  # Short with comma
            (len(text) == 1 and text.isalpha())  # Single letter
        )
        
        # Check if this looks like a continuation
        is_continuation = (
            i > 0 and 
            speaker == current_speaker and
            is_fragment and
            current_group and
            len(current_group[-1].get('text', '')) < 15  # Previous was also short
        )
        
        if is_continuation:
            current_group.append(caption)
        else:
            # Process accumulated group
            if current_group:
                if len(current_group) > 1:  # Only merge if multiple fragments
                    merged_caption = merge_caption_group(current_group)
                    merged_captions.append(merged_caption)
                else:
                    merged_captions.append(current_group[0])
            
            # Start new group
            current_group = [caption]
            current_speaker = speaker
    
    # Don't forget the last group
    if current_group:
        if len(current_group) > 1:
            merged_caption = merge_caption_group(current_group)
            merged_captions.append(merged_caption)
        else:
            merged_captions.append(current_group[0])
    
    # Re-index the merged captions
    for i, caption in enumerate(merged_captions):
        caption['index'] = i
    
    return merged_captions

def merge_caption_group(caption_group):
    """Merge a group of caption fragments into one coherent caption"""
    if len(caption_group) == 1:
        return caption_group[0].copy()
    
    # Combine text with proper spacing
    combined_text = ""
    for caption in caption_group:
        text = caption.get('text', '').strip()
        if combined_text and not combined_text.endswith((' ', ',', '.', '!', '?')):
            combined_text += " "
        combined_text += text
    
    # Use timing from first and last caption in group
    merged_caption = {
        'text': combined_text.strip(),
        'speaker': caption_group[0].get('speaker', 'Speaker 1'),
        'start_time': caption_group[0].get('start_time', '0:00:00.00'),
        'end_time': caption_group[-1].get('end_time', '0:00:01.00'),
        'index': caption_group[0].get('index', 0)
    }
    
    return merged_caption

def validate_and_fix_captions(captions):
    """
    Validate and fix caption issues before processing
    """
    # First, merge fragments
    captions = merge_fragmented_captions(captions)
    
    # Then ensure each caption has reasonable duration
    MIN_DURATION = 0.8  # seconds
    MAX_DURATION = 4.0  # seconds
    
    for i, caption in enumerate(captions):
        text = caption.get('text', '').strip()
        if not text:
            continue
        
        # Estimate reasonable duration based on text length
        words = len(text.split())
        estimated_duration = max(MIN_DURATION, min(words * 0.3, MAX_DURATION))
        
        # Update end time if needed
        start_time = caption.get('start_time', '0:00:00.00')
        # This would need the time conversion functions from the main system
        # For now, just ensure the structure is correct
    
    return captions

# Add this function to the ASS caption update system
def preprocess_captions_for_update(captions):
    """
    Preprocess captions before updating to fix common issues
    """
    # Check if captions are fragmented
    avg_text_length = sum(len(c.get('text', '')) for c in captions) / len(captions) if captions else 0
    
    if avg_text_length < 15:  # Likely fragmented
        print("⚠️ Detected fragmented captions, merging...")
        captions = merge_fragmented_captions(captions)
        print(f"✅ Merged to {len(captions)} captions")
    
    return captions
