"""
剧本生成模块
根据场景和字幕生成专业格式的剧本
"""

from typing import List, Dict, Optional
from datetime import timedelta

class ScreenplayGenerator:
    """剧本生成器类"""
    
    def __init__(self):
        """初始化剧本生成器"""
        self.screenplay = ""
        
    def generate(self, scenes: List[Dict], 
                subtitles: List[Dict],
                video_info: Dict) -> str:
        """
        生成剧本
        
        Args:
            scenes: 场景列表
            subtitles: 字幕列表
            video_info: 视频信息
        
        Returns:
            剧本文本
        """
        # 同步字幕到场景
        scenes_with_dialogue = self._sync_subtitles_to_scenes(scenes, subtitles)
        
        # 分析三幕结构
        acts = self._analyze_three_act_structure(scenes_with_dialogue)
        
        # 生成剧本
        screenplay_parts = []
        
        # 标题页
        screenplay_parts.append(self._generate_title_page(video_info))
        
        # 角色列表
        characters = self._extract_characters(subtitles)
        if characters:
            screenplay_parts.append(self._generate_character_list(characters))
        
        # 三幕结构概述
        screenplay_parts.append(self._generate_act_summary(acts))
        
        # 详细场景剧本
        screenplay_parts.append(self._generate_detailed_screenplay(
            scenes_with_dialogue, acts
        ))
        
        # 统计信息
        screenplay_parts.append(self._generate_statistics(
            scenes_with_dialogue, subtitles
        ))
        
        self.screenplay = "\n\n".join(screenplay_parts)
        return self.screenplay
    
    def _sync_subtitles_to_scenes(self, scenes: List[Dict], 
                                  subtitles: List[Dict]) -> List[Dict]:
        """将字幕同步到场景"""
        scenes_with_dialogue = []
        
        for scene in scenes:
            scene_copy = scene.copy()
            scene_copy['dialogues'] = []
            
            # 查找属于该场景的字幕
            for subtitle in subtitles:
                if (subtitle['start'] >= scene['start'] and 
                    subtitle['start'] < scene['end']):
                    scene_copy['dialogues'].append({
                        'time': subtitle['start'] - scene['start'],
                        'text': subtitle['text'],
                        'speaker': self._identify_speaker(subtitle['text'])
                    })
            
            scenes_with_dialogue.append(scene_copy)
        
        return scenes_with_dialogue
    
    def _analyze_three_act_structure(self, scenes: List[Dict]) -> Dict:
        """分析三幕结构"""
        total_scenes = len(scenes)
        
        # 按照经典三幕结构划分（25%-50%-25%）
        act1_end = int(total_scenes * 0.25)
        act2_end = int(total_scenes * 0.75)
        
        acts = {
            '第一幕': {
                'scenes': scenes[:act1_end],
                'type': '开端',
                'description': '故事背景介绍，人物登场'
            },
            '第二幕': {
                'scenes': scenes[act1_end:act2_end],
                'type': '发展',
                'description': '冲突展开，情节推进'
            },
            '第三幕': {
                'scenes': scenes[act2_end:],
                'type': '高潮与结局',
                'description': '矛盾激化，故事收尾'
            }
        }
        
        return acts
    
    def _extract_characters(self, subtitles: List[Dict]) -> List[str]:
        """提取角色名称"""
        characters = set()
        
        for subtitle in subtitles:
            text = subtitle['text']
            
            # 简单的角色识别规则
            # 1. 查找冒号前的文字（如 "张三：你好"）
            if '：' in text or ':' in text:
                parts = text.replace(':', '：').split('：')
                if len(parts) > 1:
                    character = parts[0].strip()
                    if len(character) <= 10:  # 角色名不太长
                        characters.add(character)
            
            # 2. 查找常见姓氏
            for surname in ['张', '王', '李', '赵', '刘', '陈', '杨', '黄']:
                if surname in text:
                    # 尝试提取可能的人名
                    import re
                    pattern = f'{surname}[\\u4e00-\\u9fa5]{{1,2}}'
                    matches = re.findall(pattern, text)
                    for match in matches:
                        if 2 <= len(match) <= 3:
                            characters.add(match)
        
        return sorted(list(characters))
    
    def _identify_speaker(self, text: str) -> str:
        """识别说话人"""
        # 如果文本包含角色标记
        if '：' in text or ':' in text:
            parts = text.replace(':', '：').split('：')
            if len(parts) > 1:
                return parts[0].strip()
        
        # 根据内容特征判断
        if text.startswith('（') or text.startswith('('):
            return '旁白'
        
        return '未知'
    
    def _generate_title_page(self, video_info: Dict) -> str:
        """生成标题页"""
        title = f"""
{"="*80}
                            剧 本
{"="*80}

片名: {video_info.get('filename', '未知')}
时长: {video_info.get('duration_str', '未知')}
格式: {video_info.get('width', 0)}x{video_info.get('height', 0)} @ {video_info.get('fps', 0):.1f}fps

{"="*80}
"""
        return title
    
    def _generate_character_list(self, characters: List[str]) -> str:
        """生成角色列表"""
        if not characters:
            return ""
        
        char_list = "【主要角色】\n" + "-"*40 + "\n"
        for i, char in enumerate(characters, 1):
            char_list += f"{i}. {char}\n"
        
        return char_list
    
    def _generate_act_summary(self, acts: Dict) -> str:
        """生成三幕概述"""
        summary = "【三幕结构】\n" + "="*40 + "\n\n"
        
        for act_name, act_data in acts.items():
            total_duration = sum(s.get('duration', 0) for s in act_data['scenes'])
            dialogue_count = sum(len(s.get('dialogues', [])) for s in act_data['scenes'])
            
            summary += f"{act_name} - {act_data['type']}\n"
            summary += f"  场景数: {len(act_data['scenes'])}\n"
            summary += f"  时长: {timedelta(seconds=int(total_duration))}\n"
            summary += f"  对话数: {dialogue_count}\n"
            summary += f"  {act_data['description']}\n\n"
        
        return summary
    
    def _generate_detailed_screenplay(self, scenes: List[Dict], 
                                     acts: Dict) -> str:
        """生成详细剧本"""
        screenplay = "【详细剧本】\n" + "="*80 + "\n\n"
        
        scene_number = 1
        current_act = 1
        act_boundaries = [
            len(acts['第一幕']['scenes']),
            len(acts['第一幕']['scenes']) + len(acts['第二幕']['scenes'])
        ]
        
        for i, scene in enumerate(scenes):
            # 标记幕的开始
            if i == 0:
                screenplay += f"第一幕 - 开端\n" + "-"*40 + "\n\n"
            elif i == act_boundaries[0]:
                screenplay += f"\n第二幕 - 发展\n" + "-"*40 + "\n\n"
            elif i == act_boundaries[1]:
                screenplay += f"\n第三幕 - 高潮与结局\n" + "-"*40 + "\n\n"
            
            # 场景标题
            screenplay += f"场景 {scene_number}\n"
            screenplay += f"时间: {self._format_time(scene['start'])} - {self._format_time(scene['end'])}\n"
            
            # 场景描述
            location = self._determine_location(scene)
            time_of_day = self._determine_time_of_day(scene)
            screenplay += f"\n{location} - {time_of_day}\n\n"
            
            # 场景说明
            if 'description' in scene:
                screenplay += f"  {scene['description']}\n\n"
            
            # 对话
            if scene.get('dialogues'):
                for dialogue in scene['dialogues']:
                    speaker = dialogue.get('speaker', '未知')
                    if speaker != '未知':
                        screenplay += f"            {speaker.upper()}\n"
                    screenplay += f"        {dialogue['text']}\n\n"
            elif scene.get('faces', 0) > 0:
                # 有人物但没有对话
                screenplay += f"  [场景中有{scene['faces']}个人物，无对话]\n\n"
            
            screenplay += "-"*40 + "\n\n"
            scene_number += 1
        
        return screenplay
    
    def _generate_statistics(self, scenes: List[Dict], 
                            subtitles: List[Dict]) -> str:
        """生成统计信息"""
        stats = "【统计信息】\n" + "="*40 + "\n\n"
        
        # 场景统计
        total_duration = sum(s.get('duration', 0) for s in scenes)
        avg_scene_duration = total_duration / len(scenes) if scenes else 0
        
        stats += f"场景总数: {len(scenes)}\n"
        stats += f"总时长: {timedelta(seconds=int(total_duration))}\n"
        stats += f"平均场景时长: {avg_scene_duration:.1f}秒\n\n"
        
        # 对话统计
        total_dialogues = sum(len(s.get('dialogues', [])) for s in scenes)
        scenes_with_dialogue = sum(1 for s in scenes if s.get('dialogues'))
        
        stats += f"对话总数: {total_dialogues}\n"
        stats += f"有对话场景: {scenes_with_dialogue}/{len(scenes)}\n\n"
        
        # 场景类型分布
        bright_scenes = sum(1 for s in scenes if s.get('brightness', 0) > 150)
        dark_scenes = sum(1 for s in scenes if s.get('brightness', 0) < 50)
        action_scenes = sum(1 for s in scenes if s.get('motion', 0) > 20)
        
        stats += "场景类型分布:\n"
        stats += f"  明亮场景: {bright_scenes}\n"
        stats += f"  暗场景: {dark_scenes}\n"
        stats += f"  动作场景: {action_scenes}\n"
        
        return stats
    
    def _determine_location(self, scene: Dict) -> str:
        """判断场景地点"""
        brightness = scene.get('brightness', 100)
        
        if brightness < 50:
            return "内景"
        elif brightness > 150:
            return "外景"
        else:
            return "内景"
    
    def _determine_time_of_day(self, scene: Dict) -> str:
        """判断时间"""
        brightness = scene.get('brightness', 100)
        
        if brightness < 30:
            return "夜"
        elif brightness < 80:
            return "黄昏"
        elif brightness < 150:
            return "日"
        else:
            return "日"
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        return str(timedelta(seconds=int(seconds)))