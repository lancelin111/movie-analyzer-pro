#!/usr/bin/env python3
"""
MKV视频转换和处理工具
支持MKV格式的完整处理流程
"""

import subprocess
from pathlib import Path
from typing import Optional

class MKVProcessor:
    def __init__(self, input_path: str):
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"文件不存在: {input_path}")
        
    def convert_to_mp4(self, output_path: Optional[str] = None) -> Path:
        """转换MKV到MP4"""
        if output_path is None:
            output_path = self.input_path.with_suffix('.mp4')
        else:
            output_path = Path(output_path)
        
        print(f"🔄 转换 MKV 到 MP4...")
        cmd = [
            'ffmpeg', '-y', '-i', str(self.input_path),
            '-c:v', 'copy',  # 复制视频流（快速）
            '-c:a', 'copy',  # 复制音频流
            '-c:s', 'mov_text',  # 转换字幕格式
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ 转换完成: {output_path}")
            return output_path
        except subprocess.CalledProcessError:
            # 如果直接复制失败，尝试重新编码
            print("⚠️ 直接复制失败，尝试重新编码...")
            cmd = [
                'ffmpeg', '-y', '-i', str(self.input_path),
                '-c:v', 'libx264',  # H.264编码
                '-preset', 'fast',
                '-c:a', 'aac',  # AAC音频
                str(output_path)
            ]
            subprocess.run(cmd, check=True)
            print(f"✅ 转换完成: {output_path}")
            return output_path
    
    def extract_subtitles(self, output_dir: Optional[str] = None) -> list:
        """提取MKV中的所有字幕"""
        if output_dir is None:
            output_dir = self.input_path.parent
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(exist_ok=True)
        
        print(f"📝 提取字幕...")
        
        # 获取字幕流信息
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 's',
            '-show_entries', 'stream=index,codec_name:stream_tags=language',
            '-of', 'json',
            str(self.input_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        import json
        info = json.loads(result.stdout)
        
        extracted_files = []
        
        for stream in info.get('streams', []):
            index = stream['index']
            codec = stream.get('codec_name', 'unknown')
            lang = stream.get('tags', {}).get('language', 'unknown')
            
            # 确定输出格式
            if codec in ['subrip', 'srt']:
                ext = 'srt'
            elif codec in ['ass', 'ssa']:
                ext = 'ass'
            elif codec in ['webvtt', 'vtt']:
                ext = 'vtt'
            else:
                ext = 'srt'  # 默认尝试SRT
            
            output_file = output_dir / f"{self.input_path.stem}_track{index}_{lang}.{ext}"
            
            # 提取字幕
            cmd = [
                'ffmpeg', '-y', '-i', str(self.input_path),
                '-map', f'0:s:{info["streams"].index(stream)}',
                str(output_file)
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"  ✅ 提取字幕 {index} ({lang}): {output_file.name}")
                extracted_files.append(output_file)
            except:
                print(f"  ❌ 无法提取字幕 {index}")
        
        if not extracted_files:
            print("  ❌ 没有找到可提取的字幕")
        
        return extracted_files
    
    def process_for_analysis(self) -> dict:
        """处理MKV文件以便进行分析"""
        result = {
            'original': str(self.input_path),
            'converted': None,
            'subtitles': []
        }
        
        # 转换为MP4
        mp4_path = self.convert_to_mp4()
        result['converted'] = str(mp4_path)
        
        # 提取字幕
        subtitles = self.extract_subtitles()
        result['subtitles'] = [str(s) for s in subtitles]
        
        return result

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python mkv_processor.py <MKV文件路径>")
        return
    
    mkv_file = sys.argv[1]
    
    try:
        processor = MKVProcessor(mkv_file)
        result = processor.process_for_analysis()
        
        print("\n" + "="*50)
        print("✅ MKV 处理完成！")
        print(f"📁 原始文件: {result['original']}")
        print(f"📁 转换文件: {result['converted']}")
        if result['subtitles']:
            print(f"📝 提取字幕: {len(result['subtitles'])} 个")
            for sub in result['subtitles']:
                print(f"   - {Path(sub).name}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")

if __name__ == "__main__":
    main()
