# Movie Analyzer Pro 🎬

专业的电影分析与剪辑系统，支持中文视频分析，同时支持韩语、英语等多语言。

## 功能特点 ✨

### 核心功能
- 🔍 **智能内容识别** - 自动检测并跳过片头、片尾、广告等非正片内容
- 🎭 **智能场景检测** - 自动识别场景变化，分析场景特征
- 📝 **多语言字幕提取** - 支持嵌入字幕、OCR识别、语音识别（Whisper）
- 📜 **专业剧本生成** - 自动生成三幕结构剧本，包含场景描述和对话
- ✨ **精彩片段检测** - 基于运动、色彩、人物等多维度检测精彩片段
- 🎤 **智能解说生成** - 自动生成专业解说词，支持多种风格
- 🎬 **视频剪辑导出** - 自动剪辑精彩片段，生成预告片

### 支持格式
- 视频：MP4, MKV, AVI, MOV, FLV等
- 字幕：SRT, ASS, VTT
- 音频：AAC, MP3, WAV

### 语言支持
- 🇨🇳 中文（主要）
- 🇰🇷 韩语
- 🇺🇸 英语
- 🇯🇵 日语
- 🌍 自动检测

## 安装 📦

### 系统要求
- Python 3.8+
- FFmpeg
- 4GB+ RAM（推荐8GB）

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/movie-analyzer-pro.git
cd movie-analyzer-pro

# 安装Python依赖
pip install -r requirements.txt

# 安装系统依赖（macOS）
brew install ffmpeg

# 安装系统依赖（Ubuntu/Debian）
sudo apt-get install ffmpeg

# 安装可选依赖（语音识别）
pip install openai-whisper

# 安装可选依赖（OCR）
pip install pytesseract
brew install tesseract  # macOS
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim  # Ubuntu
```

## 快速开始 🚀

### 基础使用

```bash
# 分析中文视频（默认）
python movie_analyzer_pro.py your_video.mp4

# 分析韩语视频
python movie_analyzer_pro.py korean_movie.mkv --language ko

# 生成5分钟精彩片段
python movie_analyzer_pro.py your_video.mp4 --highlights 300

# 导出字幕
python movie_analyzer_pro.py your_video.mp4 --subtitles --format srt
```

### 高级选项

```bash
python movie_analyzer_pro.py video.mp4 \
    --language zh \              # 语言（zh/ko/en/ja/auto）
    --duration 600 \             # 分析时长限制（秒）
    --output results \           # 输出目录
    --highlights 180 \           # 生成3分钟精彩片段
    --subtitles \                # 导出字幕
    --format srt                # 字幕格式
```

## 项目结构 📁

```
movie-analyzer-pro/
├── movie_analyzer_pro.py      # 主程序入口
├── modules/                    # 功能模块
│   ├── __init__.py
│   ├── video_processor.py     # 视频处理
│   ├── scene_analyzer.py      # 场景分析
│   ├── subtitle_extractor.py  # 字幕提取
│   ├── screenplay_generator.py # 剧本生成
│   ├── highlight_detector.py  # 精彩检测
│   └── narration_generator.py # 解说生成
├── output/                     # 输出目录
│   ├── analysis_results.json  # 分析结果
│   ├── screenplay.txt         # 生成剧本
│   ├── narration.txt          # 解说词
│   ├── highlights_*.mp4       # 精彩片段
│   └── subtitles.*            # 字幕文件
├── requirements.txt            # 依赖列表
└── README.md                   # 说明文档
```

## 使用示例 💡

### 1. 完整电影分析

```python
from movie_analyzer_pro import MovieAnalyzerPro

# 创建分析器
analyzer = MovieAnalyzerPro("movie.mp4", "output")

# 分析视频
results = analyzer.analyze_video(language="zh", duration_limit=600)

# 生成精彩片段
analyzer.create_highlight_video(duration=300, with_narration=True)

# 导出字幕
analyzer.export_subtitles(format="srt", bilingual=True)
```

### 2. 批量处理

```bash
# 批量分析多个视频
for video in *.mp4; do
    python movie_analyzer_pro.py "$video" --language auto
done
```

### 3. 自定义分析

```python
# 只进行场景分析
from modules.scene_analyzer import SceneAnalyzer

analyzer = SceneAnalyzer("video.mp4")
scenes = analyzer.detect_scenes(max_duration=600, threshold=30.0)
```

## 输出说明 📊

### 分析结果 (analysis_results.json)
```json
{
  "video_info": {
    "filename": "movie.mp4",
    "duration": 7200,
    "resolution": "1920x1080",
    "fps": 24.0
  },
  "scenes": [...],
  "subtitles": [...],
  "highlights": [...],
  "screenplay": "...",
  "narration": "..."
}
```

### 剧本格式
```
================================================================================
                            剧 本
================================================================================

场景 1
时间: 0:00:00 - 0:00:24

内景 - 夜

  黑暗的场景，静态

            角色A
        这是一段对话...

----------------------------------------
```

## 性能优化 ⚡

### 处理大文件
- 使用 `--duration` 限制分析时长
- 分段处理长视频
- 调整场景检测阈值

### 提高准确度
- 使用更大的Whisper模型：`medium` 或 `large`
- 调整OCR语言设置
- 手动校对生成的字幕

## 常见问题 ❓

### Q: 支持哪些视频格式？
A: 支持FFmpeg能处理的所有格式，包括MP4、MKV、AVI、MOV等。

### Q: 如何提高字幕识别准确度？
A: 
1. 使用Whisper的更大模型
2. 确保音频质量清晰
3. 指定正确的语言参数

### Q: 内存不足怎么办？
A: 
1. 减少分析时长 `--duration 300`
2. 降低视频分辨率
3. 分段处理视频

### Q: 如何处理无字幕视频？
A: 系统会自动尝试：
1. 语音识别（Whisper）
2. OCR识别硬字幕
3. 生成模拟对话

## 贡献指南 🤝

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black modules/
```

## 许可证 📄

MIT License

## 致谢 🙏

- FFmpeg - 视频处理
- OpenAI Whisper - 语音识别
- OpenCV - 计算机视觉
- MoviePy - 视频编辑
- Edge-TTS - 语音合成

## 联系方式 📧

- Issue: [GitHub Issues](https://github.com/yourusername/movie-analyzer-pro/issues)
- Email: your-email@example.com

---

Made with ❤️ by Movie Analyzer Pro Team