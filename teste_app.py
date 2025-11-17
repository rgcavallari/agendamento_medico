# teste_app.py

import pytest
from datetime import date
import app as agendamento_app 
from app import app, init_db

@pytest.fixture
def setup_module(module):
    """Configuração inicial para os testes."""
    # Garante que o banco e a tabela existem antes de testar
    init_db()
    app.config["TESTING"] = True


def test_pagina_agendar_carrega():
    """Verifica se a página /agendar responde com status 200."""
    client = app.test_client()
    resp = client.get("/agendar")
    assert resp.status_code == 200
    assert b"Agendamento" in resp.data or b"Novo agendamento" in resp.data


def test_pagina_agendamentos_carrega():
    """Verifica se a página de agendamentos responde com status 200."""
    client = app.test_client()
    resp = client.get("/lista")
    assert resp.status_code == 200


def client(tmp_path):
    """
    Cria um app de teste com um banco SQLite isolado para cada execução.
    """
    # Usa um banco de testes em vez do consultas.db "real"
    test_db = tmp_path / "test_consultas.db"
    agendamento_app.DB_NAME = str(test_db)

    # Inicializa o banco de dados de teste
    agendamento_app.init_db()

    agendamento_app.app.config["TESTING"] = True

    with agendamento_app.app.test_client() as client:
        yield client


def test_agendamento_valido(client):
    """
    Deve permitir agendar uma consulta em dia útil, horário válido,
    para um médico específico.
    """
    dados = {
        "nome": "Paciente Teste",
        "email": "paciente@teste.com",
        "telefone": "11999999999",
        "data": "2025-03-03",   # Segunda-feira
        "hora": "10:00",
        "medico": "A",
    }

    resp = client.post("/agendar", data=dados, follow_redirects=True)

    # Verifica se a mensagem de sucesso apareceu
    assert b"Consulta agendada com sucesso!" in resp.data

    # Verifica se está listando o agendamento na página de agendamentos
    resp_lista = client.get("/lista")
    assert b"Paciente Teste" in resp_lista.data
    assert b"2025-03-03" in resp_lista.data
    assert b"10:00" in resp_lista.data
    assert b"M\xc3\xa9dico A" in resp_lista.data  # "Médico A" em UTF-8


def test_nao_permite_mesmo_medico_mesmo_dia(client):
    """
    Não deve permitir dois agendamentos para o mesmo médico no mesmo dia.
    """
    dados1 = {
        "nome": "Paciente 1",
        "email": "p1@teste.com",
        "telefone": "11111111",
        "data": "2025-03-03",  # Segunda-feira
        "hora": "09:00",
        "medico": "B",
    }
    dados2 = {
        "nome": "Paciente 2",
        "email": "p2@teste.com",
        "telefone": "22222222",
        "data": "2025-03-03",  # mesmo dia
        "hora": "11:00",       # outro horário, mas mesmo médico
        "medico": "B",
    }

    # Primeiro agendamento deve funcionar
    resp1 = client.post("/agendar", data=dados1, follow_redirects=True)
    assert b"Consulta agendada com sucesso!" in resp1.data

    # Segundo deve falhar por conflito de médico+dIA (regra UNIQUE)
    resp2 = client.post("/agendar", data=dados2, follow_redirects=True)
    assert b"Ja existe um agendamento para esse m" in resp2.data or \
           b"J\xc3\xa1 existe um agendamento para esse m" in resp2.data  # trata acento


def test_nao_permite_fim_de_semana(client):
    """
    Não deve permitir agendamentos aos sábados ou domingos.
    """
    dados = {
        "nome": "Paciente Fim de Semana",
        "email": "wek@teste.com",
        "telefone": "33333333",
        "data": "2025-03-01",  # 2025-03-01 é sábado
        "hora": "10:00",
        "medico": "C",
    }

    resp = client.post("/agendar", data=dados, follow_redirects=True)

    assert b"Agendamentos s\xc3\xb3 podem ser feitos de segunda a sexta-feira." in resp.data


def test_nao_permite_horario_invalido(client):
    """
    Não deve permitir horários fora da faixa 08:00–16:00 (início).
    """
    dados = {
        "nome": "Paciente Hora Invalida",
        "email": "hora@teste.com",
        "telefone": "44444444",
        "data": "2025-03-03",  # segunda-feira
        "hora": "07:00",       # fora da faixa
        "medico": "A",
    }

    resp = client.post("/agendar", data=dados, follow_redirects=True)

    assert b"Hor\xc3\xa1rios permitidos: in\xc3\xadcio entre 08:00 e 16:00, de 1 em 1 hora." in resp.data

