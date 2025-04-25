import os
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infantinho3.settings')
    django.setup()
    from checklists.models import ChecklistTemplate, ChecklistItem

    nome = 'Português 5.º ano'
    ano = '5.º ano'
    disciplina = 'Português'
    descricao = 'Aprendizagens essenciais da disciplina de português 5.º ano.'

    objetivos = [
        # ORALIDADE – Compreensão
        'ORALIDADE – Compreensão: Selecionar informação relevante em função dos objetivos de escuta e registá-la por meio de técnicas diversas.',
        'ORALIDADE – Compreensão: Organizar a informação do texto e registá-la, por meio de técnicas diversas.',
        'ORALIDADE – Compreensão: Controlar a produção discursiva a partir do feedback dos interlocutores.',
        # ORALIDADE – Expressão
        'ORALIDADE – Expressão: Preparar apresentações orais (exposição, reconto, tomada de posição) individualmente ou após discussão de diferentes pontos de vista.',
        'ORALIDADE – Expressão: Planificar e produzir textos orais com diferentes finalidades.',
        'ORALIDADE – Expressão: Intervir, com dúvidas e questões, em interações com diversos graus de formalidade, com respeito por regras de uso da palavra.',
        'ORALIDADE – Expressão: Captar e manter a atenção da audiência (postura corporal, expressão facial, clareza, volume e tom de voz).',
        'ORALIDADE – Expressão: Produzir um discurso com elementos de coesão adequados (concordância; tempos verbais; advérbios; variação das anáforas; uso de conectores frásicos e textuais mais frequentes).',
        # LEITURA
        'LEITURA: Ler textos com características narrativas e expositivas, associados a finalidades lúdicas, estéticas e informativas.',
        'LEITURA: Realizar leitura em voz alta, silenciosa e autónoma.',
        'LEITURA: Explicitar o sentido global de um texto.',
        'LEITURA: Fazer inferências, justificando-as.',
        'LEITURA: Identificar tema(s), ideias principais e pontos de vista.',
        'LEITURA: Reconhecer a forma como o texto está estruturado (partes e subpartes).',
        'LEITURA: Compreender a utilização de recursos expressivos para a construção de sentido do texto.',
        'LEITURA: Utilizar procedimentos de registo e tratamento de informação.',
        'LEITURA: Analisar textos em função do género textual a que pertencem (estruturação e finalidade): verbete de enciclopédia, entrevista, anúncio publicitário, notícia e carta formal (em diversos suportes).',
        # EDUCAÇÃO LITERÁRIA
        'EDUCAÇÃO LITERÁRIA: Ler integralmente textos literários de natureza narrativa, lírica e dramática (no mínimo, um livro infantojuvenil, quatro poemas, duas lendas, três contos de autor e um texto dramático – selecionados da literatura para a infância, de adaptações de clássicos e da tradição popular).',
        'EDUCAÇÃO LITERÁRIA: Interpretar o texto em função do género literário.',
        'EDUCAÇÃO LITERÁRIA: Inferir o sentido conotativo de palavras e expressões.',
        'EDUCAÇÃO LITERÁRIA: Reconhecer a estrutura e os elementos constitutivos do texto narrativo: personagens, narrador, contexto temporal e espacial, ação.',
        'EDUCAÇÃO LITERÁRIA: Explicar recursos expressivos utilizados na construção dos textos literários (designadamente personificação, comparação).',
        'EDUCAÇÃO LITERÁRIA: Analisar o modo como os temas, as experiências e os valores são representados nas obras lidas e compará-lo com outras manifestações artísticas (música, pintura, escultura, cinema, etc.).',
        'EDUCAÇÃO LITERÁRIA: Valorizar a diversidade cultural patente nos textos.',
        'EDUCAÇÃO LITERÁRIA: Fazer declamações e representações teatrais.',
        'EDUCAÇÃO LITERÁRIA: Desenvolver um projeto de leitura que integre explicitação de objetivos de leitura pessoais e comparação de temas comuns em livros, em géneros e em manifestações artísticas diferentes (obras escolhidas em contrato de leitura com o(a) professor(a)).',
        # ESCRITA
        'ESCRITA: Descrever pessoas, objetos e paisagens em função de diferentes finalidades e géneros textuais.',
        'ESCRITA: Planificar a escrita por meio do registo de ideias e da sua hierarquização.',
        'ESCRITA: Escrever textos organizados em parágrafos, de acordo com o género textual que convém à finalidade comunicativa.',
        'ESCRITA: Escrever com respeito pelas regras de ortografia e de pontuação.',
        'ESCRITA: Aperfeiçoar o texto depois de redigido.',
        'ESCRITA: Escrever textos de natureza narrativa integrando os elementos que circunscrevem o acontecimento, o tempo e o lugar, o desencadear da ação, o desenvolvimento e a conclusão, com recurso a vários conectores de tempo, de causa, de explicação e de contraste.',
        'ESCRITA: Escrever textos em que se defenda uma posição com argumentos e conclusão coerentes, individualmente ou após discussão de diferentes pontos de vista.',
        # GRAMÁTICA
        'GRAMÁTICA: Identificar a classe das palavras: verbo principal (transitivo e intransitivo) e verbo auxiliar, advérbio, conjunção.',
        'GRAMÁTICA: Conjugar verbos regulares e irregulares no pretérito mais-que-perfeito (simples e composto) do modo indicativo.',
        'GRAMÁTICA: Identificar o particípio passado e o gerúndio dos verbos.',
        'GRAMÁTICA: Sistematizar processos de formação do feminino dos nomes e adjetivos.',
        'GRAMÁTICA: Sistematizar a flexão nominal e adjetival quanto ao número.',
        'GRAMÁTICA: Identificar os constituintes da frase com as seguintes funções sintáticas: sujeito (simples e composto), vocativo, predicado; complemento (direto e indireto).',
        'GRAMÁTICA: Distinguir frases simples de frases complexas.',
        'GRAMÁTICA: Empregar, de modo intencional e adequado, conectores com valor de tempo, de causa, de explicação e de contraste.',
        'GRAMÁTICA: Analisar palavras a partir dos seus elementos constitutivos (base, radical e afixos), com diversas finalidades (deduzir significados, integrar na classe gramatical, formar famílias de palavras).',
        'GRAMÁTICA: Compreender a composição como processo de formação de palavras.',
        'GRAMÁTICA: Explicitar regras de utilização dos sinais de pontuação.',
        'GRAMÁTICA: Mobilizar formas de tratamento mais usuais no relacionamento interpessoal, em diversos contextos de formalidade.'
    ]

    template, created = ChecklistTemplate.objects.get_or_create(
        nome=nome, ano=ano, disciplina=disciplina,
        defaults={'descricao': descricao}
    )
    if not created:
        print('Template já existe. Abortando para evitar duplicação.')
        return

    for ordem, objetivo in enumerate(objetivos, 1):
        ChecklistItem.objects.create(
            template=template,
            descricao=objetivo,
            criterios='',
            ordem=ordem,
            contratualizado_em_conselho=False
        )
    print(f"ChecklistTemplate e {len(objetivos)} ChecklistItems criados com sucesso!")

if __name__ == '__main__':
    main() 