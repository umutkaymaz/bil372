CREATE DATABASE buharindan;

USE buharindan;

CREATE TABLE users_table (
	user_id varchar(20) PRIMARY KEY,
	user_name varchar(50) NOT NULL,
	user_city varchar(20) NOT NULL,
	user_restofaddress varchar(100) NOT NULL,
	user_phonenumber char(11) NOT NULL,
	user_passwordhashes TEXT NOT NULL
);

CREATE TABLE listings_table (
    listing_id INT(9) PRIMARY KEY auto_increment,
    listing_name VARCHAR(200) NOT NULL,
    listing_price DECIMAL(6,2) NOT NULL,
    listing_ownerid VARCHAR(20) NOT NULL,
    listing_condition ENUM('Kusursuz', 'İyi', 'Orta', 'Yıpranmış') NOT NULL,
    listing_date DATE NOT NULL,
    listing_desc VARCHAR(200),
    listing_imagepath text,
    FOREIGN KEY (listing_ownerid) REFERENCES users_table(user_id)
);


CREATE TABLE comments_table (
	comment_id int(9) PRIMARY KEY AUTO_INCREMENT,
	comment_content varchar(200) NOT NULL,
	comment_date date NOT NULL,
	comment_ownerid varchar(20) NOT NULL,
	comment_listingid int(9) NOT NULL,
	FOREIGN KEY (comment_ownerid) REFERENCES users_table(user_id),
	FOREIGN KEY (comment_listingid) REFERENCES listings_table(listing_id)
);

CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name ENUM(
        'Aksiyon', 'Macera', 'Rol Yapma', 'Strateji',
        'Simülasyon', 'Spor', 'Bulmaca',
        'Hayatta Kalma', 'Korku', 'Platform'
    ) NOT NULL UNIQUE
);

CREATE TABLE listing_genres (
    listing_id INT NOT NULL,
    genre_id INT NOT NULL,

    PRIMARY KEY (listing_id, genre_id),

    FOREIGN KEY (listing_id) REFERENCES listings_table(listing_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
);

INSERT INTO genres (genre_name) VALUES
('Aksiyon'),
('Macera'),
('Rol Yapma'),
('Strateji'),
('Simülasyon'),
('Spor'),
('Bulmaca'),
('Hayatta Kalma'),
('Korku'),
('Platform');

INSERT INTO users_table (
    user_id, user_name, user_city, user_restofaddress, user_phonenumber, user_passwordhashes
) VALUES
('davidgilmour70',   'David Gilmour',    'İstanbul',    'Kadıköy, Moda Mahallesi',      '05510000001', 'hash_david'),
('thomyorke68',      'Thom Yorke',       'Ankara',      'Çankaya, Bahçelievler',        '05510000002', 'hash_thom'),
('kurtcobain67',     'Kurt Cobain',      'İzmir',       'Karşıyaka, Bostanlı',          '05510000003', 'hash_kurt'),
('freddiemercury46', 'Freddie Mercury',  'Bursa',       'Nilüfer, FSM Bulvarı',         '05510000004', 'hash_freddie'),
('jameshetfield63',  'James Hetfield',   'Antalya',     'Konyaaltı, Liman Mah.',        '05510000005', 'hash_james'),
('haykocepkin81',    'Hayko Cepkin',     'Eskişehir',   'Tepebaşı, Üniversite Cad.',    '05510000006', 'hash_hayko'),
('barismanco1923',   'Barış Manço',      'Trabzon',     'Ortahisar, Meydan Mah.',       '05510000007', 'hash_baris'),
('cemkaraca1945',    'Cem Karaca',       'Gaziantep',   'Şahinbey, Çarşı İçleri',       '05510000008', 'hash_cem'),
('ozzyosbourne48',   'Ozzy Osbourne',    'Kayseri',     'Melikgazi, Merkez Mah.',       '05510000009', 'hash_ozzy'),
('kirkhammett62',    'Kirk Hammett',     'Diyarbakır',  'Kayapınar, Bulvar Cad.',       '05510000010', 'hash_kirk');

-- 20 İLAN (listing_imagepath = NULL)
INSERT INTO listings_table (
    listing_name, listing_price, listing_ownerid,
    listing_condition, listing_date, listing_desc, listing_imagepath
) VALUES
('The Witcher 3: Wild Hunt (PC)',        350.00, 'davidgilmour70',   'İyi',        '2024-11-01', 'Tüm DLC''ler dahil, kutulu PC sürümü. Çizik yok.', '/images/1.jpg'),
('Elden Ring (PS5)',                     800.00, 'thomyorke68',      'Kusursuz',   '2024-10-15', 'Bir kez bitirildi, tertemiz durumda, faturasız.', NULL),
('Red Dead Redemption 2 (PS4)',          450.00, 'kurtcobain67',     'İyi',        '2024-09-20', 'Kapağında ufak deformeler var, disk sorunsuz.', NULL),
('Cyberpunk 2077 (PC)',                  300.00, 'freddiemercury46', 'Orta',       '2024-08-10', 'Kutu yıpranmış, oyun sorunsuz çalışıyor.', NULL),
('Hades (Nintendo Switch)',              600.00, 'jameshetfield63',  'Kusursuz',   '2024-07-05', 'Neredeyse hiç oynanmadı, tertemiz kartuş.', NULL),
('Hollow Knight (PC)',                   200.00, 'haykocepkin81',    'İyi',        '2024-06-18', 'Steam hesabı devri değil, kutulu lisans.', NULL),
('God of War Ragnarök (PS5)',            900.00, 'barismanco1923',   'Kusursuz',   '2024-11-25', 'Sadece ana senaryo oynandı, çizik yok.', '/images/7.webp'),
('The Last of Us Part II (PS4)',         350.00, 'cemkaraca1945',    'İyi',        '2024-05-30', 'Kapakta hafif çizik var, disk temiz.', '/images/8.jpg'),
('Sekiro: Shadows Die Twice (PC)',       400.00, 'ozzyosbourne48',   'Orta',       '2024-04-22', 'Kutu köşeleri ezik, çalışmasında sorun yok.', NULL),
('Dark Souls III (PS4)',                 320.00, 'kirkhammett62',    'Yıpranmış',  '2024-03-12', 'Diskte hafif çizikler var ama açılıyor.', NULL),
('Grand Theft Auto V (PS4)',             280.00, 'davidgilmour70',   'Orta',       '2024-02-01', 'Online pek oynanmadı, hikaye bitmiş durumda.', '/images/11.jpg'),
('Stardew Valley (Nintendo Switch)',     550.00, 'thomyorke68',      'Kusursuz',   '2024-01-20', 'Kutu, kitapçık tam, hediye gelen oyun.', NULL),
('Sid Meier''s Civilization VI (PC)',    260.00, 'kurtcobain67',     'İyi',        '2023-12-10', 'Strateji sevenler için ideal, kutu sağlam.', NULL),
('Minecraft (PS4)',                      300.00, 'freddiemercury46', 'İyi',        '2023-11-05', 'Çocuk için alınmıştı, az oynandı.', NULL),
('Portal 2 (PC)',                        150.00, 'jameshetfield63',  'Orta',       '2023-10-01', 'Eski kutu, nostalji sevenler için.', NULL),
('Resident Evil 4 Remake (PS5)',         850.00, 'haykocepkin81',    'Kusursuz',   '2024-09-01', 'Tek oturuşta bitirildi, çizik yok.', NULL),
('Bloodborne (PS4)',                     400.00, 'barismanco1923',   'İyi',        '2023-09-15', 'Sert kapak hafif çizik, disk temiz.', '/images/17.webp'),
('Celeste (Nintendo Switch)',            500.00, 'cemkaraca1945',    'Kusursuz',   '2024-06-01', 'Koleksiyon için alınmış, hiç oynanmadı.', '/images/18.webp'),
('Disco Elysium: Final Cut (PC)',        330.00, 'ozzyosbourne48',   'İyi',        '2024-05-05', 'Hikaye odaklı oyunları sevene tavsiye edilir.', NULL),
('Baldur''s Gate 3 (PC)',                950.00, 'kirkhammett62',    'Kusursuz',   '2024-11-10', 'Sadece Act 1 oynandı, neredeyse yeni gibi.', NULL);

-- 30 YORUM
INSERT INTO comments_table (
    comment_content, comment_date, comment_ownerid, comment_listingid
) VALUES
('Fiyat biraz yüksek gibi, pazarlık payı var mı?',                    '2024-11-02', 'thomyorke68',      1),
('Kaydetme dosyası da yanında veriliyor mu?',                         '2024-11-03', 'kurtcobain67',     1),
('Kargo yapar mısınız, İstanbul dışına gönderim var mı?',             '2024-11-04', 'jameshetfield63',  1),

('Oyun tertemiz duruyor, kutunun fotoğrafını ekleyebilir misiniz?',   '2024-10-16', 'davidgilmour70',   2),
('Takasa açık mısınız, elimde God of War var.',                       '2024-10-17', 'freddiemercury46', 2),

('Hesap devri değil değil mi, sadece disk?',                          '2024-09-21', 'haykocepkin81',    3),
('Online modu sorunsuz çalışıyor mu hâlâ?',                           '2024-09-22', 'barismanco1923',   3),

('Patch sonrası performans nasıl, kasma oluyor mu?',                  '2024-08-11', 'cemkaraca1945',    4),
('Kutu yıpranmış yazmışsınız, disk durumu nasıl?',                    '2024-08-12', 'ozzyosbourne48',   4),

('Elden Ring ile takas düşünür müsünüz?',                             '2024-07-06', 'kirkhammett62',    5),
('Fiyat son mu, 550 olsa hemen alırım.',                              '2024-07-07', 'kurtcobain67',     5),

('Steam sürümü mü, aktivasyon nasıl oluyor?',                         '2024-06-19', 'thomyorke68',      6),

('God of War ile birlikte paket yaparsanız ikisini alırım.',          '2024-11-26', 'haykocepkin81',    7),
('Diskte herhangi bir çizik var mı, fotoğraf atar mısınız?',          '2024-11-26', 'cemkaraca1945',    7),

('Oyun Türkçe altyazı destekli mi?',                                  '2024-05-31', 'davidgilmour70',   8),
('Kampanya döneminde mi alınmıştı, fatura mevcut mu?',                '2024-06-01', 'ozzyosbourne48',   8),

('Zorluk seviyesi çok mu yüksek, tavsiye eder misiniz?',              '2024-04-23', 'jameshetfield63',  9),

('Çalıştırırken ses yapıyor mu, konsol sıkıntısız mı?',               '2024-03-13', 'thomyorke68',      10),
('Kutusu yıpranmış yazıyor, hediye etmeye uygun mudur?',              '2024-03-14', 'freddiemercury46', 10),

('Online hesabı da veriyor musunuz, sadece disk mi?',                 '2024-02-02', 'barismanco1923',   11),
('Kargo dahili mi yoksa alıcı mı ödeyecek?',                          '2024-02-03', 'kirkhammett62',    11),

('Co-op oynanabiliyor mu, ikinci joy-con gerekiyor mu?',              '2024-01-21', 'davidgilmour70',   12),

('Tüm DLC paketleri mevcut mu?',                                      '2023-12-11', 'cemkaraca1945',    13),

('Diskte bölgesel kilit var mı, TR PSN ile uyumlu mu?',               '2023-11-06', 'kurtcobain67',     14),

('Kutusu hasarlı yazmışsınız, fotoğraf paylaşabilir misiniz?',        '2023-10-02', 'haykocepkin81',    15),

('Oyunda Türkçe dil desteği var mı?',                                 '2024-09-02', 'jameshetfield63',  16),
('Ses sistemiyle oynayınca sesler nasıldır, tizler patlıyor mu?',     '2024-09-03', 'thomyorke68',      16),

('Bloodborne çok zor diyorlar, yeni başlayan için uygun mu?',         '2023-09-16', 'ozzyosbourne48',   17),

('Fiyat biraz tuzlu ama koleksiyonluk gibi duruyor.',                 '2024-06-02', 'freddiemercury46', 18),

('Hikaye odaklı oyun seviyorum, pişman eder mi?',                     '2024-05-06', 'barismanco1923',   19),

('Bu fiyata kaçırılmaz gibi, hala satılık mı?',                       '2024-11-11', 'davidgilmour70',   20);