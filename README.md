# 🚀 JobHunter Pro - Guia de Instalação Completa

## 📋 Visão Geral

Este guia fornece instruções detalhadas para instalar e executar o **JobHunter Pro** localmente com todas as funcionalidades, incluindo análise de currículo.

## 🌐 Acesso Online

**URL da Aplicação Deployada:** https://3dhkilc8mdne.manus.space

> **Nota:** A versão online possui todas as funcionalidades principais, exceto a análise de currículo que requer instalação local.

## 💻 Instalação Local Completa

### Pré-requisitos

- **Python 3.11+**
- **Node.js 20+** (opcional, apenas para desenvolvimento do frontend)
- **Google Chrome** ou **Chromium**
- **Git**
- **Conexão com internet**

### 1. Download dos Arquivos

Os arquivos do projeto estão disponíveis no diretório `/home/ubuntu/job-automation/` do sandbox.

### 2. Configuração do Ambiente Python

```bash
# Navegue até o diretório do projeto
cd job-automation

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Linux/Mac:
source venv/bin/activate
# No Windows:
venv\Scripts\activate

# Instale as dependências completas
pip install -r requirements.txt

# Instale dependências adicionais para análise de currículo
pip install nltk PyPDF2 regex
```

### 3. Configuração do NLTK (Para Análise de Currículo)

```python
# Execute este código Python uma vez para baixar os recursos do NLTK
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

### 4. Estrutura de Arquivos

Certifique-se de que a estrutura está assim:

```
job-automation/
├── src/
│   ├── models/
│   ├── routes/
│   ├── automation/
│   ├── analysis/
│   ├── static/
│   └── main.py
├── venv/
├── requirements.txt
└── README.md
```

### 5. Configuração do Banco de Dados

O banco SQLite será criado automaticamente na primeira execução em:
`src/database/app.db`

### 6. Execução da Aplicação

```bash
# Certifique-se de estar no diretório do projeto com o ambiente virtual ativo
cd job-automation
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Execute a aplicação
python src/main.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 🔧 Configuração das Credenciais

### Credenciais Fornecidas

Use as seguintes credenciais para teste:

#### LinkedIn
- **Email:** rena.recalchi@gmail.com
- **Senha:** Yumi1703$

#### Infojobs
- **Email:** renan.recalchi.adm@gmail.com
- **Login:** Via Google

#### Catho
- **Email:** renan.recalchi.adm@gmail.com
- **Login:** Via Google

#### Gupy
- **CPF:** 44211319892
- **Senha:** Gordinez123@

## 🎯 Como Usar

### 1. Configuração Inicial
1. Acesse `http://localhost:5000`
2. Vá para a aba **"Configuração"**
3. Insira as credenciais fornecidas

### 2. Configuração de Busca
1. Acesse a aba **"Busca"**
2. Configure os filtros:
   - **Localização:** São Paulo
   - **Salário Mínimo:** R$ 1.900,00
   - **Modalidade:** Sua preferência
   - **Plataformas:** Selecione as desejadas

### 3. Execução da Automação
1. Clique em **"Iniciar"**
2. Acompanhe o progresso na barra
3. Monitore os logs no terminal

### 4. Análise de Currículo (Apenas Local)
1. Acesse a aba **"Currículo"**
2. Faça upload do seu currículo (PDF, DOC, TXT)
3. Visualize a análise e recomendações

## 🔍 Funcionalidades Principais

### ✅ Disponíveis Online e Local
- ✅ Gerenciamento de credenciais
- ✅ Busca automatizada de vagas
- ✅ Filtros avançados
- ✅ Dashboard de resultados
- ✅ Interface com tema escuro
- ✅ Terminal de execução em tempo real

### 🏠 Apenas na Instalação Local
- 📄 **Análise de Currículo**
  - Upload de arquivos PDF, DOC, TXT
  - Análise de adequação por tipo de vaga
  - Sistema de avaliação por estrelas
  - Sugestões personalizadas de melhoria

### 🚧 Em Desenvolvimento
- 📱 **Contato via WhatsApp**
- 🔍 **Busca de contatos de RH**
- 📊 **Relatórios avançados**

## 🛠️ Solução de Problemas

### Erro de WebDriver
```bash
pip uninstall webdriver-manager
pip install webdriver-manager
```

### Erro de Dependências NLTK
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Erro de Banco de Dados
```bash
rm src/database/app.db
# Reinicie a aplicação para recriar o banco
```

### Chrome não encontrado
- Instale o Google Chrome ou Chromium
- No Ubuntu: `sudo apt install chromium-browser`

## 📊 Tipos de Vaga Suportados

1. **Analista Financeiro**
2. **Contas a Pagar**
3. **Contas a Receber**
4. **Analista de Precificação**
5. **Analista de Custos**

## 🔒 Segurança

- Credenciais armazenadas localmente no SQLite
- Comunicação HTTPS na versão deployada
- Logs detalhados para auditoria
- Rate limiting para evitar bloqueios

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte este guia
2. Verifique os logs no terminal
3. Entre em contato através dos canais oficiais

## 🎉 Recursos Avançados

### Análise de Currículo (Local)
- **Palavras-chave específicas** por área
- **Análise de experiência** (Júnior/Pleno/Sênior)
- **Avaliação de formação** acadêmica
- **Sugestões personalizadas** de melhoria
- **Sistema de estrelas** (0-5) por área

### Automação Inteligente
- **Detecção automática** de formulários
- **Preenchimento inteligente** de dados
- **Controle de velocidade** para evitar bloqueios
- **Retry automático** em caso de falhas

---

**JobHunter Pro v1.0** - Sua ferramenta completa para automação de busca de vagas na área financeira! 🎯

