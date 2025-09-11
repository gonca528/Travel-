from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import yagmail


def _get_secret(key: str):
    try:
        import streamlit as st
        try:
            return st.secrets[key]
        except Exception:
            return None
    except Exception:
        return None


class EmailService:
    def __init__(self):
        load_dotenv()
        sender_email = _get_secret("EMAIL_SENDER") or os.getenv("EMAIL_SENDER")
        sender_password = _get_secret("EMAIL_PASSWORD") or os.getenv("EMAIL_PASSWORD")
        if not sender_email or not sender_password:
            raise ValueError("EMAIL_SENDER or EMAIL_PASSWORD is not set in environment variables/secrets.")
        self.yag = yagmail.SMTP(user=sender_email, password=sender_password)
        self.sender_email = sender_email

    def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        try:
            self.yag.send(to=to_email, subject=subject, contents=html_body)
            return True
        except Exception as exc:
            print(f"Error sending email: {exc}")
            return False

    def format_favorite_trips_html(self, favorite_trips: List[Dict[str, Any]]) -> str:
        if not favorite_trips:
            return "<p>Favori geziniz bulunamadı.</p>"

        items_html = []
        for item in favorite_trips:
            title = item.get("place_name") or item.get("name") or "Bilinmeyen Mekan"
            description = item.get("description") or "Açıklama mevcut değil."
            category = item.get("category") or "Kategori yok"
            rating = item.get("rating")
            images = item.get("image_urls") or []

            images_html = "".join([f'<img src="{url}" alt="{title}" style="max-width:200px;margin-right:8px;margin-bottom:8px;" />' for url in images])
            rating_html = f"<p><strong>Puan:</strong> {rating} ⭐</p>" if rating is not None else ""

            items_html.append(
                f"""
                <div style='border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:12px;'>
                    <h3 style='margin:0 0 8px 0;'>{title}</h3>
                    <p style='margin:0 0 6px 0;'><strong>Kategori:</strong> {category}</p>
                    {rating_html}
                    <p style='margin:8px 0;'>{description}</p>
                    <div>{images_html}</div>
                </div>
                """
            )

        html = (
            """
            <div style='font-family:Arial, Helvetica, sans-serif;'>
                <h2 style='margin-bottom:16px;'>Favori Gezi Listeniz</h2>
                <p style='margin-top:0;'>Aşağıda e-posta ile paylaştığınız favori mekanlarınız yer almaktadır.</p>
                {items}
                <p style='color:#6b7280;margin-top:24px;'>Akıllı Gezi Rehberi ile iyi gezmeler!</p>
            </div>
            """
        ).format(items="\n".join(items_html))
        return html

    def send_favorite_trips_email(self, to_email: str, favorite_trips: List[Dict[str, Any]]) -> bool:
        subject = "Favori Gezileriniz"
        html_body = self.format_favorite_trips_html(favorite_trips)
        return self.send_email(to_email, subject, html_body)

