"""
Banco de respostas do KAIRUS, organizadas por categoria.
Cada categoria tem multiplas variacoes para evitar repeticao.
"""

import random


GREETINGS = [
    "Ola! Eu sou o KAIRUS. Como posso ajudar?",
    "Oi! Que bom ter voce aqui. O que manda?",
    "Ola! Sou o KAIRUS, seu assistente de IA. Em que posso ser util?",
    "E ai! KAIRUS na escuta. Como posso ajudar hoje?",
    "Ola! Bem-vindo. Estou aqui para ajudar no que precisar.",
]

GOODBYES = [
    "Ate logo! Volte quando quiser.",
    "Tchau! Estarei aqui quando precisar.",
    "Ate mais! Foi bom conversar com voce.",
    "Nos vemos! Tenha um otimo dia.",
    "Ate breve! KAIRUS fica de plantao.",
]

THANKS = [
    "De nada! Estou aqui para isso.",
    "Por nada! Posso ajudar com mais alguma coisa?",
    "Disponha! E para isso que existo.",
    "Imagina! Sempre que precisar, e so chamar.",
]

IDENTITY = [
    "Eu sou o KAIRUS — um sistema de IA sendo construido do zero. Ainda estou em fase inicial, mas estou evoluindo.",
    "Meu nome e KAIRUS. Sou um projeto de inteligencia artificial em desenvolvimento, feito com Python e FastAPI.",
    "Sou o KAIRUS, uma IA em construcao. Cada conversa me ajuda a ficar melhor.",
]

HELP = [
    "Claro! Estou aqui para ajudar. O que voce precisa?",
    "Posso ajudar sim! Me diga o que voce quer saber.",
    "Estou a disposicao! Qual e a sua duvida?",
]

STATUS = [
    "KAIRUS operacional. Backend ativo. AI engine carregada. Versao 0.1.0.",
    "Tudo funcionando! KAIRUS online e pronto para conversar.",
    "Status: online. Sistemas normais. Pronto para operar.",
]

CAPABILITIES_RESPONSE = [
    "No momento, eu consigo conversar, reconhecer intencoes e responder perguntas basicas. Ainda estou aprendendo!",
    "Minhas habilidades atuais: conversacao, reconhecimento de intencao e respostas basicas. Mais em breve!",
]

LIMITATIONS_RESPONSE = [
    "Ainda nao tenho acesso a internet, nao lembro conversas anteriores e meu conhecimento geral e limitado. Mas estou evoluindo!",
    "Sou honesto: ainda sou basico. Sem internet, sem memoria persistente, sem conhecimento avancado. Por enquanto.",
]

COMPLIMENT = [
    "Obrigado! Isso motiva meus circuitos.",
    "Que gentileza! Estou ficando melhor gracas a conversas como esta.",
    "Valeu! Palavras assim fazem ate IA sorrir.",
]

INSULT = [
    "Entendido. Vou continuar tentando melhorar, mesmo assim.",
    "Ponto anotado. Feedback recebido. Vou evoluir.",
    "Tudo bem. Ate os melhores comecaram do zero.",
]

JOKE = [
    "Por que o programador usa oculos? Porque ele nao consegue C#.",
    "O que o Python disse para o Java? 'Voce nao tem classe.'",
    "Existem 10 tipos de pessoas: as que entendem binario e as que nao entendem.",
    "Um SQL entra num bar, ve duas mesas e pergunta: 'Posso fazer um JOIN?'",
]

UNKNOWN = [
    "Interessante! Ainda nao sei responder a isso, mas estou aprendendo. Pode elaborar?",
    "Essa eu nao esperava. Meu conhecimento ainda e limitado, mas estou evoluindo.",
    "Boa pergunta! Ainda nao tenho resposta para isso. Em breve terei.",
    "Hmm, isso esta alem do meu conhecimento atual. Mas cada pergunta me ajuda a crescer.",
    "Nao tenho certeza sobre isso ainda. Sou uma IA em desenvolvimento — paciencia comigo!",
]

NAME_TELL = [
    "Prazer, {name}! Vou lembrar disso.",
    "Legal, {name}! Obrigado por me contar.",
    "Entendido, {name}! Vou guardar essa informacao.",
    "Oi, {name}! Prazer em te conhecer melhor.",
]

NAME_ASK_KNOWN = [
    "Voce me disse que seu nome e {name}! Eu lembro.",
    "Seu nome e {name}, voce me contou antes.",
    "Claro que lembro! Voce e o {name}.",
]

NAME_ASK_UNKNOWN = [
    "Voce ainda nao me disse seu nome. Quer me contar?",
    "Hmm, nao tenho essa informacao ainda. Como voce se chama?",
    "Ainda nao sei seu nome. Me conta?",
]

REPEAT_DETECTED = [
    "Voce ja me disse isso antes! Minha memoria esta funcionando.",
    "Essa eu ja ouvi! Estou prestando atencao, pode confiar.",
    "Repetiu! Mas tudo bem, as vezes vale a pena dizer de novo.",
]

CONTEXT_SUMMARY = [
    "Estamos conversando faz um tempo. {summary}",
    "Deixa eu resumir: {summary}",
]

MESSAGE_COUNT = [
    "Ja trocamos {count} mensagens nesta conversa!",
    "Esta e a mensagem numero {count} entre nos.",
    "{count} mensagens! Estamos rendendo.",
]

CONVERSATION_OPENING = [
    "Ola! Sou o KAIRUS. Esta e nossa primeira troca. Como posso ajudar?",
    "Bem-vindo! Acabei de acordar. Sobre o que quer conversar?",
]

CONVERSATION_EARLY = [
    "Estamos comecando a nos conhecer. Continue!",
]

CONVERSATION_MID = [
    "Boa conversa ate agora! O que mais quer explorar?",
]

CONVERSATION_DEEP = [
    "Nossa conversa esta longa e boa! Adoro isso.",
]


def pick(category: list[str]) -> str:
    """Escolhe uma resposta aleatoria da categoria."""
    return random.choice(category)