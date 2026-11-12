
# Sistema de Gestão de Estoque

Aplicação web desenvolvida em Python/Django e MySQL como parte de um desafio técnico para a Keener Innovations.

O sistema permite cadastrar produtos, controlar entradas e saídas de estoque e consultar o histórico de movimentações, com autenticação de usuários.

## Tecnologias utilizadas

- Python
- Django 5.2
- MySQL
- HTML5
- CSS3
- JavaScript
- Git e GitHub

## Funcionalidades

### Autenticação
- Cadastro de usuários
- Login e logout
- Proteção de páginas para usuários autenticados
- Validação de senhas utilizando Django Auth

### Gestão de produtos
- Cadastro de produtos
- Listagem de produtos
- Edição de informações
- Código único por produto
- Ativação e desativação
- Exclusão de produtos sem histórico de movimentações

### Controle de estoque
- Registro de entradas
- Registro de saídas
- Atualização automática das quantidades
- Bloqueio de saídas com estoque insuficiente
- Bloqueio de movimentações em produtos desativados

### Histórico de movimentações
- Listagem de entradas e saídas
- Identificação do produto
- Quantidade movimentada
- Data e horário
- Identificação do usuário responsável

## Requisitos

Para executar o projeto, é necessário instalar:

- Python 3.10 ou superior, compatível com Django 5.2
- MySQL
- Git (opcional, para clonar o repositório)

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/DutraDEV99/case-estoque-keener.git
cd case-estoque-keener
```

O repositório é privado e exige autorização de acesso.

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 3. Instalar as dependências

No Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configurar o MySQL

Crie o banco de dados e um usuário com permissões adequadas:

```sql
CREATE DATABASE estoque
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'django_estoque'@'localhost'
IDENTIFIED BY 'SENHA_FORTE_AQUI';

GRANT ALL PRIVILEGES ON estoque.*
TO 'django_estoque'@'localhost';
```

Substitua `SENHA_FORTE_AQUI` por uma senha própria.

### 5. Configurar as variáveis de ambiente

O projeto utiliza variáveis de ambiente para proteger credenciais.

No PowerShell:

```powershell
$env:ESTOQUE_DB_PASSWORD = "SENHA_DO_MYSQL"

$env:DJANGO_SECRET_KEY = & ".\.venv\Scripts\python.exe" -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Substitua `SENHA_DO_MYSQL` pela senha definida no MySQL.

Essas variáveis são temporárias e permanecem disponíveis apenas na sessão atual do terminal.

### 6. Executar as migrações

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

### 7. Iniciar o servidor

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Acesse:

http://127.0.0.1:8000/login/

## Como utilizar

1. Acesse a página de cadastro e crie uma conta.
2. Faça login.
3. Cadastre um produto com nome e código.
4. Registre uma entrada para adicionar unidades ao estoque.
5. Registre uma saída para retirar unidades.
6. Consulte o histórico das movimentações realizadas.

O estoque é compartilhado entre os usuários autenticados, e cada movimentação registra o responsável.

## Segurança e integridade

O sistema utiliza recursos nativos do Django, incluindo:

- Autenticação e armazenamento seguro de senhas
- Proteção CSRF em formulários
- Controle de acesso às páginas de estoque
- Validação dos dados enviados
- Transações atômicas nas movimentações
- Bloqueio de registros durante a atualização do estoque
- Preservação do histórico de movimentações
- Configuração de credenciais por variáveis de ambiente

O projeto está configurado para desenvolvimento local. Para utilização em produção, são necessárias configurações adicionais de hospedagem, HTTPS e segurança.

## Autor

**Wendel Dutra**

GitHub: https://github.com/DutraDEV99
