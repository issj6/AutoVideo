import json
import os
import subprocess

import ffmpy


def split_video(input_file, output_file, start, end, without_audio=True, volume=None):
    """
    根据开始时间与时长分割视频，去除音频
    :param input_file:
    :param output_file:
    :param start:
    :param end:
    :param without_audio:
    :param volume:
    :return:
    """
    input_file_param = []
    if start:
        input_file_param.extend(['-ss', str(start)])
    if end:
        input_file_param.extend(['-to', str(end)])
    out_param = ['-an', '-loglevel', 'error'] if without_audio else ['-loglevel', 'error']
    if without_audio is False and volume:
        out_param = out_param.extend(['-filter:a', f'volume={volume}'])
    ff = ffmpy.FFmpeg(
        inputs={input_file: input_file_param},
        # outputs={f'{temp_folder}/video_{index}.mp4': [
        #     '-vcodec', 'copy', '-acodec', 'copy', '-an'
        # ]}
        outputs={output_file: out_param}
    )
    ff.run()


def split_audio(input_file, output_file, start, duration):
    """
    分割音频
    :param input_file:
    :param output_file:
    :param start:
    :param duration:
    :return:
    """
    ff = ffmpy.FFmpeg(
        inputs={input_file: [
            '-ss', str(start),
            '-t', str(duration),
        ]},
        outputs={output_file: ['-loglevel', 'error']}
    )
    ff.run()


def get_media_duration(input_file_path):
    """
    获取媒体时长
    :param input_file_path:
    :return:
    """
    ff = ffmpy.FFprobe(
        inputs={input_file_path: [
            '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'json'
        ]})
    video_info = ff.run(stdout=subprocess.PIPE)
    video_duration = json.loads(video_info[0].decode())['format']['duration']
    return video_duration


def concat_video(input_files_list, output_file, temp_folder):
    """
    合并视频
    :param input_files_list:
    :param output_file:
    :param temp_folder:
    :return:
    """
    # new_input_files_list = []
    # # 将无声视频添加静音音轨
    # for input_file in input_files_list:
    #     if "without_subtitle" in input_file and "with_audio" not in input_file:
    #         ff = ffmpy.FFmpeg(
    #             global_options=['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=24000'],
    #             inputs={input_file: None},
    #             outputs={
    #                 input_file.split('.')[0] + "_with_audio." + input_file.split('.')[1]: [
    #                     '-c:v', 'copy', '-c:a', 'pcm_s16le', '-ar', '24000', '-ac', '1', '-shortest', '-loglevel',
    #                     'error'
    #                 ]
    #             }
    #         )
    #         ff.run()
    #         new_input_files_list.append(input_file.split('.')[0] + "_with_audio." + input_file.split('.')[1])
    #     else:
    #         new_input_files_list.append(input_file)

    # print("待合成片段：", input_files_list)

    os.makedirs(temp_folder, exist_ok=True)
    concat_file = os.path.join(temp_folder, 'concat_list.txt')

    with open(concat_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join([
            f'file {video_path}' for video_path in input_files_list
        ]))

    ff = ffmpy.FFmpeg(
        global_options=['-f', 'concat'],
        inputs={concat_file: ['-safe', '0']},
        outputs={output_file: ['-c:v', 'copy', '-loglevel', 'error']}
    )
    ff.run()


def concat_video_and_audio(video_input_file, audio_input_file, output_file):
    """
    将视频与音频合并
    :param video_input_file:
    :param audio_input_file:
    :param output_file:
    :return:
    """
    video_duration = get_media_duration(video_input_file)
    audio_duration = get_media_duration(audio_input_file)

    # 如果音频时长大于视频时长，则将音频时长裁剪至与视频时长相同
    # if audio_duration > video_duration:
    #     new_audio = audio_input_file.split('.')[0] + '_split_time.' + audio_input_file.split('.')[1]
    #     split_audio(audio_input_file, new_audio, 0,
    #                 video_duration)
    #     audio_input_file = new_audio

    ff = ffmpy.FFmpeg(
        inputs={video_input_file: None, audio_input_file: None},
        outputs={output_file: [
            '-c:a', 'pcm_s16le', '-ar', '24000', '-ac', '1',
            # '-vf', f"drawtext=fontcolor=white:fontsize=50:text='{subtitle.strip('.'.strip(','))}':x=(w-text_w)/2:y=100",
            # '-y',
            '-shortest', '-af', 'apad', '-loglevel', 'error'
        ]}
    )

    ff.run()


def change_video_speed(input_file, output_file, speed=1.00):
    """
    视频变速
    :param input_file:
    :param output_file:
    :param speed:
    :return:
    """
    ff = ffmpy.FFmpeg(
        inputs={
            input_file: None
        },
        outputs={
            output_file: [
                '-vf', f'setpts=PTS*{speed}', '-loglevel', 'error'
            ]
        }
    )
    ff.run()


def video_add_subtitles(video_file, srt_file, output_file, subtitle_position, font_size, max_line=3):
    """ffmpeg -i final_video.mp4 -vf "subtitles=final_subtitles.srt:force_style='FontSize=30,WarpStyle=3,Alignment=6'" -c:a copy -y output.mp4"""
    ff = ffmpy.FFmpeg(
        inputs={video_file: None},
        outputs={output_file: ['-vf',
                               f"subtitles={srt_file}:force_style='FontSize={font_size},WarpStyle={max_line},Alignment={subtitle_position}'",
                               '-y', '-loglevel', 'error']}
    )

    ff.run()


# video_add_subtitles("/Users/yang/PycharmProjects/video_translation/files/20240221_01/final_video.mp4",
#                     "/Users/yang/PycharmProjects/video_translation/files/20240221_01/final_subtitles.srt",
#                     "/Users/yang/PycharmProjects/video_translation/files/20240221_01/output.mp4", 5, 28, max_line=3)

# 添加字幕
# ffmpeg -i final_video.mp4 -vf "subtitles=final_subtitles.srt:force_style='FontSize=40,WarpStyle=2'" -c:a copy output.mp4
