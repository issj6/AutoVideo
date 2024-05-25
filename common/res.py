from rest_framework.response import Response


class Res(Response):
    def __init__(self, code=200, msg='OK', data=None, status=None, headers=None, content_type=None, **kwargs):
        dic = {'code': code, 'msg': msg}
        if data:
            dic['data'] = data

        dic.update(kwargs)  # 这里使用update
        super().__init__(data=dic, status=status,
                         template_name=None, headers=headers,
                         exception=False, content_type=content_type)
