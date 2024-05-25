# 视频自动化项目后端

## 项目简介

本项目为前后端分离项目，可以完成视频的一些自动化处理

该仓库为项目后端，使用Python Django DRF框架完成

项目集成了视频自动化处理，该部分使用了Ffmpeg，Ffmpeg环境部分需要自动配置

### 主要工具：

- Django DRF
- Celery
- Ffmpeg

### API:

- 语音转文本：火山引擎
- 文本翻译：DeepL
- 文本转语音：微软云

## 项目启动

1. 启动Web

```shell
python manage.py 0.0.0.0
```

2. 启动Celery

```shell
celery -A celery_tasks.main worker --loglevel=info
```

