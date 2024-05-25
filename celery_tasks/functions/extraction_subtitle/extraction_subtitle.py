import datetime
import json
import os
import uuid
from time import sleep

from moviepy.editor import VideoFileClip
from tqdm import tqdm

from autovideo import settings
from celery_tasks.alioss.tasks import upload_alioss_from_file
from celery_tasks.functions.common import stt
from celery_tasks.functions.common.common_utils import download_file
from celery_tasks.functions.common.ffmpeg_utils import get_media_duration, split_video, concat_video, \
    concat_video_and_audio, video_add_subtitles
from celery_tasks.functions.common.subtitle_translation import translation
from celery_tasks.functions.common.tts import text_to_speech
from celery_tasks.functions.common.utils import generate_srt, parse_srt_file, write_new_srt_file, convert_to_ms, \
    delete_folder
from celery_tasks.functions.common.video_hand import separate_audio
from common.alioss import sign_url
from tasks.models import Task


def extraction_subtitle(task_object):
    original_filename = task_object.get('original_filename')
    task_id = task_object.get('id')

    args = json.loads(task_object.get('task_args'))
    source_lang = args['source_lang']
    each_max_char = args['each_max_char']

    task = Task.objects.get(pk=task_id)
    while not task.source_file:
        sleep(3)
        task = Task.objects.get(pk=task_id)
    source_file = task.source_file
    task.task_status = 2
    task.start_processing_time = datetime.datetime.now()
    task.save()

    # 临时文件夹/变量
    temp_files_storage = settings.TEMP_FILE_STORAGE_PATH
    base_folder = os.path.join(temp_files_storage, f"task_{task_id}")
    if not os.path.exists(base_folder):
        os.mkdir(base_folder)
    filename = original_filename.rsplit('.')[0]
    suffix = original_filename.rsplit('.')[-1]

    print("Start Processing ...")

    # 1.下载文件
    file_url = sign_url(source_file)
    video_path = os.path.join(base_folder, "original_video." + suffix)
    download_file(file_url, video_path)

    # 2.分离音频
    print("开始分离音频...")
    complete_video = VideoFileClip(video_path)
    audio_path = separate_audio(complete_video, base_folder=base_folder)

    # 3.识别字幕
    print("开始识别字幕...")
    srt_path = f"{base_folder}/{filename}_{source_lang}.srt"
    subtitles = stt.speech_to_subtitle(audio_path, language=source_lang, words_per_line=each_max_char)
    # 生成srt字幕文件
    generate_srt(subtitles, srt_path)

    # 6.上传aliyun oss
    print("处理完成，开始上传aliyun oss...")
    new_filename = str(uuid.uuid4()) + ".srt"
    upload_alioss_from_file(new_filename, srt_path)

    # 7.写入数据库
    task.task_status = 3
    task.end_processing_time = datetime.datetime.now()
    task.res_file = new_filename
    task.save()

    # 8.删除临时文件夹
    delete_folder(base_folder)
