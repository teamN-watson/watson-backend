from django.db.models import Count, Q
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Review, ReviewComment, ReviewLike, ReviewCommentLike
from .serializers import (
    ReviewSerializer,
    ReviewCommentSerializer,
    ReviewLikeSerializer,
    ReviewCommentLikeSerializer,
    GameSerializer,
    GameSearchSerializer,
)
from django.db.models import Count
from accounts.models import Game, Block, Notice
from django.db.models import Case, When, Value, IntegerField
from django.core.paginator import Paginator
from django.http import JsonResponse


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
        blocked_users = (
            Block.objects.filter(blocker=request.user).values_list(
                "blocked_user", flat=True
            )
            if request.user.is_authenticated
            else []
        )
        sort_by = request.query_params.get(
            "sort_by", "recent"
        )  # 기본 정렬 기준: 최신순
        category = request.query_params.get("category", None)  # 카테고리 필터링 추가

        # annotate로 필드 추가 / 'related_name="likes"로 연결된 ReviewLike 모델의 is_active 필드 값이 1인 경우 추천, -1인 경우 비추천'
        reviews = Review.objects.annotate(
            total_likes=Count("likes", filter=Q(likes__is_active=1)),
            total_dislikes=Count("likes", filter=Q(likes__is_active=-1)),
        )

        # 카테고리 필터링 적용
        if category:
            reviews = reviews.filter(categories__contains=[category])

        # 정렬 기준 적용
        if sort_by == "popular":  # 인기순
            reviews = reviews.order_by("-total_likes", "-created_at")
        elif sort_by == "views":  # 조회순
            reviews = reviews.order_by("-view_count", "-created_at")
        else:  # 최신순
            reviews = reviews.order_by("-created_at")

        serializer = ReviewSerializer(
            reviews,
            many=True,
            context={"request": request, "blocked_users": list(blocked_users)},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """새 리뷰 생성"""
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            # Game 객체 가져오기
            app_id = serializer.validated_data.get("app_id")
            user = request.user

            # 동일한 app_id와 user 조합의 리뷰가 이미 존재하는지 확인
            if Review.objects.filter(app_id=app_id, user=user).exists():
                return Response(
                    {"detail": "한 게임의 리뷰는 하나만 작성 가능합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )  # 이미 리뷰가 존재하는 경우 에러 반환

            # app_id와 매칭되는 Game 객체 찾기
            game = Game.objects.filter(appID=app_id).first()
            if not game:
                return Response(
                    {"app_id": "유효하지 않은 app_id 입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 리뷰 생성
            review = serializer.save(user=request.user)

            # Game의 genres를 categories로 저장
            review.categories = game.genres  # Game의 genres를 리뷰에 설정
            review.save()

            # 응답용 데이터 생성
            response_data = serializer.data.copy()
            response_data["game_name"] = game.name
            response_data["header_image"] = game.header_image

            return Response(response_data, status=status.HTTP_201_CREATED)

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

        # 차단된 사용자 목록 가져오기
        blocked_users = (
            Block.objects.filter(blocker=request.user).values_list(
                "blocked_user", flat=True
            )
            if request.user.is_authenticated
            else []
        )

        # 조회수 증가 로직
        review.view_count += 1
        review.save()

        serializer = ReviewSerializer(
            review, context={"request": request, "blocked_users": list(blocked_users)}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """특정 리뷰 수정"""
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user:
            return Response(
                {"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            app_id = serializer.validated_data.get("app_id")

            # app_id 중복 체크: 현재 리뷰를 제외한 동일 app_id가 존재하는지 확인
            if (
                app_id
                and Review.objects.filter(app_id=app_id, user=request.user)
                .exclude(pk=pk)
                .exists()
            ):
                return Response(
                    {"detail": "한 게임에는 한 리뷰만 작성 가능합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # app_id 유효성 검사
            if app_id and not Game.objects.filter(appID=app_id).exists():
                return Response(
                    {"app_id": "유효하지 않은 app_id 입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 유효한 경우 리뷰 저장
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """특정 리뷰 삭제"""
        review = get_object_or_404(Review, pk=pk)

        if review.user != request.user:
            return Response(
                {"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        review.delete()
        return Response(
            {"detail": "리뷰가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
        )


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
        comments = (
            review.comments.all()
        )  # Review 모델의 related_name="comments"로 연결된 댓글 가져오기
        serializer = ReviewCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, review_id):
        """특정 리뷰에 댓글 생성"""
        review = get_object_or_404(Review, pk=review_id)
        serializer = ReviewCommentSerializer(data=request.data)
        if serializer.is_valid():
            # 댓글 저장
            comment = serializer.save(user=request.user, review=review)

            # 알림 생성: 리뷰 작성자에게
            if (
                review.user and review.user != request.user
            ):  # 본인이 작성한 리뷰에 댓글을 단 경우 제외
                Notice.objects.create(
                    user_id=review.user,
                    type=Notice.TYPE_COMMENT,  # 댓글 알림 타입 (3)
                    content=f"{request.user.nickname}님이 '{review.content[:20]}...'에 댓글을 남겼습니다.",
                )

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
            return Response(
                {"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = ReviewCommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """댓글 삭제"""
        comment = get_object_or_404(ReviewComment, pk=pk)

        if comment.user != request.user:
            return Response(
                {"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response(
            {"detail": "댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
        )


class ReviewLikeAPIView(APIView):
    """
    특정 리뷰에 좋아요 또는 비추천 생성 및 상태 변경
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        """좋아요/비추천 생성 및 상태 변경"""
        review = get_object_or_404(Review, pk=review_id)

        # 요청 데이터에 'is_active' 필드가 없는 경우 에러 반환
        if "is_active" not in request.data:
            return Response(
                {
                    "error": "'is_active' 필드는 필수입니다. (1=좋아요, -1=비추천, 0=중립)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewLikeSerializer(data=request.data)
        if serializer.is_valid():
            # 기존 좋아요/비추천 업데이트 또는 새로 생성
            like, created = ReviewLike.objects.update_or_create(
                user=request.user,
                review=review,
                defaults={"is_active": serializer.validated_data["is_active"]},
            )
            like_serializer = ReviewLikeSerializer(like)
            return Response(
                like_serializer.data,
                status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewCommentLikeAPIView(APIView):
    """
    특정 댓글에 좋아요 또는 비추천 생성 및 상태 변경
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        """좋아요/비추천 생성 및 상태 변경"""
        comment = get_object_or_404(ReviewComment, pk=comment_id)

        serializer = ReviewCommentLikeSerializer(data=request.data)
        if serializer.is_valid():
            # 기존 좋아요/비추천 업데이트 또는 새로 생성
            like, created = ReviewCommentLike.objects.update_or_create(
                user=request.user,
                comment=comment,
                defaults={"is_active": serializer.validated_data["is_active"]},
            )
            like_serializer = ReviewCommentLikeSerializer(like)
            return Response(
                like_serializer.data,
                status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewSearchAPIView(APIView):
    """
    리뷰 검색 API
    """

    def get(self, request):
        """리뷰 검색"""
        keyword = request.query_params.get("keyword", "").strip()
        if not keyword:
            return Response(
                {"detail": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Game 테이블에서 keyword와 매칭되는 appID 가져오기
        game_ids = Game.objects.filter(name__icontains=keyword).values_list(
            "appID", flat=True
        )

        # 검색 조건: 리뷰 내용, 카테고리, 게임 이름
        reviews = Review.objects.filter(
            Q(content__icontains=keyword)  # 리뷰 내용 검색
            | Q(categories__icontains=keyword)  # 카테고리 검색
            | Q(app_id__in=game_ids)  # Game 이름 검색 결과 매칭
        ).distinct()

        if not reviews.exists():
            return Response(
                {"detail": "검색 결과가 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        # 직렬화 및 응답
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GameDetailAPIView(APIView):
    """
    Game 상세 페이지 API
    """

    permission_classes = [AllowAny]

    def get(self, request, app_id):
        # Game 객체 가져오기
        game = get_object_or_404(Game, appID=app_id)

        # 리뷰 가져오기
        reviews = Review.objects.filter(app_id=app_id)
        my_review = None  # 기본값 설정

        # 사용자가 인증된 경우에만 자신의 리뷰 필터링
        if request.user.is_authenticated:
            my_review = reviews.filter(
                user_id=request.user.id
            ).first()  # user_id로 매칭
            reviews = reviews.exclude(user_id=request.user.id)

        # 직렬화
        game_serializer = GameSerializer(game)
        my_review_serializer = ReviewSerializer(my_review) if my_review else None
        other_reviews_serializer = ReviewSerializer(reviews, many=True)

        return Response(
            {
                "game": game_serializer.data,
                "my_review": my_review_serializer.data if my_review else None,
                "reviews": other_reviews_serializer.data,
            }
        )


class GameSearchAPIView(APIView):
    """
    검색 API
    """

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        page = request.query_params.get("page", 1)  # 현재 페이지 (기본값 1)

        if not query:
            return Response(
                {"detail": "검색어를 입력하세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        # 게임 이름에 검색어가 포함된 데이터 필터링
        games = (
            Game.objects.filter(name__icontains=query)
            .annotate(
                priority=Case(
                    When(name__iexact=query, then=Value(1)),  # 완전 일치
                    When(name__istartswith=query, then=Value(2)),  # 검색어로 시작
                    When(name__icontains=query, then=Value(3)),  # 검색어 포함
                    output_field=IntegerField(),
                )
            )
            .order_by("priority", "name")
        )  # 우선순위와 이름으로 정렬
        paginator = Paginator(games, 10)  # 페이지당 10개씩 표시

        # 현재 페이지 데이터 가져오기
        try:
            page_obj = paginator.page(page)
        except Exception as e:
            Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not games.exists():
            return Response(
                {"detail": "검색 결과가 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )

        # serializer = GameSearchSerializer(games, many=True)
        return Response(
            {
                "games": [
                    {
                        "appID": game.appID,
                        "name": game.name,
                        "header_image": game.header_image,
                    }
                    for game in page_obj
                ],
                "has_next": page_obj.has_next(),  # 다음 페이지 존재 여부
                "current_page": page_obj.number,
            },
            status=status.HTTP_200_OK,
        )
