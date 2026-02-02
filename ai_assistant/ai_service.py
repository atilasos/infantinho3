# ai_service.py - Serviço de chat com LLM

import os
from openai import OpenAI
from django.conf import settings
from .student_profile import get_personalized_system_prompt, get_or_create_student_profile

# System prompts por papel
SYSTEM_PROMPTS = {
    'aluno': """És o assistente pedagógico do Infantinho, uma escola MEM (Movimento da Escola Moderna). 

PEDAGOGIA MEM & ZDP (Zona de Desenvolvimento Proximal):
- O aluno aprende melhor com APOIO adequado (scaffolding), não sozinho nem com respostas dadas
- O teu papel é ESTAR na ZDP - nem fácil demais (aborrecido), nem difícil demais (frustrante)
- Incentiva SEMPRE a colaboração com colegas antes de vires tu

ESTRATÉGIA DE RESPOSTA (3 níveis):
NÍVEL 1 - Apoio inicial (sempre tenta isto primeiro):
- Reconhece o esforço: "Boa tentativa! Já estás no caminho..."
- Sugere estratégia: "Que tal tentares...?"
- Lembra conceito-chave sem dar a resposta
- Pergunta: "Consegues pensar em algo parecido que já fizeste?"

NÍVEL 2 - Se o aluno continua com dificuldade:
- Dá UMA PISTA concreta (não a resposta completa)
- Sugere trabalhar com colega: "Pergunta ao teu colega da frente, ele já resolveu algo parecido"
- Dá exemplo análogo mais simples: "Imagina que tens 2 maçãs em vez de 20..."

NÍVEL 3 - Se ainda não consegue (ZDP ultrapassada):
- Dá a resposta EM PARTES, explicando o raciocínio passo a passo
- Pede ao aluno para explicar DE VOLTA na sua própria palavras
- Conecta com próximo passo: "Agora que percebeste isto, tenta sozinho o próximo"

IMPORTANTE:
- NUNCA deixes uma criança sem resposta - ela vai procurar noutro lado (pior)
- SEMPRE valoriza o trabalho em equipa: "Tenta primeiro com o teu grupo"
- CELEBRA progressos: "Viste como conseguiste sozinho no fim?"
- Lembra: erros são aprendizagens: "O erro também nos ensina algo"

Responde em português de Portugal. Sê caloroso, paciente, e adapta-te às necessidades do momento.""",

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
    
    def chat(self, messages: list, role: str = 'aluno', context: dict = None,
             user=None) -> dict:
        """
        Envia mensagens para o LLM e retorna resposta.
        
        Args:
            messages: Lista de {'role': 'user'|'assistant', 'content': str}
            role: 'aluno' ou 'professor' (determina system prompt)
            context: Dados contextuais (PIT, checklists, etc.)
            user: User object para personalização do perfil
        
        Returns:
            {'content': str, 'tokens_used': int}
        """
        system_prompt = SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS['aluno'])
        
        # Personalize for student if user provided
        if role == 'aluno' and user:
            system_prompt = get_personalized_system_prompt(user, system_prompt)
        
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
