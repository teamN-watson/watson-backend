import requests
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import re


@dataclass
class YoutubeConfig:
    """
    SearchYoutube의 설정을 관리하는 데이터 클래스
    Attributes:
    youtube_api_key (str): YouTube Data API 접근을 위한 인증 키
    """
    youtube_api_key: str


class SearchYoutube:
    """
    게임 이름에 대한 리뷰 영상을 검색하는 클래스
    """

    def __init__(self, config: YoutubeConfig):
        self.config = config
        # YouTube API의 엔드포인트 URL 설정
        self.search_url = "https://www.googleapis.com/youtube/v3/search"
        self.video_url = "https://www.googleapis.com/youtube/v3/videos"

    @classmethod
    def from_env(cls):
        """
        환경 변수에서 설정을 로드하여 인스턴스를 생성하는 클래스 메서드
        """
        load_dotenv()
        config = YoutubeConfig(
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
        )
        return cls(config)

    @staticmethod
    def parse_iso8601_duration(duration: str) -> int:
        """
        ISO8601 형식의 기간 문자열을 초 단위로 변환
        이 구현은 "PT#H#M#S" 형식을 포함하여 처리합니다.
        """
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.fullmatch(duration)
        if not match:
            return 0
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        return hours * 3600 + minutes * 60 + seconds


    def search_videos(self, query: str, max_results: int = 30):
        try:
            # YouTube API 검색 파라미터 설정
            search_params = {
                'key': self.config.youtube_api_key,
                'q': query,
                'part': 'snippet',
                'maxResults': max_results,
                'type': 'video',
                'order': 'ViewCount',
                'regionCode': 'KR',
                'relevanceLanguage': 'ko'
            }

            # 검색 API 호출
            response = requests.get(self.search_url, params=search_params)
            response.raise_for_status()
            search_data = response.json()

            if 'items' not in search_data or not search_data['items']:
                print("검색 결과가 없습니다.")
                return

            video_list = []

            # 각 비디오의 상세 정보 수집
            for item in search_data['items']:
                try:
                    video_id = item['id']['videoId']
                    video_stats = self._get_video_stats(video_id)

                    # 동영상 기간 확인 및 10분 이상 2시간 이하 필터링
                    duration_iso = video_stats.get('duration')
                    if duration_iso:
                        length_seconds = self.parse_iso8601_duration(
                            duration_iso)
                        if length_seconds > 3600 or length_seconds < 600:  # 2시간 초과 또는 10분 미만 시 건너뜀
                            continue
                    else:
                        # 기간 정보가 없으면 건너뜀
                        continue

                    # 날짜 포맷 변경
                    published_at = datetime.strptime(
                        item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                    formatted_date = published_at.strftime("%Y년 %m월 %d일")

                    # 비디오 정보 추가
                    video = {
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': formatted_date,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'view_count': int(video_stats.get('viewCount', 0)),
                        'like_count': int(video_stats.get('likeCount', 0)),
                        'duration': duration_iso
                    }
                    video_list.append(video)
                except Exception as e:
                    print(f"비디오 정보 처리 중 오류 발생: {e}")
                    continue

                # 동영상 5개 쌓이면 끝
                if len(video_list) == 5:
                    break

            if not video_list:
                print("조건을 만족하는 영상이 없습니다.")
                return

            # 좋아요 수로 정렬
            video_list.sort(key=lambda x: x['like_count'], reverse=True)

            # 가장 좋아요 수가 많은 동영상 반환
            return video_list if video_list else None

        except Exception as e:
            print(f"검색 중 오류 발생: {e}")

    def _get_video_stats(self, video_id: str) -> dict:
        try:
            params = {
                'key': self.config.youtube_api_key,
                'id': video_id,
                'part': 'statistics,contentDetails'
            }

            response = requests.get(self.video_url, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get('items'):
                item = data['items'][0]
                stats = item.get('statistics', {})
                content_details = item.get('contentDetails', {})
                # duration 정보를 statistics dict에 추가
                if 'duration' in content_details:
                    stats['duration'] = content_details['duration']
                return stats
            return {}
        except Exception as e:
            print(f"비디오 통계 정보 조회 중 오류 발생: {e}")
            return {}