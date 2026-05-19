import json
import requests

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = "8615134295:AAGnodQA11PRpDgM4Tbij3z4aFaAKQX-ENg"
CHAT_ID = "2040061132"

SPREADSHEET_ID = "1wlUieP2Lxk5vrqbmv-3PCis82XP5P_zn6RBVr-MFunw"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

# =========================
# ПОДКЛЮЧЕНИЕ
# =========================

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

service = build(
    "sheets",
    "v4",
    credentials=creds
)

result = service.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID,
    includeGridData=True
).execute()

POSSIBLE_SHEETS = [
    "Весна(2026)",
    "test"
]

sheet = next(
    s for s in result["sheets"]
    if s["properties"]["title"] in POSSIBLE_SHEETS
)

rows = sheet["data"][0]["rowData"]

current = []

# =========================
# ЧТЕНИЕ ТАБЛИЦЫ
# =========================

for row in rows:

    row_cells = []

    values = row.get("values", [])

    for cell in values:

        text = cell.get(
            "formattedValue",
            ""
        )

        color = (
            cell.get(
                "effectiveFormat",
                {}
            )
            .get(
                "backgroundColor",
                {}
            )
        )

        row_cells.append({
            "text": text,
            "color": color
        })

    current.append(row_cells)

# =========================
# ЗАГРУЗКА СТАРЫХ ДАННЫХ
# =========================

try:

    with open(
        "old.json",
        "r",
        encoding="utf-8"
    ) as f:

        old = json.load(f)

except:

    old = current

# =========================
# ПОИСК ИЗМЕНЕНИЙ
# =========================

changes = []

for r in range(len(current)):

    current_row = current[r]

    if len(current_row) == 0:
        continue

    name = current_row[0]["text"].strip()

    # пропускаем пустые строки
    if not name:
        continue

    # пропускаем заголовок
    if name.lower() == "имя":
        continue

    old_row = old[r] if r < len(old) else []

    cols = max(len(current_row), len(old_row))

    for c in range(cols):

        old_cell = (
            old_row[c]
            if c < len(old_row)
            else {"text": "", "color": {}}
        )

        new_cell = (
            current_row[c]
            if c < len(current_row)
            else {"text": "", "color": {}}
        )

        old_text = old_cell["text"]
        new_text = new_cell["text"]

        old_color = old_cell["color"]
        new_color = new_cell["color"]

        # название колонки
        header = ""

        if (
            len(current) > 0
            and len(current[0]) > c
        ):
            header = current[0][c]["text"]

        # =========================
        # ИЗМЕНЕНИЕ ТЕКСТА
        # =========================

        if old_text != new_text:

            # появилось новое значение
            if old_text == "" and new_text != "":

                if new_text == "1":

                    changes.append(
                        f"⚠️ {name}\n"
                        f"└ {header}: появилась 1"
                    )

                else:

                    changes.append(
                        f"✏️ {name}\n"
                        f"└ {header}: {new_text}"
                    )

            else:

                changes.append(
                    f"🔄 {name}\n"
                    f"└ {header}: "
                    f"{old_text} → {new_text}"
                )

        # =========================
        # ИЗМЕНЕНИЕ ЦВЕТА
        # =========================

        elif old_color != new_color:

            red = new_color.get("red", 0)
            green = new_color.get("green", 0)
            blue = new_color.get("blue", 0)

            # красный
            if red > 0.8 and green < 0.6:

                changes.append(
                    f"🔴 {name}\n"
                    f"└ {header}: "
                    f"ячейка стала красной"
                )

            # зелёный
            elif green > 0.8 and red < 0.7:

                changes.append(
                    f"🟢 {name}\n"
                    f"└ {header}: "
                    f"ячейка стала зелёной"
                )

# =========================
# ОТПРАВКА В TELEGRAM
# =========================

if changes:

    text = (
        "📊 Изменения в таблице\n\n"
        + "\n\n".join(changes[:15])
    )

    if len(changes) > 15:

        text += (
            f"\n\n…и ещё "
            f"{len(changes)-15} изменений"
        )

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

# =========================
# СОХРАНЕНИЕ
# =========================

with open(
    "old.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        current,
        f,
        ensure_ascii=False
    )

print("Проверка завершена")
