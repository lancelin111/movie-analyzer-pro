"""
字幕提取模块
支持多种方式提取字幕：嵌入字幕、OCR、语音识别
"""

import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import timedelta

class SubtitleExtractor:
    """字幕提取器类"""
    
    def __init__(self, video_path: str):
        """初始化字幕提取器"""
        self.video_path = Path(video_path)
        self.subtitles = []
        
    def extract_subtitles(self, language: str = "zh", 
                         duration_limit: int = 600) -> List[Dict]:
        """
        提取字幕的主方法
        
        Args:
            language: 语言代码 (zh=中文, ko=韩语, en=英语, auto=自动)
            duration_limit: 分析时长限制（秒）
        
        Returns:
            字幕列表
        """
        # 尝试多种方法提取字幕
        
        # 1. 尝试提取嵌入字幕
        embedded_subtitles = self._extract_embedded_subtitles()
        if embedded_subtitles:
            print("  ✅ 找到嵌入字幕")
            self.subtitles = embedded_subtitles
            return embedded_subtitles
        
        # 2. 同时进行OCR和语音识别
        print("  未找到嵌入字幕，同时尝试OCR和语音识别...")
        
        # 2.1 尝试OCR识别硬字幕
        print("  🔍 尝试OCR识别硬字幕...")
        ocr_subtitles = self._extract_with_ocr(language, duration_limit)
        
        # 2.2 如果OCR找到了字幕，直接使用
        if ocr_subtitles and len(ocr_subtitles) > 5:  # 至少有5条字幕才认为是有效的
            print(f"  ✅ OCR成功识别 {len(ocr_subtitles)} 条字幕")
            self.subtitles = ocr_subtitles
            return ocr_subtitles
        
        # 2.3 如果OCR没找到或太少，使用语音识别
        print("  🎙️ OCR字幕较少，使用语音识别...")
        whisper_subtitles = self._extract_with_whisper(language, duration_limit)
        
        # 3. 选择最佳结果
        if whisper_subtitles and len(whisper_subtitles) > len(ocr_subtitles):
            print(f"  ✅ 使用语音识别结果 ({len(whisper_subtitles)} 条字幕)")
            subtitles = whisper_subtitles
        elif ocr_subtitles:
            print(f"  ✅ 使用OCR识别结果 ({len(ocr_subtitles)} 条字幕)")
            subtitles = ocr_subtitles
        else:
            print("  ⚠️ 未能提取到字幕")
            subtitles = []
        
        self.subtitles = subtitles
        return subtitles
    
    def _extract_embedded_subtitles(self) -> List[Dict]:
        """提取嵌入的字幕轨道"""
        try:
            # 检查字幕流
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 's',
                '-show_entries', 'stream=index,codec_name,codec_type:stream_tags=language',
                '-of', 'json',
                str(self.video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            info = json.loads(result.stdout)
            
            if not info.get('streams'):
                return []
            
            # 提取第一个字幕流
            output_srt = Path("temp_subtitles.srt")
            cmd = [
                'ffmpeg', '-y', '-i', str(self.video_path),
                '-map', '0:s:0',
                str(output_srt)
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0 and output_srt.exists():
                subtitles = self._parse_srt(str(output_srt))
                output_srt.unlink()  # 删除临时文件
                return subtitles
                
        except Exception as e:
            print(f"  提取嵌入字幕失败: {e}")
        
        return []
    
    def _extract_with_whisper(self, language: str, duration_limit: int) -> List[Dict]:
        """使用Whisper进行语音识别"""
        try:
            import whisper
            
            # 创建临时音频文件
            audio_path = Path("temp_audio.wav")
            cmd = [
                'ffmpeg', '-y', '-i', str(self.video_path),
                '-t', str(duration_limit),
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                str(audio_path)
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if not audio_path.exists():
                return []
            
            # 使用Whisper识别
            print(f"  加载Whisper模型...")
            model = whisper.load_model("base")
            
            # 设置语言
            whisper_lang = {
                'zh': 'zh',
                'ko': 'ko',
                'en': 'en',
                'ja': 'ja',
                'auto': None
            }.get(language, None)
            
            print(f"  识别中 (语言: {whisper_lang or 'auto'})...")
            result = model.transcribe(
                str(audio_path),
                language=whisper_lang,
                task="transcribe"
            )
            
            # 转换为字幕格式
            subtitles = []
            for segment in result['segments']:
                subtitles.append({
                    'id': segment['id'],
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip(),
                    'language': language
                })
            
            # 清理临时文件
            audio_path.unlink()
            
            return subtitles
            
        except ImportError:
            print("  Whisper未安装，跳过语音识别")
        except Exception as e:
            print(f"  语音识别失败: {e}")
        
        return []
    
    def _extract_with_ocr(self, language: str, duration_limit: int) -> List[Dict]:
        """使用OCR识别硬字幕"""
        try:
            import cv2
            import numpy as np
            
            # 尝试使用EasyOCR（效果更好）
            ocr_engine = None
            try:
                import easyocr
                # EasyOCR语言映射
                lang_map = {
                    'zh': ['ch_sim', 'en'],
                    'en': ['en'],
                    'ko': ['ko', 'en'],
                    'ja': ['ja', 'en']
                }
                languages = lang_map.get(language, ['ch_sim', 'en'])
                print(f"    初始化EasyOCR (语言: {languages})...")
                reader = easyocr.Reader(languages, gpu=False)
                ocr_engine = "easyocr"
            except ImportError:
                try:
                    import pytesseract
                    ocr_engine = "pytesseract"
                    print("    使用pytesseract进行OCR...")
                except ImportError:
                    print("    未安装OCR库（EasyOCR或pytesseract）")
                    return []
            
            cap = cv2.VideoCapture(str(self.video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            subtitles = []
            last_text = ""
            last_start = 0
            
            # 每3秒采样一次（减少处理量）
            sample_interval = 3.0
            sample_frames = int(fps * sample_interval)
            max_frames = int(duration_limit * fps)
            
            print(f"    处理进度:")
            processed = 0
            
            for frame_idx in range(0, max_frames, sample_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                processed += 1
                current_time = frame_idx / fps
                
                # 显示进度
                if processed % 10 == 0:
                    progress = (frame_idx / max_frames) * 100
                    print(f"      {progress:.1f}% ({current_time:.1f}秒)")
                
                # 裁剪字幕区域（底部30%）
                subtitle_region = frame[int(height * 0.7):, :]
                
                # 预处理图像
                gray = cv2.cvtColor(subtitle_region, cv2.COLOR_BGR2GRAY)
                _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
                
                # OCR识别
                text = ""
                if ocr_engine == "easyocr":
                    results = reader.readtext(subtitle_region, detail=0)
                    text = ' '.join(results).strip()
                elif ocr_engine == "pytesseract":
                    import pytesseract
                    ocr_lang = {
                        'zh': 'chi_sim',
                        'en': 'eng',
                        'ko': 'kor',
                        'ja': 'jpn'
                    }.get(language, 'chi_sim')
                    text = pytesseract.image_to_string(
                        binary,
                        lang=ocr_lang,
                        config='--psm 7'
                    ).strip()
                
                # 清理文本
                text = ' '.join(text.split())
                if len(text) < 2:
                    text = ""
                
                # 如果识别到新文本
                if text and text != last_text:
                    # 保存上一条字幕
                    if last_text:
                        subtitles.append({
                            'id': len(subtitles),
                            'start': last_start,
                            'end': current_time,
                            'text': last_text,
                            'language': language
                        })
                    
                    last_text = text
                    last_start = current_time
            
            # 添加最后一条字幕
            if last_text:
                subtitles.append({
                    'id': len(subtitles),
                    'start': last_start,
                    'end': max_frames / fps,
                    'text': last_text,
                    'language': language
                })
            
            cap.release()
            
            print(f"    OCR识别完成，提取了 {len(subtitles)} 条字幕")
            return subtitles
            
        except Exception as e:
            print(f"  OCR识别失败: {e}")
        
        return []
    
    def _parse_srt(self, srt_path: str) -> List[Dict]:
        """解析SRT字幕文件"""
        subtitles = []
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割字幕块
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 解析ID
                try:
                    sub_id = int(lines[0])
                except:
                    continue
                
                # 解析时间戳
                time_match = re.match(
                    r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})',
                    lines[1]
                )
                
                if time_match:
                    start = (int(time_match.group(1)) * 3600 +
                            int(time_match.group(2)) * 60 +
                            int(time_match.group(3)) +
                            int(time_match.group(4)) / 1000)
                    end = (int(time_match.group(5)) * 3600 +
                          int(time_match.group(6)) * 60 +
                          int(time_match.group(7)) +
                          int(time_match.group(8)) / 1000)
                    
                    # 获取文本
                    text = ' '.join(lines[2:])
                    
                    subtitles.append({
                        'id': sub_id - 1,
                        'start': start,
                        'end': end,
                        'text': text
                    })
        
        return subtitles
    
    def translate_subtitles(self, target_lang: str = "zh") -> List[Dict]:
        """翻译字幕"""
        if not self.subtitles:
            return []
        
        try:
            from googletrans import Translator
            translator = Translator()
            
            translated = []
            for sub in self.subtitles:
                try:
                    result = translator.translate(
                        sub['text'],
                        dest=target_lang
                    )
                    
                    translated.append({
                        **sub,
                        'original_text': sub['text'],
                        'text': result.text,
                        'translation': result.text,
                        'source_lang': result.src,
                        'target_lang': target_lang
                    })
                except:
                    translated.append(sub)
            
            return translated
            
        except ImportError:
            print("  googletrans未安装，跳过翻译")
            return self.subtitles
    
    def export_subtitles(self, subtitles: List[Dict], 
                        output_path: str, format: str = "srt"):
        """导出字幕文件"""
        output_path = Path(output_path)
        
        if format == "srt":
            self._export_srt(subtitles, output_path)
        elif format == "ass":
            self._export_ass(subtitles, output_path)
        elif format == "vtt":
            self._export_vtt(subtitles, output_path)
        else:
            raise ValueError(f"不支持的字幕格式: {format}")
    
    def export_bilingual_subtitles(self, subtitles: List[Dict],
                                  output_path: str, format: str = "srt"):
        """导出双语字幕"""
        bilingual_subs = []
        
        for sub in subtitles:
            text = sub['text']
            if 'translation' in sub:
                text = f"{sub['original_text']}\\N{sub['translation']}"
            
            bilingual_subs.append({
                **sub,
                'text': text
            })
        
        self.export_subtitles(bilingual_subs, output_path, format)
    
    def _export_srt(self, subtitles: List[Dict], output_path: Path):
        """导出SRT格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles, 1):
                f.write(f"{i}\n")
                start = self._format_srt_time(sub['start'])
                end = self._format_srt_time(sub['end'])
                f.write(f"{start} --> {end}\n")
                f.write(f"{sub['text']}\n\n")
    
    def _export_ass(self, subtitles: List[Dict], output_path: Path):
        """导出ASS格式字幕"""
        # ASS文件头
        header = """[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            
            for sub in subtitles:
                start = self._format_ass_time(sub['start'])
                end = self._format_ass_time(sub['end'])
                text = sub['text'].replace('\n', '\\N')
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
    
    def _export_vtt(self, subtitles: List[Dict], output_path: Path):
        """导出WebVTT格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for sub in subtitles:
                start = self._format_vtt_time(sub['start'])
                end = self._format_vtt_time(sub['end'])
                f.write(f"{start} --> {end}\n")
                f.write(f"{sub['text']}\n\n")
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化SRT时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_ass_time(self, seconds: float) -> str:
        """格式化ASS时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """格式化WebVTT时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"