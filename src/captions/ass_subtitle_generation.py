#!/usr/bin/env python3
"""
🎬 Phase 3: ASS Subtitle Generation & Video Integration 🎬
Creates ASS subtitle files with viral styling and burns them into video
"""

import os
import ffmpeg
import json
from datetime import datetime
from typing import List, Dict, Optional
from viral_word_detection import ViralCaptionProcessor, ViralCaptionSegment

class ASSSubtitleGenerator:
    """Generates ASS subtitle files with viral styling"""
    
    def __init__(self):
        # ASS styling parameters
        self.font_name = "Arial Black"
        self.font_size = 24  # Reduced from 48 to 24 (half size)
        self.outline_width = 2  # Reduced proportionally 
        self.shadow_depth = 1   # Reduced proportionally
        self.margin_bottom = 40  # Distance from bottom of screen
        
        # Animation settings
        self.fade_in_duration = 200   # ms
        self.fade_out_duration = 200  # ms
        self.pop_scale = 120          # % scale for pop-in effect
        self.pop_duration = 300       # ms
    
    def generate_ass_header(self, spatial_speakers=None) -> str:
        """Generate ASS file header with viral styles (optionally with spatial speaker colors)"""
        
        # Base header
        header = f"""[Script Info]
Title: Viral Clip Captions
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding

"""
        
        # Add styles for spatial speakers if provided
        if spatial_speakers:
            for speaker in spatial_speakers:
                style_name = "Matt" if speaker.position_id == 0 else "Shane" if speaker.position_id == 1 else f"Speaker{speaker.position_id + 1}"
                ass_color = self.hex_to_ass_color(speaker.color)
                
                header += f"Style: {style_name},{self.font_name},{self.font_size},{ass_color},&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{self.outline_width},{self.shadow_depth},2,30,30,{self.margin_bottom},1\n"
        else:
            # Default styles
            header += f"Style: Matt,{self.font_name},{self.font_size},&H00FFBF00,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{self.outline_width},{self.shadow_depth},2,30,30,{self.margin_bottom},1\n"
            header += f"Style: Shane,{self.font_name},{self.font_size},&H000045FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{self.outline_width},{self.shadow_depth},2,30,30,{self.margin_bottom},1\n"
            header += f"Style: Speaker3,{self.font_name},{self.font_size},&H0032CD32,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{self.outline_width},{self.shadow_depth},2,30,30,{self.margin_bottom},1\n"
            header += f"Style: Speaker4,{self.font_name},{self.font_size},&H00B469FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{self.outline_width},{self.shadow_depth},2,30,30,{self.margin_bottom},1\n"
        
        # Default style
        header += f"Style: Default,{self.font_name},{self.font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{self.outline_width},{self.shadow_depth},2,30,30,{self.margin_bottom},1\n"
        
        header += "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        return header
    
    def hex_to_ass_color(self, hex_color: str) -> str:
        """Convert hex color to ASS BGR format"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert RGB to BGR for ASS format
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16) 
        b = int(hex_color[4:6], 16)
        
        # ASS uses BGR format
        ass_color = f"&H00{b:02X}{g:02X}{r:02X}"
        return ass_color
    
    def seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.CC)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def get_speaker_style(self, speaker_name: str) -> str:
        """Get ASS style name for speaker with spatial consistency"""
        # Check if we have spatial colors mapping
        if hasattr(self, 'spatial_colors') and self.spatial_colors:
            if speaker_name in self.spatial_colors:
                return self.spatial_colors[speaker_name]['style_name']
        
        # Fallback to original mapping
        style_mapping = {
            "Matt": "Matt",
            "Shane": "Shane", 
            "Left Speaker": "Matt",      # Spatial mapping
            "Right Speaker": "Shane",    # Spatial mapping
            "Speaker 1": "Matt",         # Fallback
            "Speaker 2": "Shane",        # Fallback
            "Speaker 3": "Speaker3",
            "Speaker 4": "Speaker4"
        }
        
        return style_mapping.get(speaker_name, "Default")
    
    def format_viral_text(self, segment: ViralCaptionSegment) -> str:
        """Format text with viral word highlighting"""
        text = segment.text
        
        # If no viral words, return as-is
        if not segment.has_viral_words:
            return text
        
        # Replace viral word markers with ASS styling
        # [VIRAL]word[/VIRAL] → {\c&H0000D7FF&\fs52\b1}WORD{\r}
        viral_color = "&H0000D7FF"  # Gold in ASS BGR format
        
        import re
        
        # Pattern to match [VIRAL]text[/VIRAL] markers
        pattern = r'\[VIRAL\](.*?)\[/VIRAL\]'
        
        def replace_viral(match):
            word = match.group(1)
            # ASS styling: change color to gold, increase font size, make bold
            return f"{{\\c{viral_color}&\\fs{self.font_size + 2}\\b1}}{word.upper()}{{\\r}}"
        
        formatted_text = re.sub(pattern, replace_viral, segment.styled_text)
        return formatted_text
    
    def create_subtitle_line(self, segment: ViralCaptionSegment) -> str:
        """Create a single ASS subtitle line"""
        start_time = self.seconds_to_ass_time(segment.start_time)
        end_time = self.seconds_to_ass_time(segment.end_time)
        style = self.get_speaker_style(segment.speaker_name)
        
        # Format text with viral highlighting
        formatted_text = self.format_viral_text(segment)
        
        # Add pop-in animation effect
        animation = f"{{\\fad({self.fade_in_duration},{self.fade_out_duration})\\t(0,{self.pop_duration},\\fscx{self.pop_scale}\\fscy{self.pop_scale})\\t({self.pop_duration},{self.pop_duration + 100},\\fscx100\\fscy100)}}"
        
        final_text = animation + formatted_text
        
        return f"Dialogue: 0,{start_time},{end_time},{style},,0,0,0,,{final_text}"
    
    def generate_ass_file(self, segments: List[ViralCaptionSegment], output_path: str, spatial_speakers=None) -> bool:
        """Generate complete ASS subtitle file with optional spatial speaker colors"""
        try:
            print(f"📝 Generating ASS subtitle file...")
            
            # Create ASS content with spatial speaker colors if provided
            ass_content = self.generate_ass_header(spatial_speakers)
            
            # Add each subtitle line
            for segment in segments:
                subtitle_line = self.create_subtitle_line(segment)
                ass_content += subtitle_line + "\n"
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            file_size = os.path.getsize(output_path) / 1024  # KB
            print(f"✅ ASS subtitle file created: {output_path} ({file_size:.1f} KB)")
            print(f"   📊 {len(segments)} subtitle lines generated")
            
            if spatial_speakers:
                print(f"   🎯 Using {len(spatial_speakers)} spatial speaker colors")
                for speaker in spatial_speakers:
                    print(f"      {speaker.name}: {speaker.color}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating ASS file: {e}")
            return False

class ViralVideoProcessor:
    """Processes videos by burning in viral captions"""
    
    def __init__(self):
        self.caption_processor = ViralCaptionProcessor()
        self.subtitle_generator = ASSSubtitleGenerator()
    
    def create_viral_clip_with_captions(self, video_path: str, start_time: float, duration: float, output_path: str, num_speakers: int = 2) -> bool:
        """
        Complete pipeline: Extract segment → Transcribe → Generate captions → Burn into video
        """
        print("🔥 CREATING VIRAL CLIP WITH CAPTIONS!")
        print(f"📹 Input: {os.path.basename(video_path)}")
        print(f"⏰ Segment: {start_time}s-{start_time + duration}s ({duration}s)")
        print(f"🎯 Output: {output_path}")
        print("=" * 70)
        
        try:
            # Step 1: Process segment for viral captions
            print("🎤 Step 1: Processing audio for viral captions...")
            viral_segments = self.caption_processor.process_video_segment(
                video_path, start_time, duration, num_speakers
            )
            
            if not viral_segments:
                print("❌ No caption segments generated")
                return False
            
            # Step 2: Generate ASS subtitle file
            print("📝 Step 2: Generating ASS subtitle file...")
            subtitle_path = output_path.replace('.mp4', '_captions.ass')
            
            success = self.subtitle_generator.generate_ass_file(viral_segments, subtitle_path)
            if not success:
                print("❌ Failed to generate subtitle file")
                return False
            
            # Step 3: Create base video clip
            print("🎬 Step 3: Creating base video clip...")
            temp_video_path = output_path.replace('.mp4', '_temp.mp4')
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            (
                ffmpeg
                .input(video_path, ss=start_time, t=duration)
                .output(
                    temp_video_path,
                    vcodec='libx264',
                    acodec='aac',
                    vf='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
                    **{'b:v': '3M', 'b:a': '128k', 'preset': 'medium', 'crf': '23'}
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            if not os.path.exists(temp_video_path):
                print("❌ Failed to create base video clip")
                return False
            
            # Step 4: Burn in captions
            print("🔥 Step 4: Burning in viral captions...")
            
            (
                ffmpeg
                .input(temp_video_path)
                .output(
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    vf=f"ass={subtitle_path}",
                    **{'b:v': '3M', 'b:a': '128k', 'preset': 'medium', 'crf': '23'}
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Step 5: Clean up temp files
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            # Keep subtitle file for debugging if needed
            
            # Step 6: Verify output
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024*1024)
                
                # Count viral segments
                viral_count = sum(1 for seg in viral_segments if seg.has_viral_words)
                total_viral_words = sum(len(seg.viral_words) for seg in viral_segments)
                
                print("🎉 VIRAL CLIP WITH CAPTIONS CREATED!")
                print(f"✅ Output: {output_path} ({file_size:.1f} MB)")
                print(f"📊 Statistics:")
                print(f"   Duration: {duration}s")
                print(f"   Caption segments: {len(viral_segments)}")
                print(f"   Viral segments: {viral_count}")
                print(f"   Viral words: {total_viral_words}")
                print(f"   Speakers: {len(set(seg.speaker_name for seg in viral_segments))}")
                
                return True
            else:
                print("❌ Output file not created")
                return False
                
        except Exception as e:
            print(f"❌ Error creating viral clip with captions: {e}")
            return False
    
    def create_clip_data(self, output_path: str, video_id: str, start_time: float, duration: float, viral_segments: List[ViralCaptionSegment]) -> Dict:
        """Create clip data structure for compatibility with existing system"""
        viral_count = sum(1 for seg in viral_segments if seg.has_viral_words)
        total_viral_words = sum(len(seg.viral_words) for seg in viral_segments)
        
        return {
            'path': output_path,
            'video_id': video_id,
            'start_time': start_time,
            'duration': duration,
            'speakers_detected': len(set(seg.speaker_name for seg in viral_segments)),
            'speaker_names': list(set(seg.speaker_name for seg in viral_segments)),
            'speaker_colors': list(set(seg.speaker_color for seg in viral_segments)),
            'captions_added': True,
            'caption_count': len(viral_segments),
            'viral_segments': viral_count,
            'viral_words_count': total_viral_words,
            'file_size_mb': os.path.getsize(output_path) / (1024*1024) if os.path.exists(output_path) else 0,
            'created_at': datetime.now().isoformat()
        }


def main():
    """Test Phase 3: ASS Subtitle Generation & Video Integration"""
    print("🎬 PHASE 3: ASS SUBTITLE GENERATION & VIDEO INTEGRATION")
    print("Creating viral clips with burned-in captions...")
    print("=" * 80)
    
    # Find test video
    video_path = None
    downloads_dir = "downloads"
    
    if os.path.exists(downloads_dir):
        for file in os.listdir(downloads_dir):
            if file.endswith(('.mp4', '.mkv')):
                video_path = os.path.join(downloads_dir, file)
                break
    
    if not video_path:
        print("❌ No test video found")
        return
    
    # Initialize video processor
    processor = ViralVideoProcessor()
    
    # Create viral clip with captions
    output_path = "clips/viral_clip_with_captions_test.mp4"
    
    success = processor.create_viral_clip_with_captions(
        video_path=video_path,
        start_time=300,      # 5 minutes in
        duration=15,         # 15 seconds
        output_path=output_path,
        num_speakers=2
    )
    
    if success:
        print("🎉 PHASE 3 SUCCESS!")
        print("✅ Viral word detection working")
        print("✅ ASS subtitle generation working")
        print("✅ Caption burning working") 
        print("✅ Video processing working")
        
        print(f"\\n🎬 Test your viral clip: {output_path}")
        print("🔄 Ready for Phase 4: Integration with main clipper!")
        
    else:
        print("❌ Phase 3 failed - check error messages above")

if __name__ == "__main__":
    main()
