#!/usr/bin/env python3
"""
Movie Analyzer Pro - 专业电影分析与剪辑系统
主程序入口 - 支持中文/韩语等多语言视频分析
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, List
import json

# 导入各个功能模块
from modules.video_processor import VideoProcessor
from modules.scene_analyzer import SceneAnalyzer
from modules.subtitle_extractor import SubtitleExtractor
from modules.screenplay_generator import ScreenplayGenerator
from modules.highlight_detector import HighlightDetector
from modules.narration_generator import NarrationGenerator
from modules.content_detector import ContentDetector

class MovieAnalyzerPro:
    """电影分析专业版主类"""
    
    def __init__(self, video_path: str, output_dir: str = "output"):
        """初始化分析器"""
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查视频文件
        if not self.video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 初始化各个模块
        self.video_processor = VideoProcessor(video_path)
        self.scene_analyzer = SceneAnalyzer(video_path)
        self.subtitle_extractor = SubtitleExtractor(video_path)
        self.screenplay_generator = ScreenplayGenerator()
        self.highlight_detector = HighlightDetector(video_path)
        self.narration_generator = NarrationGenerator()
        
        # 分析结果存储
        self.analysis_results = {}
    
    def analyze_video(self, language: str = "zh", duration_limit: int = 600,
                      skip_intro_outro: bool = True):
        """
        分析视频
        
        Args:
            language: 语言代码 (zh=中文, ko=韩语, en=英语, auto=自动检测)
            duration_limit: 分析时长限制（秒）
        """
        print("="*60)
        print("🎬 Movie Analyzer Pro - 专业电影分析系统")
        print("="*60)
        
        # 1. 视频基本信息
        print("\n📊 [1/6] 获取视频信息...")
        video_info = self.video_processor.get_video_info()
        self.analysis_results['video_info'] = video_info
        
        print(f"  • 文件: {self.video_path.name}")
        print(f"  • 时长: {video_info['duration_str']}")
        print(f"  • 分辨率: {video_info['width']}x{video_info['height']}")
        print(f"  • 帧率: {video_info['fps']:.2f} fps")
        
        # 2. 场景检测
        print("\n🎭 [2/6] 检测场景...")
        scenes = self.scene_analyzer.detect_scenes(
            max_duration=duration_limit,
            threshold=30.0
        )
        self.analysis_results['scenes'] = scenes
        print(f"  • 检测到 {len(scenes)} 个场景")
        
        # 3. 字幕提取
        print(f"\n📝 [3/6] 提取字幕 (语言: {language})...")
        subtitles = self.subtitle_extractor.extract_subtitles(
            language=language,
            duration_limit=duration_limit
        )
        self.analysis_results['subtitles'] = subtitles
        print(f"  • 提取了 {len(subtitles)} 条字幕")
        
        # 4. 剧本生成
        print("\n📜 [4/6] 生成剧本...")
        screenplay = self.screenplay_generator.generate(
            scenes=scenes,
            subtitles=subtitles,
            video_info=video_info
        )
        self.analysis_results['screenplay'] = screenplay
        print("  • 剧本生成完成")
        
        # 5. 精彩片段检测
        print("\n✨ [5/6] 检测精彩片段...")
        highlights = self.highlight_detector.detect_highlights(
            scenes=scenes,
            max_highlights=10
        )
        self.analysis_results['highlights'] = highlights
        print(f"  • 找到 {len(highlights)} 个精彩片段")
        
        # 6. 生成解说词
        print("\n🎤 [6/6] 生成解说词...")
        narration = self.narration_generator.generate(
            scenes=scenes,
            subtitles=subtitles,
            highlights=highlights
        )
        self.analysis_results['narration'] = narration
        print("  • 解说词生成完成")
        
        # 保存结果
        self._save_results()
        
        return self.analysis_results
    
    def create_highlight_video(self, duration: int = 300, with_narration: bool = True):
        """
        创建精彩片段视频
        
        Args:
            duration: 目标时长（秒）
            with_narration: 是否添加解说
        """
        print("\n🎬 创建精彩片段视频...")
        
        if 'highlights' not in self.analysis_results:
            print("❌ 请先运行 analyze_video() 分析视频")
            return None
        
        highlights = self.analysis_results['highlights']
        
        # 选择片段以满足目标时长
        selected_clips = []
        total_duration = 0
        
        for highlight in highlights:
            clip_duration = highlight['end'] - highlight['start']
            if total_duration + clip_duration <= duration:
                selected_clips.append(highlight)
                total_duration += clip_duration
            if total_duration >= duration * 0.9:  # 达到90%目标时长即可
                break
        
        print(f"  • 选择了 {len(selected_clips)} 个片段")
        print(f"  • 总时长: {total_duration:.1f} 秒")
        
        # 生成视频
        output_path = self.output_dir / f"highlights_{duration}s.mp4"
        
        if with_narration and 'narration' in self.analysis_results:
            # 带解说的视频
            self.video_processor.create_highlight_video_with_narration(
                clips=selected_clips,
                narration=self.analysis_results['narration'],
                output_path=str(output_path)
            )
        else:
            # 纯剪辑视频
            self.video_processor.create_highlight_video(
                clips=selected_clips,
                output_path=str(output_path)
            )
        
        print(f"✅ 视频已生成: {output_path}")
        return output_path
    
    def export_subtitles(self, format: str = "srt", bilingual: bool = False):
        """
        导出字幕文件
        
        Args:
            format: 字幕格式 (srt, ass, vtt)
            bilingual: 是否生成双语字幕
        """
        if 'subtitles' not in self.analysis_results:
            print("❌ 没有可用的字幕数据")
            return None
        
        subtitles = self.analysis_results['subtitles']
        
        # 生成字幕文件
        subtitle_path = self.output_dir / f"subtitles.{format}"
        
        if bilingual and any('translation' in sub for sub in subtitles):
            # 双语字幕
            self.subtitle_extractor.export_bilingual_subtitles(
                subtitles=subtitles,
                output_path=str(subtitle_path),
                format=format
            )
        else:
            # 单语字幕
            self.subtitle_extractor.export_subtitles(
                subtitles=subtitles,
                output_path=str(subtitle_path),
                format=format
            )
        
        print(f"✅ 字幕已导出: {subtitle_path}")
        return subtitle_path
    
    def _save_results(self):
        """保存分析结果"""
        # 保存JSON数据
        json_path = self.output_dir / "analysis_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        # 保存剧本
        if 'screenplay' in self.analysis_results:
            screenplay_path = self.output_dir / "screenplay.txt"
            with open(screenplay_path, 'w', encoding='utf-8') as f:
                f.write(self.analysis_results['screenplay'])
        
        # 保存解说词
        if 'narration' in self.analysis_results:
            narration_path = self.output_dir / "narration.txt"
            with open(narration_path, 'w', encoding='utf-8') as f:
                f.write(self.analysis_results['narration'])
        
        # 生成HTML报告
        self._generate_html_report()
        
        print(f"\n📁 结果已保存至: {self.output_dir}")
    
    def _generate_html_report(self):
        """生成HTML分析报告"""
        html_path = self.output_dir / "report.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>电影分析报告 - {self.video_path.name}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            background: rgba(0, 0, 0, 0.7);
            border-radius: 10px;
            padding: 30px;
            margin: 20px 0;
        }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 30px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
        }}
        .scene-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .scene-item {{
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .highlight {{
            background: rgba(255, 215, 0, 0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 电影分析报告</h1>
        
        <h2>📊 视频信息</h2>
        <div class="info-grid">
            <div class="info-card">
                <strong>文件名:</strong> {self.video_path.name}
            </div>
            <div class="info-card">
                <strong>时长:</strong> {self.analysis_results.get('video_info', {}).get('duration_str', 'N/A')}
            </div>
            <div class="info-card">
                <strong>分辨率:</strong> {self.analysis_results.get('video_info', {}).get('width', 0)}x{self.analysis_results.get('video_info', {}).get('height', 0)}
            </div>
            <div class="info-card">
                <strong>场景数:</strong> {len(self.analysis_results.get('scenes', []))}
            </div>
        </div>
        
        <h2>🎭 场景分析</h2>
        <div class="scene-list">
            {"".join([f'<div class="scene-item {"highlight" if i < 5 else ""}">场景 {i+1}: {scene.get("duration", 0):.1f}秒</div>' 
                     for i, scene in enumerate(self.analysis_results.get('scenes', [])[:20])])}
        </div>
        
        <h2>📝 字幕统计</h2>
        <p>共提取 {len(self.analysis_results.get('subtitles', []))} 条字幕</p>
        
        <h2>✨ 精彩片段</h2>
        <p>检测到 {len(self.analysis_results.get('highlights', []))} 个精彩片段</p>
    </div>
</body>
</html>
"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Movie Analyzer Pro - 专业电影分析系统')
    
    parser.add_argument('video', help='视频文件路径')
    parser.add_argument('--language', '-l', default='zh', 
                       choices=['zh', 'ko', 'en', 'ja', 'auto'],
                       help='视频语言 (默认: zh中文)')
    parser.add_argument('--duration', '-d', type=int, default=600,
                       help='分析时长限制，单位秒 (默认: 600)')
    parser.add_argument('--output', '-o', default='output',
                       help='输出目录 (默认: output)')
    parser.add_argument('--highlights', '-hl', type=int, default=0,
                       help='生成精彩片段视频的时长，0表示不生成 (默认: 0)')
    parser.add_argument('--subtitles', '-s', action='store_true',
                       help='导出字幕文件')
    parser.add_argument('--format', '-f', default='srt',
                       choices=['srt', 'ass', 'vtt'],
                       help='字幕格式 (默认: srt)')
    
    args = parser.parse_args()
    
    try:
        # 创建分析器
        analyzer = MovieAnalyzerPro(args.video, args.output)
        
        # 分析视频
        results = analyzer.analyze_video(
            language=args.language,
            duration_limit=args.duration
        )
        
        # 生成精彩片段视频
        if args.highlights > 0:
            analyzer.create_highlight_video(duration=args.highlights)
        
        # 导出字幕
        if args.subtitles:
            analyzer.export_subtitles(format=args.format)
        
        print("\n" + "="*60)
        print("✨ 分析完成！")
        print(f"📁 结果保存在: {args.output}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()