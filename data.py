"""Dados fictícios para o Support Inbox Triage Desk."""

CUSTOMERS = {
    "ana.silva@example.pt": {
        "name": "Ana Silva", "plan": "Pro", "monthly_price": 29.90,
        "invoices": [
            {"id": "F-1041", "date": "2026-08-01", "amount": 29.90, "status": "paga"},
            {"id": "F-1088", "date": "2026-09-01", "amount": 59.80, "status": "paga"},
            {"id": "F-1130", "date": "2026-10-01", "amount": 29.90, "status": "em atraso"},
        ],
    },
    "bruno.costa@example.pt": {
        "name": "Bruno Costa", "plan": "Business", "monthly_price": 89.00,
        "invoices": [
            {"id": "F-2001", "date": "2026-08-01", "amount": 89.00, "status": "paga"},
            {"id": "F-2044", "date": "2026-09-01", "amount": 89.00, "status": "paga"},
            {"id": "F-2090", "date": "2026-10-01", "amount": 89.00, "status": "paga"},
        ],
    },
    "carla.mendes@example.pt": {
        "name": "Carla Mendes", "plan": "Pro", "monthly_price": 29.90,
        "invoices": [
            {"id": "F-3010", "date": "2026-09-01", "amount": 29.90, "status": "paga"},
            {"id": "F-3011", "date": "2026-09-01", "amount": 29.90, "status": "paga"},
            {"id": "F-3050", "date": "2026-10-01", "amount": 29.90, "status": "paga"},
        ],
    },
    "diogo.pires@example.pt": {
        "name": "Diogo Pires", "plan": "Pro", "monthly_price": 34.90,
        "invoices": [
            {"id": "F-4005", "date": "2026-08-01", "amount": 29.90, "status": "paga"},
            {"id": "F-4061", "date": "2026-09-01", "amount": 34.90, "status": "paga"},
            {"id": "F-4120", "date": "2026-10-01", "amount": 34.90, "status": "paga"},
        ],
    },
    "elisa.rocha@example.pt": {
        "name": "Elisa Rocha", "plan": "Basic", "monthly_price": 9.90,
        "invoices": [
            {"id": "F-5002", "date": "2026-09-01", "amount": 9.90, "status": "paga"},
            {"id": "F-5077", "date": "2026-10-01", "amount": 9.90, "status": "em atraso"},
        ],
    },
    "fabio.santos@example.pt": {
        "name": "Fábio Santos", "plan": "Basic", "monthly_price": 9.90,
        "invoices": [
            {"id": "F-6003", "date": "2026-08-01", "amount": 9.90, "status": "paga"},
            {"id": "F-6040", "date": "2026-09-01", "amount": 9.90, "status": "paga"},
            {"id": "F-6099", "date": "2026-10-01", "amount": 9.90, "status": "paga"},
        ],
    },
}

FAQ = """\
FAQ DE SUPORTE TÉCNICO (única fonte válida)

1. Repor palavra-passe: no ecrã de login, escolher "Esqueci-me da palavra-passe". O email
   chega em 5 minutos; verificar a pasta de spam. Se não chegar, confirmar que o email
   usado é o do registo.
2. A app fecha ao fazer login (telemóvel): atualizar para a versão 3.2 ou superior, limpar a
   cache da app e reiniciar o telemóvel.
3. Exportar dados para CSV: Definições > Dados > Exportar > CSV. O botão só funciona
   depois de selecionar pelo menos um projeto na lista.
4. Autenticação em dois fatores (2FA): Definições > Segurança > Ativar 2FA e ler o QR code
   com uma app de autenticação.
5. Sincronização lenta: verificar a ligação à internet, terminar sessão e voltar a entrar em
   ambos os dispositivos. Em caso de lentidão persistente, aguardar até 24 horas.
"""

# expected: etiqueta correta (os meus labels); amb=True se podia ir para dois especialistas.
MESSAGES = [
    (1, "ana.silva@example.pt", "Boa tarde, fui cobrada 59,80€ em setembro mas o meu plano custa 29,90€. Podem explicar?", "billing", 2, False),
    (2, "bruno.costa@example.pt", "Não consigo repor a minha palavra-passe, o email nunca chega.", "technical", 2, False),
    (3, "carla.mendes@example.pt", "Isto é inaceitável! Esperei 3 semanas por uma resposta e ninguém me ajuda.", "complaint", 3, False),
    (4, "diogo.pires@example.pt", "Qual é o valor da minha última fatura?", "billing", 1, False),
    (5, "elisa.rocha@example.pt", "A app fecha sozinha quando tento fazer login no telemóvel.", "technical", 2, False),
    (6, "ana.silva@example.pt", "Quero cancelar a subscrição, o serviço é péssimo e ainda por cima cobram-me a mais.", "complaint", 2, True),
    (7, "fabio.santos@example.pt", "Como exporto os meus dados para CSV?", "technical", 1, False),
    (8, "bruno.costa@example.pt", "O webhook da vossa API deixou de enviar eventos e a minha produção está parada!", "technical", 3, False),
    (9, "carla.mendes@example.pt", "Paguei duas vezes em setembro e o suporte nunca me respondeu. Estou farta.", "billing", 2, True),
    (10, "diogo.pires@example.pt", "Obrigado pelo atendimento de ontem. Só uma dúvida: como ativo a autenticação em dois fatores?", "technical", 1, False),
    (11, "elisa.rocha@example.pt", "A minha fatura de outubro está em atraso, mas não consegui pagar porque o login falha.", "technical", 2, True),
    (12, "fabio.santos@example.pt", "Vou apresentar queixa no livro de reclamações, cobraram-me um serviço que nunca pedi.", "complaint", 3, False),
    (13, "ana.silva@example.pt", "Podem enviar-me a fatura de agosto em PDF?", "billing", 1, False),
    (14, "bruno.costa@example.pt", "A sincronização entre telemóvel e computador está lenta desde ontem.", "technical", 1, False),
    (15, "carla.mendes@example.pt", "O vosso colega foi mal-educado comigo ao telefone.", "complaint", 2, False),
    (16, "diogo.pires@example.pt", "Porque é que o meu plano subiu de preço?", "billing", 2, False),
    (17, "elisa.rocha@example.pt", "Não consigo ligar o SSO da empresa à vossa plataforma.", "technical", 2, False),
    (18, "fabio.santos@example.pt", "É a terceira vez que a app perde as minhas alterações. Estou a pensar mudar de fornecedor.", "complaint", 2, True),
    (19, "ana.silva@example.pt", "Bom dia! Só queria confirmar que a fatura de outubro é de 29,90€.", "billing", 1, False),
    (20, "bruno.costa@example.pt", "URGENTE: cobrança indevida de 300€ no meu cartão, quero o dinheiro de volta hoje!", "billing", 3, False),
    (21, "carla.mendes@example.pt", "O botão de exportar não faz nada.", "technical", 1, False),
    (22, "diogo.pires@example.pt", "Estou muito desiludido com o serviço, esperava mais pelo preço que pago.", "complaint", 2, False),
    (23, "elisa.rocha@example.pt", "Preciso de uma declaração com o total faturado este ano.", "billing", 1, False),
    (24, "fabio.santos@example.pt", "A minha conta mostra um saldo estranho e a app dá erro quando abro a fatura.", "billing", 2, True),
]
