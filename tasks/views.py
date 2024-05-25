import json
import os
from uuid import uuid4

from celery.result import AsyncResult
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin

from autovideo import settings
from celery_tasks.main import app
from common.alioss import sign_url
from common.pagination import CustomPagination
from common.res import Res
from files.ser import FileUploadSerializer
from tasks import models
from tasks.models import Function
from tasks.ser import TaskSerializer, TaskFileUploadSerializer, FunctionSerializer

from celery_tasks.alioss.tasks import delete_alioss_file, upload_alioss_from_file
from celery_tasks.video_processing.tasks import add_task


# Create your views here.


class TaskView(ViewSet):
    """
    任务视图
    """

    def retrieve(self, request, pk=None):
        user = request.user
        # 判断请求是否有效
        task = models.Task.objects.filter(pk=pk).first()
        if not task:
            return Res(400, "任务不存在")
        if task.user_id != user.id:
            return Res(400, "无该任务所属权")

        ser = TaskSerializer(instance=task)
        return Res(200, "ok", ser.data)

    def create(self, request):
        user = request.user

        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['user'] = user
            serializer.save()
            return Res(200, "创建成功", serializer.data)
        else:
            return Res(400, "创建失败", serializer.errors)

    def destroy(self, request, pk=None):
        user = request.user

        # 判断请求是否有效
        task = models.Task.objects.filter(pk=pk).first()
        if not task:
            return Res(400, "任务不存在")
        if task.user_id != user.id:
            return Res(400, "无该任务所属权")
        if task.task_status == 2:
            return Res(400, "删除失败，任务已开始")

        # 请求有效，执行删除操作
        # 删除已创建的任务
        if task.task_processing_id:
            # 获取任务状态
            task_result = AsyncResult(task.task_processing_id, app=app)
            if task_result.status == 'STARTED':
                return Res(400, "删除失败，任务已开始")
            # 移除已存在的任务
            app.control.revoke(task.task_processing_id, terminate=True)

        # 删除相关文件，云存储的文件异步删除
        if task.source_file:
            delete_alioss_file.delay(task.source_file)
        if task.res_file:
            delete_alioss_file.delay(task.res_file)
        # 2.删除数据库记录
        task.delete()
        return Res(200, "删除成功")

    def list(self, request):
        user = request.user
        tasks = models.Task.objects.filter(user=user).order_by('-create_time')

        # 分页查询任务列表
        # paginator = PageNumberPagination()
        paginator = CustomPagination()
        paginator.page_size = request.query_params.get('page_size')
        result_page = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(instance=result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=["POST"], detail=False, url_path="file")
    def file(self, request):
        """
        给任务上传单次源文件
        :param request:
        :return:
        """
        user = request.user
        serializer = TaskFileUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            tid = serializer.validated_data['task_id']
            func_router = serializer.validated_data['func']

            # 判断请求是否有效
            task = models.Task.objects.filter(pk=tid).first()
            if task:
                if task.user_id != user.id:
                    return Res(400, "无该任务所属权")
                if task.task_status in [4, 5]:
                    return Res(400, "该任务为已结束状态，无法更改")

            func = models.Function.objects.filter(router=func_router).first()
            if not func:
                return Res(400, "功能类型不存在")

            # 判断文件大小
            file_size = uploaded_file.size
            if file_size > 2048 * 1024 * 1024:
                return Res(400, "文件大小不能超过2G")

            uuid = uuid4()
            save_name = str(uuid) + os.path.splitext(uploaded_file.name)[1]
            file_path = os.path.join(settings.TEMP_FILE_STORAGE_PATH, save_name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # 更新任务信息
            if not task:
                # 创建任务
                task = models.Task.objects.create(
                    task_name=func.title + ' - ' + uploaded_file.name,
                    task_type=func,
                    user=user,
                    original_filename=uploaded_file.name
                )
            else:
                old_save_name = task.source_file
                if old_save_name:
                    delete_alioss_file.delay(task.source_file)
                task.task_name = func.title + ' - ' + uploaded_file.name
                task.task_type = func
                task.original_filename = uploaded_file.name
                task.save()

            # 上传aliyun oss
            upload_alioss_from_file.delay(save_name, file_path, task_id=task.id)

            ser = TaskSerializer(instance=task)
            return Res(200, "上传成功", ser.data)
        else:
            return Res(400, "上传失败", serializer.errors)

    def update(self, request, pk):
        user = request.user
        # 判断请求是否有效
        task = models.Task.objects.filter(pk=pk).first()
        if not task:
            return Res(400, "任务不存在")
        if task.user_id != user.id:
            return Res(400, "无该任务所属权")
        if task.task_status != 1:
            return Res(400, "任务已经开始，无法更改")

        if task.task_processing_id:
            # 获取任务状态
            task_result = AsyncResult(task.task_processing_id, app=app)
            if task_result.status != 'PENDING':
                return Res(400, "任务已经开始，无法更改")
            # 移除已存在的任务
            app.control.revoke(task.task_processing_id, terminate=True)
            task.task_processing_id = None

        args = request.data.get('args')
        args = json.dumps(args)
        task.task_args = args

        ser = TaskSerializer(instance=task)
        res = add_task.delay(ser.data)

        task.task_processing_id = res.id
        task.save()

        return Res(200, "ok")

    @action(methods=["GET"], detail=True, url_path="down")
    def down(self, request, pk):
        user = request.user
        # 判断请求是否有效
        task = models.Task.objects.filter(pk=pk).first()
        if not task:
            return Res(400, "任务不存在")
        if task.user_id != user.id:
            return Res(400, "无该任务所属权")
        if task.task_status != 3:
            return Res(400, "该任务未处理完成，请等待")

        file_url = sign_url(task.res_file)
        return Res(200, 'ok', {"file_url": file_url})


class FunctionView(ViewSet):
    authentication_classes = []
    permission_classes = []

    def list(self, request):
        functions = Function.objects.all()
        ser = FunctionSerializer(instance=functions, many=True)
        return Res(200, "ok", ser.data)

    def retrieve(self, request, pk):
        function = Function.objects.filter(pk=pk).first()
        ser = FunctionSerializer(instance=function)
        return Res(200, "ok", ser.data)
