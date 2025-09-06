<<<<<<< HEAD
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
=======
# JobHunter Pro - Automação Inteligente de Vagas

## 🎯 Visão Geral

O **JobHunter Pro** é uma solução completa de automação para busca e inscrição em vagas de emprego, especialmente focada em posições da área financeira em São Paulo. O sistema oferece uma interface moderna com tema escuro e funcionalidades avançadas de automação.

## ✨ Funcionalidades Principais

### 🔐 Gerenciamento de Credenciais
- Armazenamento seguro de credenciais para múltiplas plataformas
- Suporte para LinkedIn, Infojobs, Catho e Gupy
- Opção de login via Google para plataformas compatíveis

### 🔍 Busca Automatizada de Vagas
- **Tipos de Vaga Suportados:**
  - Analista Financeiro
  - Contas a Pagar
  - Contas a Receber
  - Analista de Precificação
  - Analista de Custos

- **Filtros Avançados:**
  - Localização (padrão: São Paulo)
  - Salário mínimo (padrão: R$ 1.900,00)
  - Modalidade (Remoto, Híbrido, Presencial)
  - Exigência de ensino superior
  - Exigência de inglês
  - Exclusão de vagas PCD

### 📊 Dashboard de Resultados
- Estatísticas em tempo real de vagas encontradas
- Taxa de sucesso de inscrições
- Lista detalhada de vagas processadas
- Status de cada inscrição realizada

### 🖥️ Interface Moderna
- Tema escuro profissional
- Barra de progresso em tempo real
- Terminal de execução com logs detalhados
- Design responsivo e intuitivo

## 🚀 Tecnologias Utilizadas

### Backend
- **Flask** - Framework web Python
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados leve
- **Selenium** - Automação de navegador
- **NLTK** - Processamento de linguagem natural
- **BeautifulSoup** - Parsing de HTML

### Frontend
- **React** - Biblioteca JavaScript
- **Tailwind CSS** - Framework de estilização
- **Shadcn/UI** - Componentes de interface
- **Lucide Icons** - Ícones modernos
- **Vite** - Build tool

### Automação
- **WebDriver Manager** - Gerenciamento de drivers
- **Chrome WebDriver** - Controle do navegador
- **PyPDF2** - Leitura de arquivos PDF

## 📋 Pré-requisitos

- Python 3.11+
- Node.js 20+
- Chrome/Chromium instalado
- Conexão com internet

## 🛠️ Instalação e Configuração

### 1. Clone o Repositório
```bash
git clone <repository-url>
cd job-automation
```

### 2. Configure o Ambiente Python
```bash
# Ative o ambiente virtual
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configure o Banco de Dados
O banco SQLite será criado automaticamente na primeira execução.

### 4. Inicie o Servidor
```bash
python src/main.py
```

### 5. Acesse a Aplicação
Abra seu navegador e acesse: `http://localhost:5000`

## 📖 Como Usar

### 1. Configuração Inicial
1. Acesse a aba **"Configuração"**
2. Insira suas credenciais para cada plataforma:
   - **LinkedIn:** rena.recalchi@gmail.com / Yumi1703$
   - **Infojobs:** renan.recalchi.adm@gmail.com (login via Google)
   - **Catho:** renan.recalchi.adm@gmail.com (login via Google)
   - **Gupy:** 44211319892 / Gordinez123@

### 2. Configuração de Busca
1. Vá para a aba **"Busca"**
2. Configure os filtros:
   - **Localização:** São Paulo (padrão)
   - **Salário Mínimo:** R$ 1.900,00 (padrão)
   - **Modalidade:** Selecione sua preferência
   - **Plataformas:** Marque as plataformas desejadas

### 3. Execução da Automação
1. Clique no botão **"Iniciar"** no cabeçalho
2. Acompanhe o progresso na barra de progresso
3. Monitore os logs no terminal de execução
4. O botão mudará para **"Parar"** durante a execução

### 4. Visualização de Resultados
1. Acesse a aba **"Resultados"**
2. Visualize as estatísticas:
   - Total de vagas encontradas
   - Total de inscrições enviadas
   - Taxa de sucesso
3. Confira a lista detalhada de vagas processadas

## 🔧 Estrutura do Projeto
>>>>>>> branch-2

```
job-automation/
├── src/
<<<<<<< HEAD
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
=======
│   ├── models/           # Modelos de dados
│   │   ├── credentials.py
│   │   ├── jobs.py
│   │   └── whatsapp_contacts.py
│   ├── routes/           # Rotas da API
│   │   ├── automation.py
│   │   └── resume_analysis.py
│   ├── automation/       # Módulos de automação
│   │   ├── base_automation.py
│   │   └── linkedin_automation.py
│   ├── analysis/         # Análise de currículo
│   │   └── resume_analyzer.py
│   ├── static/          # Frontend construído
│   └── main.py          # Arquivo principal
├── venv/                # Ambiente virtual
└── requirements.txt     # Dependências Python
```

## 🎨 Capturas de Tela

### Dashboard Principal
![Dashboard](screenshots/dashboard.png)

### Configuração de Credenciais
![Credenciais](screenshots/credentials.png)

### Resultados da Automação
![Resultados](screenshots/results.png)

## 🔮 Funcionalidades Futuras

### 📱 Contato via WhatsApp (Em Desenvolvimento)
- Busca automática de contatos de RH
- Envio de mensagens personalizadas
- Controle de spam (máx. 11 contatos a cada 10min)
- Histórico de contatos realizados

### 📄 Análise de Currículo (Em Desenvolvimento)
- Upload de currículo em PDF/DOC
- Análise de adequação para cada tipo de vaga
- Sistema de avaliação por estrelas (0-5)
- Sugestões personalizadas de melhoria
- Análise de palavras-chave relevantes

## 🛡️ Segurança

- Credenciais armazenadas de forma segura no banco local
- Comunicação HTTPS quando em produção
- Logs detalhados para auditoria
- Controle de rate limiting para evitar bloqueios

## 🐛 Solução de Problemas

### Erro de WebDriver
```bash
# Reinstale o webdriver-manager
>>>>>>> branch-2
pip uninstall webdriver-manager
pip install webdriver-manager
```

<<<<<<< HEAD
### Erro de Dependências NLTK
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
=======
### Erro de Dependências
```bash
# Reinstale todas as dependências
pip install -r requirements.txt --force-reinstall
>>>>>>> branch-2
```

### Erro de Banco de Dados
```bash
<<<<<<< HEAD
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
=======
# Remova o banco e deixe recriar
rm src/database/app.db
```

## 📞 Suporte

Para suporte técnico ou dúvidas sobre o sistema, entre em contato através dos canais oficiais ou consulte a documentação técnica.

## 📄 Licença

Este projeto é proprietário e destinado ao uso específico conforme acordado.

---

**JobHunter Pro v1.0** - Desenvolvido com ❤️ para automatizar sua busca por oportunidades na área financeira.
>>>>>>> branch-2

