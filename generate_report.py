#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório HTML para Verificação Manual de Duplicatas
Lê o arquivo duplicate_results.json e gera interface visual interativa
"""

import json
import base64
from pathlib import Path
from datetime import datetime
from PIL import Image
import os

class HTMLReportGenerator:
    def __init__(self, json_file: str, output_file: str = None):
        self.json_file = Path(json_file)
        self.output_file = Path(output_file) if output_file else self.json_file.parent / "duplicate_report.html"
        self.data = None
        
    def load_data(self):
        """Carrega dados do JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"Dados carregados: {self.data['total_images']} imagens")
            return True
        except Exception as e:
            print(f"ERRO ao carregar JSON: {e}")
            return False
    
    def image_to_base64(self, image_path: str, max_size: tuple = (300, 300)) -> str:
        """Converte imagem para base64 para embed no HTML"""
        try:
            img_path = Path(image_path)
            if not img_path.exists():
                return ""
            
            with Image.open(img_path) as img:
                # Redimensiona mantendo proporção
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Converte para RGB se necessário
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Salva em buffer temporário
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_data = buffer.getvalue()
                
                # Converte para base64
                b64_string = base64.b64encode(img_data).decode()
                return f"data:image/jpeg;base64,{b64_string}"
        except Exception as e:
            print(f"ERRO ao processar imagem {image_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: str) -> dict:
        """Obtém informações do arquivo"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"size": "N/A", "size_mb": "N/A", "modified": "N/A"}
            
            stat = path.stat()
            return {
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024*1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            }
        except:
            return {"size": "N/A", "size_mb": "N/A", "modified": "N/A"}
    
    def generate_html(self):
        """Gera o relatório HTML completo"""
        if not self.data:
            print("ERRO: Dados não carregados")
            return False
        
        html_content = self._get_html_template()
        
        # Processa duplicatas exatas (MD5)
        md5_groups_html = ""
        if self.data.get('md5_duplicates'):
            for group_name, group_data in self.data['md5_duplicates'].items():
                md5_groups_html += self._generate_group_html(
                    group_name, 
                    group_data['files'], 
                    "exact", 
                    f"MD5: {group_data['hash'][:8]}..."
                )
        
        # Processa similares (Perceptual)
        perceptual_groups_html = ""
        if self.data.get('perceptual_duplicates'):
            for group_data in self.data['perceptual_duplicates']:
                group_name = f"similar_grupo_{group_data['grupo']}"
                perceptual_groups_html += self._generate_group_html(
                    group_name,
                    group_data['files'],
                    "similar",
                    f"Perceptual Hash (Grupo {group_data['grupo']})"
                )
        
        # Substitui placeholders
        html_content = html_content.replace('{{TOTAL_IMAGES}}', str(self.data['total_images']))
        html_content = html_content.replace('{{MD5_GROUPS}}', str(len(self.data.get('md5_duplicates', {}))))
        html_content = html_content.replace('{{PERCEPTUAL_GROUPS}}', str(len(self.data.get('perceptual_duplicates', []))))
        html_content = html_content.replace('{{TIMESTAMP}}', self.data.get('timestamp', 'N/A'))
        html_content = html_content.replace('{{MD5_GROUPS_HTML}}', md5_groups_html)
        html_content = html_content.replace('{{PERCEPTUAL_GROUPS_HTML}}', perceptual_groups_html)
        
        # Salva arquivo
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Relatório HTML gerado: {self.output_file}")
            return True
        except Exception as e:
            print(f"ERRO ao salvar HTML: {e}")
            return False
    
    def _generate_group_html(self, group_id: str, files: list, group_type: str, title: str) -> str:
        """Gera HTML para um grupo de duplicatas"""
        files_html = ""
        
        for i, file_path in enumerate(files):
            file_info = self.get_file_info(file_path)
            file_name = Path(file_path).name
            img_base64 = self.image_to_base64(file_path)
            
            # Sugere manter o primeiro (geralmente o menor nome/mais antigo)
            suggested_action = "keep" if i == 0 else "delete"
            
            files_html += f"""
            <div class="file-item">
                <div class="image-container">
                    {"<img src='" + img_base64 + "' alt='" + file_name + "'>" if img_base64 else "<div class='no-image'>Imagem não disponível</div>"}
                </div>
                <div class="file-details">
                    <div class="file-name">{file_name}</div>
                    <div class="file-stats">
                        <span>Tamanho: {file_info['size_mb']} MB</span>
                        <span>Modificado: {file_info['modified']}</span>
                    </div>
                    <div class="file-actions">
                        <label class="action-radio">
                            <input type="radio" name="{group_id}_action_{i}" value="keep" {"checked" if suggested_action == "keep" else ""}>
                            <span class="radio-label keep">Manter</span>
                        </label>
                        <label class="action-radio">
                            <input type="radio" name="{group_id}_action_{i}" value="delete" {"checked" if suggested_action == "delete" else ""}>
                            <span class="radio-label delete">Deletar</span>
                        </label>
                        <label class="action-radio">
                            <input type="radio" name="{group_id}_action_{i}" value="review">
                            <span class="radio-label review">Revisar</span>
                        </label>
                    </div>
                </div>
                <input type="hidden" class="file-path" value="{file_path}">
            </div>
            """
        
        return f"""
        <div class="group {group_type}" data-group-id="{group_id}">
            <div class="group-header">
                <h3>{title}</h3>
                <div class="group-actions">
                    <button onclick="selectAllKeepFirst('{group_id}')" class="btn btn-suggestion">Manter Primeiro</button>
                    <button onclick="selectAllDelete('{group_id}')" class="btn btn-danger">Deletar Todos</button>
                </div>
            </div>
            <div class="files-grid">
                {files_html}
            </div>
        </div>
        """    
    def _get_html_template(self) -> str:
        """Template HTML completo"""
        return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Duplicatas - Instagram Screenshots</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }
        
        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin: 1.5rem 0 0 0;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .controls {
            background: white;
            padding: 1.5rem;
            margin: 2rem auto;
            max-width: 1200px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .filter-buttons {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 0.6rem 1.2rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a6fd8;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-danger:hover {
            background: #c82333;
        }
        
        .btn-suggestion {
            background: #17a2b8;
            color: white;
        }
        
        .btn-suggestion:hover {
            background: #138496;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .section {
            margin-bottom: 3rem;
        }
        
        .section-title {
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.5rem;
        }
        
        .group {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            overflow: hidden;
            border-left: 5px solid #667eea;
        }
        
        .group.exact {
            border-left-color: #dc3545;
        }
        
        .group.similar {
            border-left-color: #ffc107;
        }
        
        .group-header {
            background: #f8f9fa;
            padding: 1.5rem;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .group-header h3 {
            margin: 0;
            color: #495057;
        }
        
        .group-actions {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .files-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            padding: 1.5rem;
        }
        
        .file-item {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.3s;
            background: #fff;
        }
        
        .file-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .image-container {
            height: 200px;
            background: #f8f9fa;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .image-container img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .no-image {
            color: #6c757d;
            text-align: center;
            padding: 2rem;
        }
        
        .file-details {
            padding: 1rem;
        }
        
        .file-name {
            font-weight: 600;
            margin-bottom: 0.5rem;
            word-break: break-all;
            font-size: 0.9rem;
        }
        
        .file-stats {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #6c757d;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        
        .file-actions {
            display: flex;
            gap: 0.5rem;
            justify-content: center;
        }
        
        .action-radio {
            cursor: pointer;
            user-select: none;
        }
        
        .action-radio input[type="radio"] {
            display: none;
        }
        
        .radio-label {
            padding: 0.4rem 0.8rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        
        .radio-label.keep {
            background: #d4edda;
            color: #155724;
        }
        
        .radio-label.delete {
            background: #f8d7da;
            color: #721c24;
        }
        
        .radio-label.review {
            background: #fff3cd;
            color: #856404;
        }
        
        .action-radio input[type="radio"]:checked + .radio-label {
            border-color: currentColor;
            font-weight: bold;
        }
        
        .results-panel {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 3px solid #667eea;
            padding: 1rem;
            box-shadow: 0 -4px 6px rgba(0,0,0,0.1);
            transform: translateY(100%);
            transition: transform 0.3s;
        }
        
        .results-panel.active {
            transform: translateY(0);
        }
        
        .results-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .results-stats {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }
        
        .results-stat {
            text-align: center;
        }
        
        .results-stat-number {
            font-size: 1.5rem;
            font-weight: bold;
            display: block;
        }
        
        .results-stat-label {
            font-size: 0.8rem;
            color: #6c757d;
        }
        
        @media (max-width: 768px) {
            .files-grid {
                grid-template-columns: 1fr;
            }
            
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .filter-buttons {
                justify-content: center;
            }
            
            .stats {
                gap: 1.5rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
        
        .filter-hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Relatório de Duplicatas</h1>
        <p class="subtitle">Instagram Screenshots - Verificação Manual</p>
        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">{{TOTAL_IMAGES}}</span>
                <span class="stat-label">Total de Imagens</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{{MD5_GROUPS}}</span>
                <span class="stat-label">Duplicatas Exatas</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{{PERCEPTUAL_GROUPS}}</span>
                <span class="stat-label">Grupos Similares</span>
            </div>
        </div>
        <p style="margin-top: 1rem; opacity: 0.8; font-size: 0.9rem;">Gerado em: {{TIMESTAMP}}</p>
    </div>

    <div class="controls">
        <div class="filter-buttons">
            <button class="btn btn-primary" onclick="showAll()">Mostrar Todos</button>
            <button class="btn btn-danger" onclick="showExact()">Duplicatas Exatas</button>
            <button class="btn btn-secondary" onclick="showSimilar()">Similares</button>
        </div>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <button class="btn btn-success" onclick="generateDeleteList()">Gerar Lista de Deleção</button>
            <button class="btn btn-suggestion" onclick="applyAllSuggestions()">Aplicar Sugestões</button>
        </div>
    </div>

    <div class="container">
        <div class="section">
            <h2 class="section-title">Duplicatas Exatas (MD5)</h2>
            <p style="margin-bottom: 2rem; color: #6c757d;">
                Estes arquivos são 100% idênticos. É seguro deletar as cópias.
            </p>
            {{MD5_GROUPS_HTML}}
        </div>

        <div class="section">
            <h2 class="section-title">Imagens Similares (Perceptual Hash)</h2>
            <p style="margin-bottom: 2rem; color: #6c757d;">
                Estas imagens são visualmente similares. Confira manualmente antes de deletar.
            </p>
            {{PERCEPTUAL_GROUPS_HTML}}
        </div>
    </div>

    <div class="results-panel" id="resultsPanel">
        <div class="results-content">
            <div class="results-stats">
                <div class="results-stat">
                    <span class="results-stat-number" id="keepCount">0</span>
                    <span class="results-stat-label">Manter</span>
                </div>
                <div class="results-stat">
                    <span class="results-stat-number" id="deleteCount">0</span>
                    <span class="results-stat-label">Deletar</span>
                </div>
                <div class="results-stat">
                    <span class="results-stat-number" id="reviewCount">0</span>
                    <span class="results-stat-label">Revisar</span>
                </div>
            </div>
            <div>
                <button class="btn btn-danger" onclick="downloadDeleteList()" id="downloadBtn" disabled>
                    Baixar Lista de Deleção
                </button>
            </div>
        </div>
    </div>

    <script>
        let currentFilter = 'all';
        
        function showAll() {
            currentFilter = 'all';
            document.querySelectorAll('.group').forEach(group => {
                group.classList.remove('filter-hidden');
            });
            updateButtonStates();
        }
        
        function showExact() {
            currentFilter = 'exact';
            document.querySelectorAll('.group').forEach(group => {
                if (group.classList.contains('exact')) {
                    group.classList.remove('filter-hidden');
                } else {
                    group.classList.add('filter-hidden');
                }
            });
            updateButtonStates();
        }
        
        function showSimilar() {
            currentFilter = 'similar';
            document.querySelectorAll('.group').forEach(group => {
                if (group.classList.contains('similar')) {
                    group.classList.remove('filter-hidden');
                } else {
                    group.classList.add('filter-hidden');
                }
            });
            updateButtonStates();
        }
        
        function updateButtonStates() {
            document.querySelectorAll('.filter-buttons .btn').forEach(btn => {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-secondary');
            });
            
            if (currentFilter === 'all') {
                document.querySelector('.filter-buttons .btn:first-child').classList.add('btn-primary');
                document.querySelector('.filter-buttons .btn:first-child').classList.remove('btn-secondary');
            } else if (currentFilter === 'exact') {
                document.querySelector('.filter-buttons .btn:nth-child(2)').classList.add('btn-primary');
                document.querySelector('.filter-buttons .btn:nth-child(2)').classList.remove('btn-secondary');
            } else if (currentFilter === 'similar') {
                document.querySelector('.filter-buttons .btn:nth-child(3)').classList.add('btn-primary');
                document.querySelector('.filter-buttons .btn:nth-child(3)').classList.remove('btn-secondary');
            }
        }
        
        function selectAllKeepFirst(groupId) {
            const group = document.querySelector(`[data-group-id="${groupId}"]`);
            const fileItems = group.querySelectorAll('.file-item');
            
            fileItems.forEach((item, index) => {
                const keepRadio = item.querySelector('input[value="keep"]');
                const deleteRadio = item.querySelector('input[value="delete"]');
                
                if (index === 0) {
                    keepRadio.checked = true;
                } else {
                    deleteRadio.checked = true;
                }
            });
            
            updateCounts();
        }
        
        function selectAllDelete(groupId) {
            const group = document.querySelector(`[data-group-id="${groupId}"]`);
            const deleteRadios = group.querySelectorAll('input[value="delete"]');
            
            deleteRadios.forEach(radio => {
                radio.checked = true;
            });
            
            updateCounts();
        }
        
        function applyAllSuggestions() {
            document.querySelectorAll('.group.exact').forEach(group => {
                const groupId = group.getAttribute('data-group-id');
                selectAllKeepFirst(groupId);
            });
        }
        
        function updateCounts() {
            const keepCount = document.querySelectorAll('input[value="keep"]:checked').length;
            const deleteCount = document.querySelectorAll('input[value="delete"]:checked').length;
            const reviewCount = document.querySelectorAll('input[value="review"]:checked').length;
            
            document.getElementById('keepCount').textContent = keepCount;
            document.getElementById('deleteCount').textContent = deleteCount;
            document.getElementById('reviewCount').textContent = reviewCount;
            
            const panel = document.getElementById('resultsPanel');
            const downloadBtn = document.getElementById('downloadBtn');
            
            if (keepCount > 0 || deleteCount > 0 || reviewCount > 0) {
                panel.classList.add('active');
                downloadBtn.disabled = deleteCount === 0;
            } else {
                panel.classList.remove('active');
                downloadBtn.disabled = true;
            }
        }
        
        function generateDeleteList() {
            updateCounts();
        }
        
        function downloadDeleteList() {
            const deleteFiles = [];
            
            document.querySelectorAll('input[value="delete"]:checked').forEach(radio => {
                const fileItem = radio.closest('.file-item');
                const filePath = fileItem.querySelector('.file-path').value;
                deleteFiles.push(filePath);
            });
            
            if (deleteFiles.length === 0) {
                alert('Nenhum arquivo selecionado para deleção!');
                return;
            }
            
            const deleteData = {
                timestamp: new Date().toISOString(),
                files_to_delete: deleteFiles,
                total_files: deleteFiles.length
            };
            
            const blob = new Blob([JSON.stringify(deleteData, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'delete_request.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            alert(`Lista de deleção gerada com ${deleteFiles.length} arquivos!\\nArquivo: delete_request.json`);
        }
        
        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('input[type="radio"]').forEach(radio => {
                radio.addEventListener('change', updateCounts);
            });
            
            updateButtonStates();
        });
    </script>
</body>
</html>'''

def main():
    # Procura o arquivo JSON no diretório pai (onde estão as imagens)
    json_file = r"C:\\Users\\henri\\Desktop\\scrape-instagram-gv\\duplicate_results.json"
    
    if not Path(json_file).exists():
        print(f"ERRO: Arquivo JSON não encontrado: {json_file}")
        print("Execute primeiro o find_duplicates.py")
        return
    
    print("Gerando relatório HTML interativo...")
    
    generator = HTMLReportGenerator(json_file)
    
    if generator.load_data():
        if generator.generate_html():
            print(f"\\nRelatório HTML criado com sucesso!")
            print(f"Arquivo: {generator.output_file}")
            print(f"\\nAbra o arquivo no navegador para verificar as duplicatas.")
            print("No relatório você pode:")
            print("- Ver thumbnails de todas as imagens")
            print("- Selecionar quais manter/deletar/revisar")
            print("- Baixar lista JSON para deleção automática")
        else:
            print("ERRO ao gerar HTML")
    else:
        print("ERRO ao carregar dados do JSON")

if __name__ == "__main__":
    main()