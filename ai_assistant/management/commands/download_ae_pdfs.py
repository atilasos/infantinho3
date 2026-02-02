#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Django management command para download dos PDFs das Aprendizagens Essenciais
Ensino Básico Português - DGE (Direção-Geral da Educação)
"""

import os
import time
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Command(BaseCommand):
    help = "Download dos PDFs das Aprendizagens Essenciais do Ensino Básico"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = self._create_session()

    def _create_session(self):
        """Cria sessão HTTP com retry automático"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=str,
            default="/tmp/infantinho3/ai_assistant/knowledge/ae",
            help="Diretório de destino para os PDFs",
        )
        parser.add_argument(
            "--anos",
            nargs="+",
            type=int,
            default=[5, 6, 7, 8, 9],
            help="Anos a descarregar (ex: 5 6 7 8 9)",
        )
        parser.add_argument(
            "--disciplinas",
            nargs="+",
            type=str,
            default=["portugues", "matematica", "ciencias", "historia"],
            help="Disciplinas a descarregar",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra o que seria descarregado sem efetuar o download",
        )

    def _get_ciclo(self, ano):
        """Determina o ciclo com base no ano"""
        if ano in [1, 2, 3, 4]:
            return "1_ciclo"
        elif ano in [5, 6]:
            return "2_ciclo"
        elif ano in [7, 8, 9]:
            return "3_ciclo"
        return None

    def _get_disciplina_url(self, ano, disciplina):
        """Gera o URL do PDF com base no ano e disciplina"""
        ciclo = self._get_ciclo(ano)
        if not ciclo:
            return None

        base_url = "https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais"
        
        # Mapeamento de disciplinas para nomes de ficheiros
        disciplina_map = {
            "portugues": "portugues",
            "matematica": "matematica",
            "ciencias": "ciencias_naturais",
            "historia": "historia",
            "estudo_do_meio": "estudo_do_meio",
            "geografia": "geografia",
            "ingles": "ingles",
        }
        
        disc_key = disciplina.lower().replace(" ", "_")
        disc_filename = disciplina_map.get(disc_key, disc_key)
        
        return f"{base_url}/{ciclo}/{ano}_{disc_filename}.pdf"

    def _download_pdf(self, url, dest_path):
        """Download de um PDF com progresso"""
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            
            with open(dest_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.stdout.write(f"\r  ↳ {percent:.1f}%", ending="")
            
            self.stdout.write("")
            return True
            
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"\n  ✗ Erro: {e}")
            return False

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        anos = options["anos"]
        disciplinas = options["disciplinas"]
        dry_run = options["dry_run"]

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("Download Aprendizagens Essenciais"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(f"\nDiretório: {output_dir}")
        self.stdout.write(f"Anos: {', '.join(map(str, anos))}")
        self.stdout.write(f"Disciplinas: {', '.join(disciplinas)}")
        if dry_run:
            self.stdout.write(self.style.WARNING("\n[MODO DRY-RUN - Sem downloads]"))
        self.stdout.write("")

        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        total_ficheiros = 0
        sucessos = 0
        falhas = 0

        for ano in anos:
            ciclo = self._get_ciclo(ano)
            if not ciclo:
                self.stderr.write(f"Ano inválido: {ano}")
                continue

            # Criar subdiretório para o ano
            ano_dir = output_dir / ciclo / f"ano_{ano}"
            if not dry_run:
                ano_dir.mkdir(parents=True, exist_ok=True)

            self.stdout.write(self.style.HTTP_INFO(f"\n📁 {ciclo.replace('_', ' ').title()} - {ano}º Ano"))
            self.stdout.write("-" * 40)

            for disciplina in disciplinas:
                url = self._get_disciplina_url(ano, disciplina)
                if not url:
                    continue

                # Nome do ficheiro local
                disc_clean = disciplina.lower().replace(" ", "_")
                filename = f"{ano}_{disc_clean}.pdf"
                dest_path = ano_dir / filename

                total_ficheiros += 1

                if dry_run:
                    self.stdout.write(f"  • {filename}")
                    self.stdout.write(f"    URL: {url}")
                    continue

                # Verificar se já existe
                if dest_path.exists():
                    size = dest_path.stat().st_size
                    self.stdout.write(f"  ✓ {filename} ({size:,} bytes) - já existe")
                    sucessos += 1
                    continue

                # Download
                self.stdout.write(f"  ↓ {filename}")
                self.stdout.write(f"    URL: {url}")
                
                if self._download_pdf(url, dest_path):
                    size = dest_path.stat().st_size
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Concluído ({size:,} bytes)"))
                    sucessos += 1
                else:
                    falhas += 1

                # Pequena pausa entre downloads
                time.sleep(0.5)

        # Resumo
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("RESUMO"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(f"Total de ficheiros: {total_ficheiros}")
        self.stdout.write(self.style.SUCCESS(f"Sucessos: {sucessos}"))
        if falhas > 0:
            self.stdout.write(self.style.ERROR(f"Falhas: {falhas}"))
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("Executa sem --dry-run para efetuar os downloads."))
