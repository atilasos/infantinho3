#!/usr/bin/env python3
"""Script para traduzir Aprendizagens Essenciais usando Ollama (modelo local)."""

import json
import requests
import sys
from pathlib import Path
from typing import List, Dict

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"  # Lighter model, good for Portuguese

PROMPT_TEMPLATE = """Tu és um especialista em pedagogia do Movimento da Escola Moderna (MEM) em Portugal.
A tua tarefa é traduzir objetivos curriculares oficiais (Aprendizagens Essenciais) em linguagem acessível a crianças de {ano}º ano.

REGRAS IMPORTANTES:
1. Usa sempre primeira pessoa: "Consigo...", "Sei...", "Faço..."
2. Linguagem simples, direta, sem termos técnicos
3. Foco na ação concreta (o que o aluno vai conseguir FAZER)
4. Inclui exemplos práticos do dia-a-dia
5. Mantém o entusiasmo e positividade

FORMATO DE RESPOSTA (JSON):
{{
    "objetivo_aluno": "Consigo... (linguagem simples, 1ª pessoa)",
    "exemplo_pratico": "Por exemplo, consigo... (situação real)",
    "como_sei_que_consegui": ["Indicador 1", "Indicador 2", "Indicador 3"]
}}

OBJETIVO OFICIAL (DGE):
Disciplina: {disciplina}
Ano: {ano}º
Domínio: {dominio}
Texto oficial: "{texto_oficial}"

TRADUÇÃO:"""


def translate_objective(disciplina: str, ano: int, dominio: str, texto_oficial: str) -> Dict:
    """Translate a single curriculum objective using Ollama."""
    prompt = PROMPT_TEMPLATE.format(
        disciplina=disciplina, ano=ano, dominio=dominio, texto_oficial=texto_oficial
    )
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.7, "num_predict": 500}
        }, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        text = result.get('response', '{}')
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {"objetivo_aluno": text.strip(), "exemplo_pratico": "N/A", "como_sei_que_consegui": []}
    except Exception as e:
        return {"objetivo_aluno": f"Erro: {str(e)}", "exemplo_pratico": "N/A", "como_sei_que_consegui": []}


MATEMATICA_5_OBJETIVOS = [
    {"codigo": "MAT-5-NO-01", "disciplina": "Matemática", "ano": 5, "dominio": "Números e Operações",
     "texto_oficial": "Compreender e usar números naturais, números decimais e números fracionários, desenvolvendo o sentido de número, incluindo a compreensão da estrutura do sistema de numeração decimal."},
    {"codigo": "MAT-5-NO-02", "disciplina": "Matemática", "ano": 5, "dominio": "Números e Operações",
     "texto_oficial": "Compreender o significado das operações aritméticas fundamentais e das suas propriedades, e desenvolver estratégias de cálculo mental e algoritmos de cálculo para resolver problemas em diversos contextos."},
    {"codigo": "MAT-5-NO-03", "disciplina": "Matemática", "ano": 5, "dominio": "Números e Operações",
     "texto_oficial": "Resolver problemas que envolvam a compreensão das relações multiplicativas entre números naturais, incluindo situações de proporcionalidade direta."},
    {"codigo": "MAT-5-GM-01", "disciplina": "Matemática", "ano": 5, "dominio": "Geometria e Medida",
     "texto_oficial": "Compreender e usar as noções de perímetro, área e ângulo, reconhecendo relações entre as grandezas e as unidades de medida, e resolver problemas em contextos diversos."},
    {"codigo": "MAT-5-GM-02", "disciplina": "Matemática", "ano": 5, "dominio": "Geometria e Medida",
     "texto_oficial": "Reconhecer e representar formas geométricas no plano e no espaço, utilizando diferentes representações e instrumentos, e compreender propriedades das figuras."},
    {"codigo": "MAT-5-OT-01", "disciplina": "Matemática", "ano": 5, "dominio": "Organização e Tratamento de Dados",
     "texto_oficial": "Recolher, organizar e representar dados, interpretar e comunicar informação contida em gráficos e tabelas, e formular questões que possam ser respondidas com base em dados."},
]


def process_all():
    results = []
    print("=" * 80)
    print("TRADUÇÃO DE APRENDIZAGENS ESSENCIAIS COM OLLAMA")
    print(f"Modelo: {MODEL}")
    print("=" * 80)
    
    for i, obj in enumerate(MATEMATICA_5_OBJETIVOS, 1):
        print(f"\n[{i}/{len(MATEMATICA_5_OBJETIVOS)}] {obj['codigo']}...", flush=True)
        translated = translate_objective(obj['disciplina'], obj['ano'], obj['dominio'], obj['texto_oficial'])
        result = {**obj, **translated}
        results.append(result)
        print(f"   ✅ {translated.get('objetivo_aluno', '')[:60]}...", flush=True)
    
    output_file = Path(__file__).parent / "knowledge" / "ae" / "5ano" / "matematica_traduzida.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"✅ Concluído! Guardado em: {output_file}")
    print(f"{'=' * 80}")
    return results


if __name__ == "__main__":
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code != 200:
            print("❌ Ollama não está a responder.")
            sys.exit(1)
    except:
        print("❌ Ollama não está a correr. Inicia com: ollama serve")
        sys.exit(1)
    
    print("✅ Ollama está a correr!")
    process_all()
