from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chatbot.models import Conversation, Message
from chatbot.serializers import MessageSerializer
from chatbot.assistant import Assistant
from chatbot.collaborate import Collaborations_Assistant
from chatbot.autoquest import AutoAssistant
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from accounts.models import Account

class ChatbotRecordAPIView(APIView):
    """
    챗봇 대화방 내역 가져오는 API
    """
    # 로그인된 사용자만 접근 가능하도록 설정
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        단순 대화방 기록 가져오기
        """
        # 1) Conversation 객체 가져오기 (account_id가 request.user.id인 경우)
        conversation = Conversation.objects.filter(
            account_id=request.user.id).first()
        
        if not conversation:
            return Response({"message": "생성된 채팅방이 없습니다."}, status=status.HTTP_204_NO_CONTENT)
        
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        


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
    # 로그인된 사용자만 접근 가능하도록 설정
    permission_classes = [IsAuthenticated]


    def post(self, request):
        """
        챗봇 응답 요청 및 대화 내역 저장
        """
        message = request.data.get("message", "")
        user_count = Account.objects.count()

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
        # 유저 수에 따라 방법 달라짐 (하이브리드 필터링)
        if user_count >= 30:
            # 유저 30명 이상 : 협업 필터링
            assistant = Collaborations_Assistant.from_env()
        else:
            # 유저 30명 미만 : 콘텐츠 기반 필터링
            assistant = Assistant.from_env()

        bot_message = {
            "conversation": conversation.id,
            "content": assistant.process_query(request, message),
            "is_user": False
        }

        bot_serializer = MessageSerializer(data=bot_message)

        # 4) 유효성 검사 및 저장
        if not user_serializer.is_valid():
            return Response({"message": "사용자의 입력이 유효하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if not bot_serializer.is_valid():
            return Response({"message": "AI 봇의 응답이 유효하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        user_serializer.save()
        bot_serializer.save()

        # 5) 만약 봇의 응답이 특정 문구(게임 관련 질문만 가능)라면, 추가 안내 메시지를 하나 더 제공
        if bot_message['content']['message'] == "죄송합니다. 게임과 관련 질문에 대해서만 응답을 제공할 수 있습니다. 🕵️":
            # 추가 안내 문구
            additional_message_dict = {
                "message": 'ex) "힐링 게임 추천해줘", "Stardew Valley에 대해 알려줘" 와 같이 게임에 관한 질문을 입력해주세요!'
            }
            
            # 두 번째 봇 메시지(추가 안내 문구) 생성
            second_bot_message = {
                "conversation": conversation.id,
                "content": additional_message_dict,
                "is_user": False
            }
            second_bot_serializer = MessageSerializer(data=second_bot_message)

            if second_bot_serializer.is_valid():
                second_bot_serializer.save()
            else:
                return Response({"message": "추가 메시지 저장 실패"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'conversation_id': conversation.id,
                'user_message': user_message['content'], 
                'bot_message': bot_message['content'],
                'bot_guide' : additional_message_dict
            }, status=status.HTTP_201_CREATED)
        
        # 6) 그 외 경우에는 기존 로직대로 한 번의 봇 메시지만 응답
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
    # 로그인된 사용자만 접근 가능하도록 설정
    permission_classes = [IsAuthenticated]


    def delete(self, request, messageid):

        message = get_object_or_404(Message, pk=messageid)
        # 객체 삭제
        message.delete()

        # 응답 반환 (필요 시)
        return Response({"message": "메시지가 정상적으로 삭제되었습니다."}, status=200)
    

class AutoChatbotAPIView(APIView):
    """
    챗봇 관련 클래스 (입력, 초기화)
    """
    # 로그인된 사용자만 접근 가능하도록 설정
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        챗봇 응답 요청 및 대화 내역 저장
        """

        # 1) Conversation 객체 가져오기
        conversation = Conversation.objects.filter(
            account_id=request.user.id).first()

        if not conversation:
            return Response({"message": "생성된 채팅방이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 2) 사용자 메시지 저장
        user_message = {
            "conversation": conversation.id,
            "content": "내 취향에 맞는 게임 추천해줘",
            "is_user": True
        }

        user_serializer = MessageSerializer(data=user_message)

        # 3) 챗봇 응답 메시지 저장
        # 3-1) 챗봇 모델 생성
        assistant = AutoAssistant.from_env()

        bot_message = {
            "conversation": conversation.id,
            "content": assistant.process_query(request),
            "is_user": False
        }

        bot_serializer = MessageSerializer(data=bot_message)

        # 4) 유효성 검사 및 저장
        if not user_serializer.is_valid():
            return Response({"message": "사용자의 입력이 유효하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if not bot_serializer.is_valid():
            return Response({"message": "AI 봇의 응답이 유효하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        user_serializer.save()
        bot_serializer.save()

        # 5) 봇 메시지 응답
        return Response({
            'conversation_id': conversation.id,
            'user_message': user_message['content'],
            'bot_message': bot_message['content']
        }, status=status.HTTP_201_CREATED)
