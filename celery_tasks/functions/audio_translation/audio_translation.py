import datetime
import json
import os
import uuid
from time import sleep

from autovideo import settings
from celery_tasks.alioss.tasks import upload_alioss_from_file
from celery_tasks.functions.common import stt
from celery_tasks.functions.common.common_utils import download_file
from celery_tasks.functions.common.subtitle_translation import translation
from celery_tasks.functions.common.tts import text_to_speech
from celery_tasks.functions.common.utils import generate_srt, parse_srt_file, write_new_srt_file, delete_folder
from common.alioss import sign_url
from tasks.models import Task


def audio_translation(task_object):
    original_filename = task_object.get('original_filename')
    task_id = task_object.get('id')

    args = json.loads(task_object.get('task_args'))
    source_lang = args['source_lang']
    target_lang = args['target_lang']
    speaker = args['speaker']
    voice_speed = float(args['voice_speed'])
    statement_interval_rate = float(args['statement_interval_rate']) - 0.25

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

    # 1.下载文件
    file_url = sign_url(source_file)
    audio_path = os.path.join(base_folder, "original_audio." + suffix)
    download_file(file_url, audio_path)

    # 2.识别字幕
    print("开始识别字幕...")
    srt_path = f"{base_folder}/{filename}_{source_lang}.srt"
    subtitles = stt.speech_to_subtitle(audio_path,language=source_lang)
    # 生成srt字幕文件
    generate_srt(subtitles, srt_path)

    # 3.翻译字幕
    print("开始翻译字幕...")
    target_lang = target_lang.split('-')[0].upper()
    # 读取核对后的字幕文件
    original_subtitles = parse_srt_file(srt_path)
    # 翻译字幕形成新的字幕
    new_subtitles = translation(original_subtitles, target_lang=target_lang)
    # 将新的字幕写入新的字幕文件
    write_new_srt_file(new_subtitles, f"{base_folder}/{filename}_{str.lower(target_lang)}.srt")

    # 4.新字幕合成语音
    print("开始合成音频...")
    audio_info, combined_audio_path = text_to_speech(new_subtitles, base_folder, speed=voice_speed,
                                                     blank_time_rate=statement_interval_rate,
                                                     each_max_char=100, voice=speaker)

    # 5.上传aliyun oss
    print("处理完成，开始上传aliyun oss...")
    new_filename = str(uuid.uuid4()) + ".wav"
    upload_alioss_from_file(new_filename, combined_audio_path)

    # 6.写入数据库
    task.task_status = 3
    task.end_processing_time = datetime.datetime.now()
    task.res_file = new_filename
    task.save()

    # 7.删除临时文件夹
    delete_folder(base_folder)
