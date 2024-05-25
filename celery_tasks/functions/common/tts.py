import json
import os
from time import sleep

import requests
import zipfile

from pydub import AudioSegment
from tqdm import tqdm

from celery_tasks.functions.common.utils import convert_to_ms, generate_srt, milliseconds_to_srt_time


def create(content, voice, speed):
    url = "https://eastasia.customvoice.api.speech.microsoft.com/api/texttospeech/3.1-preview1/batchsynthesis"
    headers = {
        'Ocp-Apim-Subscription-Key': 'xxxxxx',
        'Content-Type': 'application/json'
    }

    data = {
        "displayName": "batch synthesis sample",
        "description": "my text test",
        "textType": "PlainText",
        "inputs": content,
        "properties": {
            "outputFormat": "riff-24khz-16bit-mono-pcm",
            "wordBoundaryEnabled": 'true',
            "sentenceBoundaryEnabled": 'true',
            "concatenateResult": 'false',
            "decompressOutputFiles": 'false',
            "timeToLive": "PT24H",
        },
        "synthesisConfig": {
            "voice": voice,
            "rate": speed,
            "pitch": "medium",
            "volume": "+50%"
        }
    }
    r = requests.post(url, headers=headers, json=data).json()
    # print(r)
    print(f"音频合成ID：{r['id']}")
    return r['id']


def query(c_id):
    url = f"https://eastasia.customvoice.api.speech.microsoft.com/api/texttospeech/3.1-preview1/batchsynthesis/{c_id}"
    headers = {
        'Ocp-Apim-Subscription-Key': 'xxxxxx'
    }
    r = requests.get(url, headers=headers).json()
    if r['status'] == "Succeeded":
        return r['outputs']['result']
    else:
        return None


def download_res(url, save_path):
    # 创建保存文件夹的路径
    os.makedirs(save_path, exist_ok=True)

    # 发送HTTP请求下载ZIP文件
    response = requests.get(url)

    # 保存ZIP文件到指定位置
    zip_path = os.path.join(save_path, "file.zip")
    with open(zip_path, "wb") as f:
        f.write(response.content)

    # 解压ZIP文件到指定位置
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(save_path)

    # 删除ZIP文件
    os.remove(zip_path)

    print("音频ZIP文件下载并解压完成！")


def text_to_speech(subtitles, base_folder, voice="en-US-AndrewNeural", speed=1.05, blank_time_rate=0.7,
                   total_duration=None,each_max_char=30):
    # 创建待合成文本列表
    contents = []
    for subtitle in subtitles:
        if subtitle['text'][-1] == '.':
            contents.append({"text": (subtitle['text'].strip('.') + ',')})
        elif subtitle['text'][-1] in ['?', '？', '!', '！', ';', '；', '、']:
            contents.append({"text": subtitle['text']})
        else:
            contents.append({"text": (subtitle['text'] + ',')})

    # 合成语音
    c_id = create(contents, voice, speed)
    sleep(3)
    while True:
        res_url = query(c_id)
        if res_url:
            download_res(res_url, f"{base_folder}/audio_results")
            break
        sleep(1)

    # 合成完成，开始处理
    print("开始处理音频...")
    audio_info = []
    last_end_time = 0
    audio_list = []
    flg_time = 0
    new_subtitles_info = []
    subtitles = tqdm(subtitles)
    subtitles.set_description("音频处理进度")
    for index, subtitle in enumerate(subtitles, start=1):
        audio_path = f"{base_folder}/audio_results/{str(index).zfill(4)}.wav"
        info_json_path = f"{base_folder}/audio_results/{str(index).zfill(4)}.word.json"
        new_audio_path = f"{base_folder}/audio_results/{str(index).zfill(4)}_new.wav"

        audio = AudioSegment.from_file(audio_path, format="wav")
        # 读取合成结果信息
        with open(info_json_path, 'r') as file:
            info_json = json.load(file)
        duration = end_time = info_json[-1]["AudioOffset"] + int(info_json[-1]["Duration"] * blank_time_rate)
        # 切割原音频
        audio_output = audio[:end_time]

        # 判断该字幕前有无空白，若有则创建对应时长的空白音频
        start_time, end_time = subtitle['time'].split(' --> ')
        start_time = convert_to_ms(start_time)
        end_time = convert_to_ms(end_time)
        if start_time > last_end_time:
            silence = AudioSegment.silent(start_time - last_end_time)
            audio_list.append(silence)
            flg_time += (start_time - last_end_time)
        last_end_time = end_time

        # 音频加入待合成列表
        audio_list.append(audio_output)
        # 创建新字幕文件
        # 每n个字符添加一个新字幕
        count = 0
        temp_content = ""
        next_start_time = flg_time + 0
        for i, subtitle_temp in enumerate(info_json):
            if i == (len(info_json) - 1):
                break
            curr_item_content = ((" " if (len(temp_content) != 0 and 'z' >= subtitle_temp['Text'][-1] >= 'A') else "") +
                                 subtitle_temp['Text'])
            if (count + len(curr_item_content)) > each_max_char:
                new_subtitles_info.append({
                    'text': temp_content,
                    'start_time': next_start_time,
                    'end_time': flg_time + info_json[i - 1]['AudioOffset'] + info_json[i - 1]['Duration']
                })
                next_start_time = flg_time + subtitle_temp['AudioOffset']
                temp_content = ""
                count = 0
            temp_content += curr_item_content
            count += len(curr_item_content)
        new_subtitles_info.append({
            'text': (temp_content + info_json[-1]['Text']).strip(',').strip('.').strip(';'),
            'start_time': next_start_time,
            'end_time': flg_time + info_json[-1]['AudioOffset'] + int(info_json[-1]['Duration'] * blank_time_rate)
        })

        # 导出新音频
        audio_output.export(new_audio_path, format="wav")
        audio_info.append({
            "text": subtitle['text'].strip(',').strip('.').strip(';'),
            "duration": duration,
            "start_time": flg_time,
            "end_time": flg_time + duration,
            "audio_path": new_audio_path
        })
        flg_time += duration

    # 加入最后的空白片段对应时长的空白音频
    if total_duration and (int(total_duration * 1000) > last_end_time):
        silence = AudioSegment.silent(int(total_duration * 1000) - last_end_time)
        audio_list.append(silence)
        flg_time += (int(total_duration * 1000) - last_end_time)

    # 根据字幕空白部分创建空白语音
    # last_end_time = 0
    # new_audio_list = []
    # flg_time = 0
    # for index, subtitle in enumerate(subtitles):
    #     start_time, end_time = subtitle['time'].split(' --> ')
    #     start_time = convert_to_ms(start_time)
    #     end_time = convert_to_ms(end_time)
    #
    #     # 如果有空白片段则创建空白音频
    #     if start_time > last_end_time:
    #         # 创建静音音频
    #         silence = AudioSegment.silent(start_time - last_end_time)
    #         new_audio_list.append(silence)
    #         flg_time += (start_time - last_end_time)
    #
    #     new_audio_list.append(audio_list[index])
    #     last_end_time = end_time
    #     new_subtitles.append({
    #         'text': audio_info[index]['text'].strip('.').strip(','),
    #         'start_time': flg_time,
    #         'end_time': flg_time + audio_info[index]['duration']
    #     })
    #     flg_time += audio_info[index]['duration']

    # 生成新字幕文件
    # print(new_subtitles_info)
    generate_srt(new_subtitles_info, f"{base_folder}/final_subtitles.srt")

    # 合并所有音频片段
    combined_audio = AudioSegment.empty()
    for audio in audio_list:
        combined_audio += audio

    combined_audio.export(f"{base_folder}/combined_audio.wav", format="wav")
    # print(f"音频处理完成，音频信息：{audio_info}")
    print(f"音频处理完成")
    print(f"合并音频路径：{base_folder}/combined_audio.wav")
    print(f"合并音频总时长：{milliseconds_to_srt_time(flg_time)}")

    return audio_info, f"{base_folder}/combined_audio.wav"
