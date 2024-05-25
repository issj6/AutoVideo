import os
from uuid import uuid4

from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ViewSet

from celery_tasks.alioss.tasks import upload_alioss_from_file, delete_alioss_file
from common import alioss
from common.res import Res
from files.models import File
from files.ser import FileUploadSerializer, FileSerializer


# Create your views here.

class FileView(ViewSet):
    """
    文件视图
    """

    def upload(self, request):
        """
        上传文件
        :param request:
        :return:
        """
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():

            uploaded_file = serializer.validated_data['file']
            # new_filename = serializer.validated_data['filename'] + os.path.splitext(uploaded_file.name)[1]
            filename = uploaded_file.name
            file_size = uploaded_file.size
            file_content_type = uploaded_file.content_type

            if file_size > 2048 * 1024 * 1024:
                return Res(400, "文件大小不能超过2G")

            # 设置保存文件的路径
            # file_path = os.path.join('/Users/yang/Desktop', new_filename)
            uuid = uuid4()
            save_name = str(uuid) + os.path.splitext(filename)[1]
            file_path = os.path.join('/Users/yang/Desktop', save_name)

            # 保存文件到本地
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # 上传aliyun oss
            # res = alioss.upload(uploaded_file.open(), save_name)
            res = upload_alioss_from_file.delay(save_name, file_path)

            file = File.objects.create(
                filename=filename,
                save_name=save_name,
                file_path=file_path if file_path else None,
                file_type=file_content_type,
                user=request.user
            )

            return Res(200, "上传成功", {
                "file_id": file.id,
                "filename": filename,
                "save_name": save_name,
                "file_size": file_size,
                "file_content_type": file_content_type
            })
        else:
            return Res(400, "上传失败", serializer.errors)

    def get_files(self, request):
        """
        分页查询用户所属文件
        :param request:
        :return:
        """
        user = request.user
        files = File.objects.filter(user=user).order_by('-upload_time')

        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size')
        result_page = paginator.paginate_queryset(files, request)

        serializer = FileSerializer(instance=result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def delete_file(self, request, fid):
        """
        删除所属文件
        :param request:
        :param fid:
        :return:
        """
        file = File.objects.filter(pk=fid).first()
        if not file:
            return Res(400, "文件不存在")
        if file.user_id != request.user.id:
            return Res(400, "无该文件所属权")

        # 删除本地文件和aliyun oss文件
        if file.file_path and os.path.exists(file.file_path):
            os.remove(file.file_path)
        delete_alioss_file.delay(file.save_name)

        file.delete()
        return Res(200, "删除成功")

    def get_down_url(self, request, fid):
        """
        获取文件下载url
        :param request:
        :param fid:
        :return:
        """
        file = File.objects.filter(pk=fid).first()
        if not file:
            return Res(400, "文件不存在")
        if file.user_id != request.user.id:
            return Res(400, "无该文件所属权")

        # 获取签名URL，可通过url下载文件，有效期60s
        aliyun_oss_url = alioss.sign_url(file.save_name)
        return Res(200, "ok", {"download_url": aliyun_oss_url})
