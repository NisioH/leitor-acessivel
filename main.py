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
    page.title = "Leitor de Texto para Áudio"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.width = 600
    page.window.height = 800

    # Player de Áudio
    audio_player = ft.Audio(src="", autoplay=False)
    page.overlay.append(audio_player)

    # Área de texto
    text_field = ft.TextField(
        label="Texto para leitura",
        multiline=True,
        min_lines=10,
        max_lines=15,
        hint_text="O texto extraído aparecerá aqui..."
    )

    # Indicador de carregamento
    loading_indicator = ft.ProgressBar(visible=False)

    def on_file_result(e: ft.FilePickerResultEvent):
        print("on_file_result chamado, arquivos:", e.files)
        if not e.files:
            return

        file_info = e.files[0]
        # Se estamos na web e não temos bytes nem path, precisamos fazer o upload
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
            # Quando o upload termina, o arquivo está no diretório configurado
            class FakeFileInfo:
                def __init__(self, name, path):
                    self.name = name
                    self.path = path
                    self.bytes = None
            
            # O arquivo é salvo no subdiretório 'uploads' (conforme upload_dir configurado)
            # Mas o caminho absoluto é necessário para abrir com open() se não estiver no CWD
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

        # Se o path for relativo, tenta torná-lo absoluto se necessário, 
        # mas o open() deve funcionar se estiver no diretório de trabalho

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
                
                # Converte o dataframe para string, removendo índices e nomes de colunas se preferir,
                # ou apenas concatenando os valores de forma legível.
                extracted_text = df.to_string(index=False)

            elif ext in [".png", ".jpg", ".jpeg", ".bmp"]:
                # Ler imagem a partir de bytes (web) ou caminho local
                if file_bytes is not None:
                    img = Image.open(BytesIO(file_bytes))
                elif file_path:
                    img = Image.open(file_path)
                else:
                    raise ValueError("A imagem não pôde ser carregada (caminho e bytes ausentes).")

                # Verifica se o tesseract está acessível
                try:
                    extracted_text = pytesseract.image_to_string(img, lang='por')
                except Exception:
                    try:
                        extracted_text = pytesseract.image_to_string(img)
                    except Exception as t_ex:
                        raise RuntimeError(f"Erro no Tesseract: {t_ex}")

            text_field.value = extracted_text if extracted_text.strip() else "Nenhum texto encontrado no arquivo."
        except Exception as ex:
            text_field.value = f"Erro ao processar arquivo: {ex}"

        loading_indicator.visible = False
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_result, on_upload=on_upload_progress)
    page.overlay.append(file_picker)

    # Botão de download
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
            # Gera um nome de arquivo único para evitar conflitos e problemas de cache
            timestamp = int(time.time())
            audio_name = f"leitura_{timestamp}.mp3"
            
            # Usar o diretório de uploads que já é servido pelo Flet
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            audio_path_save = os.path.join(upload_dir, audio_name)

            # Limpa arquivos antigos de leitura no diretório de uploads
            # Mantemos os arquivos por um tempo ou apenas deletamos se necessário
            # Para economizar espaço, vamos manter apenas o último, 
            # mas agora o usuário tem a chance de baixar.
            for f in os.listdir(upload_dir):
                if f.startswith("leitura_") and f.endswith(".mp3"):
                    try:
                        os.remove(os.path.join(upload_dir, f))
                    except Exception:
                        pass

            tts = gTTS(text=text_value, lang='pt')
            tts.save(audio_path_save)
            
            # No Flet, arquivos em upload_dir são servidos na raiz ou via / se configurado.
            # Quando upload_dir é definido no ft.app(), os arquivos são acessíveis via URL.
            # Para o componente Audio na web, usamos o nome do arquivo se ele estiver no upload_dir.
            audio_player.src = audio_name
            download_button.visible = True
            page.update()
            
            # Tenta tocar, se falhar pode ser porque o arquivo ainda não está pronto no sistema de arquivos
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

    # Layout
    page.add(
        ft.Column([
            ft.Text("Leitor Acessível", size=30, weight="bold"),
            ft.Text("Transforme fotos da lousa ou arquivos de texto em voz."),
            ft.Divider(),
            ft.ElevatedButton(
                "1. Selecionar Arquivo (Foto, PDF, DOCX, XLSX, TXT)",
                icon=ft.Icons.UPLOAD_FILE,
                on_click=lambda _: file_picker.pick_files(
                    allowed_extensions=["txt", "png", "jpg", "jpeg", "pdf", "docx", "xlsx", "xls"]
                )
            ),
            loading_indicator,
            text_field,
            ft.Row([
                ft.ElevatedButton(
                    "2. Ouvir Texto",
                    icon=ft.Icons.PLAY_ARROW,
                    bgcolor=ft.Colors.GREEN_700,
                    color=ft.Colors.WHITE,
                    on_click=convert_and_play
                ),
                download_button
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    )

if __name__ == "__main__":
    # Garante que o diretório de uploads existe
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    # Define a chave secreta via variável de ambiente para evitar TypeError no ft.app()
    os.environ["FLET_SECRET_KEY"] = "some_secret_key"

    # Preferir modo web no Linux (evita problemas com GTK/OpenGL no desktop)
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
