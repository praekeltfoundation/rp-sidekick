from rest_framework import serializers


class GetOrderedContentSetSerializer(serializers.Serializer):
    fields = serializers.DictField()
