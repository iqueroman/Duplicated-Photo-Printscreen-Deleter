#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector de Imagens Duplicadas - Instagram Q&A Screenshots (VERSAO SIMPLES)
Implementa MD5 e Perceptual Hash para detectar duplicatas
CORRIGE: Problemas com caracteres especiais em nomes de arquivo
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Set

try:
    from PIL import Image
    import imagehash
except ImportError as e:
    print("Erro: Instale as dependências necessárias:")
    print("pip install Pillow imagehash")
    exit(1)

class DuplicateFinder:
    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        # Resultados
        self.md5_duplicates = defaultdict(list)
        self.perceptual_duplicates = []
        self.all_images = []
        
        print(f"Pasta origem: {self.source_dir}")
    
    def safe_file_access(self, file_path: Path) -> bool:
        """Verifica se o arquivo pode ser acessado com segurança"""
        try:
            if not file_path.exists():
                return False
            if not file_path.is_file():
                return False
            # Tenta abrir para leitura
            with open(file_path, 'rb') as f:
                f.read(1)  # Lê apenas 1 byte para testar
            return True
        except Exception:
            return False
    
    def get_image_files(self) -> List[Path]:
        """Coleta todos os arquivos de imagem da pasta"""
        images = set()  # Usar set para evitar duplicatas
        
        try:
            for file_path in self.source_dir.iterdir():
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in self.supported_formats:
                        # Verifica se o arquivo pode ser acessado
                        if self.safe_file_access(file_path):
                            images.add(file_path)
                        else:
                            print(f"AVISO: Arquivo inacessivel: {file_path.name}")
        except Exception as e:
            print(f"ERRO ao listar arquivos: {e}")
        
        images_list = sorted(list(images))
        print(f"Encontradas {len(images_list)} imagens acessiveis")
        return images_list
    
    def calculate_md5(self, file_path: Path) -> str:
        """Calcula hash MD5 do arquivo"""
        if not self.safe_file_access(file_path):
            return ""
            
        md5_hash = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            print(f"ERRO ao calcular MD5 de {file_path.name}: {e}")
            return ""
    
    def calculate_perceptual_hash(self, file_path: Path) -> str:
        """Calcula hash perceptual da imagem"""
        if not self.safe_file_access(file_path):
            return ""
            
        try:
            with Image.open(file_path) as img:
                # Usa dHash (difference hash) - bom para screenshots
                dhash = imagehash.dhash(img, hash_size=16)
                return str(dhash)
        except Exception as e:
            print(f"ERRO ao calcular hash perceptual de {file_path.name}: {e}")
            return ""
    
    def find_md5_duplicates(self):
        """Encontra duplicatas exatas usando MD5"""
        print("\\nETAPA 1: Buscando duplicatas exatas (MD5)...")
        
        images = self.get_image_files()
        self.all_images = images
        
        for i, img_path in enumerate(images):
            if i % 100 == 0:
                print(f"   Processando: {i+1}/{len(images)}")
            
            md5 = self.calculate_md5(img_path)
            if md5:
                self.md5_duplicates[md5].append(img_path)
        
        # Remove grupos com apenas 1 arquivo
        self.md5_duplicates = {k: v for k, v in self.md5_duplicates.items() if len(v) > 1}
        
        total_duplicates = sum(len(group) - 1 for group in self.md5_duplicates.values())
        print(f"RESULTADO: {len(self.md5_duplicates)} grupos com {total_duplicates} duplicatas exatas")
    
    def find_perceptual_duplicates(self, threshold: float = 0.85):
        """Encontra imagens similares usando hash perceptual"""
        print(f"\\nETAPA 2: Buscando imagens similares (Perceptual Hash, threshold={threshold})...")
        
        # Calcula hashes para todas as imagens
        image_hashes = {}
        processed = 0
        
        for img_path in self.all_images:
            phash = self.calculate_perceptual_hash(img_path)
            if phash:
                try:
                    image_hashes[img_path] = imagehash.hex_to_hash(phash)
                except:
                    print(f"ERRO ao converter hash: {img_path.name}")
            
            processed += 1
            if processed % 100 == 0:
                print(f"   Processando hashes: {processed}/{len(self.all_images)}")
        
        print(f"   Comparando similaridades...")
        
        # Compara todos os pares
        similar_groups = []
        processed_images = set()
        
        for i, (img1_path, hash1) in enumerate(image_hashes.items()):
            if img1_path in processed_images:
                continue
            
            current_group = [img1_path]
            
            for img2_path, hash2 in list(image_hashes.items())[i+1:]:
                if img2_path in processed_images:
                    continue
                
                try:
                    # Calcula diferença entre hashes (menor = mais similar)
                    diff = hash1 - hash2
                    similarity = 1.0 - (diff / 64.0)  # Normaliza para 0-1
                    
                    if similarity >= threshold:
                        current_group.append(img2_path)
                        processed_images.add(img2_path)
                except:
                    continue
            
            if len(current_group) > 1:
                similar_groups.append(current_group)
                for img in current_group:
                    processed_images.add(img)
        
        self.perceptual_duplicates = similar_groups
        total_similar = sum(len(group) - 1 for group in similar_groups)
        print(f"RESULTADO: {len(similar_groups)} grupos com {total_similar} imagens similares")
    
    def print_results(self):
        """Imprime resultados detalhados"""
        print("\\n" + "=" * 60)
        print("RELATORIO FINAL DE DUPLICATAS")
        print("=" * 60)
        
        print(f"\\nTOTAL DE IMAGENS ANALISADAS: {len(self.all_images)}")
        
        print(f"\\nDUPLICATAS EXATAS (MD5):")
        if self.md5_duplicates:
            for i, (md5_hash, files) in enumerate(self.md5_duplicates.items(), 1):
                print(f"\\n  Grupo {i} ({len(files)} arquivos):")
                for file_path in files:
                    print(f"    - {file_path.name}")
        else:
            print("  Nenhuma duplicata exata encontrada")
        
        print(f"\\nIMAGENS SIMILARES (Perceptual Hash):")
        if self.perceptual_duplicates:
            for i, group in enumerate(self.perceptual_duplicates, 1):
                print(f"\\n  Grupo {i} ({len(group)} arquivos):")
                for file_path in group:
                    print(f"    - {file_path.name}")
        else:
            print("  Nenhuma imagem similar encontrada")
        
        # Salva resultados em JSON
        self.save_results_json()
    
    def save_results_json(self):
        """Salva resultados em arquivo JSON"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_images": len(self.all_images),
            "md5_duplicates": {},
            "perceptual_duplicates": []
        }
        
        # MD5 duplicates
        for i, (md5_hash, files) in enumerate(self.md5_duplicates.items(), 1):
            results["md5_duplicates"][f"grupo_{i}"] = {
                "hash": md5_hash,
                "files": [str(f) for f in files]
            }
        
        # Perceptual duplicates
        for i, group in enumerate(self.perceptual_duplicates, 1):
            results["perceptual_duplicates"].append({
                "grupo": i,
                "files": [str(f) for f in group]
            })
        
        # Salva arquivo
        output_file = self.source_dir.parent / "duplicate_results.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\\nResultados salvos em: {output_file}")
        except Exception as e:
            print(f"ERRO ao salvar JSON: {e}")

def main():
    source_folder = r"XXXXXXXXX"
    
    if not Path(source_folder).exists():
        print(f"ERRO: Pasta não encontrada: {source_folder}")
        return
    
    print("DETECTOR DE DUPLICATAS - Instagram Screenshots")
    print("=" * 60)
    print(f"Analisando pasta: {source_folder}")
    
    finder = DuplicateFinder(source_folder)
    
    try:
        print("\\nIniciando análise completa de duplicatas...")
        print("=" * 60)
        
        # Etapa 1: MD5 (duplicatas exatas)
        finder.find_md5_duplicates()
        
        # Etapa 2: Perceptual Hash (imagens similares)
        finder.find_perceptual_duplicates(threshold=0.85)
        
        # Imprime resultados
        finder.print_results()
        
        print("\\nAnalise completa!")
        
    except KeyboardInterrupt:
        print("\\nAnalise interrompida pelo usuario")
    except Exception as e:
        print(f"\\nERRO durante análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()