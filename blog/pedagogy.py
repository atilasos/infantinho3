"""Pedagogical helpers that connect blog posts with MEM instruments."""
from django.utils.translation import gettext_lazy as _

MEM_CATEGORY_GUIDANCE = {
    'DIARIO': {
        'title': _('Diário de Turma'),
        'description': _('Sintetiza o vivido na sessão, dando voz ao secretário e à turma.'),
        'prompts': [
            _('Quais foram os momentos-chave da sessão?'),
            _('Quem assumiu responsabilidades (secretário, responsáveis de materiais, etc.) e como correu?'),
            _('Que compromissos ficaram para o próximo encontro?'),
        ],
    },
    'TEA': {
        'title': _('Trabalho de Estudo Autónomo'),
        'description': _('Regista avanços no contrato individual e dúvidas para cooperar com colegas e professor.'),
        'prompts': [
            _('Que tarefas realizaste hoje e que níveis de autonomia atingiste?'),
            _('Que dificuldades surgiram e que apoios precisas negociar?'),
            _('Que evidências (fotos, ligações, anexos) mostram o teu progresso?'),
        ],
    },
    'PROJETO': {
        'title': _('Projeto Cooperativo'),
        'description': _('Acompanha o ciclo do projeto e torna visível o contributo de cada elemento.'),
        'prompts': [
            _('Qual era o objetivo da fase de trabalho?'),
            _('Que descobertas ou produções surgiram?'),
            _('Como será partilhado o trabalho com a comunidade?'),
        ],
    },
    'CONSELHO': {
        'title': _('Conselho de Cooperação Educativa'),
        'description': _('Regista propostas, decisões e apreciações negociadas em reunião de conselho.'),
        'prompts': [
            _('Que propostas foram apresentadas e por quem?'),
            _('Que decisões foram tomadas e com que argumentos?'),
            _('Que responsabilidades foram assumidas até ao próximo conselho?'),
        ],
    },
    'TRABALHO': {
        'title': _('Partilha de Produções'),
        'description': _('Valoriza o trabalho realizado e convida à apreciação coletiva.'),
        'prompts': [
            _('Que produto ou aprendizagem queres celebrar?'),
            _('Como o realizaste e que critérios de qualidade cumpriste?'),
            _('Que feedback esperas receber da turma ou das famílias?'),
        ],
    },
    'AVISO': {
        'title': _('Aviso/Comunicação'),
        'description': _('Informa a comunidade educativa sobre acontecimentos relevantes.'),
        'prompts': [
            _('Que informação precisa chegar à turma ou às famílias?'),
            _('Que ação ou prazo está associado ao aviso?'),
            _('Há ligações ou documentos de apoio que deves anexar?'),
        ],
    },
    'REFLEXAO': {
        'title': _('Reflexão sobre a Vida da Turma'),
        'description': _('Ajuda a turma a pensar sobre relações, clima e desafios partilhados.'),
        'prompts': [
            _('Que situações ajudam a vida cooperada e merecem ser reforçadas?'),
            _('Há conflitos ou problemas a levar ao conselho?'),
            _('Que compromissos individuais ou coletivos emergem desta reflexão?'),
        ],
    },
    'OUTRO': {
        'title': _('Outro Registo Pedagógico'),
        'description': _('Utiliza esta categoria apenas quando não encontras outro instrumento adequado.'),
        'prompts': [
            _('Que objetivo pedagógico motivou este registo?'),
            _('Que ligações existem com o PIT ou listas de verificação?'),
            _('Que próximos passos queres negociar?'),
        ],
    },
}

