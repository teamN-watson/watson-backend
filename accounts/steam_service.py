import environ
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
import re
from accounts.models import (
    Account,
    SteamProfile,
    SteamReview,
    SteamPlaytime,
)

import requests
from bs4 import BeautifulSoup



def sync_new_steam_user_data(account):
    """
    신규 유저(steamId 연동)의 프로필/리뷰/플레이타임 정보를 DB에 저장.
    - 커스텀 URL 처리 제외
    - 기존 데이터 전부 삭제 없이, 프로필 공개 여부, 리뷰·플레이타임만 추가(get_or_create)
    """
    steam_id_str = account.steamId.strip()
    if not steam_id_str.isdigit():
        # 64비트 ID가 아니라면 처리 불가(커스텀 URL 변환 제외)
        return
    
    # .env에서 Steam API 키 불러오기
    env = environ.Env()
    api_key = env("STEAM_API_KEY")

    # 1) 프로필 공개 여부
    if not check_profile_public(api_key, steam_id_str):
        # 프로필이 Private -> 리뷰/플레이타임 비활성화
        sp, _ = SteamProfile.objects.get_or_create(account=account)
        sp.is_review = False
        sp.is_playtime = False
        sp.save()
        return
    
    # 2) 리뷰 크롤링(최대 3개) -> BeautifulSoup 이용
    review_data = fetch_top3_reviews(steam_id_str)


    # 3) 플레이타임(상위 2개) API 조회
    playtime_data = fetch_top2_playtime_api(api_key, steam_id_str)

    is_review = bool(review_data)
    is_playtime = bool(playtime_data)

    # 4) DB 저장
    with transaction.atomic():
        sp, _ = SteamProfile.objects.get_or_create(account=account)
        sp.is_review = is_review
        sp.is_playtime = is_playtime
        sp.save()

        # 기존 리뷰·플레이타임 삭제 대신, 중복 없는 새 데이터만 추가
        if review_data:
            for rd in review_data:
                SteamReview.objects.get_or_create(
                    account=account,
                    app_id=rd["app_id"]
                )
        if playtime_data:
            for pd in playtime_data:
                SteamPlaytime.objects.get_or_create(
                    account=account,
                    app_id=pd["app_id"]
                )


def check_profile_public(api_key, steam_id_str):
    """
    64비트 steamId (digit)인 경우만 public 여부 확인
    """
    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {"key": api_key, "steamids": steam_id_str}
    resp = requests.get(url, params=params).json()
    players = resp.get("response", {}).get("players", [])
    if not players:
        return False
    player = players[0]
    vis_state = player.get("communityvisibilitystate", 1)
    return (vis_state == 3)


def fetch_top3_reviews(steam_id_str):
    """
    Selenium 없이 상위 3개의 'Recommended' 리뷰 정보를 가져온다.
    """
    url = f"https://steamcommunity.com/profiles/{steam_id_str}/recommended"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/87.0.4280.66 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"Error fetching reviews page: {e}")
        return []

    if response.status_code != 200:
        # 프로필이 Private 상태거나 접근 실패 시 빈 리스트 반환
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    review_boxes = soup.select(".review_box")
    
    recommended = []
    for box in review_boxes:
        try:
            title_elem = box.select_one(".vote_header .title > a")
            if not title_elem or "Recommended" not in title_elem.text:
                continue

            href = title_elem.get("href", "")
            if "/recommended/" not in href:
                continue

            app_id = href.split("/recommended/")[1].split("/")[0]
            recommended.append({"app_id": app_id})

            if len(recommended) >= 3:
                break
        except Exception as e:
            print(f"리뷰 박스 처리 중 오류 발생: {e}")
            continue

    return recommended


def fetch_top2_playtime_api(api_key, steam_id_str):
    """
    GetOwnedGames API로 플레이타임이 가장 많은 상위 2개 게임(app_id) 반환.
    """
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {"key": api_key, "steamid": steam_id_str}
    try:
        resp = requests.get(url, params=params).json()
    except Exception as e:
        print("Error fetching owned games:", e)
        return []

    games = resp.get("response", {}).get("games", [])
    if not games:
        return []

    game_data = []
    for g in games:
        app_id = g.get("appid")
        pt_min = g.get("playtime_forever", 0)
        pt_hr = round(pt_min / 60.0, 2)
        game_data.append({"app_id": str(app_id), "playtime": pt_hr})

    # 플레이타임 내림차순 정렬 후 상위 2개
    sorted_data = sorted(game_data, key=lambda x: x["playtime"], reverse=True)
    return sorted_data[:2]