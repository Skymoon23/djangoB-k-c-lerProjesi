from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from django.db import IntegrityError
from course_management.models import Student


class Command(BaseCommand):
    help = 'Belirtilen Excel/CSV dosyasından öğrenci verilerini içe aktarır.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='İçe aktarılacak Excel/CSV dosyasının tam yolu')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            self.stdout.write(self.style.NOTICE(f'"{file_path}" yolu okunuyor...'))
            df = pd.read_excel(file_path)
            kayit_sayisi = 0

            for index, row in df.iterrows():
                try:
                    username = row['username']
                    password = row['password']
                    first_name = row['first_name']
                    last_name = row['last_name']
                    student_number = row['student_number']

                    # User oluştur veya al
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                        }
                    )

                    # Şifreyi her durumda uygula (yeni veya eski kullanıcı farketmez)
                    if created or not user.check_password(password):
                        user.set_password(str(password))
                        user.save()

                    # Student oluştur
                    Student.objects.get_or_create(
                        user=user,
                        defaults={
                            'student_number': student_number,
                            'department': ""
                        }
                    )

                    kayit_sayisi += 1

                except IntegrityError:
                    self.stdout.write(
                        self.style.WARNING(f"Uyarı: Kullanıcı veya Okul Numarası zaten mevcut. Kayıt atlandı."))

                except KeyError as e:
                    self.stdout.write(self.style.ERROR(
                        f"Hata: CSV'de '{e.args[0]}' sütunu bulunamadı. Lütfen sütun başlıklarını kontrol edin."))
                    raise CommandError('Veri aktarımı durduruldu.')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Hata: {username} kaydedilemedi. Hata: {e}"))

            self.stdout.write(self.style.SUCCESS(f'Başarıyla {kayit_sayisi} öğrenci kaydı veritabanına eklendi!'))

        except FileNotFoundError:
            raise CommandError(f'Belirtilen dosya bulunamadı: "{file_path}"')
        except Exception as e:
            raise CommandError(f'Dosya işlenirken genel bir hata oluştu: {e}')
