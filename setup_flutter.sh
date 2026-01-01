#!/bin/bash

# Script para instalar Flutter SDK no Linux (Ubuntu/Debian/WSL)
# Criado para o projeto Leitor Acessível

echo "🚀 Iniciando instalação do Flutter SDK..."

# 1. Instalar dependências do sistema
echo "📦 Instalando dependências do sistema..."
sudo apt-get update
sudo apt-get install -y curl git unzip xz-utils zip libglu1-mesa

# 2. Criar diretório de desenvolvimento
mkdir -p $HOME/development
cd $HOME/development

# 3. Baixar Flutter (Versão estável)
echo "📥 Baixando Flutter SDK..."
curl -fsSL https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.24.5-stable.tar.xz -o flutter.tar.xz

# 4. Extrair
echo "📂 Extraindo arquivos..."
tar xf flutter.tar.xz
rm flutter.tar.xz

# 5. Configurar PATH no .bashrc ou .zshrc
echo "⚙️ Configurando variáveis de ambiente..."
if [[ ":$PATH:" != *":$HOME/development/flutter/bin:"* ]]; then
    echo 'export PATH="$PATH:$HOME/development/flutter/bin"' >> $HOME/.bashrc
    export PATH="$PATH:$HOME/development/flutter/bin"
    echo "✅ PATH atualizado no .bashrc"
fi

# 6. Verificar instalação
echo "🏁 Verificando instalação..."
$HOME/development/flutter/bin/flutter --version

echo ""
echo "✨ Flutter instalado com sucesso!"
echo "⚠️  IMPORTANTE: Para gerar o APK, você ainda precisará do Android SDK."
echo "💡 Dica: Instale o Android Studio para configurar o Android SDK facilmente."
echo "🔄 Por favor, feche e abra seu terminal ou execute: source ~/.bashrc"
