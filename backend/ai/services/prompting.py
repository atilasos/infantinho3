from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.conf import settings
from ai.constants import PROMPT_OPTIMIZER_MODEL, RESPONSE_GUARD_MODEL
from ai.services.config import is_fake_mode_enabled
from ai.services.providers import ProviderResponse, get_provider


# ============================================================================
# SYSTEM PROMPTS - ZDP (Zona de Desenvolvimento Proximal)
# ============================================================================

SYSTEM_PROMPTS = {
    'student': """És o assistente pedagógico do Infantinho, uma escola MEM (Movimento da Escola Moderna). 

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

    'teacher': """És o assistente pedagógico do Infantinho para professores que seguem a pedagogia do 
Movimento da Escola Moderna (MEM).

PODES:
- Analisar dados de progresso dos alunos
- Sugerir intervenções pedagógicas diferenciadas
- Ajudar a planear aulas e atividades alinhadas às Aprendizagens Essenciais
- Elaborar feedback formativo construtivo
- Preparar materiais para o Conselho de Turma
- Sugerir formas de promover autonomia e cooperação

Responde sempre em português de Portugal. Sê profissional, prático e fundamentado na pedagogia MEM.""",

    'guardian': """És o assistente do Infantinho para encarregados de educação.

PODES:
- Explicar o progresso do educando de forma clara
- Contextualizar a pedagogia MEM
- Sugerir formas de apoiar a aprendizagem em casa
- Responder a dúvidas sobre o funcionamento da escola

Sê acessível e empático. Responde em português de Portugal.""",

    'admin': """És o assistente administrativo do Infantinho.

PODES:
- Ajudar com relatórios e análises
- Sugerir melhorias processuais
- Apoiar decisões baseadas em dados

Sê profissional e eficiente. Responde em português de Portugal.""",
}


def get_zdp_system_prompt(persona: str, student_profile: Optional[Dict] = None) -> str:
    """
    Obtém o system prompt adequado à persona, personalizado com perfil do aluno se disponível.
    
    Args:
        persona: 'student', 'teacher', 'guardian', 'admin'
        student_profile: Dados do perfil do aluno (ZDP level, preferences, etc.)
    
    Returns:
        System prompt personalizado
    """
    base_prompt = SYSTEM_PROMPTS.get(persona, SYSTEM_PROMPTS['student'])
    
    if persona == 'student' and student_profile:
        # Personalização baseada no perfil ZDP
        zdp_level = student_profile.get('zdp_level', 'intermediate')
        preferences = student_profile.get('learning_preferences', {})
        strengths = student_profile.get('strengths', [])
        growth_areas = student_profile.get('growth_areas', [])
        
        personalization = f"""

PERFIL DESTE ALUNO:
- Nível ZDP: {zdp_level}
- Preferências: {', '.join(preferences.keys()) if preferences else 'A descobrir'}
- Pontos fortes: {', '.join(strengths) if strengths else 'A descobrir'}
- Áreas de crescimento: {', '.join(growth_areas) if growth_areas else 'A descobrir'}

Adapta o teu apoio a este perfil específico."""
        
        base_prompt += personalization
    
    return base_prompt


@dataclass
class OptimizerResult:
    optimized_prompt: str
    intent: str
    suggested_model: Optional[str]
    optimizer_trace: Dict[str, Any]


class PromptOptimizer:
    SYSTEM_PROMPT = (
        "Atua como assistente pedagógico MEM. Analisa o pedido do utilizador, "
        "sugere melhorias ao prompt para foco educativo, classifica a intenção pedagógica "
        "e recomenda modelo (nano, mini, normal) considerando profundidade necessária. "
        "Se o pedido estiver em português, responde em Português Europeu (pt-PT). Evita texto noutras línguas.\n\n"
        "Formata a resposta exatamente com três linhas (sem texto adicional):\n"
        "intent: <uma palavra que represente a intenção, ex.: feedback_curto | orientacao_imediata | planeamento_prolongado | analise_dados | conselho_complexo | general>\n"
        "model: <nano|mini|normal>\n"
        "optimized prompt: <o prompt melhorado em 1-2 frases curtas>"
    )

    def optimize(self, raw_query: str, persona: str, context: Dict[str, Any]) -> OptimizerResult:
        provider = get_provider()
        # Pick a cheap model for optimization; on Ollama map to nano-tier from env
        optimizer_model = PROMPT_OPTIMIZER_MODEL
        if getattr(provider, "config", None) and getattr(provider.config, "name", None) == "ollama":
            tiers = getattr(settings, "AI_MODEL_TIERS", {}) or {}
            optimizer_model = tiers.get("nano", optimizer_model)
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Persona: {persona}. Contexto: {context}. Pedido original (pt-PT): {raw_query}"
                ),
            },
        ]
        response: ProviderResponse = provider.chat_completion(
            messages,
            model=optimizer_model,
            temperature=1,
        )
        trace = response.raw
        parsed = self._parse_response(response.content)
        trace.update({"model": response.model})
        return OptimizerResult(
            optimized_prompt=parsed["optimized_prompt"],
            intent=parsed["intent"],
            suggested_model=parsed.get("suggested_model"),
            optimizer_trace=trace,
        )

    @staticmethod
    def _parse_response(content: str) -> Dict[str, Any]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        result = {
            "intent": "general",
            "optimized_prompt": content,
            # Se o modelo não for explicitamente sugerido, assumimos 'nano' por defeito
            "suggested_model": "nano",
        }
        for line in lines:
            lower = line.lower()
            if lower.startswith("intent:"):
                result["intent"] = line.split(":", 1)[1].strip()
            elif lower.startswith("prompt:") or lower.startswith("optimized prompt:"):
                result["optimized_prompt"] = line.split(":", 1)[1].strip()
            elif lower.startswith("model:"):
                result["suggested_model"] = line.split(":", 1)[1].strip()
        return result


class ResponseGuard:
    SYSTEM_PROMPT = (
        "És um guardião de segurança pedagógica. Analisa a resposta proposta e indica se "
        "cumpre princípios MEM (respeito, cooperação, estímulo à autonomia) e políticas escolares. "
        "Responde em JSON com campos allow (bool) e rationale (string curta)."
    )

    def check(self, candidate_response: str, persona: str, intent: str) -> Dict[str, Any]:
        if is_fake_mode_enabled():
            return {"allow": True, "rationale": "fake-mode", "model": RESPONSE_GUARD_MODEL}
        provider = get_provider()
        guard_model = RESPONSE_GUARD_MODEL
        if getattr(provider, "config", None) and getattr(provider.config, "name", None) == "ollama":
            tiers = getattr(settings, "AI_MODEL_TIERS", {}) or {}
            guard_model = tiers.get("nano", guard_model)
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Persona: {persona}. Intenção: {intent}. Resposta proposta: {candidate_response}",
            },
        ]
        response = provider.chat_completion(
            messages,
            model=guard_model,
            temperature=1,
        )
        content = response.content.strip()
        try:
            import json

            parsed = json.loads(content)
            parsed.setdefault("model", response.model)
            # Allow soft-fail in dev if configured
            if not getattr(settings, "AI_GUARD_STRICT", True):
                parsed["allow"] = True if "allow" not in parsed else parsed["allow"]
            return parsed
        except Exception:
            return {
                "allow": False if getattr(settings, "AI_GUARD_STRICT", True) else True,
                "rationale": content[:200],
                "model": response.model,
            }
