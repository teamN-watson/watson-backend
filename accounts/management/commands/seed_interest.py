from django.core.management.base import BaseCommand
from django_seed import Seed
from accounts.models import Account, Interest, Tag


class Command(BaseCommand):
    help = "이 커맨드를 통해 게임 태그 데이터를 만듭니다."

    def handle(self, *args, **options):
        tags = [
            "핵 앤 슬래시",
            "전략",
            "실시간 전략",
            "액션 RPG",
            "롤플레잉",
            "오픈월드",
            "싱글 플레이어",
            "멀티 플레이어",
        ]

        games = [
            {"name": "리그오브레전드", "tags": ["Multiplayer", "MOBA"]},
            {"name": "로스트아크", "tags": ["RPG", "MMORPG", "Hack and Slash"]},
            {
                "name": "포켓몬스터",
                "tags": ["Creature Collector", "Turn-Based Strategy", "Exploration"],
            },
            {
                "name": "젤다의전설",
                "tags": ["Open World", "Sandbox", "Exploration", "액션 어드벤처"],
            },
            {
                "name": "마인크래프트",
                "tags": [
                    "Sandbox",
                    "Crafting",
                    "Open World Survival Craft",
                    "Multiplayer",
                ],
            },
            {"name": "서든어택", "tags": ["Shooter", "Survival", "PvP", "1인칭 슈팅"]},
            {
                "name": "오버워치",
                "tags": ["Multiplayer", "Hero Shooter", "Action", "Team-Based"],
            },
            {"name": "스타크래프트", "tags": ["RTS", "Real Time Tactics"]},
            {"name": "피파온라인", "tags": ["Sports", "eSports", "Football (Soccer)"]},
            {"name": "하스스톤", "tags": [""]},
            {"name": "디아블로", "tags": [""]},
            {"name": "패스 오브 엑자일", "tags": [""]},
            {"name": "포르자 호라이즌", "tags": ["레이싱"]},
            {"name": "알투비트", "tags": ["리듬게임"]},
            {"name": "", "tags": [""]},
            {"name": "", "tags": [""]},
        ]
        # for game in games:
        # Interest.objects.get_or_create

        self.stdout.write(self.style.SUCCESS(f"게임 태그 정보 생성 완료."))
