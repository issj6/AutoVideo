import os.path

import ffmpy
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip


def separate_audio(complete_video, base_folder):
    """
    分离音频，返回分离音频的路径
    :param complete_video:
    :param base_folder:
    :return:
    """
    audio_path = os.path.join(base_folder, "complete_audio_without_video.wav")

    audio = complete_video.audio
    audio.write_audiofile(audio_path)

    return audio_path


def set_video_mosaic(input_file, output_file, base_folder):
    """
    视频添加马赛克
    :param input_file:
    :param output_file:
    :param base_folder:
    :return:
    """

    image_path = f"{base_folder}/temp_image.jpg"
    ff = ffmpy.FFmpeg(
        inputs={input_file: ['-ss', '00:00:01']},
        outputs={image_path: ['-vframes', '1', '-loglevel', 'error']}
    )
    ff.run()

    mosaic_position = get_mosaic_position(image_path)

    output_param = ['-filter_complex']
    mosaic_param = ",".join([f"delogo=x=1:y={p['y']}:w=1918:h={1080 - p['y'] - 1}" for p in mosaic_position])
    output_param.append(mosaic_param)
    output_param.extend(['-loglevel', 'error'])

    ff = ffmpy.FFmpeg(
        inputs={input_file: None},
        outputs={output_file: output_param}
    )
    ff.run()

    os.remove(image_path)
