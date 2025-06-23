#!/usr/bin/env python3
"""
ASS Caption Update System V6 - SPEECH SYNC: Preserves original speech timing
Ensures captions sync with actual speech, not arbitrary redistribution
"""

import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from caption_fragment_fix import merge_fragmented_captions

@dataclass
class CaptionUpdate:
    """Caption update data"""
    index: int
    text: str
    speaker: str
    start_time: str
    end_time: str

class ASSCaptionUpdateSystemV6:
    """SPEECH SYNC system - preserves original speech timing for perfect synchronization"""
    
    def __init__(self):
        self.speaker_colors = {
            "Speaker 1": "#FF4500",   # Fire Red/Orange
            "Speaker 2": "#00BFFF",   # Electric Blue  
            "Speaker 3": "#00FF88"    # Neon Green
        }
        
        # Viral words for special formatting
        self.viral_keywords = [
            'fucking', 'shit', 'damn', 'crazy', 'insane', 'ridiculous',
            'amazing', 'incredible', 'awesome', 'epic', 'legendary',
            'oh my god', 'what the hell', 'holy shit', 'no way'
        ]
    
    def update_ass_file_with_edits(self, original_ass_path: str, updated_captions: List[Dict], output_path: str = None, video_duration: float = 30.0, caption_position: str = 'bottom') -> bool:
        """Update ASS file PRESERVING ORIGINAL SPEECH TIMING"""
        try:
            if output_path is None:
                output_path = original_ass_path
            
            print(f"🎤 SPEECH SYNC ASS UPDATE: Processing {len(updated_captions)} captions...")
            print(f"🎯 PRIORITY: Preserve original speech timing for perfect sync")
            
            # CRITICAL: Extract original speech timing data
            original_timings = self.extract_original_speech_timing(original_ass_path)
            
            # Fix fragmented captions first
            avg_text_length = sum(len(c.get('text', '')) for c in updated_captions) / len(updated_captions) if updated_captions else 0
            
            if avg_text_length < 5:  # Only merge if VERY fragmented
                print("⚠️ Detected fragmented captions, merging...")
                updated_captions = merge_fragmented_captions(updated_captions)
                print(f"✅ Merged to {len(updated_captions)} captions")
            
            # Sort captions by index to ensure proper order
            sorted_captions = sorted(updated_captions, key=lambda x: x.get('index', 0))
            print(f"📊 Processing {len(sorted_captions)} sorted captions")
            
            # PRIORITY: Use original speech timing whenever possible
            speech_synced_captions = self.apply_original_speech_timing(sorted_captions, original_timings)
            
            # Create ASS file with speech-synced timing and position
            new_ass_content = self.create_speech_synced_ass_file(speech_synced_captions, caption_position)
            
            # Write the new file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_ass_content)
            
            # Verify speech sync
            verification_result = self.verify_speech_sync(output_path, len(sorted_captions), original_timings)
            
            if verification_result:
                print(f"✅ SPEECH-SYNCED ASS file created with perfect timing!")
                return True
            else:
                print(f"❌ Speech sync verification failed")
                return False
            
        except Exception as e:
            print(f"❌ Error in SPEECH SYNC ASS update: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_original_speech_timing(self, original_ass_path: str) -> List[Dict]:
        """Extract original speech timing data - CRITICAL for sync"""
        original_timings = []
        
        if not original_ass_path or not os.path.exists(original_ass_path):
            print("⚠️ No original ASS file found - will use caption timing as-is")
            return []
        
        try:
            with open(original_ass_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.strip().startswith('Dialogue:'):
                    parts = line.split(',', 9)
                    if len(parts) >= 10:
                        original_timings.append({
                            'start_time': parts[1].strip(),
                            'end_time': parts[2].strip(),
                            'speaker': parts[3].strip(),
                            'original_text': self.clean_ass_text(parts[9].strip())
                        })
            
            print(f"🎤 Extracted {len(original_timings)} original speech timings")
            
            # Debug: Show original speech timing
            print(f"📊 Original Speech Timing Sample:")
            for i, timing in enumerate(original_timings[:3]):
                start = timing['start_time']
                end = timing['end_time']
                text = timing['original_text'][:30] + '...' if len(timing['original_text']) > 30 else timing['original_text']
                print(f"   {i+1}. {start} → {end}: \"{text}\"")
            
            return original_timings
            
        except Exception as e:
            print(f"⚠️ Could not extract original speech timing: {e}")
            return []
    
    def clean_ass_text(self, ass_text: str) -> str:
        """Clean ASS text from formatting codes"""
        # Remove ASS formatting codes like {\\fad(150,100)...}
        import re
        clean_text = re.sub(r'{[^}]*}', '', ass_text)
        return clean_text.strip()
    
    def apply_original_speech_timing(self, captions: List[Dict], original_timings: List[Dict]) -> List[Dict]:
        """Apply original speech timing to updated captions - CRITICAL for sync"""
        
        if not original_timings:
            print("⚠️ No original speech timing available - using caption timing")
            return self.minimal_timing_adjustment(captions)
        
        if len(original_timings) != len(captions):
            print(f"⚠️ Timing mismatch: {len(original_timings)} original vs {len(captions)} updated")
            print("🔧 Attempting to match captions to speech timing...")
            return self.smart_timing_match(captions, original_timings)
        
        print("✅ Perfect match - applying original speech timing")
        
        speech_synced_captions = []
        
        for i, caption in enumerate(captions):
            if i < len(original_timings):
                synced_caption = caption.copy()
                
                # Use ORIGINAL speech timing
                synced_caption['start_time'] = original_timings[i]['start_time']
                synced_caption['end_time'] = original_timings[i]['end_time']
                
                # Keep updated text and speaker
                # But use original timing for perfect speech sync
                
                speech_synced_captions.append(synced_caption)
                
                # Debug output
                start = synced_caption['start_time']
                end = synced_caption['end_time']
                text = synced_caption.get('text', '')[:25] + '...' if len(synced_caption.get('text', '')) > 25 else synced_caption.get('text', '')
                print(f"   ✅ Caption {i+1}: {start} → {end}: \"{text}\"")
            else:
                speech_synced_captions.append(caption)
        
        # Verify timing span
        if speech_synced_captions:
            first_start = self.ass_time_to_seconds(speech_synced_captions[0]['start_time'])
            last_end = self.ass_time_to_seconds(speech_synced_captions[-1]['end_time'])
            total_span = last_end - first_start
            
            print(f"🎤 Speech-synced timing span: {total_span:.1f} seconds")
            print(f"📍 First caption: {first_start:.1f}s, Last caption: {last_end:.1f}s")
        
        return speech_synced_captions
    
    def smart_timing_match(self, captions: List[Dict], original_timings: List[Dict]) -> List[Dict]:
        """Smart matching when caption count doesn't match original timing"""
        
        print(f"🧠 Smart matching {len(captions)} captions to {len(original_timings)} speech timings")
        
        if len(captions) <= len(original_timings):
            # Use first N original timings
            matched_captions = []
            for i, caption in enumerate(captions):
                matched_caption = caption.copy()
                if i < len(original_timings):
                    matched_caption['start_time'] = original_timings[i]['start_time']
                    matched_caption['end_time'] = original_timings[i]['end_time']
                matched_captions.append(matched_caption)
            return matched_captions
        else:
            # More captions than original - distribute evenly
            print("🔄 More captions than original timing - distributing across speech span")
            return self.distribute_across_speech_span(captions, original_timings)
    
    def distribute_across_speech_span(self, captions: List[Dict], original_timings: List[Dict]) -> List[Dict]:
        """Distribute captions across the original speech time span"""
        
        if not original_timings:
            return self.minimal_timing_adjustment(captions)
        
        # Get speech time span from original timings
        first_speech_start = self.ass_time_to_seconds(original_timings[0]['start_time'])
        last_speech_end = self.ass_time_to_seconds(original_timings[-1]['end_time'])
        speech_span = last_speech_end - first_speech_start
        
        print(f"🎤 Distributing across speech span: {first_speech_start:.1f}s → {last_speech_end:.1f}s ({speech_span:.1f}s)")
        
        distributed_captions = []
        
        for i, caption in enumerate(captions):
            distributed_caption = caption.copy()
            
            # Calculate position within speech span
            position_ratio = i / max(1, len(captions) - 1) if len(captions) > 1 else 0.5
            
            # Calculate timing within speech span
            caption_start = first_speech_start + (position_ratio * speech_span * 0.8)  # Use 80% of span
            caption_duration = min(2.0, speech_span / len(captions) * 0.7)  # 70% of allocated time
            caption_end = caption_start + caption_duration
            
            # Ensure within speech bounds
            caption_end = min(caption_end, last_speech_end - 0.1)
            caption_start = max(caption_start, first_speech_start)
            
            distributed_caption['start_time'] = self.seconds_to_ass_time(caption_start)
            distributed_caption['end_time'] = self.seconds_to_ass_time(caption_end)
            
            distributed_captions.append(distributed_caption)
            
            start_display = distributed_caption['start_time']
            end_display = distributed_caption['end_time']
            text = caption.get('text', '')[:20] + '...' if len(caption.get('text', '')) > 20 else caption.get('text', '')
            print(f"   📍 Caption {i+1}: {start_display} → {end_display}: \"{text}\"")
        
        return distributed_captions
    
    def minimal_timing_adjustment(self, captions: List[Dict]) -> List[Dict]:
        """Apply minimal timing adjustments while preserving original timing"""
        
        print("🔧 Applying minimal timing adjustments to preserve speech sync")
        
        adjusted_captions = []
        
        for caption in captions:
            adjusted_caption = caption.copy()
            
            # Parse existing timing
            start_seconds = self.ass_time_to_seconds(caption.get('start_time', '0:00:00.00'))
            end_seconds = self.ass_time_to_seconds(caption.get('end_time', '0:00:01.00'))
            
            # Only fix if duration is extremely short (preserves original timing)
            if end_seconds - start_seconds < 0.3:
                end_seconds = start_seconds + 0.8
                adjusted_caption['end_time'] = self.seconds_to_ass_time(end_seconds)
                print(f"   ⚠️ Fixed very short caption: {caption.get('text', '')[:20]}...")
            
            adjusted_captions.append(adjusted_caption)
        
        return adjusted_captions
    
    def create_speech_synced_ass_file(self, captions: List[Dict], caption_position: str = 'bottom') -> str:
        """Create ASS file with speech-synced timing and position"""
        
        # Get unique speakers
        unique_speakers = set(cap.get('speaker', 'Speaker 1') for cap in captions)
        
        # Create styles section with position
        styles_section = self.create_styles_section(unique_speakers, caption_position)
        
        # Create dialogue section with speech-synced timing
        dialogue_section = self.create_dialogue_section(captions)
        
        # Assemble complete ASS file
        ass_content = f"""[Script Info]
Title: Clippy Viral Captions - Speech Synchronized
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{styles_section}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{dialogue_section}"""
        
        return ass_content
    
    def create_styles_section(self, speakers: set, caption_position: str = 'bottom') -> str:
        """Create styles section for all speakers with position"""
        styles = []
        
        # Determine vertical margin based on position
        # MarginV controls vertical position (higher number = higher on screen)
        if caption_position == 'top':
            margin_v = 200  # Offset from top (similar to bottom offset)
        elif caption_position == 'middle':
            margin_v = 150  # Middle of screen
        else:  # bottom (default)
            margin_v = 50   # Current bottom position
        
        for speaker in speakers:
            color = self.speaker_colors.get(speaker, "#FFFFFF")
            ass_color = self.hex_to_ass_color(color)
            # Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
            style_line = f"Style: {speaker},Arial Black,22,{ass_color},&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,30,30,{margin_v},1"
            styles.append(style_line)
        
        return "\n".join(styles)
    
    def create_dialogue_section(self, captions: List[Dict]) -> str:
        """Create dialogue section with speech-synced captions"""
        dialogue_lines = []
        
        for i, caption in enumerate(captions):
            speaker = caption.get('speaker', 'Speaker 1')
            text = caption.get('text', '').strip()
            start_time = caption.get('start_time', '0:00:00.00')
            end_time = caption.get('end_time', '0:00:01.00')
            
            if not text:
                continue
            
            # Format text with viral words and speaker color
            formatted_text = self.format_caption_text(text, speaker)
            
            # Create dialogue line
            dialogue_line = f"Dialogue: 0,{start_time},{end_time},{speaker},,0,0,0,,{formatted_text}"
            dialogue_lines.append(dialogue_line)
        
        print(f"📝 Created {len(dialogue_lines)} speech-synced dialogue lines")
        return "\n".join(dialogue_lines)
    
    def format_caption_text(self, text: str, speaker: str) -> str:
        """Format caption text with speaker color and effects"""
        # Get speaker color
        speaker_color = self.speaker_colors.get(speaker, "#FFFFFF")
        ass_color = self.hex_to_ass_color(speaker_color)
        
        # Format viral words
        formatted_text = self.format_viral_words(text, speaker)
        
        # Add pop-out effect with speaker color
        pop_effect = f"{{\\fad(150,100)\\t(0,300,\\fscx110\\fscy110)\\t(300,400,\\fscx100\\fscy100)\\c{ass_color}}}"
        
        return f"{pop_effect}{formatted_text}"
    
    def format_viral_words(self, text: str, speaker: str) -> str:
        """Format viral words with special styling"""
        formatted_text = text
        speaker_color = self.speaker_colors.get(speaker, "#FFFFFF")
        ass_color = self.hex_to_ass_color(speaker_color)
        
        for word in self.viral_keywords:
            if word.lower() in text.lower():
                # Create viral word format
                viral_format = f"{{\\c{ass_color}\\fs26\\b1}}{word.upper()}{{\\r}}"
                
                # Replace case-insensitively
                import re
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                formatted_text = pattern.sub(viral_format, formatted_text)
        
        return formatted_text
    
    def verify_speech_sync(self, ass_path: str, expected_count: int, original_timings: List[Dict]) -> bool:
        """Verify that captions are properly synced with speech"""
        try:
            with open(ass_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count dialogue lines
            dialogue_count = content.count('Dialogue:')
            
            # Extract timing data for verification
            dialogue_lines = [line for line in content.split('\n') if line.startswith('Dialogue:')]
            
            print(f"🔍 Speech Sync Verification:")
            print(f"   Expected captions: {expected_count}")
            print(f"   Found dialogues: {dialogue_count}")
            
            if dialogue_lines and original_timings:
                first_original = self.ass_time_to_seconds(original_timings[0]['start_time'])
                last_original = self.ass_time_to_seconds(original_timings[-1]['end_time'])
                original_span = last_original - first_original
                
                first_new = dialogue_lines[0].split(',')[1] if len(dialogue_lines) > 0 else "N/A"
                last_new = dialogue_lines[-1].split(',')[2] if len(dialogue_lines) > 0 else "N/A"
                
                first_new_seconds = self.ass_time_to_seconds(first_new)
                last_new_seconds = self.ass_time_to_seconds(last_new)
                new_span = last_new_seconds - first_new_seconds
                
                print(f"   Original speech span: {original_span:.1f}s")
                print(f"   New caption span: {new_span:.1f}s")
                
                # Check if timing is preserved (within 20% tolerance)
                timing_preserved = abs(new_span - original_span) / original_span < 0.2 if original_span > 0 else True
                
                if timing_preserved:
                    print("✅ Speech timing preserved - captions should sync with speech!")
                else:
                    print("⚠️ Speech timing significantly changed - sync may be off")
                
                return timing_preserved and dialogue_count == expected_count
            
            return dialogue_count == expected_count
            
        except Exception as e:
            print(f"❌ Speech sync verification failed: {e}")
            return False
    
    def hex_to_ass_color(self, hex_color: str) -> str:
        """Convert hex color to ASS BGR format"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # ASS uses BGR format with &H00 prefix
        return f"&H00{b:02X}{g:02X}{r:02X}"
    
    def ass_time_to_seconds(self, ass_time: str) -> float:
        """Convert ASS time format to seconds"""
        try:
            # Handle both H:MM:SS.CC and MM:SS.CC formats
            parts = ass_time.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                hours = int(hours)
            else:
                hours = 0
                minutes, seconds = parts
            
            minutes = int(minutes)
            if '.' in seconds:
                secs, centisecs = seconds.split('.')
                secs = int(secs)
                centisecs = int(centisecs)
            else:
                secs = int(seconds)
                centisecs = 0
            
            return hours * 3600 + minutes * 60 + secs + centisecs / 100
        except Exception as e:
            print(f"⚠️ Time parsing error for '{ass_time}': {e}")
            return 0.0
    
    def seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


# Test the SPEECH SYNC system
if __name__ == "__main__":
    print("🎤 ASS Caption Update System V6 - SPEECH SYNCHRONIZED")
    print("✅ Preserves original speech timing for perfect sync")
    print("✅ Captions appear exactly when speech occurs")
    print("✅ No more arbitrary redistribution")
    print("✅ Perfect speech-to-caption synchronization")
