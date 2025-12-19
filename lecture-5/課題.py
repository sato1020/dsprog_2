import requests
import flet as ft
from datetime import datetime

# 定数
AREA_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
ICON_URL = "https://www.jma.go.jp/bosai/forecast/img/{}.svg"

# 曜日変換用
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

# エリアデータの取得
try:
    response = requests.get(AREA_URL)
    raw_data = response.json()
    offices_data = raw_data.get("offices", {})
except Exception as e:
    print(f"データ取得エラー: {e}")
    offices_data = {}

class WeatherApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.width = 800
        self.padding = 20
        self.bgcolor = ft.Colors.LIGHT_BLUE_50
        self.border_radius = 15
        
        # 週間予報を表示する横スクロールエリア
        self.forecast_row = ft.Row(
            spacing=10,
            scroll=ft.ScrollMode.AUTO, # 横スクロールを有効化
        )

        self.area_select = AreaSelect(
            on_area_changed=self.fetch_and_display_weather,
            data_json=offices_data
        )

        self.status_text = ft.Text("地域を選択してください", size=16, color=ft.Colors.GREY_700)

        self.content = ft.Column(
            controls=[
                ft.Text("週間天気予報アプリ", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                self.area_select,
                ft.Divider(),
                self.status_text,
                ft.Container(
                    content=self.forecast_row,
                    padding=10,
                    height=280, # カードの高さ確保
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def fetch_and_display_weather(self, e):
        area_code = self.area_select.value
        if not area_code:
            return

        area_name = offices_data[area_code]["name"]
        
        # リセット＆読み込み中表示
        self.forecast_row.controls.clear()
        self.status_text.value = f"{area_name} のデータを取得中..."
        self.forecast_row.controls.append(ft.ProgressRing())
        self.update()

        try:
            url = FORECAST_URL.format(area_code)
            res = requests.get(url)
            data = res.json()
            
            # data[1] が週間予報のデータを持っていることが多い
            # （地域やタイミングによってはdata[0]しかない場合もあるので簡易チェック）
            if len(data) > 1:
                weekly_data = data[1]
            else:
                weekly_data = data[0]

            # --- データの抽出 ---
            # 1. 天気コードと日付
            time_series_weather = weekly_data["timeSeries"][0]
            dates = time_series_weather["timeDefines"]
            area_weather = time_series_weather["areas"][0]
            weather_codes = area_weather["weatherCodes"]
            pops = area_weather.get("pops", []) # 降水確率

            # 2. 気温（最低・最高）
            temps_min = []
            temps_max = []
            if len(weekly_data["timeSeries"]) > 1:
                time_series_temp = weekly_data["timeSeries"][1]
                area_temp = time_series_temp["areas"][0]
                temps_min = area_temp.get("tempsMin", [])
                temps_max = area_temp.get("tempsMax", [])

            # ローディング消去
            self.forecast_row.controls.clear()
            self.status_text.value = f"{area_name} の週間天気"

            # --- カードの作成ループ ---
            for i in range(len(weather_codes)):
                # 日付のパース
                dt = datetime.fromisoformat(dates[i])
                date_str = f"{dt.month}/{dt.day} ({WEEKDAYS[dt.weekday()]})"
                
                code = weather_codes[i]
                pop = pops[i] + "%" if i < len(pops) and pops[i] else "-"
                
                # 気温（データ数が合わないことがあるため安全に取得）
                t_min = temps_min[i] if i < len(temps_min) and temps_min[i] else "-"
                t_max = temps_max[i] if i < len(temps_max) and temps_max[i] else "-"
                
                # カードを作成して追加
                card = self.create_daily_card(date_str, code, pop, t_min, t_max)
                self.forecast_row.controls.append(card)

        except Exception as ex:
            self.status_text.value = "情報の取得に失敗しました"
            self.forecast_row.controls.append(ft.Text(f"エラー詳細: {ex}", color=ft.Colors.RED))
        
        self.update()

    def create_daily_card(self, date_text, weather_code, pop, t_min, t_max):
        """1日分の情報を表示するカードUIを作成する関数"""
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
                    ft.Text(f"降水 {pop}", size=12, color=ft.Colors.BLUE),
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

class AreaSelect(ft.Dropdown):
    def __init__(self, on_area_changed, data_json):
        super().__init__()
        self.label = "地域を選択"
        self.width = 300
        self.on_change = on_area_changed
        self.data_json = data_json
        self.options = self.get_area_options()

    def get_area_options(self):
        options = []
        for code, info in self.data_json.items():
            options.append(ft.dropdown.Option(key=code, text=info["name"]))
        return options

def main(page: ft.Page):
    page.title = "Weekly Weather App"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE_GREY_100
    
    app = WeatherApp()
    page.add(app)

if __name__ == "__main__":
    ft.app(target=main)