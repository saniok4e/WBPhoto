from flask import Flask, request, render_template_string, jsonify
from pathlib import Path
from datetime import datetime
import socket
import qrcode
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser


# =========================================================
# НАСТРОЙКИ
# =========================================================

PORT = 8080

PHOTO_DIR = Path(r"C:\WB_Brak")

PHOTO_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


HTML = """
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0,
               maximum-scale=1.0,
               user-scalable=no">

<meta name="apple-mobile-web-app-capable"
      content="yes">

<meta name="apple-mobile-web-app-status-bar-style"
      content="black-translucent">

<meta name="apple-mobile-web-app-title"
      content="Брак">

<title>Фото брака</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    background: #f2f2f7;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    text-align: center;
    padding: 25px 20px 40px;
}

.container {
    width: 100%;
    max-width: 500px;
    margin: auto;
}

.title {
    font-size: 32px;
    font-weight: 800;
    margin-top: 25px;
    margin-bottom: 35px;
}

.camera-button {
    width: 100%;
    height: 280px;
    background: white;
    border-radius: 30px;
    border: none;

    box-shadow:
        0 8px 30px rgba(0, 0, 0, 0.08);

    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    cursor: pointer;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
}

.camera-button:active {
    transform: scale(0.98);
}

.camera-icon {
    font-size: 85px;
    line-height: 1;
    margin-bottom: 25px;
}

.camera-text {
    font-size: 24px;
    font-weight: 800;
}

.status {
    min-height: 32px;
    margin-top: 30px;
    font-size: 20px;
    font-weight: 700;
}

.preview {
    display: none;
    width: 100%;
    max-height: 350px;
    object-fit: contain;
    margin-top: 25px;
    border-radius: 20px;
}

.info {
    margin-top: 45px;
    color: #777;
    font-size: 16px;
    line-height: 1.5;
}

input {
    display: none;
}

</style>

</head>

<body>

<div class="container">

<div class="title">
📦 Фото брака
</div>

<label class="camera-button">

<div class="camera-icon">
📷
</div>

<div class="camera-text">
СФОТОГРАФИРОВАТЬ
</div>

<input
    id="photo"
    type="file"
    accept="image/*"
    capture="environment"
>

</label>

<div id="status" class="status">
Готово к работе
</div>

<img id="preview" class="preview">

<div class="info">
После фотографии файл автоматически
отправится на рабочий компьютер.
</div>

</div>

<script>

const input =
    document.getElementById("photo");

const status =
    document.getElementById("status");

const preview =
    document.getElementById("preview");


input.addEventListener(
    "change",
    async function () {

        if (!input.files.length) {
            return;
        }

        const file =
            input.files[0];

        preview.src =
            URL.createObjectURL(file);

        preview.style.display =
            "block";

        status.innerText =
            "⏳ Отправляем фото...";


        const formData =
            new FormData();

        formData.append(
            "photo",
            file
        );


        try {

            const response =
                await fetch(
                    "/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const result =
                await response.json();


            if (result.success) {

                status.innerText =
                    "✅ Фото отправлено";


                setTimeout(
                    function () {

                        status.innerText =
                            "Готово к следующему фото";

                        preview.style.display =
                            "none";

                    },
                    1200
                );

            } else {

                status.innerText =
                    "❌ Ошибка отправки";
            }


        } catch (error) {

            console.error(error);

            status.innerText =
                "❌ Нет связи с компьютером";
        }


        input.value = "";

    }
);

</script>

</body>

</html>
"""


# =========================================================
# СЧЁТЧИК
# =========================================================

photos_today = 0


def get_today_count():

    global photos_today

    today_folder = (
        PHOTO_DIR /
        datetime.now().strftime("%Y-%m-%d")
    )

    if not today_folder.exists():
        photos_today = 0
        return 0

    photos_today = len(
        list(today_folder.glob("*.jpg"))
    )

    return photos_today


# =========================================================
# WEB
# =========================================================

@app.route("/")
def index():

    return render_template_string(HTML)


# =========================================================
# ПОЛУЧЕНИЕ ФОТО
# =========================================================

@app.route("/upload", methods=["POST"])
def upload():

    global photos_today

    if "photo" not in request.files:

        return jsonify({
            "success": False,
            "error": "Фото отсутствует"
        }), 400


    photo = request.files["photo"]


    if not photo.filename:

        return jsonify({
            "success": False,
            "error": "Пустой файл"
        }), 400


    now = datetime.now()


    date_folder = (
        PHOTO_DIR /
        now.strftime("%Y-%m-%d")
    )


    date_folder.mkdir(
        parents=True,
        exist_ok=True
    )


    existing = list(
        date_folder.glob("*.jpg")
    )


    number = len(existing) + 1


    filename = (
        f"{number:03d}_"
        f"{now.strftime('%H-%M-%S')}.jpg"
    )


    filepath = (
        date_folder /
        filename
    )


    photo.save(filepath)


    photos_today = number


    print(
        f"[PHOTO] {filepath}"
    )


    # Обновляем окно Windows

    if gui_root is not None:

        gui_root.after(
            0,
            update_counter
        )


    return jsonify({

        "success": True,

        "filename": filename

    })


# =========================================================
# IP
# =========================================================

def get_local_ip():

    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


    try:

        s.connect(
            ("8.8.8.8", 80)
        )

        ip = s.getsockname()[0]


    except Exception:

        ip = "127.0.0.1"


    finally:

        s.close()


    return ip


# =========================================================
# WINDOWS GUI
# =========================================================

gui_root = None
counter_label = None


def update_counter():

    if counter_label is not None:

        counter_label.config(
            text=f"Фото сегодня: {photos_today}"
        )


def open_folder():

    import os

    os.startfile(
        PHOTO_DIR
    )


def open_browser():

    webbrowser.open(
        current_url
    )


def create_gui():

    global gui_root
    global counter_label


    gui_root = tk.Tk()

    gui_root.title(
        "WB Photo"
    )


    gui_root.geometry(
        "520x800"
    )


    gui_root.minsize(
        480,
        650
    )


    gui_root.configure(
        bg="#f2f2f7"
    )


    # -----------------------------------------------------
    # Заголовок
    # -----------------------------------------------------

    title = tk.Label(

        gui_root,

        text="WB PHOTO",

        font=(
            "Segoe UI",
            28,
            "bold"
        ),

        bg="#f2f2f7",

        fg="#111111"
    )


    title.pack(
        pady=(30, 5)
    )


    subtitle = tk.Label(

        gui_root,

        text="Подключение iPhone",

        font=(
            "Segoe UI",
            16
        ),

        bg="#f2f2f7",

        fg="#666666"
    )


    subtitle.pack(
        pady=(0, 20)
    )


    # -----------------------------------------------------
    # QR
    # -----------------------------------------------------

    qr_image = tk.PhotoImage(
        file=str(qr_path)
    )


    qr_label = tk.Label(

        gui_root,

        image=qr_image,

        bg="white",

        padx=20,

        pady=20
    )


    qr_label.image = qr_image


    qr_label.pack(
        pady=10
    )


    instruction = tk.Label(

        gui_root,

        text=
        "Откройте камеру iPhone\n"
        "и наведите её на QR-код",

        font=(
            "Segoe UI",
            15
        ),

        bg="#f2f2f7",

        fg="#333333"
    )


    instruction.pack(
        pady=(10, 20)
    )


    # -----------------------------------------------------
    # Статус
    # -----------------------------------------------------

    status = tk.Label(

        gui_root,

        text="●  Система работает",

        font=(
            "Segoe UI",
            16,
            "bold"
        ),

        bg="#f2f2f7",

        fg="#16803c"
    )


    status.pack(
        pady=5
    )


    # -----------------------------------------------------
    # Счётчик
    # -----------------------------------------------------

    counter_label = tk.Label(

        gui_root,

        text=f"Фото сегодня: {photos_today}",

        font=(
            "Segoe UI",
            15
        ),

        bg="#f2f2f7",

        fg="#555555"
    )


    counter_label.pack(
        pady=10
    )


    # -----------------------------------------------------
    # Кнопка папки
    # -----------------------------------------------------

    folder_button = tk.Button(

        gui_root,

        text="📁  Открыть папку с фото",

        command=open_folder,

        font=(
            "Segoe UI",
            14,
            "bold"
        ),

        bg="white",

        fg="#222222",

        relief="flat",

        padx=20,

        pady=12,

        cursor="hand2"
    )


    folder_button.pack(
        pady=15
    )


    # -----------------------------------------------------
    # Ссылка для браузера
    # -----------------------------------------------------

    browser_button = tk.Button(

        gui_root,

        text="🌐  Открыть на этом компьютере",

        command=open_browser,

        font=(
            "Segoe UI",
            11
        ),

        bg="#f2f2f7",

        fg="#555555",

        relief="flat",

        cursor="hand2"
    )


    browser_button.pack(
        pady=5
    )


    gui_root.mainloop()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    global current_url
    global qr_path


    current_ip = get_local_ip()


    current_url = (
        f"http://{current_ip}:{PORT}"
    )


    # ---------------------------------------------
    # Загружаем количество фотографий
    # ---------------------------------------------

    get_today_count()


    # ---------------------------------------------
    # Создаём QR
    # ---------------------------------------------

    qr = qrcode.make(
        current_url
    )


    qr_path = Path(
        "WB_Photo_QR.png"
    )


    qr.save(
        qr_path
    )


    print()
    print("=" * 60)
    print("                    WB PHOTO")
    print("=" * 60)
    print()
    print(
        f"Адрес: {current_url}"
    )
    print()
    print(
        f"Фото: {PHOTO_DIR}"
    )
    print()


    # ---------------------------------------------
    # Flask запускаем в отдельном потоке
    # ---------------------------------------------

    server_thread = threading.Thread(

        target=lambda:
            app.run(
                host="0.0.0.0",
                port=PORT,
                debug=False,
                use_reloader=False
            ),

        daemon=True
    )


    server_thread.start()


    # ---------------------------------------------
    # Показываем окно Windows
    # ---------------------------------------------

    create_gui()
