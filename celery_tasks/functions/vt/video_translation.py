import os

from moviepy.editor import VideoFileClip

from autovideo import settings
from celery_tasks.functions.common import stt
from celery_tasks.functions.common.common_utils import download_file
from celery_tasks.functions.common.utils import generate_srt
from celery_tasks.functions.common.video_hand import separate_audio


def video_translation(file_url, file_name_all, args=None):
    source_lang = args['source_lang']
    target_lang = args['target_lang']
    speaker = args['speaker']
    check_subtitle = args['check_subtitle']
    o_audio = args['o_audio']
    new_subtitle = args['new_subtitle']
    voice_speed = args['voice_speed']

    # 临时文件夹
    temp_files_storage = settings.TEMP_FILE_STORAGE_PATH
    filename = file_name_all.split('.')[0]

    # 1.下载文件
    base_folder = os.path.join(temp_files_storage, file_name_all.split('.')[0])
    video_path = os.path.join(base_folder, "original_video.mp4")
    download_file(file_url, video_path)

    # 2.分离音频
    print("开始分离音频...")
    complete_video = VideoFileClip(video_path)
    audio_path = separate_audio(complete_video, base_folder=base_folder)

    # 3.识别字幕
    print("开始识别字幕...")
    srt_path = f"{base_folder}/{filename}_{source_lang}.srt"
    subtitles = stt.speech_to_subtitle(audio_path)
    # 生成srt字幕文件
    generate_srt(subtitles, srt_path)
    print(f"识别字幕完成，请前往核对并修改，字幕文件路径：{srt_path}")


def test():
    file_url = "https://autovideo-yang0000111.oss-cn-beijing.aliyuncs.com/fc8f23ef-a99a-4830-9f7a-25e443d921f2.mp4?Expires=1711216782&OSSAccessKeyId=TMP.3Kg5ouw1K34mNNAWmgjbfBgXewFYz635rjgbXBsfGzArKxLwzeFXPHKtwGUFSEEqrbgJ6EHeJFwLttxoXKcUPhrPW37EpB&Signature=dv6QWdj8WpwDfJUhCFQbHesEP78%3D"
    video_translation(file_url)


test()
