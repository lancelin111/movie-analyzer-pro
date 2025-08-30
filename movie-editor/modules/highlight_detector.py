"""
精彩片段检测模块
使用多种算法检测视频中的精彩片段
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path

class HighlightDetector:
    """精彩片段检测器类"""
    
    def __init__(self, video_path: str):
        """初始化精彩片段检测器"""
        self.video_path = Path(video_path)
        self.highlights = []
        
    def detect_highlights(self, scenes: List[Dict] = None,
                         max_highlights: int = 10,
                         min_duration: float = 3.0,
                         max_duration: float = 30.0) -> List[Dict]:
        """
        检测精彩片段
        
        Args:
            scenes: 场景列表（可选）
            max_highlights: 最大精彩片段数
            min_duration: 最小片段时长
            max_duration: 最大片段时长
        
        Returns:
            精彩片段列表
        """
        if scenes:
            # 基于场景分析检测精彩片段
            highlights = self._detect_from_scenes(scenes, max_highlights)
        else:
            # 直接从视频检测精彩片段
            highlights = self._detect_from_video(max_highlights, min_duration, max_duration)
        
        self.highlights = highlights
        return highlights
    
    def _detect_from_scenes(self, scenes: List[Dict], 
                           max_highlights: int) -> List[Dict]:
        """基于场景分析检测精彩片段"""
        # 计算每个场景的精彩度分数
        scored_scenes = []
        
        for scene in scenes:
            score = self._calculate_scene_score(scene)
            scored_scenes.append({
                **scene,
                'highlight_score': score
            })
        
        # 按分数排序
        scored_scenes.sort(key=lambda x: x['highlight_score'], reverse=True)
        
        # 选择最精彩的片段
        highlights = []
        for scene in scored_scenes[:max_highlights]:
            highlights.append({
                'id': len(highlights),
                'start': scene['start'],
                'end': scene['end'],
                'duration': scene['duration'],
                'score': scene['highlight_score'],
                'reason': self._get_highlight_reason(scene),
                'type': self._classify_highlight_type(scene)
            })
        
        return highlights
    
    def _detect_from_video(self, max_highlights: int,
                          min_duration: float,
                          max_duration: float) -> List[Dict]:
        """直接从视频检测精彩片段"""
        cap = cv2.VideoCapture(str(self.video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 分析关键指标
        metrics = []
        sample_interval = int(fps)  # 每秒采样一次
        
        for frame_idx in range(0, frame_count, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # 计算各项指标
            metric = {
                'frame_idx': frame_idx,
                'time': frame_idx / fps,
                'motion': self._calculate_motion(cap, frame, fps),
                'edges': self._calculate_edges(frame),
                'color_variance': self._calculate_color_variance(frame),
                'brightness': np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)),
                'faces': self._detect_faces(frame)
            }
            
            # 计算综合分数
            metric['score'] = self._calculate_metric_score(metric)
            metrics.append(metric)
        
        cap.release()
        
        # 找出高分片段
        highlights = self._extract_highlight_segments(
            metrics, fps, max_highlights, min_duration, max_duration
        )
        
        return highlights
    
    def _calculate_scene_score(self, scene: Dict) -> float:
        """计算场景的精彩度分数"""
        score = 0.0
        
        # 运动分数（动作场景更精彩）
        motion = scene.get('motion', 0)
        if motion > 20:
            score += 30
        elif motion > 10:
            score += 20
        else:
            score += 5
        
        # 人物分数（有人物的场景更重要）
        faces = scene.get('faces', 0)
        score += faces * 15
        
        # 对话分数（有对话的场景更重要）
        dialogues = len(scene.get('dialogues', []))
        score += dialogues * 10
        
        # 时长分数（适中时长更好）
        duration = scene.get('duration', 0)
        if 5 <= duration <= 20:
            score += 20
        elif 3 <= duration <= 30:
            score += 10
        
        # 亮度分数（正常亮度更好）
        brightness = scene.get('brightness', 0)
        if 50 <= brightness <= 150:
            score += 10
        
        return score
    
    def _calculate_motion(self, cap, current_frame, fps) -> float:
        """计算运动量"""
        # 获取下一帧
        next_idx = cap.get(cv2.CAP_PROP_POS_FRAMES)
        cap.set(cv2.CAP_PROP_POS_FRAMES, next_idx)
        ret, next_frame = cap.read()
        
        if not ret:
            return 0.0
        
        # 转换为灰度图
        gray1 = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
        
        # 计算光流
        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        # 计算运动幅度
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        motion_score = np.mean(magnitude)
        
        # 恢复帧位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, next_idx - 1)
        
        return float(motion_score)
    
    def _calculate_edges(self, frame) -> float:
        """计算边缘复杂度"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return float(np.sum(edges) / (frame.shape[0] * frame.shape[1]))
    
    def _calculate_color_variance(self, frame) -> float:
        """计算颜色方差"""
        # 转换到HSV空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算色调的方差
        hue_variance = np.var(hsv[:, :, 0])
        
        # 计算饱和度的方差
        sat_variance = np.var(hsv[:, :, 1])
        
        return float(hue_variance + sat_variance)
    
    def _detect_faces(self, frame) -> int:
        """检测人脸数量"""
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        return len(faces)
    
    def _calculate_metric_score(self, metric: Dict) -> float:
        """计算综合分数"""
        score = 0.0
        
        # 运动权重
        score += metric['motion'] * 30
        
        # 边缘权重
        score += metric['edges'] * 20
        
        # 颜色多样性权重
        score += min(metric['color_variance'] / 1000, 20)
        
        # 人脸权重
        score += metric['faces'] * 25
        
        # 亮度权重（适中亮度加分）
        if 50 <= metric['brightness'] <= 150:
            score += 10
        
        return score
    
    def _extract_highlight_segments(self, metrics: List[Dict],
                                   fps: float,
                                   max_highlights: int,
                                   min_duration: float,
                                   max_duration: float) -> List[Dict]:
        """提取精彩片段"""
        # 按分数排序
        metrics.sort(key=lambda x: x['score'], reverse=True)
        
        highlights = []
        used_times = set()
        
        for metric in metrics:
            if len(highlights) >= max_highlights:
                break
            
            # 检查是否与已选片段重叠
            start_time = metric['time']
            if any(abs(start_time - t) < min_duration * 2 for t in used_times):
                continue
            
            # 确定片段时长
            duration = min(max_duration, max(min_duration, 10.0))
            end_time = start_time + duration
            
            highlights.append({
                'id': len(highlights),
                'start': start_time,
                'end': end_time,
                'duration': duration,
                'score': metric['score'],
                'reason': f"高动态场景 (运动:{metric['motion']:.1f})",
                'type': 'action' if metric['motion'] > 5 else 'dialogue'
            })
            
            used_times.add(start_time)
        
        # 按时间顺序排序
        highlights.sort(key=lambda x: x['start'])
        
        return highlights
    
    def _get_highlight_reason(self, scene: Dict) -> str:
        """获取精彩原因描述"""
        reasons = []
        
        if scene.get('motion', 0) > 20:
            reasons.append("高动态场景")
        
        if scene.get('faces', 0) >= 3:
            reasons.append("多人互动")
        elif scene.get('faces', 0) > 0:
            reasons.append("人物场景")
        
        if len(scene.get('dialogues', [])) > 2:
            reasons.append("重要对话")
        
        return "，".join(reasons) if reasons else "综合评分高"
    
    def _classify_highlight_type(self, scene: Dict) -> str:
        """分类精彩片段类型"""
        if scene.get('motion', 0) > 20:
            return 'action'
        elif len(scene.get('dialogues', [])) > 0:
            return 'dialogue'
        elif scene.get('faces', 0) > 2:
            return 'group'
        else:
            return 'scenic'