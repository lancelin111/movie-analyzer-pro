"""
场景分析模块
检测视频中的场景变化、分析场景特征
"""

import cv2
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path

class SceneAnalyzer:
    """场景分析器类"""
    
    def __init__(self, video_path: str):
        """初始化场景分析器"""
        self.video_path = Path(video_path)
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        
    def detect_scenes(self, max_duration: int = 600, 
                     threshold: float = 30.0) -> List[Dict]:
        """
        检测场景变化
        
        Args:
            max_duration: 最大分析时长（秒）
            threshold: 场景切换阈值
        
        Returns:
            场景列表
        """
        scenes = []
        self.cap = cv2.VideoCapture(str(self.video_path))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 限制分析帧数
        max_frames = min(int(max_duration * self.fps), self.frame_count)
        
        prev_frame = None
        scene_start = 0
        scene_frames = []
        
        for frame_idx in range(0, max_frames, int(self.fps)):  # 每秒采样一帧
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # 计算帧差
                diff = cv2.absdiff(prev_frame, gray)
                mean_diff = np.mean(diff)
                
                # 检测场景切换
                if mean_diff > threshold:
                    # 分析场景特征
                    scene_info = self._analyze_scene_frames(scene_frames)
                    
                    scenes.append({
                        'id': len(scenes),
                        'start': scene_start / self.fps,
                        'end': frame_idx / self.fps,
                        'duration': (frame_idx - scene_start) / self.fps,
                        'brightness': scene_info['brightness'],
                        'motion': scene_info['motion'],
                        'faces': scene_info['faces'],
                        'description': self._generate_scene_description(scene_info)
                    })
                    
                    scene_start = frame_idx
                    scene_frames = []
            
            scene_frames.append(gray)
            prev_frame = gray
        
        # 添加最后一个场景
        if scene_frames:
            scene_info = self._analyze_scene_frames(scene_frames)
            scenes.append({
                'id': len(scenes),
                'start': scene_start / self.fps,
                'end': max_frames / self.fps,
                'duration': (max_frames - scene_start) / self.fps,
                'brightness': scene_info['brightness'],
                'motion': scene_info['motion'],
                'faces': scene_info['faces'],
                'description': self._generate_scene_description(scene_info)
            })
        
        self.cap.release()
        return scenes
    
    def _analyze_scene_frames(self, frames: List[np.ndarray]) -> Dict:
        """分析场景帧的特征"""
        if not frames:
            return {'brightness': 0, 'motion': 0, 'faces': 0}
        
        # 计算平均亮度
        brightness = np.mean([np.mean(frame) for frame in frames])
        
        # 计算运动量（帧间差异）
        motion = 0
        if len(frames) > 1:
            diffs = []
            for i in range(1, len(frames)):
                diff = cv2.absdiff(frames[i-1], frames[i])
                diffs.append(np.mean(diff))
            motion = np.mean(diffs)
        
        # 检测人脸（简化版）
        faces = 0
        if frames:
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            # 只检测中间帧
            mid_frame = frames[len(frames)//2]
            detected_faces = face_cascade.detectMultiScale(mid_frame, 1.1, 4)
            faces = len(detected_faces)
        
        return {
            'brightness': float(brightness),
            'motion': float(motion),
            'faces': faces
        }
    
    def _generate_scene_description(self, scene_info: Dict) -> str:
        """生成场景描述"""
        desc_parts = []
        
        # 亮度描述
        if scene_info['brightness'] < 50:
            desc_parts.append("暗场景")
        elif scene_info['brightness'] < 150:
            desc_parts.append("正常光线")
        else:
            desc_parts.append("明亮场景")
        
        # 运动描述
        if scene_info['motion'] > 20:
            desc_parts.append("高动态")
        elif scene_info['motion'] > 10:
            desc_parts.append("中等动态")
        else:
            desc_parts.append("静态")
        
        # 人物描述
        if scene_info['faces'] > 0:
            desc_parts.append(f"{scene_info['faces']}人")
        
        return "，".join(desc_parts)
    
    def analyze_scene_composition(self, scene: Dict) -> Dict:
        """分析场景构图"""
        self.cap = cv2.VideoCapture(str(self.video_path))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # 获取场景中间帧
        mid_time = (scene['start'] + scene['end']) / 2
        frame_idx = int(mid_time * self.fps)
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        
        if not ret:
            self.cap.release()
            return {}
        
        height, width = frame.shape[:2]
        
        # 分析构图
        composition = {
            'rule_of_thirds': self._check_rule_of_thirds(frame),
            'symmetry': self._check_symmetry(frame),
            'leading_lines': self._detect_leading_lines(frame),
            'depth': self._analyze_depth(frame),
            'color_palette': self._extract_color_palette(frame)
        }
        
        self.cap.release()
        return composition
    
    def _check_rule_of_thirds(self, frame: np.ndarray) -> bool:
        """检查三分法构图"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 简化版：检查边缘是否集中在三分线附近
        h, w = edges.shape
        thirds_h = [h//3, 2*h//3]
        thirds_w = [w//3, 2*w//3]
        
        # 统计三分线附近的边缘点
        margin = 20
        edge_count = 0
        
        for y in thirds_h:
            edge_count += np.sum(edges[y-margin:y+margin, :])
        for x in thirds_w:
            edge_count += np.sum(edges[:, x-margin:x+margin])
        
        total_edges = np.sum(edges)
        return edge_count / (total_edges + 1) > 0.3
    
    def _check_symmetry(self, frame: np.ndarray) -> float:
        """检查对称性"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # 水平对称性
        left = gray[:, :w//2]
        right = cv2.flip(gray[:, w//2:], 1)
        
        # 调整大小使其相同
        min_w = min(left.shape[1], right.shape[1])
        left = left[:, :min_w]
        right = right[:, :min_w]
        
        # 计算相似度
        diff = cv2.absdiff(left, right)
        symmetry_score = 1 - (np.mean(diff) / 255)
        
        return float(symmetry_score)
    
    def _detect_leading_lines(self, frame: np.ndarray) -> int:
        """检测引导线"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 使用霍夫变换检测直线
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, 
                                minLineLength=100, maxLineGap=10)
        
        return len(lines) if lines is not None else 0
    
    def _analyze_depth(self, frame: np.ndarray) -> str:
        """分析景深"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算图像的模糊程度（拉普拉斯方差）
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        if variance < 100:
            return "浅景深"
        elif variance < 500:
            return "中景深"
        else:
            return "深景深"
    
    def _extract_color_palette(self, frame: np.ndarray) -> List[str]:
        """提取主色调"""
        # 缩小图像以加速处理
        small = cv2.resize(frame, (100, 100))
        
        # 转换为RGB
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        
        # 重塑为像素列表
        pixels = rgb.reshape(-1, 3)
        
        # 使用K-means聚类找到主色调
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=5, random_state=42)
        kmeans.fit(pixels)
        
        # 获取主色调
        colors = kmeans.cluster_centers_.astype(int)
        
        # 转换为十六进制颜色代码
        palette = []
        for color in colors:
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
            palette.append(hex_color)
        
        return palette