import csv
from django.core.management.base import BaseCommand
from accounts.models import Game

class Command(BaseCommand):
    help = "이 커맨드를 통해 CSV 파일의 데이터를 Game 모델에 적재합니다."

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='CSV 파일의 경로')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # 데이터를 Game 모델에 저장
                    Game.objects.get_or_create(
                        appID=int(row['appID']),
                        name=row['name'],
                        release_date=row['release_date'],
                        required_age=int(row['required_age']) if row['required_age'] != '' else 0,
                        price=float(row['price']) if row['price'] != '' else 0.0,
                        header_image=row['header_image'],
                        windows=row['windows'].lower() == 'true',
                        mac=row['mac'].lower() == 'true',
                        linux=row['linux'].lower() == 'true',
                        metacritic_score=int(row['metacritic_score']) if row['metacritic_score'] != '' else 0,
                        metacritic_url=row['metacritic_url'],
                        supported_languages=eval(row['supported_languages']) if row['supported_languages'] else [],
                        categories=eval(row['categories']) if row['categories'] else [],
                        genres=eval(row['genres']) if row['genres'] else [],
                        screenshots=eval(row['screenshots']) if row['screenshots'] else [],
                        movies=eval(row['movies']) if row['movies'] else [],
                        estimated_owners=row['estimated_owners'],
                        median_playtime_forever=int(row['median_playtime_forever']) if row['median_playtime_forever'] != '' else 0,
                        tags=eval(row['tags']) if row['tags'] else {}
                    )
            
            self.stdout.write(self.style.SUCCESS("CSV 데이터를 성공적으로 적재했습니다."))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"파일을 찾을 수 없습니다: {file_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"오류 발생: {str(e)}"))