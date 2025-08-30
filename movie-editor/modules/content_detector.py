"""
内容检测模块
自动识别片头、片尾、广告等非正片内容
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import subprocess
import json

class ContentDetector:
    """检测视频中的片头、片尾、广告等内容"""
    
    def __init__(self, video_path: str):
        """初始化内容检测器"""
        self.video_path = Path(video_path)
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.width = 0
        self.height = 0
        
    def detect_content_boundaries(self, sample_duration: int = 600) -> Dict:
        """
        检测内容边界（片头、片尾、广告）
        
        Args:
            sample_duration: 采样时长（秒），默认分析前10分钟
            
        Returns:
            包含片头、片尾、正片时间段的字典
        """
        print("\n🔍 检测视频内容结构...")
        
        # 打开视频
        self.cap = cv2.VideoCapture(str(self.video_path))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_duration = self.frame_count / self.fps
        
        print(f"  • 视频总时长: {total_duration/60:.1f}分钟")
        
        # 1. 检测片头
        intro_end = self._detect_intro()
        
        # 2. 检测片尾
        outro_start = self._detect_outro()
        
        # 3. 检测广告/中断
        ad_segments = self._detect_ads(intro_end, outro_start, sample_duration)
        
        # 4. 检测黑场（常见的分段标志）
        black_segments = self._detect_black_frames(intro_end, outro_start)
        
        self.cap.release()
        
        # 整理结果
        result = {
            'total_duration': total_duration,
            'intro': {
                'start': 0,
                'end': intro_end,
                'duration': intro_end
            },
            'outro': {
                'start': outro_start,
                'end': total_duration,
                'duration': total_duration - outro_start
            },
            'main_content': {
                'start': intro_end,
                'end': outro_start,
                'duration': outro_start - intro_end
            },
            'ads': ad_segments,
            'black_frames': black_segments
        }
        
        # 打印检测结果
        print(f"\n✅ 内容结构检测完成:")
        print(f"  • 片头: 0:00 - {self._format_time(intro_end)}")
        print(f"  • 正片: {self._format_time(intro_end)} - {self._format_time(outro_start)}")
        print(f"  • 片尾: {self._format_time(outro_start)} - {self._format_time(total_duration)}")
        
        if ad_segments:
            print(f"  • 检测到 {len(ad_segments)} 个广告段")
        
        return result
    
    def _detect_intro(self) -> float:
        """
        检测片头结束时间
        通过以下特征判断：
        1. 音频突变（背景音乐结束）
        2. 场景快速切换结束
        3. 文字/LOGO消失
        4. 黑场过渡
        """
        print("  🎬 检测片头...")
        
        # 分析前3分钟
        max_intro_duration = min(180, self.frame_count / self.fps)
        
        # 特征检测
        features = []
        
        # 1. 场景切换频率分析
        scene_changes = self._analyze_scene_change_frequency(0, max_intro_duration)
        
        # 2. 文字密度分析（片头通常有演职员表）
        text_density = self._analyze_text_density(0, max_intro_duration)
        
        # 3. 音频分析（如果可能）
        audio_changes = self._analyze_audio_changes(0, max_intro_duration)
        
        # 综合判断片头结束点
        intro_end = 0
        
        # 查找场景切换频率降低的点
        for i in range(1, len(scene_changes)):
            if scene_changes[i] < scene_changes[i-1] * 0.5:  # 切换频率降低50%
                intro_end = i * 10  # 每10秒一个采样点
                break
        
        # 如果没找到明显的片头，默认30秒
        if intro_end == 0:
            intro_end = min(30, max_intro_duration)
        
        return intro_end
    
    def _detect_outro(self) -> float:
        """
        检测片尾开始时间
        通过以下特征判断：
        1. 滚动字幕开始
        2. 黑场
        3. 音频淡出
        """
        print("  🎬 检测片尾...")
        
        total_duration = self.frame_count / self.fps
        
        # 分析最后5分钟
        check_duration = min(300, total_duration)
        outro_start = total_duration - check_duration
        
        # 从后向前检查
        for t in range(int(total_duration - 30), int(outro_start), -10):
            # 检查是否有滚动字幕
            if self._has_rolling_credits(t):
                return t
            
            # 检查是否是黑场
            if self._is_black_frame(t):
                # 确认后续都是黑场或字幕
                if self._is_ending_content(t, total_duration):
                    return t
        
        # 默认最后1分钟为片尾
        return max(total_duration - 60, total_duration * 0.95)
    
    def _detect_ads(self, intro_end: float, outro_start: float, 
                   sample_duration: int) -> List[Dict]:
        """检测广告段落"""
        ads = []
        
        # 广告通常有以下特征：
        # 1. 突然的音量变化
        # 2. 画面风格突变
        # 3. 固定的时长（15秒、30秒等）
        
        # 这里简化处理，主要通过场景突变检测
        check_end = min(intro_end + sample_duration, outro_start)
        
        # TODO: 实现更复杂的广告检测逻辑
        
        return ads
    
    def _detect_black_frames(self, start: float, end: float) -> List[Dict]:
        """检测黑场段落"""
        black_segments = []
        
        sample_interval = 5  # 每5秒检查一次
        current_black_start = None
        
        for t in range(int(start), int(end), sample_interval):
            if self._is_black_frame(t):
                if current_black_start is None:
                    current_black_start = t
            else:
                if current_black_start is not None:
                    # 黑场结束
                    if t - current_black_start >= 2:  # 至少2秒的黑场才记录
                        black_segments.append({
                            'start': current_black_start,
                            'end': t,
                            'duration': t - current_black_start
                        })
                    current_black_start = None
        
        return black_segments
    
    def _analyze_scene_change_frequency(self, start: float, end: float) -> List[float]:
        """分析场景切换频率"""
        frequencies = []
        window_size = 10  # 10秒窗口
        
        for t in range(int(start), int(end), window_size):
            changes = self._count_scene_changes(t, min(t + window_size, end))
            frequencies.append(changes / window_size)
        
        return frequencies
    
    def _count_scene_changes(self, start: float, end: float) -> int:
        """统计时间段内的场景切换次数"""
        changes = 0
        
        # 每秒采样一帧
        start_frame = int(start * self.fps)
        end_frame = int(end * self.fps)
        
        prev_frame = None
        for frame_idx in range(start_frame, end_frame, int(self.fps)):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            if prev_frame is not None:
                # 计算帧差异
                diff = cv2.absdiff(frame, prev_frame)
                mean_diff = np.mean(diff)
                
                if mean_diff > 30:  # 阈值
                    changes += 1
            
            prev_frame = frame
        
        return changes
    
    def _analyze_text_density(self, start: float, end: float) -> List[float]:
        """分析文字密度（片头通常有演职员表）"""
        densities = []
        
        # 简化：通过边缘检测估算文字区域
        window_size = 10
        
        for t in range(int(start), int(end), window_size):
            frame_idx = int(t * self.fps)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                density = np.sum(edges > 0) / edges.size
                densities.append(density)
            else:
                densities.append(0)
        
        return densities
    
    def _analyze_audio_changes(self, start: float, end: float) -> List[float]:
        """分析音频变化（需要ffmpeg）"""
        # TODO: 实现音频分析
        return []
    
    def _has_rolling_credits(self, time: float) -> bool:
        """检查是否有滚动字幕"""
        # 检查连续几帧，看是否有垂直移动的文字
        frames_to_check = 5
        frame_idx = int(time * self.fps)
        
        frames = []
        for i in range(frames_to_check):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx + i * int(self.fps/5))
            ret, frame = self.cap.read()
            if ret:
                # 只保留底部区域（字幕通常在这里）
                bottom = frame[int(self.height * 0.5):, :]
                gray = cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)
                frames.append(gray)
        
        if len(frames) < 2:
            return False
        
        # 检查是否有垂直移动
        for i in range(1, len(frames)):
            # 计算光流或模板匹配来检测垂直移动
            # 这里简化：比较帧差异
            diff = cv2.absdiff(frames[i], frames[i-1])
            if np.mean(diff) > 10:  # 有明显变化
                return True
        
        return False
    
    def _is_black_frame(self, time: float) -> bool:
        """检查是否是黑场"""
        frame_idx = int(time * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        
        if not ret:
            return False
        
        # 计算平均亮度
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        return mean_brightness < 20  # 阈值
    
    def _is_ending_content(self, start: float, end: float) -> bool:
        """检查是否是结尾内容（黑场或字幕）"""
        # 采样几个点检查
        for t in range(int(start), int(end), 10):
            if not self._is_black_frame(t) and not self._has_rolling_credits(t):
                return False
        return True
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def extract_main_content(self, output_path: str = None) -> str:
        """
        提取主要内容（去除片头片尾）
        
        Args:
            output_path: 输出路径，如果为None则自动生成
            
        Returns:
            输出文件路径
        """
        # 检测内容边界
        boundaries = self.detect_content_boundaries()
        
        # 生成输出路径
        if output_path is None:
            output_path = self.video_path.stem + "_main_content" + self.video_path.suffix
        
        output_path = Path(output_path)
        
        print(f"\n✂️ 提取主要内容...")
        print(f"  • 开始: {self._format_time(boundaries['main_content']['start'])}")
        print(f"  • 结束: {self._format_time(boundaries['main_content']['end'])}")
        print(f"  • 时长: {boundaries['main_content']['duration']/60:.1f}分钟")
        
        # 使用ffmpeg剪切视频
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.video_path),
            '-ss', str(boundaries['main_content']['start']),
            '-to', str(boundaries['main_content']['end']),
            '-c', 'copy',  # 直接复制，不重新编码
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ 主要内容已保存: {output_path}")
            return str(output_path)
        else:
            print(f"  ❌ 提取失败: {result.stderr}")
            return None


def test_content_detection(video_path: str):
    """测试内容检测"""
    detector = ContentDetector(video_path)
    
    # 检测内容边界
    boundaries = detector.detect_content_boundaries()
    
    # 保存检测结果
    output_dir = Path("output/content_detection")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result_path = output_dir / "boundaries.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(boundaries, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 检测结果已保存: {result_path}")
    
    # 提取主要内容
    main_content_path = output_dir / "main_content.mp4"
    detector.extract_main_content(str(main_content_path))
    
    return boundaries


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = "/Users/linguangjie/movie-editor/生万物-01.mp4"
    
    test_content_detection(video_path)