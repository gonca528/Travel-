# 🌍 Akıllı Gezi Rehberi  

Akıllı Gezi Rehberi, seyahat planlamanızı yaparken size özel öneriler sunan akıllı bir rehberdir.  
Seçtiğiniz şehir, kategori ve ek özelliklere göre en uygun gezi noktalarını listeler.  
## 🚀 Proje Hakkında  

- Kullanıcı, gitmek istediği şehri seçer.  
- **Kategori Seçenekleri:** Doğa, Müze, Kültür  
- **Ek Özellikler:** Yemek, Otopark, Wi-Fi  
- Filtreleme sonrasında kullanıcıya önerilen gezi yerleri **kart yapısında** gösterilir.  
- Kartlarda şu bilgiler yer alır:  
  - Puan bilgisi  
  - Önerilen ziyaret saati  
  - Merkeze uzaklık  
  - Genel açıklama  
  - Seçilen ek özelliklere dair bilgiler  
- Harita üzerinde önerilen yerler görüntülenebilir.  
- Hava durumu bilgisi seçilen tarih aralığı için alınır.  
- Kullanıcı, gezi planını **e-posta ile paylaşabilir**.  

---
## 🛠 Kullanılan Teknolojiler  

- **Python**  
- **Streamlit** – web arayüzü  
- **Recommendation Engine** – kişiselleştirilmiş öneriler  
- **Weather Service** – hava durumu entegrasyonu  
- **Email Service** – planları e-posta ile gönderme  
- **Map Component** – önerilen yerleri harita üzerinde gösterme  
- **UUID** – kullanıcı/oturum kimlikleri oluşturma  
## 📦 Gerekli Kütüphaneler  
- **import streamlit as st**  
- **import uuid**  
- **from services.recommendation_engine import RecommendationEngine, RecommendationResult**  
- **from components.recommendation_cards import display_recommendation_card**  
- **from components.map_component import map_component**  
- **from components.filters_component import filters_component**  
- **from services.email_service import EmailService**  
- **from services.weather_service import WeatherService**  
- **from datetime import date, timedelta**
---

## 🛠 Projeye Dair Görseller

Burası, kullanıcının kendi seçimlerine göre belirlediği kısımdır.
![Capstone9](images/Capstone1.jpeg)

