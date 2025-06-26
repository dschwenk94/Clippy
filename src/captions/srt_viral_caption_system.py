#!/usr/bin/env python3
"""
🎯 SRT CAPTION SYSTEM - ULTIMATE FIX
Switch from ASS to SRT format for reliable caption display
"""

import os
import re
from typing import List, Dict

class SRTViralCaptionSystem:
    """SRT-based caption system that actually works reliably"""
    
    def __init__(self):
        # Viral words that get emphasis
        self.viral_words = [
            'oh my god', 'fucking', 'shit', 'damn', 'crazy', 'insane', 'ridiculous',
            'what the hell', 'holy shit', 'no way', 'seriously', 'amazing', 'incredible'
        ]
    
    def calculate_rapid_fire_timing(self, captions: List[Dict], total_duration: float = 30.0) -> List[Dict]:
        """Calculate timing for rapid-fire conversations"""
        if not captions:
            return []
        
        # For rapid-fire: 2-second captions with 0.3-second gaps
        caption_duration = 2.0
        gap_duration = 0.3
        
        # Adjust if we have too many captions for the duration
        total_time_needed = len(captions) * (caption_duration + gap_duration)
        if total_time_needed > total_duration:
            available_time = total_duration - (len(captions) * gap_duration)
            caption_duration = available_time / len(captions)
            caption_duration = max(1.0, caption_duration)  # Minimum 1.0 seconds
        
        # Assign sequential timing
        timed_captions = []
        current_time = 0.0
        
        for i, caption in enumerate(captions):
            start_time = current_time
            end_time = start_time + caption_duration
            
            timed_caption = {
                'index': i + 1,  # SRT uses 1-based indexing
                'text': caption.get('text', '').strip(),
                'speaker': caption.get('speaker', 'Speaker 1'),
                'start_time': start_time,
                'end_time': end_time
            }
            
            timed_captions.append(timed_caption)
            current_time = end_time + gap_duration
        
        return timed_captions
    
    def format_viral_text_srt(self, text: str) -> str:
        """Apply viral word formatting for SRT (uppercase only)"""
        formatted_text = text
        
        # Simple uppercase for viral words
        for viral_word in self.viral_words:
            if viral_word.lower() in text.lower():
                pattern = re.compile(re.escape(viral_word), re.IGNORECASE)
                formatted_text = pattern.sub(lambda m: m.group().upper(), formatted_text)
        
        return formatted_text
    
    def seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def generate_srt_file(self, captions: List[Dict], output_path: str, duration: float = 30.0) -> bool:
        """Generate SRT subtitle file"""
        try:
            print(f"🎯 Generating SRT file with {len(captions)} captions")
            
            # Calculate timing
            timed_captions = self.calculate_rapid_fire_timing(captions, duration)
            
            if not timed_captions:
                print("❌ No timed captions to generate")
                return False
            
            # Build SRT content
            srt_content = ""
            
            for caption in timed_captions:
                start_time = self.seconds_to_srt_time(caption['start_time'])
                end_time = self.seconds_to_srt_time(caption['end_time'])
                text = self.format_viral_text_srt(caption['text'])
                
                # Add speaker identification
                speaker_prefix = f"[{caption['speaker']}] " if len(set(cap['speaker'] for cap in timed_captions)) > 1 else ""
                
                # SRT format: index, timing, text, blank line
                srt_content += f"{caption['index']}\\n"
                srt_content += f"{start_time} --> {end_time}\\n"
                srt_content += f"{speaker_prefix}{text}\\n"
                srt_content += "\\n"
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            print(f"✅ Generated SRT file: {os.path.basename(output_path)}")
            print(f"⏱️  Total duration: {timed_captions[-1]['end_time']:.1f}s")
            print(f"🎯 Sequential SRT timing!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating SRT file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_captions_from_srt(self, srt_file_path: str) -> List[Dict]:
        """Extract captions from SRT file for editing"""
        captions = []
        
        if not os.path.exists(srt_file_path):
            print(f"❌ SRT file not found: {srt_file_path}")
            return captions
        
        try:
            with open(srt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT format
            subtitle_blocks = content.strip().split('\\n\\n')
            
            for i, block in enumerate(subtitle_blocks):
                lines = block.strip().split('\\n')
                if len(lines) >= 3:
                    try:
                        index = int(lines[0])
                        timing = lines[1]
                        text = '\\n'.join(lines[2:])
                        
                        # Extract speaker if present
                        speaker = 'Speaker 1'
                        if text.startswith('[') and '] ' in text:
                            speaker_end = text.find('] ')
                            speaker = text[1:speaker_end]
                            text = text[speaker_end + 2:]
                        
                        captions.append({
                            'index': i,
                            'text': text.strip(),
                            'speaker': speaker
                        })
                    except:
                        continue
            
            print(f"📝 Extracted {len(captions)} captions from SRT file")
            return captions
            
        except Exception as e:
            print(f"❌ Error extracting SRT captions: {e}")
            return []
    
    def update_captions_from_web_input_srt(self, original_srt_path: str, updated_captions: List[Dict], duration: float = 30.0) -> bool:
        """Update SRT file from web app caption edits"""
        try:
            print(f"🔄 Updating captions with SRT system...")
            print(f"📝 Processing {len(updated_captions)} caption updates")
            
            # Backup original
            backup_path = original_srt_path + '.srt_backup'
            if os.path.exists(original_srt_path):
                with open(original_srt_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"📋 SRT backup created: {os.path.basename(backup_path)}")
            
            # Generate new SRT file
            success = self.generate_srt_file(updated_captions, original_srt_path, duration)
            
            if success:
                print("✅ SRT caption update successful!")
                return True
            else:
                print("❌ SRT caption update failed")
                return False
                
        except Exception as e:
            print(f"❌ Error updating SRT captions: {e}")
            return False


def test_srt_system():
    """Test the SRT caption system"""
    print("🎯 TESTING SRT VIRAL CAPTION SYSTEM")
    print("=" * 50)
    
    # Create test captions
    test_captions = [
        {'text': 'OH MY GOD this is working!', 'speaker': 'Speaker 1'},
        {'text': 'FUCKING incredible!', 'speaker': 'Speaker 2'}, 
        {'text': 'I know right?', 'speaker': 'Speaker 1'},
        {'text': 'This is INSANE', 'speaker': 'Speaker 2'},
        {'text': 'What the hell was wrong before?', 'speaker': 'Speaker 1'}
    ]
    
    # Test the SRT system
    caption_system = SRTViralCaptionSystem()
    
    # Test SRT generation
    test_output = "/Users/davisschwenke/Youtube Clips/clips/test_srt_captions.srt"
    success = caption_system.generate_srt_file(test_captions, test_output, 30.0)
    
    if success:
        print(f"\\n✅ SRT test successful! Generated: {test_output}")
        
        # Show what the SRT file looks like
        print("\\n📄 SRT file preview:")
        with open(test_output, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:300] + "..." if len(content) > 300 else content)
        
        print("\\n🎯 SRT caption system ready!")
        print("📝 This should display as clean captions, not raw code!")
        return True
    else:
        print("\\n❌ SRT test failed")
        return False

def main():
    """Test the SRT caption system"""
    print("🎯 SRT VIRAL CAPTION SYSTEM - ULTIMATE FIX")
    print("=" * 60)
    
    test_srt_system()
    
    print("\\n🔧 SRT ADVANTAGES:")
    print("✅ More reliable than ASS format")
    print("✅ Simpler format, less likely to break")
    print("✅ Better FFmpeg compatibility")
    print("✅ Clean text display")
    print("✅ No complex formatting codes")
    
    print("\\n📝 Next: Integrate SRT system into the clipper!")

if __name__ == "__main__":
    main()
