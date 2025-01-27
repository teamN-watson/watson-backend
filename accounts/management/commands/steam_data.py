import environ
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
import re
from bs4 import BeautifulSoup
from accounts.models import (
    Account,
    SteamProfile,
    SteamReview,
    SteamPlaytime,
)


class Command(BaseCommand):
    help = "Steam 프로필/리뷰/플레이타임 정보를 가져와 DB에 반영"

    def handle(self, *args, **options):
        # 1) 환경 변수에서 API 키 불러오기
        env = environ.Env()
        api_key = env("STEAM_API_KEY")  # .env에 STEAM_API_KEY=... 설정

        # 2) steamId가 비어있지 않은 Account를 모두 가져온다
        accounts = Account.objects.exclude(steamId="")
        
        # 3) 각 Account에 대해 프로필/리뷰/플레이타임 업데이트
        for account in accounts:
            steam_id_str = account.steamId.strip()

            # 4) 전체 프로필 공개 여부 API로 확인
            visibility_public = self.check_profile_public(api_key, steam_id_str)

            # 기본값 False로 시작
            is_review = False
            is_playtime = False

            if visibility_public:
                # (A) 게임 목록 공개 여부 판단 (참고용)
                owned_games_public = self.check_owned_games_public(api_key, steam_id_str)
                

                # (B) 리뷰 크롤링 (최대 3개) - BeautifulSoup 이용
                review_data = self.fetch_top3_reviews(steam_id_str)
                if review_data:
                    is_review = True  # 한 개라도 있으면 True


                # (C) 플레이타임 API로 가져오기 (상위 2개)
                playtime_data = self.fetch_top2_playtime_api(api_key, steam_id_str)
                if playtime_data:
                    is_playtime = True
                

                # (D) DB 저장
                with transaction.atomic():
                    # SteamProfile
                    sp, _ = SteamProfile.objects.get_or_create(account=account)
                    sp.is_review = is_review
                    sp.is_playtime = is_playtime
                    sp.save()

                    # 기존 리뷰/플레이타임 삭제 후 재생성 (중복 방지)
                    SteamReview.objects.filter(account=account).delete()
                    SteamPlaytime.objects.filter(account=account).delete()

                    if is_review:
                        for rd in review_data:
                            SteamReview.objects.create(
                                account=account,
                                app_id=rd["app_id"]
                                # review_text=rd["review_text"] 등 리뷰 내용 필요하면 추가
                            )
                    if is_playtime:
                        for pd in playtime_data:
                            SteamPlaytime.objects.create(
                            account=account,
                            app_id=pd["app_id"],
                            )
            else:
                # 프로필 자체가 Private -> is_review=False, is_playtime=False
                with transaction.atomic():
                    sp, _ = SteamProfile.objects.get_or_create(account=account)
                    sp.is_review = False
                    sp.is_playtime = False
                    sp.save()

                    # 관련 리뷰/플레이타임 전부 삭제 (혹시 이전에 있으면)
                    SteamReview.objects.filter(account=account).delete()
                    SteamPlaytime.objects.filter(account=account).delete()

        self.stdout.write(self.style.SUCCESS("Steam 데이터 처리 완료."))

    # -------------------------------------------------------
    # (A) 스팀 프로필이 Public인지 판별 (communityvisibilitystate)
    # -------------------------------------------------------
    def check_profile_public(self, api_key, steam_id_str):
        # steam_id_str이 64비트 숫자인지 커스텀 url인지 확인
        # GetPlayerSummaries는 64비트 SteamID만 받으므로
        # 커스텀 url -> 변환 단계가 필요할 수도 있다.
        # 여기서는 간단히 "커스텀 URL은 communityvisibilitystate 판단 불가"라고 가정하거나,
        # vanity URL -> steamid64 변환 API(ResolveVanityURL)를 사용 가능.
        #
        # 예시: https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/
        #       ?key=XXXX&vanityurl=커스텀URL
        #       -> response: { "response": { "success": 1, "steamid": "7656119..." } }
        #
        # 여기서는 단순히 숫자 판별로만 진행. 테스트는 아직 못함
        steamid64 = None
        if steam_id_str.isdigit():
            steamid64 = steam_id_str
        else:
            # 커스텀 URL -> ResolveVanityURL API로 변환 시도 (간단 버전)
            steamid64 = self.resolve_vanity_url(api_key, steam_id_str)

            if not steamid64:
                # Vanity URL도 해결 안 된다면, 그냥 False 처리 ㅜ
                return False

        # communityvisibilitystate 확인
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {"key": api_key, "steamids": steamid64}
        resp = requests.get(url, params=params).json()
        players = resp.get("response", {}).get("players", [])
        if not players:
            return False

        player = players[0]
        vis_state = player.get("communityvisibilitystate", 1)
        return (vis_state == 3)

    # -------------------------------------------------------
    # (B) 게임 목록(owned games) 공개 여부 확인
    # -------------------------------------------------------
    def check_owned_games_public(self, api_key, steam_id_str):
        # 마찬가지로 steam_id_str -> steamid64 변환
        steamid64 = steam_id_str if steam_id_str.isdigit() else self.resolve_vanity_url(api_key, steam_id_str)
        if not steamid64:
            return False

        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        params = {"key": api_key, "steamid": steamid64}
        resp = requests.get(url, params=params).json()
        # Game details가 비공개면 "response": {} 이거나 games 없음
        games = resp.get("response", {}).get("games", [])
        # games가 있다면 True로 볼 수 있음
        return len(games) > 0

    # -------------------------------------------------------
    # (C) 리뷰 페이지 크롤링 (상위 3개 'Recommended') - BeautifulSoup 사용
    # -------------------------------------------------------
    def fetch_top3_reviews(self, steam_id_str):
        base_url = "https://steamcommunity.com/"
        # 프로필 주소 결정
        if steam_id_str.isdigit():
            url = f"{base_url}profiles/{steam_id_str}/recommended"
        else:
            url = f"{base_url}id/{steam_id_str}/recommended"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/87.0.4280.66 Safari/537.36"
            )
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                # 프로필이 Private 상태거나 접근 실패 시 빈 리스트
                return []
            soup = BeautifulSoup(response.text, "html.parser")
        except:
            # 요청 실패 시 빈 리스트
            return []

        boxes = soup.select(".review_box")
        recommended = []
        for box in boxes:
            try:
                title_elem = box.select_one(".vote_header .title > a")
                if title_elem and "Recommended" in title_elem.text:
                    href = title_elem.get("href", "")
                    if "/recommended/" in href:
                        app_id = href.split("/recommended/")[1].split("/")[0]
                        recommended.append({"app_id": app_id})
                        if len(recommended) >= 3:
                            break
            except:
                # 파싱 실패 시 다음 리뷰로 넘어감
                continue

        return recommended

    # -------------------------------------------------------
    # (D) 플레이 타임 크롤링 (상위 2개) / 최근 플레이 게임을 기준으로 추출하려 했는데
    # 로그인이 필요해서 그냥 API로 가져오도록 함(비공개 여부 파악 힘듬)
    # -------------------------------------------------------

    def fetch_top2_playtime_api(self, api_key, steam_id_str):
    
        # steam_id_str(64비트 숫자)에 대해 GetOwnedGames API를 호출해,
        # playtime_forever 기준으로 상위 2개 app_id를 리턴한다.
        # return 형식: [{"app_id": 233860, "playtime": 304.55}, ...]
    
        # 1) SteamID64 확인
        # 커스텀 URL이면, self.resolve_vanity_url(api_key, steam_id_str)로 변환
        if not steam_id_str.isdigit():
            steam_id_str = self.resolve_vanity_url(api_key, steam_id_str)
            if not steam_id_str:
                return []

        # 2) API 호출
        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        params = {
            "key": api_key,
            "steamid": steam_id_str,
            #"include_appinfo": True,           # 게임 이름 등 추가 정보
            #"include_played_free_games": True  # Free to play 게임도 포함할지 여부
        }
        try:
            resp = requests.get(url, params=params).json()
        except Exception as e:
            print("Error fetching owned games:", e)
            return []

        # 3) 응답 파싱
        games = resp.get("response", {}).get("games", [])
        if not games:
            # 게임이 하나도 없거나 비공개인 경우
            return []

        # 4) playtime_forever (분) → 시간 단위로 변환, 내림차순 정렬
        game_data = []
        for g in games:
            app_id = g.get("appid")
            pt_min = g.get("playtime_forever", 0)  # 분 단위
            pt_hr = round(pt_min / 60.0, 2)        # 시간 단위 (소수점 2자리 예시)
            game_data.append({"app_id": str(app_id), "playtime": pt_hr})

        # 5) 플레이 타임 내림차순 정렬 후 상위 2개
        sorted_data = sorted(game_data, key=lambda x: x["playtime"], reverse=True)
        top2 = sorted_data[:2]
        return top2


    # -------------------------------------------------------
    # (E) 커스텀 URL -> 64비트 steamid 변환 (ResolveVanityURL)
    # 테스트는 아직 못함..
    # -------------------------------------------------------

    def resolve_vanity_url(self, api_key, vanity_str):
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        params = {"key": api_key, "vanityurl": vanity_str}
        resp = requests.get(url, params=params).json()
        success = resp.get("response", {}).get("success", 42)
        if success == 1:
            return resp["response"]["steamid"]  # 64비트 ID
        else:
            return None
