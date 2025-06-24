#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de Deleções - Executa deleção dos arquivos selecionados no HTML
Lê arquivo delete_request.json e move arquivos para backup antes de deletar
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import os

def create_backup_and_delete(delete_request_file: str = "delete_request.json"):
    """Processa solicitação de deleção com backup automático"""
    
    # Verifica se arquivo de solicitação existe
    request_path = Path(delete_request_file)
    if not request_path.exists():
        print(f"ERRO: Arquivo não encontrado: {delete_request_file}")
        print("Execute primeiro o relatório HTML e selecione arquivos para deletar")
        return
    
    try:
        # Carrega solicitação
        with open(request_path, 'r', encoding='utf-8') as f:
            delete_data = json.load(f)
        
        files_to_delete = delete_data.get('files_to_delete', [])
        if not files_to_delete:
            print("ERRO: Nenhum arquivo para deletar na solicitação")
            return
        
        print(f"Processando deleção de {len(files_to_delete)} arquivos...")
        
        # Cria pasta de backup com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"backup_deletions_{timestamp}")
        backup_dir.mkdir(exist_ok=True)
        
        print(f"Pasta de backup criada: {backup_dir}")
        
        # Processa cada arquivo
        deleted_count = 0
        error_count = 0
        
        for file_path in files_to_delete:
            try:
                source_path = Path(file_path)
                
                if not source_path.exists():
                    print(f"AVISO: Arquivo não encontrado: {source_path.name}")
                    error_count += 1
                    continue
                
                # Cria backup
                backup_path = backup_dir / source_path.name
                shutil.copy2(source_path, backup_path)
                
                # Deleta original
                source_path.unlink()
                
                print(f"Deletado: {source_path.name}")
                deleted_count += 1
                
            except Exception as e:
                print(f"ERRO ao processar {Path(file_path).name}: {e}")
                error_count += 1
        
        # Salva log da operação
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "backup_directory": str(backup_dir),
            "total_requested": len(files_to_delete),
            "successfully_deleted": deleted_count,
            "errors": error_count,
            "deleted_files": [str(Path(f).name) for f in files_to_delete if Path(f).exists() == False]
        }
        
        log_file = backup_dir / "deletion_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"\\nRESULTADO:")
        print(f"- Arquivos deletados: {deleted_count}")
        print(f"- Erros: {error_count}")
        print(f"- Backup salvo em: {backup_dir}")
        print(f"- Log detalhado: {log_file}")
        
        if deleted_count > 0:
            print(f"\\nSUCESSO: {deleted_count} arquivos foram deletados com backup!")
        
    except Exception as e:
        print(f"ERRO durante processamento: {e}")

def restore_backup(backup_dir: str):
    """Restaura arquivos de um backup específico"""
    backup_path = Path(backup_dir)
    
    if not backup_path.exists():
        print(f"ERRO: Pasta de backup não encontrada: {backup_dir}")
        return
    
    # Lê log do backup
    log_file = backup_path / "deletion_log.json"
    if not log_file.exists():
        print(f"ERRO: Log do backup não encontrado: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # Pasta original (assume que é a pasta pai do primeiro arquivo)
        original_dir = Path("C:\\\\Users\\\\henri\\\\Desktop\\\\scrape-instagram-gv\\\\prints")
        
        print(f"Restaurando {log_data['successfully_deleted']} arquivos...")
        
        restored_count = 0
        for file_path in backup_path.iterdir():
            if file_path.is_file() and file_path.name != "deletion_log.json":
                try:
                    # Restaura arquivo
                    dest_path = original_dir / file_path.name
                    shutil.copy2(file_path, dest_path)
                    
                    print(f"Restaurado: {file_path.name}")
                    restored_count += 1
                    
                except Exception as e:
                    print(f"ERRO ao restaurar {file_path.name}: {e}")
        
        print(f"\\nRESTAURAÇÃO COMPLETA: {restored_count} arquivos restaurados")
        
    except Exception as e:
        print(f"ERRO durante restauração: {e}")

def list_backups():
    """Lista todos os backups disponíveis"""
    backup_dirs = [d for d in Path(".").iterdir() if d.is_dir() and d.name.startswith("backup_deletions_")]
    
    if not backup_dirs:
        print("Nenhum backup encontrado")
        return
    
    print("BACKUPS DISPONÍVEIS:")
    print("=" * 40)
    
    for backup_dir in sorted(backup_dirs):
        log_file = backup_dir / "deletion_log.json"
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                timestamp = log_data.get('timestamp', 'Unknown')
                deleted_count = log_data.get('successfully_deleted', 0)
                
                print(f"📁 {backup_dir.name}")
                print(f"   Data: {timestamp}")
                print(f"   Arquivos: {deleted_count}")
                print()
                
            except:
                print(f"📁 {backup_dir.name} (log corrompido)")
        else:
            print(f"📁 {backup_dir.name} (sem log)")

def main():
    print("PROCESSADOR DE DELEÇÕES - Instagram Screenshots")
    print("=" * 50)
    
    while True:
        print("\\nOpções:")
        print("1. Processar lista de deleção (delete_request.json)")
        print("2. Listar backups disponíveis")
        print("3. Restaurar backup")
        print("4. Sair")
        
        choice = input("\\nEscolha uma opção (1-4): ").strip()
        
        if choice == "1":
            create_backup_and_delete()
        elif choice == "2":
            list_backups()
        elif choice == "3":
            list_backups()
            backup_name = input("\\nDigite o nome da pasta de backup: ").strip()
            if backup_name:
                restore_backup(backup_name)
        elif choice == "4":
            print("Saindo...")
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    main()