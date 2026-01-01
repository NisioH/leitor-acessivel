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
        run: flet build apk --project "Leitor Acessível"
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: LeitorAcessivel-APK
          path: build/apk/*.apk
```

5.  Sempre que você fizer um `git push`, o GitHub vai gerar o APK. Você poderá baixá-lo na aba **Actions** do seu repositório. O arquivo baixado terá o nome **LeitorAcessivel-APK**.

---

## 💻 Opção 2: Configuração Local (Se você tiver Flutter instalado)

Se você preferir gerar no seu computador, precisará configurar o ambiente.

### 1. Instalar o Flutter SDK
Você pode instalar manualmente seguindo o [Guia Oficial](https://docs.flutter.dev/get-started/install) ou usar o script que criei para facilitar (Linux/WSL):

No terminal, execute:
```bash
chmod +x setup_flutter.sh
./setup_flutter.sh
```

### 2. Instalar o Android SDK
O Flet depende do Android SDK para criar o APK. A forma mais fácil é:
1.  Baixar e instalar o [Android Studio](https://developer.android.com/studio).
2.  Abrir o Android Studio e seguir o assistente para instalar o **Android SDK**, **Android SDK Command-line Tools** e o **CMake**.
3.  Executar `flutter doctor` no terminal para garantir que tudo está ok.

### 3. Comando para gerar
Com o ambiente pronto, abra o terminal na pasta do projeto e execute:
```bash
flet build apk --project "Leitor Acessível"
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
