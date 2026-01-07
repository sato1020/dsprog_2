import sqlite3
import flet as ft
from datetime import datetime

# 定数
DB_NAME = 'weather.db'
ICON_URL = "https://www.jma.go.jp/bosai/forecast/img/{}.svg"
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

class WeatherAppDB(ft.Container):
    def __init__(self):
        super().__init__()
        # 後に書かれたコードのUI設定を反映
        self.width = 800
        self.padding = 20
        self.bgcolor = ft.Colors.LIGHT_BLUE_50
        self.border_radius = 15
        
        # 週間予報を表示する横スクロールエリア
        self.forecast_row = ft.Row(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        # データベースから地域リストを取得してドロップダウンを作成
        self.area_select = ft.Dropdown(
            label="地域を選択",
            width=300,
            on_change=self.display_weather_from_db,
            options=self.get_area_options_from_db()
        )

        self.status_text = ft.Text("地域を選択してください", size=16, color=ft.Colors.GREY_700)

        # 全体のレイアウト構成
        self.content = ft.Column(
            controls=[
                ft.Text("週間天気予報アプリ (DB版)", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                self.area_select,
                ft.Divider(),
                self.status_text,
                ft.Container(
                    content=self.forecast_row,
                    padding=10,
                    height=280,
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def get_area_options_from_db(self):
        """DBから保存されている地域名とコードを取得してドロップダウンの選択肢にする"""
        options = []
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT area_code, city_name FROM weather ORDER BY area_code")
            rows = cur.fetchall()
            for code, name in rows:
                options.append(ft.dropdown.Option(key=code, text=name))
            conn.close()
        except Exception as e:
            print(f"DB読み込みエラー: {e}")
        return options

    def display_weather_from_db(self, e):
        """選択された地域のデータをDBから読み込んでカードを表示"""
        area_code = self.area_select.value
        if not area_code:
            return

        # UIのリセット
        self.forecast_row.controls.clear()
        
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row # カラム名でアクセスできるようにする
            cur = conn.cursor()
            
            # SQLで対象地域のデータを取得
            cur.execute("SELECT * FROM weather WHERE area_code = ? ORDER BY date ASC", (area_code,))
            rows = cur.fetchall()
            
            if rows:
                area_name = rows[0]["city_name"]
                self.status_text.value = f"{area_name} の週間天気"
                
                for row in rows:
                    # 日付のフォーマット整形
                    # DB内の '2026-01-07T...' から '1/7 (水)' の形式を作る
                    dt = datetime.fromisoformat(row["date"])
                    date_str = f"{dt.month}/{dt.day} ({WEEKDAYS[dt.weekday()]})"
                    
                    # カードを作成して追加（後に書かれたコードのUIを再現）
                    card = self.create_daily_card(
                        date_text=date_str,
                        weather_code=row["weather_code"],
                        pop=row["pop"],
                        t_min=row["temp_min"],
                        t_max=row["temp_max"]
                    )
                    self.forecast_row.controls.append(card)
            else:
                self.status_text.value = "データがDBに見つかりませんでした"
            
            conn.close()
        except Exception as ex:
            self.status_text.value = "DBデータの読み込みに失敗しました"
            print(f"詳細エラー: {ex}")
        
        self.update()

    def create_daily_card(self, date_text, weather_code, pop, t_min, t_max):
        """後に書かれたコードと全く同じデザインのカードUI"""
        # 降水確率の表示調整（DBが数値のみの場合を考慮）
        pop_display = f"{pop}%" if "%" not in str(pop) and pop != "-" else pop

        return ft.Container(
            width=100,
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLUE_GREY_100,
            ),
            content=ft.Column(
                controls=[
                    ft.Text(date_text, weight=ft.FontWeight.BOLD, size=14, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=5),
                    ft.Image(
                        src=ICON_URL.format(weather_code),
                        width=50, height=50,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    ft.Text(f"降水 {pop_display}", size=12, color=ft.Colors.BLUE),
                    ft.Divider(height=5),
                    ft.Row(
                        controls=[
                            ft.Text(f"{t_max}℃", color=ft.Colors.RED, size=12),
                            ft.Text("/", size=12),
                            ft.Text(f"{t_min}℃", color=ft.Colors.BLUE, size=12),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.START
            )
        )

def main(page: ft.Page):
    page.title = "Weekly Weather App (DB-UI Integrated)"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE_GREY_100
    
    # 統合されたDB版アプリを追加
    app = WeatherAppDB()
    page.add(app)

if __name__ == "__main__":
    ft.app(target=main)