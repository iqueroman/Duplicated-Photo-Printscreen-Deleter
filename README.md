# Detector de Imagens Duplicadas

Sistema completo para detectar e remover imagens duplicadas com interface visual para conferência manual.

## 🚀 Funcionalidades

- **Detecção de duplicatas exatas** (MD5 Hash)
- **Detecção de imagens similares** (Perceptual Hash)
- **Relatório HTML interativo** com thumbnails
- **Deleção segura com backup automático**
- **Restauração de backups**

## 📁 Estrutura dos Arquivos

```
📦 Duplicated-Photo-Printscreen-Deleter/
├── 🔍 find_duplicates.py      # Script principal de detecção
├── 📊 generate_report.py      # Gerador do relatório HTML
├── 🗑️ delete_files.py         # Processador de deleções
├── 📋 requirements.txt        # Dependências
├── 📖 README.md              # Este arquivo
└── 💾 backup_deletions_*/     # Pastas de backup (geradas automaticamente)
```

## 🛠️ Instalação

```bash
# Instale as dependências
pip install -r requirements.txt
```

**Dependências principais:**
- `Pillow>=10.0.0` - Processamento de imagens
- `imagehash>=4.3.1` - Cálculo de hash perceptual

## 📋 Como Usar

### 1️⃣ Detectar Duplicatas
```bash
python find_duplicates.py
```

**O que faz:**
- Analisa todas as imagens na pasta configurada
- Encontra duplicatas exatas (MD5)
- Encontra imagens similares (Perceptual Hash)
- Gera arquivo `duplicate_results.json`

### 2️⃣ Gerar Relatório Visual
```bash
python generate_report.py
```

**O que faz:**
- Lê o arquivo `duplicate_results.json`
- Gera relatório HTML interativo
- Abre automaticamente no navegador
- Permite seleção visual de quais arquivos deletar

### 3️⃣ Deletar Arquivos Selecionados
```bash
python delete_files.py
```

**O que faz:**
- Processa arquivo `delete_request.json` (gerado pelo HTML)
- Cria backup automático antes de deletar
- Remove arquivos selecionados
- Gera log detalhado da operação

## 🎯 Fluxo de Trabalho Completo

```
📁 Pasta com Imagens
    ↓
🔍 python find_duplicates.py
    ↓
📄 duplicate_results.json
    ↓
📊 python generate_report.py
    ↓
🌐 Relatório HTML (abre no navegador)
    ↓
👁️ Conferência Visual
    ↓
💾 delete_request.json (download)
    ↓
🗑️ python delete_files.py
    ↓
✅ Duplicatas Removidas + 🛡️ Backup Criado
```

## ⚙️ Configuração

### Pasta de Origem (lembre-se de configurar)
Edite o arquivo `find_duplicates.py` linha ~240:
```python
source_folder = r"XXXXXXX"
```

### Thresholds de Similaridade
No arquivo `find_duplicates.py`:
```python
# Perceptual Hash (0.0 a 1.0, padrão: 0.85)
finder.find_perceptual_duplicates(threshold=0.85)
```

## 📊 Relatório HTML

### Funcionalidades do Relatório:
- ✅ **Thumbnails lado a lado** para comparação visual
- ✅ **Filtros**: Duplicatas exatas / Similares / Todos
- ✅ **Seleção por grupo**: Manter primeiro / Deletar todos
- ✅ **Sugestões automáticas** para duplicatas exatas
- ✅ **Contador dinâmico** de arquivos selecionados
- ✅ **Download da lista** de deleção em JSON

### Controles:
- **Manter**: Arquivo será preservado
- **Deletar**: Arquivo será removido (com backup)
- **Revisar**: Marcar para análise posterior

## 🛡️ Segurança e Backup

### Backup Automático
- Todo arquivo deletado é **copiado para backup** antes da remoção
- Backups ficam em `backup_deletions_YYYYMMDD_HHMMSS/`
- Log detalhado salvo em `deletion_log.json`

### Restauração
```bash
python delete_files.py
# Escolha opção 3: Restaurar backup
```

## 📈 Exemplo de Resultados

```
🔍 DETECTOR DE DUPLICATAS - Resultados
════════════════════════════════════════
📂 Total de imagens analisadas: 3.622
🔄 Grupos de duplicatas exatas: 15
👥 Grupos similares encontrados: 127
💾 Arquivos deletados: 138
💿 Espaço liberado: ~50MB
```

## 🎛️ Especificações Técnicas

### Formatos Suportados
- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp`

### Algoritmos Utilizados
- **MD5**: Hash criptográfico para duplicatas exatas
- **dHash**: Difference Hash para detecção de similaridade
- **Thumbnail**: Redimensionamento otimizado para performance

### Performance
- **Processamento em lotes** de 100 arquivos
- **Thumbnails otimizados** para HTML (300x300px)
- **Validação de acesso** para arquivos com caracteres especiais

## 🐛 Resolução de Problemas

### Erro: "Arquivo não encontrado"
- Verifique se o caminho da pasta está correto no `find_duplicates.py`
- Confirme se existem imagens na pasta configurada

### Erro: "Caracteres especiais"
- Script tem proteção contra nomes com acentos/símbolos
- Arquivos problemáticos são listados como "inacessíveis"

### Erro: "Dependências não instaladas"
```bash
pip install Pillow imagehash
```

### Erro: "JSON não encontrado"
- Execute primeiro `python find_duplicates.py`
- Verifique se o arquivo `duplicate_results.json` foi gerado

## 📝 Arquivos Gerados

### Durante Detecção:
- `duplicate_results.json` - Resultados da análise completa

### Durante Relatório:
- `duplicate_report.html` - Relatório visual interativo

### Durante Seleção:
- `delete_request.json` - Lista de arquivos para deletar (baixado do HTML)

### Após Deleção:
- `backup_deletions_YYYYMMDD_HHMMSS/` - Pasta de backup
- `deletion_log.json` - Log detalhado da operação

## 🎯 Casos de Uso

### Instagram Screenshots Q&A
- **Duplicatas por scroll**: Detecta screenshots repetidos
- **Timestamps diferentes**: Identifica mesmo conteúdo em horários diferentes
- **Qualidades diferentes**: Encontra versões com compressão distinta

### Screenshots Gerais
- **Capturas de tela** de qualquer aplicativo
- **Fotos similares** com pequenas diferenças
- **Limpeza de downloads** duplicados

## 📊 Métricas de Performance

### Dataset Teste (3.622 imagens):
- ⏱️ **Tempo de análise**: ~2-3 minutos
- 🔍 **Duplicatas encontradas**: 15 grupos exatos
- 👁️ **Similares detectados**: 127 grupos
- 💾 **Economia de espaço**: ~138 arquivos removidos

## 🚀 Execução Rápida

Para uso completo em sequência:

```bash
# 1. Detecta duplicatas
python find_duplicates.py

# 2. Gera relatório HTML (abre automaticamente)
python generate_report.py

# 3. [No navegador] Selecione arquivos e baixe delete_request.json

# 4. Execute deleção
python delete_files.py
```

## 🔧 Desenvolvimento

### Estrutura do Código:
```python
# find_duplicates.py
class DuplicateFinder:
    - get_image_files()          # Coleta arquivos válidos
    - calculate_md5()            # Hash exato
    - calculate_perceptual_hash() # Hash perceptual
    - find_md5_duplicates()      # Busca duplicatas exatas
    - find_perceptual_duplicates() # Busca similares
    - save_results_json()        # Salva resultados
```

### Customização:
- Modifique thresholds de similaridade
- Ajuste tamanhos de thumbnail
- Configure formatos de arquivo suportados

---

**Desenvolvido para limpeza eficiente de screenshots duplicados do Instagram Q&A** 📸

**Última atualização**: Sistema organizado com 3 scripts principais e documentação completa.