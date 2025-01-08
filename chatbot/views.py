from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from chatbot.models import Conversation, Message




class ChatbotAPIView(APIView):
    """
    챗봇 응답 요청 및 내역 저장
    """
    def post(self, request, conversation_id=None):
        user = request.user if request.user.is_authenticated else None
        content = request.data.get('content', '')

        # 1) conversation 객체 가져오기 (없는 경우 새로 생성할 수도 있음)
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = Conversation.objects.create(user=user)

        # 2) 사용자 메시지 저장
        user_message = Message.objects.create(
            conversation=conversation,
            content=content,
            is_user=True
        )

        # 3) 챗봇 응답 생성 로직
        chatbot_answer = get_chatbot_answer(
            content)

        # 4) 챗봇 메시지 저장
        bot_message = Message.objects.create(
            conversation=conversation,
            content=chatbot_answer,
            is_user=False
        )

        # 5) 최종 응답
        return Response({
            'conversation_id': conversation.id,
            'user_message': user_message.content,
            'bot_message': bot_message.content
        }, status=status.HTTP_201_CREATED)
