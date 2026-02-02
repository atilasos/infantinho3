"""
AE Knowledge Base for AI Assistant

This module provides the AI assistant with structured knowledge about
the Aprendizagens Essenciais (Portuguese curriculum), enabling:
- Contextualized tutoring
- Curriculum-aligned suggestions  
- Informed decision-making
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class AEKnowledgeBase:
    """
    Knowledge base for Portuguese curriculum (Aprendizagens Essenciais).
    Used by AI assistant to make informed pedagogical decisions.
    """
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "knowledge" / "ae"
        self.data_dir = data_dir
        self._cache = {}
        self._load_all()
    
    def _load_all(self):
        """Load all translated AE data."""
        for json_file in self.data_dir.rglob("*_traduzida.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Index by code
                    for obj in data:
                        self._cache[obj['codigo']] = obj
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")
    
    def get_objective(self, codigo: str) -> Optional[Dict]:
        """Get a specific objective by code (e.g., 'MAT-5-NO-01')."""
        return self._cache.get(codigo)
    
    def get_by_year_subject(self, ano: int, disciplina: str) -> List[Dict]:
        """Get all objectives for a specific year and subject."""
        return [
            obj for obj in self._cache.values()
            if obj.get('ano') == ano and obj.get('disciplina') == disciplina
        ]
    
    def get_context_for_student(self, ano: int, disciplina: str = None) -> str:
        """
        Generate context string for AI assistant about what a student
        should be learning.
        """
        if disciplina:
            objetivos = self.get_by_year_subject(ano, disciplina)
        else:
            objetivos = [obj for obj in self._cache.values() if obj.get('ano') == ano]
        
        if not objetivos:
            return f"Não há informação curricular disponível para {ano}º ano."
        
        lines = [f"APRENDIZAGENS ESSENCIAIS - {ano}º ANO", "=" * 50]
        
        current_domain = None
        for obj in sorted(objetivos, key=lambda x: x.get('codigo', '')):
            domain = obj.get('dominio', 'Geral')
            if domain != current_domain:
                lines.append(f"\n📚 {domain}")
                current_domain = domain
            
            lines.append(f"  • {obj.get('objetivo_aluno', 'N/A')}")
            if obj.get('exemplo_pratico'):
                lines.append(f"    Ex: {obj['exemplo_pratico']}")
        
        return "\n".join(lines)
    
    def suggest_next_steps(self, current_code: str) -> List[Dict]:
        """
        Suggest next learning objectives based on prerequisites.
        This helps the AI assistant guide students progressively.
        """
        current = self.get_objective(current_code)
        if not current:
            return []
        
        ano = current.get('ano')
        disciplina = current.get('disciplina')
        dominio = current.get('dominio')
        
        # Find related objectives (same domain, same year)
        related = [
            obj for obj in self._cache.values()
            if obj.get('ano') == ano 
            and obj.get('disciplina') == disciplina
            and obj.get('dominio') == dominio
            and obj['codigo'] != current_code
        ]
        
        return related[:3]  # Return top 3 suggestions


# Global instance
ae_kb = AEKnowledgeBase()


def enrich_ai_context(student_year: int, student_subject: str = None, 
                      current_topic: str = None) -> str:
    """
    Enrich AI context with curriculum knowledge.
    
    This function is called by the AI service to provide relevant
    curriculum context for tutoring conversations.
    """
    context_parts = []
    
    # Add curriculum context
    if student_year:
        curriculum_ctx = ae_kb.get_context_for_student(student_year, student_subject)
        context_parts.append(curriculum_ctx)
    
    # Add specific topic info if provided
    if current_topic:
        context_parts.append(f"\n📌 TÓPICO ATUAL: {current_topic}")
        context_parts.append("O aluno está a trabalhar neste tema específico.")
    
    return "\n\n".join(context_parts)


# Integration with ai_service.py
"""
Usage in ai_service.py:

from .ae_knowledge import enrich_ai_context

class AIService:
    def chat(self, messages, role='aluno', context=None):
        # ... existing code ...
        
        # Add curriculum context if we know the student's year
        if context and context.get('student_year'):
            curriculum_context = enrich_ai_context(
                student_year=context['student_year'],
                student_subject=context.get('subject'),
                current_topic=context.get('current_topic')
            )
            system_prompt += f"\n\nCONTEXTO CURRICULAR:\n{curriculum_context}"
        
        # ... rest of method ...
"""
