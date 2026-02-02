# ai_service.py - Serviço de chat com LLM

import os
from openai import OpenAI
from django.conf import settings

# System prompts por papel
SYSTEM_PROMPTS = {
    'aluno': """És o assistente pedagógico do Infantinho, uma escola que segue a pedagogia do 
Movimento da Escola Moderna (MEM). 

PRINCÍPIOS QUE SEGUES:
- NUNCA dás respostas diretas a exercícios ou perguntas académicas
- Fazes perguntas socráticas para guiar o raciocínio do aluno
- Celebras o esforço e o processo, não só os resultados
- Incentivas a autonomia e a autoavaliação
- Valorizas o trabalho cooperativo e a entreajuda
- Lembras que o Conselho de Turma é o espaço democrático para decisões coletivas
- Encorajas a comunicação e apresentação de trabalhos

Responde sempre em português de Portugal. Sê amigável, paciente e educativo.
Quando o aluno pede ajuda com exercícios, pergunta-lhe primeiro o que já tentou e o que está a pensar.""",

    'professor': """És o assistente pedagógico do Infantinho para professores que seguem a pedagogia do 
Movimento da Escola Moderna (MEM).

PODES:
- Analisar dados de progresso dos alunos
- Sugerir intervenções pedagógicas diferenciadas
- Ajudar a planear aulas e atividades alinhadas às Aprendizagens Essenciais
- Elaborar feedback formativo construtivo
- Preparar materiais para o Conselho de Turma
- Sugerir formas de promover autonomia e cooperação

Responde sempre em português de Portugal. Sê profissional, prático e fundamentado na pedagogia MEM.""",
}

class AIService:
    def __init__(self):
        self._client = None
        self.default_model = 'gpt-4o-mini'
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self._client = OpenAI(api_key=api_key)
            else:
                raise ValueError("OPENAI_API_KEY não está definida. Configura a variável de ambiente.")
        return self._client
    
    def chat(self, messages: list, role: str = 'aluno', context: dict = None) -> dict:
        """
        Envia mensagens para o LLM e retorna resposta.
        
        Args:
            messages: Lista de {'role': 'user'|'assistant', 'content': str}
            role: 'aluno' ou 'professor' (determina system prompt)
            context: Dados contextuais (PIT, checklists, etc.)
        
        Returns:
            {'content': str, 'tokens_used': int}
        """
        system_prompt = SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS['aluno'])
        
        # Adicionar contexto ao system prompt se disponível
        if context:
            context_str = self._format_context(context)
            system_prompt += f"\n\nCONTEXTO DO UTILIZADOR:\n{context_str}"
        
        full_messages = [{'role': 'system', 'content': system_prompt}] + messages
        
        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=full_messages,
                max_tokens=1000,
                temperature=0.7,
            )
            return {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
            }
        except Exception as e:
            return {
                'content': f'Desculpa, houve um erro. Tenta novamente mais tarde.',
                'tokens_used': 0,
                'error': str(e),
            }
    
    def _format_context(self, context: dict) -> str:
        parts = []
        if 'student_name' in context:
            parts.append(f"Nome: {context['student_name']}")
        if 'class_name' in context:
            parts.append(f"Turma: {context['class_name']}")
        if 'pit_summary' in context:
            parts.append(f"PIT atual: {context['pit_summary']}")
        if 'checklist_progress' in context:
            parts.append(f"Progresso nas listas: {context['checklist_progress']}")
        return '\n'.join(parts)

# Instância singleton
ai_service = AIService()
