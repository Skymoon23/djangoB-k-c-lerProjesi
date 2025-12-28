# Ders Yönetimi ve Çıktı Değerlendirme Sistemi (OBE)

Bu proje, üniversite bölümleri için geliştirilmiş, **Öğrenci**, **Öğretim Görevlisi** ve **Bölüm Başkanı** rollerini içeren kapsamlı bir ders yönetim sistemidir. Sistem, klasik not takibinin ötesine geçerek, derslerin öğrenim çıktıları (Learning Outcomes) ile program çıktıları (Program Outcomes) arasındaki ilişkiyi analiz eden **Çıktı Tabanlı Eğitim (Outcome Based Education)** altyapısına sahiptir.

## Özellikler

Proje `course_management` uygulaması altında şu temel yetenekleri sunar:

* **Gelişmiş Kullanıcı Yönetimi:**
    * `Profile` modeli üzerinden Öğrenci, Öğretim Görevlisi ve Bölüm Başkanı rolleri.
    * Kullanıcıların sisteme giriş ve yetkilendirme süreçleri.

* **Ders ve Müfredat İşlemleri:**
    * Ders oluşturma, kodlama ve hoca atamaları.
    * Öğrencilerin derslere kaydı (`Enrolled Courses`).
    * Ders izlencesi (Syllabus) yükleme (PDF/Docx).

* **Değerlendirme ve Not Sistemi:**
    * Her ders için dinamik değerlendirme bileşenleri (Vize, Final, Proje vb.) tanımlama.
    * Her bileşenin başarı notuna etki yüzdesini belirleme.
    * Öğrenci not girişi ve takibi.

* **Çıktı Tabanlı Değerlendirme (OBE):**
    * **Program Çıktıları (PO):** Bölümün genel hedeflerinin tanımlanması.
    * **Öğrenim Çıktıları (LO):** Her dersin kazandırmayı hedeflediği yetkinlikler.
    * **İlişki Matrisleri:**
        * Sınav Soruları/Bileşenleri <--> Öğrenim Çıktıları (Ağırlıklı).
        * Öğrenim Çıktıları <--> Program Çıktıları (Ağırlıklı).

* **Toplu Veri Aktarımı:**
    * Excel dosyası kullanarak sisteme toplu öğrenci kaydı yapabilme özelliği.



  ##  Proje Yapısı

Proje, rollerin ve işlevlerin ayrılması amacıyla modüler bir yapıda geliştirilmiştir:

```text
.
├── CSE311PROJECTT/          # Proje konfigürasyonları
├── course_management/       # Veritabanı modelleri ve temel mantık
├── headteacher/             # Bölüm başkanı paneli ve işlevleri
├── student/                 # Öğrenci paneli, not görüntüleme ve diğer özellikler
├── teacher/                 # Eğitmen paneli, not girişi ve diğer fonksiyonlar
├── templates/               # Frontend (HTML) dosyaları
├── manage.py                # Django yönetim aracı
└── requirements.txt         # Proje gereksinimleri
 ```   




## Teknolojiler

Proje aşağıdaki temel teknolojiler üzerine inşa edilmiştir:

* **Python 3.x**
* **Django** (v5.x)
* **Pandas:** Excel veri işleme ve toplu aktarımlar için.
* **Python-dotenv:** Ortam değişkenlerini yönetmek için.

## Kurulum Adımları

Projeyi yerel ortamınızda çalıştırmak için aşağıdaki adımları izleyin:

1.  **Projeyi Klonlayın:**
    ```bash
    git clone [https://github.com/kullaniciadi/proje-repo.git](https://github.com/kullaniciadi/proje-repo.git)
    cd proje-repo
    ```

2.  **Sanal Ortam Oluşturun ve Aktifleştirin:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Gereksinimleri Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Yeni SECRET_KEY alın ve Ayarlarını Yapılandırın**
    ```bash
    python manage.py shell
    >>> from django.core.management.utils import get_random_secret_key
        print(get_random_secret_key())
    ```
    
5.  **DEBUG Ayarını Yapın**
    # setting.py
    DEBUG = True

6.  **Veritabanı Oluşturma (Migrate):**
    ```bash
    python manage.py migrate
    ```

7.  **Yönetici Hesabı (Superuser) Oluşturun:**
    ```bash
    python manage.py createsuperuser
    ```

8.  **Sunucuyu Başlatın:**
    ```bash
    python manage.py runserver
    ```

## Kullanım Kılavuzu

### Toplu Öğrenci Ekleme
Sisteme öğrencileri tek tek eklemek yerine bir Excel dosyası ile toplu olarak yükleyebilirsiniz.

1.  Excel dosyanızda şu başlıkların olduğundan emin olun: `username`, `password`, `first_name`, `last_name`, `student_number`, `email`.
2.  Aşağıdaki komutu terminalde çalıştırın:
    ```bash
    python manage.py import_students "dosya_yolu/ogrenciler.xlsx"
    ```
    *Bu komut, mükerrer kayıtları (username veya öğrenci numarası) otomatik olarak atlar ve yeni kayıtları oluşturur.*

### Rol Tanımlama
Kayıt olan veya eklenen kullanıcıların sisteme erişebilmesi için `Profile` modeli üzerinden rollerinin (`student`, `instructor` vb.) atanması gerekmektedir. Bu işlem Django Admin paneli üzerinden yapılabilir.


---
*Geliştirici Notu: `requirements.txt` dosyasında belirtilen Django sürümü güncel kararlı sürümle uyumlu olacak şekilde yapılandırılmalıdır.*
