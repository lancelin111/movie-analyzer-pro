"""
视频处理模块
处理视频的基本操作：剪辑、合并、转换等
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import timedelta

class VideoProcessor:
    """视频处理器类"""
    
    def __init__(self, video_path: str):
        """初始化视频处理器"""
        self.video_path = Path(video_path)
        self.video_info = None
        
    def get_video_info(self) -> Dict:
        """获取视频基本信息"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(self.video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        # 提取视频流信息
        video_stream = None
        audio_stream = None
        
        for stream in data.get('streams', []):
            if stream['codec_type'] == 'video' and not video_stream:
                video_stream = stream
            elif stream['codec_type'] == 'audio' and not audio_stream:
                audio_stream = stream
        
        # 构建信息字典
        duration = float(data['format'].get('duration', 0))
        self.video_info = {
            'filename': self.video_path.name,
            'path': str(self.video_path),
            'duration': duration,
            'duration_str': str(timedelta(seconds=int(duration))),
            'size': int(data['format'].get('size', 0)),
            'size_mb': int(data['format'].get('size', 0)) / (1024 * 1024),
            'format': data['format'].get('format_name', 'unknown'),
            'width': video_stream.get('width', 0) if video_stream else 0,
            'height': video_stream.get('height', 0) if video_stream else 0,
            'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
            'video_codec': video_stream.get('codec_name', 'unknown') if video_stream else 'none',
            'audio_codec': audio_stream.get('codec_name', 'unknown') if audio_stream else 'none',
            'audio_channels': audio_stream.get('channels', 0) if audio_stream else 0,
        }
        
        return self.video_info
    
    def extract_segment(self, start: float, end: float, output_path: str) -> bool:
        """提取视频片段"""
        duration = end - start
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-i', str(self.video_path),
            '-t', str(duration),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    def extract_clips(self, timestamps: List[Tuple[float, float]], 
                     output_dir: str = "clips") -> List[str]:
        """批量提取视频片段"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        clip_paths = []
        for i, (start, end) in enumerate(timestamps):
            output_path = output_dir / f"clip_{i:03d}.mp4"
            if self.extract_segment(start, end, str(output_path)):
                clip_paths.append(str(output_path))
                print(f"  ✓ 片段 {i+1}/{len(timestamps)} 已提取")
            else:
                print(f"  ✗ 片段 {i+1}/{len(timestamps)} 提取失败")
        
        return clip_paths
    
    def merge_clips(self, clip_paths: List[str], output_path: str,
                   transition: str = "fade") -> bool:
        """合并视频片段"""
        # 创建文件列表
        list_file = Path("temp_list.txt")
        with open(list_file, 'w') as f:
            for clip in clip_paths:
                f.write(f"file '{clip}'\n")
        
        # 合并视频
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        # 清理临时文件
        list_file.unlink()
        
        return result.returncode == 0
    
    def create_highlight_video(self, clips: List[Dict], 
                              output_path: str) -> bool:
        """创建精彩片段视频"""
        # 提取片段
        timestamps = [(clip['start'], clip['end']) for clip in clips]
        clip_paths = self.extract_clips(timestamps)
        
        if not clip_paths:
            return False
        
        # 合并片段
        success = self.merge_clips(clip_paths, output_path)
        
        # 清理临时文件
        for path in clip_paths:
            Path(path).unlink()
        
        return success
    
    def create_highlight_video_with_narration(self, clips: List[Dict],
                                             narration: str,
                                             output_path: str) -> bool:
        """创建带解说的精彩片段视频"""
        # 首先创建视频
        temp_video = "temp_highlights.mp4"
        if not self.create_highlight_video(clips, temp_video):
            return False
        
        # 生成解说音频
        narration_audio = "temp_narration.mp3"
        self._generate_narration_audio(narration, narration_audio)
        
        # 混合音频
        cmd = [
            'ffmpeg', '-y',
            '-i', temp_video,
            '-i', narration_audio,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        # 清理临时文件
        Path(temp_video).unlink()
        Path(narration_audio).unlink()
        
        return result.returncode == 0
    
    def _generate_narration_audio(self, text: str, output_path: str):
        """生成解说音频（使用edge-tts）"""
        try:
            import edge_tts
            import asyncio
            
            async def generate():
                voice = "zh-CN-XiaoxiaoNeural"
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_path)
            
            asyncio.run(generate())
        except ImportError:
            print("  ⚠️ edge-tts未安装，跳过解说音频生成")
            # 生成空音频文件
            subprocess.run([
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', 'anullsrc=r=44100:cl=stereo',
                '-t', '10',
                output_path
            ], capture_output=True)
    
    def convert_format(self, output_path: str, format: str = "mp4") -> bool:
        """转换视频格式"""
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.video_path),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    def extract_audio(self, output_path: str) -> bool:
        """提取音频"""
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.video_path),
            '-vn',
            '-acodec', 'mp3',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    def add_watermark(self, watermark_text: str, output_path: str) -> bool:
        """添加水印"""
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.video_path),
            '-vf', f"drawtext=text='{watermark_text}':fontcolor=white:fontsize=24:x=10:y=10",
            '-codec:a', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0