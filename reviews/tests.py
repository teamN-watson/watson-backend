from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Review
from accounts.models import Game

class ReviewSearchAPITest(APITestCase):
    """ReviewSearchAPIView 테스트"""

    @classmethod
    def setUpTestData(cls):
        """테스트 데이터를 생성합니다."""
        cls.game1 = Game.objects.create(
            appID=101,
            name="RPG Adventure Game",  # 이름을 예상 값과 동일하게 수정
            supported_languages={"en": "English", "kr": "Korean"},
            genres=["RPG", "Adventure"],
            header_image="http://example.com/rpg_adventure.jpg"
        )
        cls.game2 = Game.objects.create(
            appID=102,
            name="Action Blast Game",
            supported_languages={"en": "English", "fr": "French"},
            genres=["Action"],
            header_image="http://example.com/action_blast.jpg"
        )
        cls.game3 = Game.objects.create(
            appID=103,
            name="Puzzle Game World",
            supported_languages={"en": "English", "jp": "Japanese"},
            genres=["Puzzle", "Casual"],
            header_image="http://example.com/puzzle_world.jpg"
        )

        cls.review1 = Review.objects.create(
            content="Amazing RPG game!",
            app_id=101,
            categories=["RPG", "Adventure"],
            score=4.5
        )

        cls.review2 = Review.objects.create(
            content="Loved the action game!",  # 'game' 포함
            app_id=102,
            categories=["Action"],
            score=4.0
        )
        cls.review3 = Review.objects.create(
            content="Fun and relaxing game!",  # 'game' 포함
            app_id=103,
            categories=["Puzzle", "Casual"],
            score=4.8
        )

    def test_search_by_content(self):
        """리뷰 내용으로 검색 테스트"""
        url = reverse('reviews:review_search')  # URL 네임스페이스에 따라 변경
        response = self.client.get(url, {'keyword': 'Amazing'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], "Amazing RPG game!")

    def test_search_by_category(self):
        """카테고리로 검색 테스트"""
        url = reverse('reviews:review_search')
        response = self.client.get(url, {'keyword': 'Action'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['categories'], ["Action"])

    def test_search_by_game_name(self):
        """게임 이름으로 검색 테스트"""
        url = reverse('reviews:review_search')
        response = self.client.get(url, {'keyword': 'RPG Adventure'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['game_name'], "RPG Adventure Game") 

    def test_search_with_no_results(self):
        """검색 결과가 없는 경우 테스트"""
        url = reverse('reviews:review_search')
        response = self.client.get(url, {'keyword': 'Nonexistent'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "검색 결과가 없습니다.")

    def test_search_with_empty_keyword(self):
        """검색어가 비어 있는 경우 테스트"""
        url = reverse('reviews:review_search')
        response = self.client.get(url, {'keyword': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "검색어를 입력해주세요.")

    def test_search_by_partial_game_name(self):
        """게임 이름의 일부로 검색 테스트"""
        url = reverse('reviews:review_search')
        response = self.client.get(url, {'keyword': 'Adventure'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['game_name'], "RPG Adventure Game")  # 예상 값을 데이터와 일치

    def test_search_with_multiple_matches(self):
        """여러 결과가 매칭되는 경우 테스트"""
        url = reverse('reviews:review_search')
        response = self.client.get(url, {'keyword': 'game'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 3개의 리뷰가 매칭됨
