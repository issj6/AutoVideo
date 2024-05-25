from rest_framework import serializers

from tasks import models


class TaskFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    task_id = serializers.IntegerField()
    func = serializers.CharField()


class TaskSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    start_processing_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    end_processing_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    # task_status = serializers.CharField(source="get_task_status_display")
    task_status_text = serializers.CharField(source="get_task_status_display")
    task_type_text = serializers.CharField(source="task_type.title")

    class Meta:
        model = models.Task
        fields = "__all__"


class FunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Function
        fields = "__all__"
