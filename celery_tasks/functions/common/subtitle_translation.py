# deppl账号：
# bayoupierre1@gmail.com
# 65vy3fqv8z
# 密钥:708feea9-a7ae-b324-b747-99893a95c0df:fx
import requests


def translation(subtitles, target_lang="EN"):
    """
    字幕翻译
    :param subtitles:
    :param target_lang:
    :return:
    """
    text_list = [subtitle['text'] for subtitle in subtitles]
    base_url = "https://api-free.deepl.com"
    url = f"{base_url}/v2/translate"

    headers = {
        'Host': 'api-free.deepl.com',
        'Authorization': 'DeepL-Auth-Key 708feea9-a7ae-b324-b747-99893a95c0df:fx',
        'Content-Type': 'application/json'
    }

    data = {"text": text_list, "target_lang": target_lang}
    r = requests.post(url, headers=headers, json=data).json()

    # 将原字幕的时间与翻译结果组合成新的字幕
    new_subtitles = []
    for index, subtitle in enumerate(subtitles):
        new_subtitles.append({
            'time': subtitle['time'],
            'text': r['translations'][index]['text']
        })
    return new_subtitles
