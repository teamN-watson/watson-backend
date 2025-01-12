from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chatbot.models import Conversation, Message
from chatbot.serializers import MessageSerializer
from chatbot.assistant import Assistant
from django.shortcuts import get_object_or_404

class ChatbotRecordAPIView(APIView):
    """
    챗봇 대화방 내역 가져오는 API
    """
    def post(self, request):
        """
        대화방 기록 가져오기, 대화방 기록이 없을 땐 새로 만듦
        """
        # 1) Conversation 객체 가져오기 (account_id가 request.user.id인 경우)
        conversation = Conversation.objects.filter(account_id=request.user.id).first()

        if not conversation:
            conversation = Conversation.objects.create(
                account_id=request.user.id)

            # 3️⃣ 채팅방 첫 개설 시 기본 메시지 추가
            welcome_messages = [
                {"message": "안녕하세요! 저는 게임 추천 및 검색을 돕는 AI 왓슨입니다! 🕵️"},
                {"message": "게임 추천을 원하신다면 원하시는 게임의 특징을, 특정 게임에 대해 알고싶으시다면 정확한 게임 제목을 영어로 입력해주세요!"}
            ]

            # 반복문으로 메시지 생성
            for msg in welcome_messages:
                Message.objects.create(
                    conversation=conversation,
                    content=msg,
                    is_user=False
                )
        
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ChatbotAPIView(APIView):
    """
    챗봇 관련 클래스 (입력, 초기화)
    """
    def post(self, request):
        """
        챗봇 응답 요청 및 대화 내역 저장
        """
        message = request.data.get("message", "")

        # 1) Conversation 객체 가져오기
        conversation = Conversation.objects.filter(account_id=request.user.id).first()

        if not conversation:
            return Response({"message": "생성된 채팅방이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2) 사용자 메시지 저장
        user_message = {
                "conversation": conversation.id,
                "content": request.data,
                "is_user": True
            }
        
        user_serializer = MessageSerializer(data=user_message)

        # 3) 챗봇 응답 메시지 저장
        # 3-1) 챗봇 모델 생성
        assistant = Assistant.from_env()
        bot_message = {
            "conversation": conversation.id,
            "content": assistant.process_query(request, message),
            "is_user": False
        }

        bot_serializer = MessageSerializer(data=bot_message)

        if user_serializer.is_valid():
            if bot_serializer.is_valid():
                user_serializer.save()
                bot_serializer.save()
            
            else:
                return Response({"message": "AI 봇의 응답이 유효하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "사용자의 입력이 유효하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'conversation_id': conversation.id,
            'user_message': user_message['content'],
            'bot_message': bot_message['content']
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        # 1) Conversation 객체 가져오기
        conversation = Conversation.objects.filter(
            account_id=request.user.id).first()
        
        if not conversation:
            return Response({"message": "생성된 채팅방이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 객체 삭제
        conversation.delete()

        # 응답 반환 (필요 시)
        return Response({"message": "채팅방이 정상적으로 삭제되었습니다."}, status=200)


class DeleteChatbotRecordAPIView(APIView):
    """
    챗봇 대화 중 특정 메시지 삭제하는 API
    """
    def delete(self, request, messageid):

        message = get_object_or_404(Message, pk=messageid)
        # 객체 삭제
        message.delete()

        # 응답 반환 (필요 시)
        return Response({"message": "메시지가 정상적으로 삭제되었습니다."}, status=200)