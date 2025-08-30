#!/usr/bin/env python3
"""
Movie Analyzer Pro - 基础使用示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from movie_analyzer_pro import MovieAnalyzerPro

def example_basic_analysis():
    """基础视频分析示例"""
    print("="*60)
    print("示例1: 基础视频分析")
    print("="*60)
    
    # 创建分析器实例
    analyzer = MovieAnalyzerPro("your_video.mp4", "output")
    
    # 执行分析（分析前10分钟）
    results = analyzer.analyze_video(
        language="zh",           # 中文视频
        duration_limit=600,       # 分析前600秒
        skip_intro_outro=True     # 自动跳过片头片尾
    )
    
    # 打印分析结果
    print(f"\n📊 分析结果:")
    print(f"  • 视频时长: {results['video_info']['duration_str']}")
    print(f"  • 场景数量: {len(results['scenes'])}")
    print(f"  • 字幕数量: {len(results['subtitles'])}")
    print(f"  • 精彩片段: {len(results['highlights'])}")

def example_highlight_extraction():
    """精彩片段提取示例"""
    print("\n" + "="*60)
    print("示例2: 精彩片段提取")
    print("="*60)
    
    analyzer = MovieAnalyzerPro("your_video.mp4", "output")
    
    # 先分析视频
    analyzer.analyze_video(language="zh", duration_limit=600)
    
    # 生成3分钟精彩片段集锦
    highlight_path = analyzer.create_highlight_video(
        duration=180,           # 3分钟
        with_narration=True     # 添加解说
    )
    
    print(f"✅ 精彩片段已生成: {highlight_path}")

def example_subtitle_extraction():
    """字幕提取示例"""
    print("\n" + "="*60)
    print("示例3: 字幕提取")
    print("="*60)
    
    from modules.subtitle_extractor import SubtitleExtractor
    
    # 创建字幕提取器
    extractor = SubtitleExtractor("your_video.mp4")
    
    # 提取字幕（自动选择最佳方式）
    subtitles = extractor.extract_subtitles(
        language="zh",
        duration_limit=600
    )
    
    # 导出为SRT格式
    extractor.export_subtitles(
        subtitles=subtitles,
        output_path="output/subtitles.srt",
        format="srt"
    )
    
    print(f"✅ 提取了 {len(subtitles)} 条字幕")

def example_scene_analysis():
    """场景分析示例"""
    print("\n" + "="*60)
    print("示例4: 场景分析")
    print("="*60)
    
    from modules.scene_analyzer import SceneAnalyzer
    
    # 创建场景分析器
    analyzer = SceneAnalyzer("your_video.mp4")
    
    # 检测场景
    scenes = analyzer.detect_scenes(
        max_duration=600,      # 分析前10分钟
        threshold=30.0         # 场景切换阈值
    )
    
    # 打印场景信息
    print(f"检测到 {len(scenes)} 个场景:")
    for i, scene in enumerate(scenes[:5], 1):
        print(f"  场景{i}: {scene['start']:.1f}-{scene['end']:.1f}秒, "
              f"时长{scene['duration']:.1f}秒")

def example_content_detection():
    """内容边界检测示例（片头片尾）"""
    print("\n" + "="*60)
    print("示例5: 片头片尾检测")
    print("="*60)
    
    from modules.content_detector import ContentDetector
    
    # 创建内容检测器
    detector = ContentDetector("your_video.mp4")
    
    # 检测内容边界
    boundaries = detector.detect_content_boundaries()
    
    # 打印检测结果
    print(f"片头: 0:00 - {boundaries['intro']['duration']:.0f}秒")
    print(f"正片: {boundaries['main_content']['start']:.0f}秒 - "
          f"{boundaries['main_content']['end']:.0f}秒")
    print(f"片尾: {boundaries['outro']['start']:.0f}秒 - 结束")
    
    # 提取正片
    main_content_path = detector.extract_main_content()
    print(f"✅ 正片已提取: {main_content_path}")

def example_ocr_subtitle():
    """OCR字幕识别示例"""
    print("\n" + "="*60)
    print("示例6: OCR硬字幕识别")
    print("="*60)
    
    from ocr_subtitle_extractor import OCRSubtitleExtractor
    
    # 创建OCR提取器
    extractor = OCRSubtitleExtractor("your_video.mp4", language="zh")
    
    # 提取硬字幕
    subtitles = extractor.extract_subtitles(
        duration_limit=300,     # 分析5分钟
        sample_interval=2.0,    # 每2秒采样一次
        subtitle_region=(0.7, 1.0)  # 底部30%区域
    )
    
    print(f"✅ OCR识别了 {len(subtitles)} 条字幕")
    
    # 显示前3条
    for i, sub in enumerate(subtitles[:3], 1):
        print(f"  {i}. [{sub['start']:.1f}s] {sub['text']}")

def main():
    """主函数"""
    print("🎬 Movie Analyzer Pro - 使用示例")
    print("="*60)
    print("\n注意: 请将 'your_video.mp4' 替换为实际的视频文件路径\n")
    
    # 取消注释以运行相应的示例
    
    # example_basic_analysis()      # 基础分析
    # example_highlight_extraction() # 精彩片段
    # example_subtitle_extraction()  # 字幕提取
    # example_scene_analysis()       # 场景分析
    # example_content_detection()    # 片头片尾检测
    # example_ocr_subtitle()         # OCR识别
    
    print("\n提示: 编辑此文件并取消注释相应的示例函数来运行")

if __name__ == "__main__":
    main()