import pytest
import app as app_module  # importa o seu app.py


def contar_agendamentos():
    """Função auxiliar para contar registros no banco."""
    conn = app_module.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM agendamentos")
    (total,) = cur.fetchone()
    conn.close()
    return total


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Cria um cliente de teste do Flask usando um banco SQLite temporário.
    """
    # Aponta o DB_NAME do app para um arquivo temporário
    test_db = tmp_path / "test_consultas.db"
    monkeypatch.setattr(app_module, "DB_NAME", str(test_db))

    # Recria o banco de testes
    app_module.init_db()

    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    return client


def test_agendamento_valido(client):
    """
    Deve permitir agendar uma consulta válida (dia útil e horário correto).
    """
    # 2025-11-17 é uma segunda-feira
    resposta = client.post(
        "/agendar",
        data={
            "nome": "Paciente Teste",
            "email": "teste@example.com",
            "telefone": "11999999999",
            "data": "2025-11-17",
            "hora": "09:00",
            "medico": "A",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"Consulta agendada com sucesso!" in resposta.data
    assert contar_agendamentos() == 1


def test_nao_permite_fim_de_semana(client):
    """
    Não deve permitir agendar consulta em fim de semana.
    """
    # 2025-11-22 é um sábado
    resposta = client.post(
        "/agendar",
        data={
            "nome": "Paciente FimSemana",
            "email": "fimsemana@example.com",
            "telefone": "11999999999",
            "data": "2025-11-22",
            "hora": "10:00",
            "medico": "B",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"Agendamentos s\xc3\xb3 podem ser feitos de segunda a sexta-feira." in resposta.data
    assert contar_agendamentos() == 0


def test_nao_permite_mesmo_medico_mesmo_dia(client):
    """
    Não deve permitir dois agendamentos para o mesmo médico no mesmo dia,
    mesmo em horários diferentes.
    """
    dados = {
        "nome": "Paciente 1",
        "email": "pac1@example.com",
        "telefone": "11999999999",
        "data": "2025-11-18",  # terça-feira
        "hora": "08:00",
        "medico": "C",
    }

    # Primeiro agendamento — deve funcionar
    resposta1 = client.post("/agendar", data=dados, follow_redirects=True)
    assert resposta1.status_code == 200
    assert b"Consulta agendada com sucesso!" in resposta1.data
    assert contar_agendamentos() == 1

    # Segundo agendamento — mesmo médico e mesma data, hora diferente
    dados2 = dados.copy()
    dados2["hora"] = "10:00"

    resposta2 = client.post("/agendar", data=dados2, follow_redirects=True)
    assert resposta2.status_code == 200
    assert b"J\xc3\xa1 existe um agendamento para esse m\xc3\xa9dico nesta data." in resposta2.data
    # Continua só com 1 agendamento
    assert contar_agendamentos() == 1
