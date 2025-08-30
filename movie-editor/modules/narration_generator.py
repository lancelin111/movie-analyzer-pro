"""
解说词生成模块
根据场景和字幕生成解说词
"""

from typing import List, Dict, Optional
from datetime import timedelta

class NarrationGenerator:
    """解说词生成器类"""
    
    def __init__(self):
        """初始化解说词生成器"""
        self.narration = ""
        
    def generate(self, scenes: List[Dict],
                subtitles: List[Dict],
                highlights: List[Dict],
                style: str = "professional") -> str:
        """
        生成解说词
        
        Args:
            scenes: 场景列表
            subtitles: 字幕列表
            highlights: 精彩片段列表
            style: 解说风格 (professional/casual/humorous)
        
        Returns:
            解说词文本
        """
        # 分析内容
        content_analysis = self._analyze_content(scenes, subtitles)
        
        # 根据风格生成解说词
        if style == "professional":
            narration = self._generate_professional_narration(
                content_analysis, scenes, highlights
            )
        elif style == "casual":
            narration = self._generate_casual_narration(
                content_analysis, scenes, highlights
            )
        elif style == "humorous":
            narration = self._generate_humorous_narration(
                content_analysis, scenes, highlights
            )
        else:
            narration = self._generate_professional_narration(
                content_analysis, scenes, highlights
            )
        
        self.narration = narration
        return narration
    
    def _analyze_content(self, scenes: List[Dict],
                        subtitles: List[Dict]) -> Dict:
        """分析内容特征"""
        analysis = {
            'total_scenes': len(scenes),
            'total_duration': sum(s.get('duration', 0) for s in scenes),
            'dialogue_count': len(subtitles),
            'scene_types': {},
            'mood': self._analyze_mood(scenes),
            'pacing': self._analyze_pacing(scenes),
            'genre': self._guess_genre(scenes, subtitles)
        }
        
        # 统计场景类型
        for scene in scenes:
            scene_type = self._classify_scene_type(scene)
            analysis['scene_types'][scene_type] = \
                analysis['scene_types'].get(scene_type, 0) + 1
        
        return analysis
    
    def _analyze_mood(self, scenes: List[Dict]) -> str:
        """分析整体氛围"""
        avg_brightness = np.mean([s.get('brightness', 100) for s in scenes])
        avg_motion = np.mean([s.get('motion', 0) for s in scenes])
        
        if avg_brightness < 50:
            if avg_motion > 15:
                return "紧张刺激"
            else:
                return "阴郁神秘"
        elif avg_brightness < 150:
            if avg_motion > 15:
                return "动感活力"
            else:
                return "平和自然"
        else:
            return "明快轻松"
    
    def _analyze_pacing(self, scenes: List[Dict]) -> str:
        """分析节奏"""
        avg_duration = np.mean([s.get('duration', 0) for s in scenes])
        
        if avg_duration < 5:
            return "快节奏"
        elif avg_duration < 15:
            return "中等节奏"
        else:
            return "慢节奏"
    
    def _guess_genre(self, scenes: List[Dict],
                     subtitles: List[Dict]) -> str:
        """猜测类型"""
        # 基于场景和对话特征猜测
        avg_motion = np.mean([s.get('motion', 0) for s in scenes])
        face_scenes = sum(1 for s in scenes if s.get('faces', 0) > 0)
        
        if avg_motion > 20:
            return "动作片"
        elif face_scenes / len(scenes) > 0.7:
            if len(subtitles) / len(scenes) > 2:
                return "剧情片"
            else:
                return "爱情片"
        else:
            return "纪录片"
    
    def _classify_scene_type(self, scene: Dict) -> str:
        """分类场景类型"""
        if scene.get('motion', 0) > 20:
            return "动作场景"
        elif scene.get('faces', 0) > 2:
            return "群体场景"
        elif scene.get('faces', 0) > 0:
            return "人物场景"
        else:
            return "环境场景"
    
    def _generate_professional_narration(self, analysis: Dict,
                                        scenes: List[Dict],
                                        highlights: List[Dict]) -> str:
        """生成专业解说词"""
        narration_parts = []
        
        # 开场白
        opening = self._generate_opening(analysis, "professional")
        narration_parts.append(opening)
        
        # 内容概述
        overview = self._generate_overview(analysis, scenes)
        narration_parts.append(overview)
        
        # 精彩片段介绍
        if highlights:
            highlight_intro = self._generate_highlight_introduction(highlights)
            narration_parts.append(highlight_intro)
        
        # 场景解说
        scene_narration = self._generate_scene_narration(scenes[:5])  # 前5个场景
        narration_parts.append(scene_narration)
        
        # 结束语
        closing = self._generate_closing(analysis, "professional")
        narration_parts.append(closing)
        
        return "\n\n".join(narration_parts)
    
    def _generate_casual_narration(self, analysis: Dict,
                                  scenes: List[Dict],
                                  highlights: List[Dict]) -> str:
        """生成轻松解说词"""
        narration_parts = []
        
        # 随意的开场
        opening = f"嘿，朋友们！今天给大家带来一部{analysis['genre']}，"
        opening += f"整体感觉{analysis['mood']}，节奏{analysis['pacing']}。"
        narration_parts.append(opening)
        
        # 简单介绍
        intro = f"这部片子有{analysis['total_scenes']}个场景，"
        intro += f"时长{timedelta(seconds=int(analysis['total_duration']))}。"
        narration_parts.append(intro)
        
        # 精彩推荐
        if highlights:
            reco = f"我特别推荐{len(highlights)}个精彩片段，绝对不容错过！"
            narration_parts.append(reco)
        
        return "\n\n".join(narration_parts)
    
    def _generate_humorous_narration(self, analysis: Dict,
                                    scenes: List[Dict],
                                    highlights: List[Dict]) -> str:
        """生成幽默解说词"""
        narration_parts = []
        
        # 幽默开场
        opening = f"各位观众老爷们好！今天咱们要聊的这部{analysis['genre']}，"
        opening += f"那叫一个{analysis['mood']}啊！"
        narration_parts.append(opening)
        
        # 调侃内容
        if analysis['pacing'] == "快节奏":
            joke = "剪辑师是不是喝了红牛？这节奏快得我眼睛都跟不上了！"
        elif analysis['pacing'] == "慢节奏":
            joke = "导演是想让我们修身养性吗？这节奏慢得我都想倍速播放了！"
        else:
            joke = "不快不慢，刚刚好，导演深谙中庸之道啊！"
        narration_parts.append(joke)
        
        return "\n\n".join(narration_parts)
    
    def _generate_opening(self, analysis: Dict, style: str) -> str:
        """生成开场白"""
        if style == "professional":
            opening = f"各位观众朋友，欢迎收看本期影片解析。"
            opening += f"今天我们要分析的是一部{analysis['genre']}，"
            opening += f"影片整体呈现{analysis['mood']}的氛围，"
            opening += f"采用{analysis['pacing']}的叙事手法。"
        else:
            opening = f"大家好！今天带来一部精彩的{analysis['genre']}。"
        
        return opening
    
    def _generate_overview(self, analysis: Dict,
                          scenes: List[Dict]) -> str:
        """生成内容概述"""
        overview = f"本片共包含{analysis['total_scenes']}个场景，"
        overview += f"总时长{timedelta(seconds=int(analysis['total_duration']))}。"
        
        # 场景类型分布
        if analysis['scene_types']:
            overview += "\n\n场景构成："
            for scene_type, count in analysis['scene_types'].items():
                percentage = (count / analysis['total_scenes']) * 100
                overview += f"\n  • {scene_type}: {count}个 ({percentage:.1f}%)"
        
        # 对话统计
        if analysis['dialogue_count'] > 0:
            overview += f"\n\n影片包含{analysis['dialogue_count']}段对话，"
            overview += f"平均每个场景{analysis['dialogue_count']/analysis['total_scenes']:.1f}段对话。"
        
        return overview
    
    def _generate_highlight_introduction(self, highlights: List[Dict]) -> str:
        """生成精彩片段介绍"""
        intro = f"本片精选了{len(highlights)}个精彩片段：\n\n"
        
        for i, highlight in enumerate(highlights[:5], 1):
            time_str = timedelta(seconds=int(highlight['start']))
            intro += f"{i}. [{time_str}] {highlight.get('reason', '精彩场景')}\n"
        
        return intro
    
    def _generate_scene_narration(self, scenes: List[Dict]) -> str:
        """生成场景解说"""
        narration = "场景解析：\n\n"
        
        for i, scene in enumerate(scenes, 1):
            time_str = timedelta(seconds=int(scene['start']))
            narration += f"场景{i} [{time_str}]：\n"
            
            # 场景描述
            if 'description' in scene:
                narration += f"  {scene['description']}\n"
            
            # 人物信息
            if scene.get('faces', 0) > 0:
                narration += f"  画面中出现{scene['faces']}个人物\n"
            
            # 对话信息
            if scene.get('dialogues'):
                narration += f"  包含{len(scene['dialogues'])}段对话\n"
            
            narration += "\n"
        
        return narration
    
    def _generate_closing(self, analysis: Dict, style: str) -> str:
        """生成结束语"""
        if style == "professional":
            closing = "以上就是本期的影片分析。"
            closing += f"这部{analysis['genre']}以其{analysis['mood']}的风格，"
            closing += f"为我们呈现了一个精彩的故事。"
            closing += "\n感谢您的收看，我们下期再见！"
        else:
            closing = "好了，今天的分享就到这里。"
            closing += "喜欢的话记得点赞关注哦！"
        
        return closing

# 导入numpy（如果需要的话）
try:
    import numpy as np
except ImportError:
    # 如果没有numpy，使用简单的替代
    class np:
        @staticmethod
        def mean(values):
            return sum(values) / len(values) if values else 0