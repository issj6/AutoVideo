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


def video_translation(task_object):
    original_filename = task_object.get('original_filename')
    task_id = task_object.get('id')

    args = json.loads(task_object.get('task_args'))
    source_lang = args['source_lang']
    target_lang = args['target_lang']
    speaker = args['speaker']
    check_subtitle = args['check_subtitle']
    o_audio = args['o_audio']
    new_subtitle = args['new_subtitle']
    each_max_char = args['each_max_char']
    font_size = args['font_size']
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
    video_path = os.path.join(base_folder, "original_video." + suffix)
    download_file(file_url, video_path)

    # 2.分离音频
    print("开始分离音频...")
    complete_video = VideoFileClip(video_path)
    audio_path = separate_audio(complete_video, base_folder=base_folder)

    # 3.识别字幕
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
    total_duration = float(get_media_duration(video_path))
    audio_info, combined_audio_path = text_to_speech(new_subtitles, base_folder, speed=voice_speed,
                                                     blank_time_rate=statement_interval_rate,
                                                     each_max_char=each_max_char,
                                                     total_duration=total_duration, voice=speaker)

    # 5.根据新音频时长与旧字幕时间处理视频
    print("开始处理视频...")
    os.makedirs(os.path.join(base_folder, "temp"), exist_ok=True)
    video_list = []
    last_end_time = "00:00:00.0"
    new_subtitles = tqdm(new_subtitles)
    new_subtitles.set_description("视频处理进度")
    for index, subtitle in enumerate(new_subtitles):
        start_time, end_time = subtitle['time'].split(' --> ')
        start_time = start_time.replace(',', '.')
        end_time = end_time.replace(',', '.')
        # 裁剪无字幕片段
        if convert_to_ms(start_time) > convert_to_ms(last_end_time):
            split_video(video_path, f"{base_folder}/temp/video_without_subtitle_{index}.mp4", last_end_time,
                        start_time)
            video_list.append(f"{base_folder}/temp/video_without_subtitle_{index}.mp4")

        # 分割视频
        split_video(video_path, f"{base_folder}/temp/video_{index}.mp4", start_time, end_time)

        temp_video = VideoFileClip(f"{base_folder}/temp/video_{index}.mp4")
        t = -0.03 if index % 2 == 0 else 0
        temp_video = temp_video.speedx(final_duration=float(get_media_duration(audio_info[index]['audio_path'])) + t)
        temp_video.write_videofile(f"{base_folder}/temp/video_change_speed_{index}.mp4", threads=16, logger=None)
        temp_video.close()

        video_list.append(f"{base_folder}/temp/video_change_speed_{index}.mp4")
        last_end_time = end_time

    split_video(video_path, f"{base_folder}/temp/video_without_subtitle_final.mp4", last_end_time, None)
    video_list.append(f"{base_folder}/temp/video_without_subtitle_final.mp4")
    # 合并视频片段
    print("视频处理完成，开始合并视频片段...")
    concat_video(video_list, f"{base_folder}/combined_video.mp4", temp_folder=f"{base_folder}/temp")
    audio_duration = get_media_duration(combined_audio_path)
    combined_video_temp = VideoFileClip(f"{base_folder}/combined_video.mp4")
    combined_video_temp = combined_video_temp.speedx(final_duration=float(audio_duration))
    combined_video_temp.write_videofile(f"{base_folder}/temp/combined_video_change_speed.mp4", threads=16, logger=None)
    combined_video_temp.close()

    print("开始合并音视频...")
    concat_video_and_audio(f"{base_folder}/temp/combined_video_change_speed.mp4", combined_audio_path,
                           f"{base_folder}/final_video.mp4")
    print(f"合并完成，视频已保存至：{base_folder}/final_video.mp4")
    res_video_path = f"{base_folder}/final_video.mp4"

    if new_subtitle != "no":
        print("开始添加字幕...")
        position_dict = {
            "left-bottom": 1,
            "center-bottom": 2,
            "right-bottom": 3,
            "center-left": 9,
            "center-center": 10,
            "center-right": 11,
            "left-top": 5,
            "center-top": 6,
            "right-top": 7,
        }
        video_add_subtitles(f"{base_folder}/final_video.mp4", f"{base_folder}/final_subtitles.srt",
                            f"{base_folder}/final_video_with_subtitle.mp4", position_dict[new_subtitle], font_size, 3)
        res_video_path = f"{base_folder}/final_video_with_subtitle.mp4"
        print("开始添加字幕...")

    # 6.上传aliyun oss
    print("处理完成，开始上传aliyun oss...")
    new_filename = str(uuid.uuid4()) + ".mp4"
    upload_alioss_from_file(new_filename, res_video_path)

    # 7.写入数据库
    task.task_status = 3
    task.end_processing_time = datetime.datetime.now()
    task.res_file = new_filename
    task.save()

    # 8.删除临时文件夹
    delete_folder(base_folder)
