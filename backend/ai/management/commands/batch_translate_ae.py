#!/usr/bin/env python3
"""
Batch processor for Aprendizagens Essenciais using local Ollama.
Generates Markdown files for all years (1-9) and subjects.
Runs in background - doesn't block other work.
"""

import json
import requests
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"  # Lightweight, good for Portuguese

# All subjects by cycle
SUBJECTS = {
    "1_ciclo": {  # 1st-4th grade
        1: ["portugues", "matematica", "estudo_do_meio"],
        2: ["portugues", "matematica", "estudo_do_meio"],
        3: ["portugues", "matematica", "estudo_do_meio"],
        4: ["portugues", "matematica", "estudo_do_meio"],
    },
    "2_ciclo": {  # 5th-6th grade
        5: ["portugues", "matematica", "ciencias_naturais", "historia_geografia"],
        6: ["portugues", "matematica", "ciencias_naturais", "historia_geografia"],
    },
    "3_ciclo": {  # 7th-9th grade
        7: ["portugues", "matematica", "ciencias_naturais", "historia_geografia", "ingles"],
        8: ["portugues", "matematica", "ciencias_naturais", "historia_geografia", "ingles"],
        9: ["portugues", "matematica", "ciencias_naturais", "historia_geografia", "ingles"],
    }
}

# Sample objectives for each subject (to be expanded)
SAMPLE_OBJECTIVES = {
    "portugues": [
        {"code": "PORT-{ano}-01", "domain": "Leitura", "official": "Ler e compreender textos narrativos, descritivos e expositivos, identificando o tema, a ideia principal e as informações explícitas e implícitas."},
        {"code": "PORT-{ano}-02", "domain": "Escrita", "official": "Produzir textos coerentes e coesos, adequados ao tema, ao propósito e ao destinatário, utilizando vocabulário adequado e estruturas sintáticas variadas."},
        {"code": "PORT-{ano}-03", "domain": "Oralidade", "official": "Expressar-se oralmente de forma clara, fluente e adequada à situação comunicativa, respeitando as regras de cortesia e os turnos de fala."},
    ],
    "matematica": [
        {"code": "MAT-{ano}-01", "domain": "Números", "official": "Compreender e usar números naturais, inteiros, racionais e decimais, desenvolvendo o sentido de número."},
        {"code": "MAT-{ano}-02", "domain": "Álgebra", "official": "Identificar padrões, relações e regularidades, e usar expressões algébricas para representar situações."},
        {"code": "MAT-{ano}-03", "domain": "Geometria", "official": "Reconhecer e representar formas geométricas, compreendendo propriedades e relações."},
    ],
    "ciencias_naturais": [
        {"code": "CN-{ano}-01", "domain": "Materiais", "official": "Identificar propriedades dos materiais e compreender as suas aplicações no quotidiano."},
        {"code": "CN-{ano}-02", "domain": "Seres Vivos", "official": "Reconhecer a diversidade de seres vivos e compreender as relações entre eles e o ambiente."},
    ],
    "historia_geografia": [
        {"code": "HG-{ano}-01", "domain": "Tempo", "official": "Identificar e ordenar acontecimentos no tempo, estabelecendo relações entre o passado e o presente."},
        {"code": "HG-{ano}-02", "domain": "Espaço", "official": "Localizar e representar elementos no espaço, usando diferentes tipos de mapas e representações."},
    ],
}

PROMPT_TEMPLATE = """Tu és um especialista em pedagogia MEM (Movimento da Escola Moderna) em Portugal.

MISSÃO: Traduzir este objetivo curricular oficial (Aprendizagens Essenciais) para linguagem acessível a crianças de {ano}º ano.

PRINCÍPIOS MEM:
- Aprendizagem sócio-construtivista (Vygotsky)
- Zona de Desenvolvimento Proximal (ZDP) - apoio adequado
- Valorização do trabalho colaborativo
- Autonomia progressiva

REGRAS DE TRADUÇÃO:
1. Usa PRIMEIRA PESSOA: "Consigo...", "Sei...", "Faço..."
2. Linguagem simples, direta, sem termos técnicos
3. Foco na AÇÃO CONCRETA (o que a criança vai conseguir FAZER)
4. Inclui exemplo prático do dia-a-dia
5. Mantém entusiasmo e positividade

FORMATO DE RESPOSTA (Markdown):

### {code}: {domain}

**Original (DGE):**
> {official}

**Para o Aluno:**
Consigo [ação concreta em linguagem simples].

**Exemplo Prático:**
Por exemplo, consigo [situação real do dia-a-dia].

**Como sei que consegui:**
- [Indicador 1 concreto]
- [Indicador 2 concreto]
- [Indicador 3 concreto]

**Estratégias de Apoio:**
- [Dica 1 para ajudar]
- [Dica 2 para ajudar]

---

OBJETIVO A TRADUZIR:
Ano: {ano}º
Domínio: {domain}
Código: {code}
Texto oficial: "{official}"

TRADUÇÃO:"""


def translate_objective(ano: int, code: str, domain: str, official: str) -> str:
    """Translate a single objective using Ollama."""
    prompt = PROMPT_TEMPLATE.format(
        ano=ano, code=code, domain=domain, official=official
    )
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 800
            }
        }, timeout=120)
        
        response.raise_for_status()
        result = response.json()
        return result.get('response', 'Erro na tradução')
        
    except Exception as e:
        return f"Erro: {str(e)}"


def process_year_subject(ano: int, subject: str, output_dir: Path) -> int:
    """Process all objectives for a year/subject. Returns count."""
    objectives = SAMPLE_OBJECTIVES.get(subject, [])
    if not objectives:
        return 0
    
    md_content = f"""# {subject.replace('_', ' ').title()} - {ano}º Ano

**Gerado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Modelo:** {MODEL}
**Fonte:** Aprendizagens Essenciais (DGE)

---

"""
    
    count = 0
    for obj in objectives:
        code = obj['code'].format(ano=ano)
        print(f"  Translating {code}...", flush=True)
        
        translated = translate_objective(
            ano=ano,
            code=code,
            domain=obj['domain'],
            official=obj['official']
        )
        
        md_content += translated + "\n\n"
        count += 1
        
        # Small delay to not overwhelm the system
        time.sleep(0.5)
    
    # Save to file
    filename = f"{subject}.md"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return count


def main():
    """Main processing loop."""
    print("=" * 80)
    print("BATCH PROCESSOR - APRENDIZAGENS ESSENCIAIS")
    print(f"Modelo: {MODEL}")
    print(f"Início: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)
    
    # Check Ollama
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code != 200:
            print("❌ Ollama não responde")
            sys.exit(1)
    except:
        print("❌ Ollama offline. Inicia com: ollama serve")
        sys.exit(1)
    
    print("✅ Ollama OK\n")
    
    base_dir = Path("/tmp/infantinho3/backend/ai/knowledge/ae")
    total = 0
    
    # Process all years and subjects
    for cycle, years in SUBJECTS.items():
        print(f"\n📚 Ciclo: {cycle}")
        
        for ano, subjects in years.items():
            print(f"\n  🎓 {ano}º Ano:")
            output_dir = base_dir / f"{ano}ano"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for subject in subjects:
                print(f"    📖 {subject}...", end=" ", flush=True)
                count = process_year_subject(ano, subject, output_dir)
                total += count
                print(f"✅ ({count} objetivos)")
    
    print("\n" + "=" * 80)
    print(f"✅ CONCLUÍDO: {total} objetivos traduzidos")
    print(f"Fim: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
