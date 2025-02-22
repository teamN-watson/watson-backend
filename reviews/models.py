from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from accounts.models import Game


class Review(models.Model):
    """Review 모델 설정"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # 유저가 삭제되어도 리뷰는 남아있음 (유저 정보는 null로 표시됨)
        null=True,
        blank=True,
        related_name="reviews",
    )
    content = models.TextField()  # 리뷰 내용
    app_id = (
        models.IntegerField()
    )  # Steam API에서 가져온 게임 ID (해당 게임 리뷰 작성 페이지로 이동할때 프론트엔드가 app_id 전달함)
    score = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,  # 평점은 필수가 아님
    )  # 별점: 0.5 단위(별 반개 단위), 최대 5.0 (별 다섯개)
    categories = ArrayField(
        models.CharField(max_length=50), default=list, blank=True
    )  # 리뷰 카테고리
    view_count = models.PositiveIntegerField(default=0)  # 조회수
    created_at = models.DateTimeField(auto_now_add=True)  # 리뷰 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 리뷰 수정 시간

    def save(self, *args, **kwargs):
        """저장 시 app_id가 변경되면 categories 업데이트"""
        # 기존 app_id 확인
        original_app_id = None
        if self.pk:  # 기존에 저장된 객체라면
            original_app_id = Review.objects.get(pk=self.pk).app_id

        # app_id가 변경된 경우
        if original_app_id != self.app_id:
            game = Game.objects.filter(appID=self.app_id).first()
            if game:
                self.categories = (
                    game.genres
                )  # 새로운 app_id에 따른 categories 업데이트

        super().save(*args, **kwargs)

    @property
    def game(self):
        """app_id를 기반으로 Game 객체 반환"""
        from accounts.models import Game  # Game 모델 임포트

        return Game.objects.filter(appID=self.app_id).first()

    @property
    def game_name(self):
        """Game 이름 반환"""
        return self.game.name if self.game else "Unknown Game"

    @property
    def header_image(self):
        """Game 헤더 이미지 반환"""
        return self.game.header_image if self.game else None

    def __str__(self):
        if self.user:
            nickname = self.user.nickname
        else:
            nickname = "알수없음"

        return f"Review 작성자 : {nickname} - 스팀 게임 번호 : {self.app_id} - 게임 이름 : {self.game.name} - 평점 : ({self.score})"

    class Meta:
        ordering = ["-created_at"]  # 최신순 정렬


class ReviewComment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,  # 리뷰 삭제 시 댓글도 삭제
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # 유저 삭제 시 댓글 작성자는 "알수없음"으로 표시
        null=True,
        blank=True,
        related_name="review_comments",
    )

    content = models.TextField()  # 댓글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 댓글 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 댓글 수정 시간

    def __str__(self):
        return f"Comment by {self.user.nickname if self.user else '알수없음'} on Review {self.review.id}"

    class Meta:
        ordering = ["created_at"]  # 생성 순서대로 정렬


class ReviewLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # 유저가 삭제되면 좋아요 기록도 삭제
        related_name="review_likes",
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,  # 리뷰가 삭제되면 좋아요 기록도 삭제
        related_name="likes",
    )
    is_active = models.IntegerField(
        choices=[(1, "좋아요"), (-1, "비추천"), (0, "중립")],  # 기본값
        default=0,  # 기본 상태는 중립
    )
    created_at = models.DateTimeField(auto_now_add=True)  #  생성 시간
    updated_at = models.DateTimeField(auto_now=True)  #  상태 변경 시간

    def __str__(self):
        return f"Review {self.review.id} - Liked by {self.user.nickname if self.user else '알수없음'} ({'좋아요' if self.is_active == 1 else '안좋아요' if self.is_active == -1 else '중립'})"

    class Meta:
        unique_together = ("user", "review")  # 유저-리뷰 조합 중복 방지
        ordering = ["-created_at"]  # 최신 좋아요 순서대로 정렬


class ReviewCommentLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # 유저가 삭제되면 좋아요 기록도 삭제
        related_name="comment_likes",
    )
    comment = models.ForeignKey(
        ReviewComment,
        on_delete=models.CASCADE,  # 댓글이 삭제되면 좋아요 기록도 삭제
        related_name="likes_on_comment",
    )
    is_active = models.IntegerField(
        choices=[(1, "좋아요"), (-1, "비추천"), (0, "중립")],  # 기본값
        default=0,  # 기본 상태는 중립
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 상태 변경 시간

    def __str__(self):
        return f"Comment {self.comment.id} - Liked by {self.user.nickname if self.user else '알수없음'} ({'좋아요' if self.is_active == 1 else '안좋아요' if self.is_active == -1 else '중립'})"

    class Meta:
        unique_together = ("user", "comment")  # 유저-댓글 조합 중복 방지
