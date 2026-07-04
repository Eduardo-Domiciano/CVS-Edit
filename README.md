# Editor CSV

Aplicativo desktop para visualizar e editar arquivos CSV, com interface gráfica construída em **PySide6** (Qt for Python).

## Funcionalidades

- **Abrir CSV** — por diálogo de arquivo, arrastar e soltar ou argumento na linha de comando
- **Criar CSV** — define os nomes das colunas e salva um arquivo novo
- **Edição inline** — altere células e cabeçalhos diretamente na tabela
- **Linhas** — adicionar linhas e remover linhas marcadas com checkbox
- **Colunas** — adicionar, remover ou apagar todos os dados de uma coluna
- **Transformações de texto** — caixa baixa, caixa alta e inicial maiúscula (dados ou títulos)
- **Detecção de delimitador** — reconhece automaticamente `,`, `;`, tab e `|`
- **Controle de alterações** — aviso ao fechar ou abrir outro arquivo com mudanças não salvas

## Requisitos

- Python 3.10+
- Linux (X11) com a biblioteca `libxcb-cursor0` (exigida pelo Qt 6.5+)

```bash
sudo apt install libxcb-cursor0
```

## Instalação

```bash
git clone https://github.com/Eduardo-Domiciano/CVS-Edit.git
cd CVS-Edit

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Abrir um arquivo diretamente:

```bash
python main.py caminho/para/arquivo.csv
```

### Atalhos de teclado

| Atalho | Ação |
|--------|------|
| `Ctrl+N` | Criar CSV |
| `Ctrl+O` | Abrir CSV |
| `Ctrl+S` | Salvar |
| `Ctrl+Shift+S` | Salvar como |
| `Ctrl+Q` | Sair |

## Estrutura do projeto

O código segue o padrão **MVC**:

```
.
├── main.py                          # Ponto de entrada
├── app/
│   ├── controllers/
│   │   └── main_controller.py       # Lógica de negócio e coordenação
│   ├── models/
│   │   └── csv_table_model.py       # Modelo de dados da tabela CSV
│   └── views/
│       ├── main_window.py           # Janela principal
│       ├── create_csv_dialog.py     # Diálogo de criação de CSV
│       └── widgets/                 # Componentes visuais customizados
├── requirements.txt
└── visualizador-csv.spec            # Configuração PyInstaller
```

## Empacotamento (opcional)

Para gerar um executável com PyInstaller:

```bash
pip install pyinstaller
pyinstaller visualizador-csv.spec
```

O binário será gerado em `dist/visualizador-csv`.

## Licença

Consulte o repositório para informações de licenciamento.
