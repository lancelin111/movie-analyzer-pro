#!/usr/bin/env python3
"""
OCR字幕提取器
专门用于识别视频中的硬字幕（烧录字幕）
支持中文、英文等多语言
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import subprocess
import json

# 尝试导入不同的OCR库
OCR_AVAILABLE = None
try:
    import easyocr
    OCR_AVAILABLE = "easyocr"
    print("✅ 使用 EasyOCR（推荐，识别率高）")
except ImportError:
    try:
        import pytesseract
        from PIL import Image
        OCR_AVAILABLE = "pytesseract"
        print("⚠️ 使用 Pytesseract（需要安装tesseract）")
    except ImportError:
        print("❌ 未安装OCR库，请安装 easyocr 或 pytesseract")

class OCRSubtitleExtractor:
    """OCR字幕提取器"""
    
    def __init__(self, video_path: str, language: str = "zh"):
        """
        初始化OCR提取器
        
        Args:
            video_path: 视频路径
            language: 语言代码 (zh=中文, en=英文, ko=韩语)
        """
        self.video_path = Path(video_path)
        self.language = language
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.width = 0
        self.height = 0
        
        # 初始化OCR
        self._init_ocr()
        
    def _init_ocr(self):
        """初始化OCR引擎"""
        if OCR_AVAILABLE == "easyocr":
            # EasyOCR语言映射
            lang_map = {
                'zh': ['ch_sim', 'en'],  # 简体中文+英文
                'en': ['en'],
                'ko': ['ko', 'en'],
                'ja': ['ja', 'en']
            }
            languages = lang_map.get(self.language, ['ch_sim', 'en'])
            
            print(f"🔄 初始化 EasyOCR (语言: {languages})...")
            self.reader = easyocr.Reader(languages, gpu=False)
            
        elif OCR_AVAILABLE == "pytesseract":
            # Tesseract语言映射
            self.tesseract_lang = {
                'zh': 'chi_sim',
                'en': 'eng',
                'ko': 'kor',
                'ja': 'jpn'
            }.get(self.language, 'chi_sim')
            
            print(f"🔄 初始化 Pytesseract (语言: {self.tesseract_lang})...")
    
    def extract_subtitles(self, 
                         duration_limit: int = 600,
                         sample_interval: float = 1.0,
                         subtitle_region: Tuple[float, float] = (0.6, 1.0)) -> List[Dict]:
        """
        提取硬字幕
        
        Args:
            duration_limit: 分析时长限制（秒）
            sample_interval: 采样间隔（秒）
            subtitle_region: 字幕区域 (顶部比例, 底部比例)，默认底部40%
        
        Returns:
            字幕列表
        """
        print(f"\n🎯 开始OCR字幕提取...")
        print(f"  • 视频: {self.video_path.name}")
        print(f"  • 语言: {self.language}")
        print(f"  • 采样间隔: {sample_interval}秒")
        print(f"  • 字幕区域: 画面底部{(1-subtitle_region[0])*100:.0f}%")
        
        # 打开视频
        self.cap = cv2.VideoCapture(str(self.video_path))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"  • 视频信息: {self.width}x{self.height} @ {self.fps:.2f}fps")
        
        # 计算采样帧
        sample_frames = int(self.fps * sample_interval)
        max_frames = min(int(duration_limit * self.fps), self.frame_count)
        
        subtitles = []
        last_text = ""
        last_start = 0
        processed_frames = 0
        
        print(f"\n📊 处理进度:")
        
        for frame_idx in range(0, max_frames, sample_frames):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            processed_frames += 1
            current_time = frame_idx / self.fps
            
            # 每10秒显示进度
            if processed_frames % 10 == 0:
                progress = (frame_idx / max_frames) * 100
                print(f"  处理中... {progress:.1f}% ({current_time:.1f}秒)")
            
            # 提取字幕区域
            subtitle_frame = self._extract_subtitle_region(frame, subtitle_region)
            
            # 预处理图像
            processed_frame = self._preprocess_frame(subtitle_frame)
            
            # OCR识别
            text = self._ocr_frame(processed_frame)
            
            # 清理文本
            text = self._clean_text(text)
            
            # 如果识别到新文本
            if text and text != last_text:
                # 保存上一条字幕
                if last_text:
                    subtitles.append({
                        'id': len(subtitles),
                        'start': last_start,
                        'end': current_time,
                        'text': last_text,
                        'confidence': 0.8  # 置信度（如果OCR提供的话）
                    })
                
                last_text = text
                last_start = current_time
        
        # 添加最后一条字幕
        if last_text:
            subtitles.append({
                'id': len(subtitles),
                'start': last_start,
                'end': max_frames / self.fps,
                'text': last_text,
                'confidence': 0.8
            })
        
        self.cap.release()
        
        print(f"\n✅ OCR提取完成!")
        print(f"  • 识别字幕数: {len(subtitles)}")
        
        # 显示前3条字幕
        if subtitles:
            print(f"\n📝 字幕示例:")
            for i, sub in enumerate(subtitles[:3], 1):
                print(f"  {i}. [{sub['start']:.1f}s] {sub['text'][:50]}...")
        
        return subtitles
    
    def _extract_subtitle_region(self, frame: np.ndarray, 
                                region: Tuple[float, float]) -> np.ndarray:
        """提取字幕区域"""
        h, w = frame.shape[:2]
        
        # 计算字幕区域
        top = int(h * region[0])
        bottom = int(h * region[1])
        
        # 提取区域
        subtitle_region = frame[top:bottom, :]
        
        return subtitle_region
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """预处理图像以提高OCR识别率"""
        # 转换为灰度图
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # 方法1：二值化（适合白色字幕）
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # 方法2：自适应阈值（适合复杂背景）
        # binary = cv2.adaptiveThreshold(gray, 255, 
        #                               cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #                               cv2.THRESH_BINARY, 11, 2)
        
        # 去噪
        denoised = cv2.medianBlur(binary, 3)
        
        # 放大以提高识别率
        scaled = cv2.resize(denoised, None, fx=2, fy=2, 
                           interpolation=cv2.INTER_CUBIC)
        
        return scaled
    
    def _ocr_frame(self, frame: np.ndarray) -> str:
        """对单帧进行OCR识别"""
        if OCR_AVAILABLE == "easyocr":
            # EasyOCR识别
            results = self.reader.readtext(frame, detail=0)
            text = ' '.join(results)
            
        elif OCR_AVAILABLE == "pytesseract":
            # Pytesseract识别
            text = pytesseract.image_to_string(
                frame,
                lang=self.tesseract_lang,
                config='--psm 7'  # 单行文本模式
            )
        else:
            text = ""
        
        return text.strip()
    
    def _clean_text(self, text: str) -> str:
        """清理OCR识别的文本"""
        # 移除多余空格
        text = ' '.join(text.split())
        
        # 移除特殊字符（可选）
        # text = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', text)
        
        # 移除太短的文本（可能是误识别）
        if len(text) < 2:
            return ""
        
        return text
    
    def extract_with_multiple_methods(self, duration_limit: int = 600) -> Dict:
        """
        使用多种方法提取字幕，返回最佳结果
        """
        results = {}
        
        # 方法1：底部40%区域
        print("\n🔍 方法1: 扫描底部40%区域...")
        subtitles_bottom = self.extract_subtitles(
            duration_limit=duration_limit,
            subtitle_region=(0.6, 1.0)
        )
        results['bottom'] = subtitles_bottom
        
        # 方法2：底部20%区域（更精确）
        print("\n🔍 方法2: 扫描底部20%区域...")
        subtitles_narrow = self.extract_subtitles(
            duration_limit=duration_limit,
            subtitle_region=(0.8, 1.0)
        )
        results['narrow'] = subtitles_narrow
        
        # 选择最佳结果（字幕数量最多的）
        best_method = max(results.keys(), key=lambda k: len(results[k]))
        best_subtitles = results[best_method]
        
        print(f"\n✨ 最佳方法: {best_method} (识别{len(best_subtitles)}条字幕)")
        
        return {
            'subtitles': best_subtitles,
            'method': best_method,
            'all_results': results
        }

def test_ocr_extraction(video_path: str, language: str = "zh"):
    """测试OCR字幕提取"""
    print("="*60)
    print("🎯 OCR字幕提取测试")
    print("="*60)
    
    # 检查视频文件
    if not Path(video_path).exists():
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 创建提取器
    extractor = OCRSubtitleExtractor(video_path, language)
    
    # 提取字幕（测试30秒）
    subtitles = extractor.extract_subtitles(
        duration_limit=30,
        sample_interval=1.0,
        subtitle_region=(0.7, 1.0)  # 底部30%
    )
    
    # 保存结果
    output_dir = Path("output/ocr_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存为SRT
    srt_path = output_dir / "ocr_subtitles.srt"
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time(sub['start'])} --> {format_time(sub['end'])}\n")
            f.write(f"{sub['text']}\n\n")
    
    print(f"\n✅ 字幕已保存: {srt_path}")
    
    # 保存JSON
    json_path = output_dir / "ocr_subtitles.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(subtitles, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON已保存: {json_path}")

def format_time(seconds: float) -> str:
    """格式化时间为SRT格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def install_requirements():
    """安装所需依赖"""
    print("📦 安装OCR依赖...")
    
    # 安装easyocr
    subprocess.run(["pip3", "install", "easyocr"], check=False)
    
    # 或安装pytesseract
    # subprocess.run(["pip3", "install", "pytesseract", "pillow"], check=False)
    # macOS: brew install tesseract tesseract-lang
    # Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        language = sys.argv[2] if len(sys.argv) > 2 else "zh"
        test_ocr_extraction(video_path, language)
    else:
        # 测试生万物视频
        test_video = "/Users/linguangjie/movie-editor/生万物-01.mp4"
        if Path(test_video).exists():
            test_ocr_extraction(test_video, "zh")
        else:
            print("用法: python ocr_subtitle_extractor.py <视频路径> [语言]")
            print("示例: python ocr_subtitle_extractor.py video.mp4 zh")