import flet as ft
import os
import sys
import tempfile
from io import BytesIO
import pytesseract
from PIL import Image
from gtts import gTTS
import PyPDF2
import docx
import pandas as pd



def main(page: ft.Page):
    page.title = "Leitor Acessível"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = "adaptive"  # Permite scroll em telas pequenas

    # Configurações responsivas para mobile
    if page.web:
        page.theme = ft.Theme(
            page_transitions={"android": "zoom", "ios": "cupertino", "macos": "none"}
        )

    # Player de Áudio
    audio_player = ft.Audio(src="", autoplay=False)
    page.overlay.append(audio_player)

    # Área de texto - responsiva para mobile
    text_field = ft.TextField(
        label="Texto para leitura",
        multiline=True,
        min_lines=5,
        max_lines=20,
        hint_text="O texto extraído aparecerá aqui...",
        expand=False,
        text_size=14,
    )

    # Indicador de carregamento
    loading_indicator = ft.ProgressBar(visible=False)

    def on_file_result(e: ft.FilePickerResultEvent):
        print("on_file_result chamado, arquivos:", e.files)
        if not e.files:
            return

        file_info = e.files[0]
     
        if page.web and not file_info.path and not getattr(file_info, "bytes", None):
            loading_indicator.visible = True
            page.update()
            
            upload_url = page.get_upload_url(file_info.name, 600)
            file_picker.upload([
                ft.FilePickerUploadFile(
                    file_info.name,
                    upload_url=upload_url,
                )
            ])
            return

        process_file(file_info)

    def on_upload_progress(e: ft.FilePickerUploadEvent):
        if e.progress == 1.0:
            class FakeFileInfo:
                def __init__(self, name, path):
                    self.name = name
                    self.path = path
                    self.bytes = None
            
            
            uploaded_file_path = os.path.join(os.getcwd(), "uploads", e.file_name)
            process_file(FakeFileInfo(e.file_name, uploaded_file_path))
        elif e.error:
            loading_indicator.visible = False
            text_field.value = f"Erro no upload: {e.error}"
            page.update()

    def process_file(file_info):
        loading_indicator.visible = True
        page.update()

        file_bytes = getattr(file_info, "bytes", None)
        file_name = getattr(file_info, "name", "uploaded_file")
        file_path = file_info.path

        try:
            extracted_text = ""
            if file_path:
                ext = os.path.splitext(file_path)[1].lower()
            else:
                ext = os.path.splitext(file_name)[1].lower()

            if ext == ".txt":
                if file_bytes is not None:
                    try:
                        extracted_text = file_bytes.decode("utf-8")
                    except Exception:
                        extracted_text = file_bytes.decode("latin-1", errors="replace")
                elif file_path:
                    with open(file_path, "r", encoding="utf-8") as f:
                        extracted_text = f.read()
                else:
                    raise ValueError("O conteúdo do arquivo não pôde ser lido (caminho e bytes ausentes).")

            elif ext == ".pdf":
                if file_bytes is not None:
                    pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                elif file_path:
                    pdf_reader = PyPDF2.PdfReader(file_path)
                else:
                    raise ValueError("O PDF não pôde ser carregado.")
                
                for page_pdf in pdf_reader.pages:
                    extracted_text += (page_pdf.extract_text() or "") + "\n"

            elif ext == ".docx":
                if file_bytes is not None:
                    doc = docx.Document(BytesIO(file_bytes))
                elif file_path:
                    doc = docx.Document(file_path)
                else:
                    raise ValueError("O DOCX não pôde ser carregado.")
                
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"

            elif ext in [".xlsx", ".xls"]:
                if file_bytes is not None:
                    df = pd.read_excel(BytesIO(file_bytes))
                elif file_path:
                    df = pd.read_excel(file_path)
                else:
                    raise ValueError("O arquivo Excel não pôde ser carregado.")
                
                extracted_text = df.to_string(index=False)

            elif ext in [".png", ".jpg", ".jpeg", ".bmp"]:
                if file_bytes is not None:
                    img = Image.open(BytesIO(file_bytes))
                elif file_path:
                    img = Image.open(file_path)
                else:
                    raise ValueError("A imagem não pôde ser carregada (caminho e bytes ausentes).")

                try:
                    extracted_text = pytesseract.image_to_string(img, lang='por')
                except Exception as first_ex:
                    try:
                        extracted_text = pytesseract.image_to_string(img)
                    except Exception as t_ex:
                        # OCR pode não estar disponível em mobile/web
                        if page.web:
                            raise RuntimeError(
                                "⚠️ OCR de imagens não está disponível na versão web/mobile.\n\n"
                                "Para extrair texto de imagens, use a versão desktop instalada localmente.\n"
                                "Você pode usar arquivos PDF, DOCX, XLSX ou TXT normalmente."
                            )
                        else:
                            raise RuntimeError(f"Erro no Tesseract: {t_ex}\n\nCertifique-se de que o Tesseract OCR está instalado.")

            text_field.value = extracted_text if extracted_text.strip() else "Nenhum texto encontrado no arquivo."
        except Exception as ex:
            text_field.value = f"Erro ao processar arquivo: {ex}"

        loading_indicator.visible = False
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_result, on_upload=on_upload_progress)
    page.overlay.append(file_picker)

    download_button = ft.ElevatedButton(
        "Baixar Áudio (.mp3)",
        icon=ft.Icons.DOWNLOAD,
        visible=False,
        on_click=lambda _: page.launch_url(audio_player.src)
    )

    def convert_and_play(e):
        print("convert_and_play chamado")
        text_value = (text_field.value or "").strip()
        if not text_value:
            text_field.value = "Nenhum texto para converter."
            page.update()
            return
        
        loading_indicator.visible = True
        download_button.visible = False
        page.update()

        try:
            import time
            timestamp = int(time.time())
            audio_name = f"leitura_{timestamp}.mp3"
            
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            audio_path_save = os.path.join(upload_dir, audio_name)

            for f in os.listdir(upload_dir):
                if f.startswith("leitura_") and f.endswith(".mp3"):
                    try:
                        os.remove(os.path.join(upload_dir, f))
                    except Exception:
                        pass

            tts = gTTS(text=text_value, lang='pt')
            tts.save(audio_path_save)
            
            audio_player.src = audio_name
            download_button.visible = True
            page.update()
            
            success = False
            for _ in range(5):
                try:
                    audio_player.play()
                    success = True
                    break
                except:
                    time.sleep(0.2)
            
            if not success:
                raise Exception("Não foi possível iniciar o áudio.")
        except Exception as ex:
            text_field.value = f"Erro ao gerar áudio: {ex}"
        
        loading_indicator.visible = False
        page.update()

    # Layout responsivo para mobile
    # Aviso sobre OCR em mobile
    ocr_warning = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.ORANGE_700, size=20),
            ft.Text(
                "⚠️ OCR de imagens não disponível na versão web/mobile",
                size=12,
                color=ft.Colors.ORANGE_700,
                weight="bold"
            )
        ], tight=True),
        bgcolor=ft.Colors.ORANGE_50,
        border_radius=8,
        padding=10,
        visible=page.web
    )

    page.add(
        ft.Column([
            ft.Text("Leitor Acessível", size=28, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.Text(
                "Transforme arquivos de texto em voz",
                size=14,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.GREY_700
            ),
            ft.Divider(),
            ocr_warning,
            ft.Container(
                content=ft.ElevatedButton(
                    "📁 Selecionar Arquivo",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: file_picker.pick_files(
                        allowed_extensions=["txt", "pdf", "docx", "xlsx", "xls"] if page.web else ["txt", "png", "jpg", "jpeg", "pdf", "docx", "xlsx", "xls"]
                    ),
                    width=300,
                    height=50,
                ),
                alignment=ft.alignment.center
            ),
            ft.Text(
                "PDF • DOCX • XLSX • TXT" + ("" if page.web else " • Imagens"),
                size=12,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            ),
            loading_indicator,
            ft.Container(
                content=text_field,
                expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.ElevatedButton(
                        "🔊 Ouvir Texto",
                        icon=ft.Icons.PLAY_ARROW,
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                        on_click=convert_and_play,
                        width=300,
                        height=50,
                    ),
                    download_button
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center
            )
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=15,
        scroll=ft.ScrollMode.AUTO
        )
    )

if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    os.environ["FLET_SECRET_KEY"] = "some_secret_key"

    if sys.platform.startswith("linux"):
        print("Iniciando Flet em modo web (Linux detected)")
        ft.app(
            target=main,
            view=ft.AppView.WEB_BROWSER,
            upload_dir="uploads",
        )
    else:
        try:
            ft.app(target=main, upload_dir="uploads")
        except Exception as e:
            print(f"Erro ao iniciar modo desktop, tentando modo web: {e}")
            ft.app(
                target=main,
                view=ft.AppView.WEB_BROWSER,
                upload_dir="uploads",
            )
