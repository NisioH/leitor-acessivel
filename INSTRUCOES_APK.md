# 📱 Como Gerar o APK (Android) do Leitor Acessível

Para gerar o APK de um aplicativo Flet, você tem duas opções principais: usar o **GitHub Actions** (recomendado, pois não exige configurar nada no seu PC) ou **configurar o ambiente local**.

---

## 🛠️ Opção 1: GitHub Actions (Mais Fácil)

O Flet permite gerar o APK automaticamente sempre que você enviar o código para o GitHub.

1.  Crie uma conta no [GitHub](https://github.com/), se não tiver.
2.  Crie um novo repositório e suba os arquivos do seu projeto.
3.  Crie uma pasta chamada `.github/workflows` na raiz do projeto.
4.  Crie um arquivo chamado `build.yml` dentro dessa pasta com o seguinte conteúdo:

```yaml
name: Build APK
on:
  push:
    branches: [ main, master ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          channel: 'stable'
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flet
      - name: Build APK
        run: flet build apk
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-release
          path: build/apk/*.apk
```

5.  Sempre que você fizer um `git push`, o GitHub vai gerar o APK. Você poderá baixá-lo na aba **Actions** do seu repositório.

---

## 💻 Opção 2: Configuração Local (Se você tiver Flutter instalado)

Se você preferir gerar no seu computador, precisará:

1.  **Instalar o Flutter SDK:** [Guia de Instalação](https://docs.flutter.dev/get-started/install)
2.  **Instalar o Android SDK:** (Vem com o Android Studio)
3.  **Comando para gerar:**
    Abra o terminal na pasta do projeto e execute:
    ```bash
    flet build apk
    ```

---

## ⚠️ Observação Importante sobre o OCR (Tesseract)

O seu aplicativo usa a biblioteca `pytesseract`, que depende do programa **Tesseract OCR** instalado no sistema operacional.

*   **No Windows/Linux:** Funciona se o Tesseract estiver instalado.
*   **No Android (APK):** O Tesseract **não vem instalado no Android**. 

**O que vai acontecer no APK:**
Como o seu código já possui uma função `ocr_online` (usando a API do OCR.space), o aplicativo vai detectar que o Tesseract não está disponível no celular e **usará automaticamente o OCR Online**. Isso é bom, pois garante que o app funcione no celular, mas exigirá internet para ler fotos.

---

## 📝 Dicas para o APK

*   As permissões de Câmera e Armazenamento já estão configuradas no seu `pyproject.toml`.
*   O nome do pacote definido é `com.nisioh.leitoracessivel`.
