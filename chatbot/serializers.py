from rest_framework import serializers
from chatbot.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    """
    챗봇 대화 내역 직렬화
    """
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'content', 'is_user', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    """
    챗봇 대화방 정보 직렬화
    """
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'created_at', 'messages']
        read_only_fields = ['id', 'created_at', 'messages']
