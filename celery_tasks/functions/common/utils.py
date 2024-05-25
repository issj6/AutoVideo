import json
import os
import re
import subprocess

import ffmpy


def subtitle_handler(content):
    """
    返回内容处理
    :param content:
    :return:
    """
    subtitles = []
    content = content['utterances']
    for item in content:
        text = item['text']
        start_time = item['start_time']
        end_time = item['end_time']
        subtitles.append({
            "text": text,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time
        })
    # for item in subtitle:
    #     print(item['time'], item['text'])
    return subtitles


def milliseconds_to_srt_time(milliseconds):
    """
    将毫秒转换为小时、分钟、秒和毫秒
    :param milliseconds:
    :return:
    """
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    # 格式化时间为SRT格式：hh:mm:ss,mmm
    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}'


def generate_srt(subtitles, output_file):
    """
    生成字幕文件
    :param subtitles:
    :param output_file:
    :return:
    """
    with open(output_file, 'w') as f:
        for i, subtitle in enumerate(subtitles, start=1):
            start_time = milliseconds_to_srt_time(subtitle['start_time'])
            end_time = milliseconds_to_srt_time(subtitle['end_time'])
            text = subtitle['text']
            # 写入字幕序号
            f.write(str(i) + '\n')
            # 写入时间轴
            f.write(f'{start_time} --> {end_time}\n')
            # 写入字幕内容
            f.write(text + '\n')
            # 写入空行分隔字幕
            f.write('\n')


def parse_srt_file(srt_file):
    """
    读取字幕文件
    :param srt_file:
    :return:
    """
    subs = []
    with open(srt_file, 'r') as file:
        lines = file.read().split('\n\n')
        for line in lines:
            if line.strip() != '':
                sub_dict = {}
                sub_lines = line.split('\n')
                sub_dict['time'] = sub_lines[1]
                sub_dict['text'] = ' '.join(sub_lines[2:])
                subs.append(sub_dict)
    return subs


def write_new_srt_file(subs, output_srt_file):
    """
    将翻译后的文件写成新的字幕文件
    :param subs:
    :param output_srt_file:
    :return:
    """
    with open(output_srt_file, 'w') as file:
        for index, subtitle in enumerate(subs, start=1):
            file.write(str(index) + '\n')
            file.write(subtitle['time'] + '\n')
            file.write(subtitle['text'] + '\n\n')


def convert_to_ms(time_string):
    """
    时间转换为毫秒
    :param time_string:
    :return:
    """
    hours, minutes, seconds, milliseconds = map(int, re.findall(r'\d+', time_string))
    ms = (hours * 3600 * 1000 + minutes * 60 * 1000 + seconds * 1000 + milliseconds)
    return ms


def delete_folder(folder_path):
    """
    删除文件夹和其中的文件
    :param folder_path:
    :return:
    """
    if os.path.exists(folder_path):
        # 删除文件夹内的所有文件
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                delete_folder(file_path)  # 递归删除子文件夹

        # 删除空文件夹
        os.rmdir(folder_path)
        print(f"文件夹 '{folder_path.split('/')[-1]}' 及其内部的文件已成功删除")
    else:
        print(f"文件夹 '{folder_path}' 不存在。")
