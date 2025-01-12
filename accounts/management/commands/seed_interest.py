from django.core.management.base import BaseCommand
from django_seed import Seed
from accounts.models import Account, Interest, Tag


class Command(BaseCommand):
    help = "이 커맨드를 통해 게임 태그 데이터를 만듭니다."

    def handle(self, *args, **options):
        games = [
            {"name": "리그오브레전드", "tags": ["Team-Based", "MOBA", "eSports"]},
            {"name": "로스트아크", "tags": ["RPG", "MMORPG", "Hack and Slash"]},
            {
                "name": "포켓몬스터",
                "tags": ["Creature Collector", "Turn-Based Strategy", "Exploration"],
            },
            {
                "name": "젤다의전설",
                "tags": ["Open World", "Sandbox", "Exploration", "Action-Adventure"],
            },
            {
                "name": "마인크래프트",
                "tags": [
                    "Sandbox",
                    "Survival",
                    "Crafting",
                    "Open World Survival Craft",
                ],
            },
            {"name": "서든어택", "tags": ["Shooter", "Survival", "Competitive"]},
            {
                "name": "오버워치",
                "tags": [
                    "Team-Based",
                    "Hero Shooter",
                    "Action",
                    "Third-Person Shooter",
                ],
            },
            {
                "name": "스타크래프트",
                "tags": ["RTS", "Grand Strategy", "Real Time Tactics", "Space"],
            },
            {"name": "피파온라인", "tags": ["Sports", "eSports", "Football (Soccer)"]},
            {
                "name": "하스스톤",
                "tags": ["Turn-Based Strategy", "Card Game", "Card Battler"],
            },
            {
                "name": "디아블로",
                "tags": ["Hack and Slash", "Exploration", "Action RPG"],
            },
            {
                "name": "패스 오브 엑자일",
                "tags": ["Hack and Slash", "Exploration", "Action RPG"],
            },
            {"name": "알투비트", "tags": ["Casual", "Rhythm"]},
            {"name": "테일즈런너", "tags": ["Adventure", "Sports", "Racing"]},
            {"name": "카트라이더", "tags": ["Action", "Racing"]},
        ]
        for game in games:
            interest, _ = Interest.objects.get_or_create(name=game["name"])
            for tag in game["tags"]:
                get_tag = Tag.objects.get(name_en=tag)
                interest.tags.add(get_tag)

        self.stdout.write(self.style.SUCCESS(f"게임 태그 정보 생성 완료."))
