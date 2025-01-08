from django.db.models import Count, Q
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Review, ReviewComment, ReviewLike
from .serializers import ReviewSerializer, ReviewCommentSerializer, ReviewLikeSerializer
from django.db.models import Count


class ReviewAPIView(APIView):
    """
    리뷰 목록 조회 및 새 리뷰 생성
    """

    def get_permissions(self):
        """
        메서드별 권한 부여
        """
        if self.request.method == "GET":
            return [AllowAny()]
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        """리뷰 목록 조회"""
        sort_by = request.query_params.get('sort_by', 'recent')  # 기본 정렬 기준: 최신순

        # annotate로 좋아요 및 비추천 수 계산 / 'related_name="likes"로 연결된 ReviewLike 모델의 is_active 필드 값이 1인 경우 추천, -1인 경우 비추천'
        reviews = Review.objects.annotate(
            total_likes=Count('likes', filter=Q(likes__is_active=1)),
            total_dislikes=Count('likes', filter=Q(likes__is_active=-1))
        )

        # 정렬 기준 적용
        if sort_by == 'popular':  # 인기순
            reviews = reviews.order_by('-total_likes', '-created_at')
        elif sort_by == 'views':  # 조회순
            reviews = reviews.order_by('-view_count', '-created_at')
        else:  # 최신순
            reviews = reviews.order_by('-created_at')

        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
        """새 리뷰 생성 """
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # 현재 요청 유저를 저장
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewDetailAPIView(APIView):
    """
    특정 리뷰 조회, 수정, 삭제
    """

    def get_permissions(self):
        """
        메서드별 권한 설정
        """
        if self.request.method == "GET":
            return [AllowAny()]
        if self.request.method in ["PUT", "DELETE"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get(self, request, pk):
        """특정 리뷰 조회"""
        review = get_object_or_404(Review, pk=pk)

        # 조회수 증가 로직
        review.view_count += 1
        review.save()
        
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """특정 리뷰 수정"""
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user:
            return Response({"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """특정 리뷰 삭제"""
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user:
            return Response({"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        review.delete()
        return Response({"detail": "리뷰가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)

class ReviewCommentAPIView(APIView):
    """
    특정 리뷰에 댓글 생성 및 조회
    """
    def get_permissions(self):
        """
        메서드별 권한 설정
        """
        if self.request.method == "GET":
            return [AllowAny()]
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return super().get_permissions()

    def get(self, request, review_id):
        """특정 리뷰의 댓글 목록 조회"""
        review = get_object_or_404(Review, pk=review_id)
        comments = review.comments.all()  # Review 모델의 related_name="comments"로 연결된 댓글 가져오기
        serializer = ReviewCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, review_id):
        """특정 리뷰에 댓글 생성"""
        review = get_object_or_404(Review, pk=review_id)
        serializer = ReviewCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, review=review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewCommentDetailAPIView(APIView):
    """
    특정 댓글 수정 및 삭제
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        """댓글 수정"""
        comment = get_object_or_404(ReviewComment, pk=pk)

        if comment.user != request.user:
            return Response({"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewCommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """댓글 삭제"""
        comment = get_object_or_404(ReviewComment, pk=pk)

        if comment.user != request.user:
            return Response({"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"detail": "댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)

class ReviewLikeAPIView(APIView):
    """
    특정 리뷰에 좋아요 또는 비추천 생성 및 상태 변경
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        """좋아요/비추천 생성 및 상태 변경"""
        review = get_object_or_404(Review, pk=review_id)

        serializer = ReviewLikeSerializer(data=request.data)
        if serializer.is_valid():
            # 기존 좋아요/비추천 업데이트 또는 새로 생성
            like, created = ReviewLike.objects.update_or_create(
                user=request.user, review=review, defaults={"is_active": serializer.validated_data["is_active"]}
            )
            like_serializer = ReviewLikeSerializer(like)
            return Response(like_serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
