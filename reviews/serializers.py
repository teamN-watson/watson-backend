from rest_framework import serializers
from .models import Review, ReviewComment, ReviewLike, ReviewCommentLike
from accounts.models import Game, Block


class ReviewCommentSerializer(serializers.ModelSerializer):
    """ReviewComment 모델 직렬화"""

    nickname = serializers.SerializerMethodField()

    class Meta:
        model = ReviewComment
        fields = [
            "id",
            "review",
            "user",
            "nickname",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "review", "created_at", "updated_at"]

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"


class ReviewCommentLikeSerializer(serializers.ModelSerializer):
    """ReviewCommentLike 모델 직렬화"""

    class Meta:
        model = ReviewCommentLike
        fields = ["id", "comment", "user", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "comment", "user", "created_at", "updated_at"]


class ReviewLikeSerializer(serializers.ModelSerializer):
    """ReviewLike 모델 직렬화"""

    nickname = serializers.SerializerMethodField()

    class Meta:
        model = ReviewLike
        fields = [
            "id",
            "review",
            "user",
            "nickname",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "review", "user", "created_at", "updated_at"]

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"

    def validate_is_active(self, value):
        """is_active 필드 값 검증"""
        if value not in [1, -1, 0]:
            raise serializers.ValidationError(
                "is_active 값은 1(좋아요), -1(비추천), 0(중립) 중 하나여야 합니다."
            )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Review 모델 직렬화"""

    nickname = serializers.SerializerMethodField()  # 사용자 닉네임 반환
    content_display = serializers.SerializerMethodField()  # 차단된 사용자 콘텐츠 처리
    comments = ReviewCommentSerializer(many=True, read_only=True)  # 연결된 댓글들
    total_likes = serializers.IntegerField(read_only=True)  # annotate로 계산된 값
    total_dislikes = serializers.IntegerField(read_only=True)  # annotate로 계산된 값
    game_name = serializers.CharField(read_only=True)
    header_image = serializers.CharField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "nickname",
            "content",
            "content_display",
            "app_id",
            "game_name",
            "header_image",
            "score",
            "categories",
            "created_at",
            "updated_at",
            "comments",
            "total_likes",
            "total_dislikes",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "comments",
            "total_likes",
            "total_dislikes",
            "game_name",
            "header_image",
            "categories",
            "content_display",
        ]
        
        extra_kwargs = {
            "content": {
                "required": True,
                "error_messages": {
                    "required": "리뷰 내용을 입력해야 합니다.",
                    "blank": "리뷰 내용은 비워둘 수 없습니다.",
                },
            },
            "score": {
                "required": True,
                "error_messages": {
                    "required": "평점을 입력해야 합니다.",
                    "invalid": "올바른 평점을 입력해주세요.",
                    "blank": "평점은 비워둘 수 없습니다.",
                },
            },
            "app_id": {
                "required": True,
                "error_messages": {
                    "required": "게임 ID(app_id)는 필수입니다.",
                    "invalid": "올바른 게임 ID를 입력해주세요.",
                    "blank": "게임 ID는 비워둘 수 없습니다.",
                },
            },
        }

    def get_nickname(self, obj):
        """유저 닉네임 반환 (유저가 없으면 '알수없음')"""
        return obj.user.nickname if obj.user else "알수없음"

    def get_content_display(self, obj):
        blocked_users = self.context.get("blocked_users", [])
        if obj.user and obj.user.id in blocked_users:
            return "이 사용자의 리뷰는 차단되어 표시되지 않습니다."
        return obj.content

    def validate_score(self, value):
        """
        평점 검증: 0.5~5.0 사이의 값만 허용하고, 0.5 단위로 작성되어야 함.
        """
        if not (0.5 <= value <= 5.0):
            raise serializers.ValidationError(
                "평점은 0.5에서 5.0 사이의 값이어야 합니다."
            )
        if value * 10 % 5 != 0:
            raise serializers.ValidationError("평점은 0.5 단위로 작성되어야 합니다.")
        return value


class GameSerializer(serializers.ModelSerializer):
    """
    Game 모델 직렬화
    """

    class Meta:
        model = Game
        fields = ["appID", "name", "header_image", "genres", "supported_languages"]


class GameSearchSerializer(serializers.ModelSerializer):
    """
    리뷰 작성에 필요한 Game 모델 검색용 직렬화
    """

    class Meta:
        model = Game
        fields = ["appID", "name", "header_image"]  # 검색에 필요한 필드만 포함
