import os
import sys
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, init_db
from datetime import date

# Atenção: DB_NAME é variável global em app.py
import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Cria um cliente de teste do Flask usando um banco de dados temporário
    para cada teste.
    """
    test_db = tmp_path / "test_consultas.db"

    # Redireciona o app para usar outro arquivo de banco de dados
    monkeypatch.setattr(app_module, "DB_NAME", str(test_db))

    # Inicializa as tabelas no banco de teste
    init_db()

    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_agendamento_valido(client):
    """
    Deve permitir agendar uma consulta válida:
    - dia útil
    - horário entre 08:00 e 16:00
    - médico A/B/C
    """
    # Segunda-feira fixa (2025-06-02 é uma segunda)
    data_str = "2025-06-02"

    resp = client.post(
        "/agendar",
        data={
            "nome": "Paciente Teste",
            "email": "teste@example.com",
            "telefone": "11999999999",
            "data": data_str,
            "hora": "10:00",
            "medico": "A",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Consulta agendada com sucesso!" in resp.data


def test_nao_permite_mesmo_medico_mesmo_dia(client):
    """
    Não deve permitir dois agendamentos com o MESMO médico
    na MESMA data.
    """
    data_str = "2025-06-02"  # segunda-feira

    # Primeiro agendamento
    resp1 = client.post(
        "/agendar",
        data={
            "nome": "Paciente 1",
            "email": "p1@example.com",
            "telefone": "111111111",
            "data": data_str,
            "hora": "09:00",
            "medico": "B",
        },
        follow_redirects=True,
    )
    assert b"Consulta agendada com sucesso!" in resp1.data

    # Segundo agendamento com o mesmo médico e mesma data
    resp2 = client.post(
        "/agendar",
        data={
            "nome": "Paciente 2",
            "email": "p2@example.com",
            "telefone": "222222222",
            "data": data_str,
            "hora": "11:00",  # pode ser outra hora, a regra é só por dia
            "medico": "B",
        },
        follow_redirects=True,
    )

    assert resp2.status_code == 200
    assert b"Ja existe um agendamento para esse medico nesta data." in resp2.data or \
           b"Já existe um agendamento para esse médico nesta data." in resp2.data


def test_nao_permite_fim_de_semana(client):
    """
    Não deve permitir agendamento em sábado ou domingo.
    """
    # 2025-06-01 é domingo
    data_domingo = "2025-06-01"

    resp = client.post(
        "/agendar",
        data={
            "nome": "Paciente Fim de Semana",
            "email": "fds@example.com",
            "telefone": "333333333",
            "data": data_domingo,
            "hora": "09:00",
            "medico": "C",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Agendamentos so podem ser feitos de segunda a sexta-feira." in resp.data or \
           b"Agendamentos s\xc3\xb3 podem ser feitos de segunda a sexta-feira." in resp.data


def test_nao_permite_horario_invalido(client):
    """
    Não deve permitir agendamento fora dos horários:
    início entre 08:00 e 16:00, de 1 em 1 hora.
    """
    data_str = "2025-06-02"  # segunda-feira

    # Horário inválido: 07:00
    resp = client.post(
        "/agendar",
        data={
            "nome": "Paciente Hora Invalida",
            "email": "hora@example.com",
            "telefone": "444444444",
            "data": data_str,
            "hora": "07:00",
            "medico": "A",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Horarios permitidos" in resp.data or \
           b"Hor\u00e1rios permitidos" in resp.data
