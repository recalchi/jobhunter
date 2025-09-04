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

```
job-automation/
├── src/
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
pip uninstall webdriver-manager
pip install webdriver-manager
```

### Erro de Dependências
```bash
# Reinstale todas as dependências
pip install -r requirements.txt --force-reinstall
```

### Erro de Banco de Dados
```bash
# Remova o banco e deixe recriar
rm src/database/app.db
```

## 📞 Suporte

Para suporte técnico ou dúvidas sobre o sistema, entre em contato através dos canais oficiais ou consulte a documentação técnica.

## 📄 Licença

Este projeto é proprietário e destinado ao uso específico conforme acordado.

---

**JobHunter Pro v1.0** - Desenvolvido com ❤️ para automatizar sua busca por oportunidades na área financeira.

