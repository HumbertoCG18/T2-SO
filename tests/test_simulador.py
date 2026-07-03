# Testes do simulador. Executar: python tests/test_simulador.py

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from memoria_variavel import MemoriaVariavel, EspacoInsuficiente as FaltaVar
from memoria_buddy import (
    MemoriaBuddy, EspacoInsuficiente as FaltaBuddy, proxima_potencia2, eh_potencia2,
)
from main import parse_linha

_falhas = 0


def checa(nome, condicao):
    global _falhas
    status = "PASS" if condicao else "FALHOU"
    if not condicao:
        _falhas += 1
    print(f"  [{status}] {nome}")


def alocar_ok(mem, pid, tam):
    try:
        mem.alocar(pid, tam)
        return True
    except (FaltaVar, FaltaBuddy):
        return False


def teste_worst_enunciado():
    print("teste_worst_enunciado")
    m = MemoriaVariavel(16, "worst")
    seq = [
        ("IN", "A", 3, [13]),
        ("IN", "B", 2, [11]),
        ("IN", "C", 1, [10]),
        ("OUT", "A", None, [3, 10]),
        ("IN", "D", 3, [3, 7]),
        ("OUT", "B", None, [5, 7]),
        ("OUT", "C", None, [6, 7]),
        ("OUT", "D", None, [16]),
    ]
    for cmd, pid, tam, esperado in seq:
        if cmd == "IN":
            m.alocar(pid, tam)
        else:
            m.liberar(pid)
        checa(f"{cmd}({pid}) -> {esperado}", m.blocos_livres() == esperado)


def teste_circular():
    print("teste_circular")
    m = MemoriaVariavel(16, "circular")
    passos = [
        ("IN", "A", 4, [12]),
        ("IN", "B", 4, [8]),
        ("IN", "C", 4, [4]),
        ("OUT", "A", None, [4, 4]),
        ("OUT", "C", None, [4, 8]),
        ("IN", "D", 4, [8]),   # wrap: ocupa o buraco no inicio
        ("IN", "E", 4, [4]),
    ]
    for cmd, pid, tam, esperado in passos:
        if cmd == "IN":
            m.alocar(pid, tam)
        else:
            m.liberar(pid)
        checa(f"{cmd}({pid}) -> {esperado}", m.blocos_livres() == esperado)


def teste_fragmentacao_externa():
    print("teste_fragmentacao_externa")
    m = MemoriaVariavel(16, "worst")
    for pid in "ABCD":
        m.alocar(pid, 4)
    m.liberar("A")
    m.liberar("C")
    checa("livres dispersos [4,4]", m.blocos_livres() == [4, 4])
    checa("frag externa 0.5 (maior 4 de 8)", m.fragmentacao_externa() == 0.5)
    falhou = not alocar_ok(m, "E", 5)
    checa("IN(E,5) -> ESPACO INSUFICIENTE (frag. externa)", falhou)
    m.liberar("D")
    checa("frag externa 1/3 apos OUT(D)",
          abs(m.fragmentacao_externa() - 1 / 3) < 1e-9)
    m.liberar("B")
    checa("frag externa 0 com memoria toda livre", m.fragmentacao_externa() == 0.0)

    m2 = MemoriaVariavel(8, "worst")
    m2.alocar("X", 8)
    checa("frag externa 0 com memoria cheia", m2.fragmentacao_externa() == 0.0)


def teste_casos_de_erro():
    print("teste_casos_de_erro")
    m = MemoriaVariavel(8, "worst")

    m.alocar("A", 4)
    m.liberar("A")
    checa("reuso de ID apos OUT", alocar_ok(m, "A", 8))

    duplicado = False
    try:
        m.alocar("A", 1)
    except ValueError:
        duplicado = True
    checa("IN duplicado de ID ativo levanta ValueError", duplicado)

    inexistente = False
    try:
        m.liberar("Z")
    except ValueError:
        inexistente = True
    checa("OUT de ID inexistente levanta ValueError", inexistente)

    m2 = MemoriaVariavel(8, "worst")
    checa("IN > memoria -> ESPACO INSUFICIENTE", not alocar_ok(m2, "X", 9))

    m3 = MemoriaVariavel(8, "worst")
    m3.alocar("Q", 2)
    m3.liberar("Q")
    double = False
    try:
        m3.liberar("Q")
    except ValueError:
        double = True
    checa("double free levanta ValueError", double)


def teste_buddy_arredondamento():
    print("teste_buddy_arredondamento")
    casos = [(1, 1), (2, 2), (3, 4), (11, 16), (21, 32), (32, 32), (33, 64)]
    for entrada, esperado in casos:
        checa(f"proxima_potencia2({entrada}) == {esperado}",
              proxima_potencia2(entrada) == esperado)


def teste_buddy_figura():
    print("teste_buddy_figura")
    m = MemoriaBuddy(256)
    m.alocar("A", 21)
    checa("blocos buddy livres == [32,64,128]", m.blocos_livres() == [32, 64, 128])
    checa("fragmentacao interna == 11 (32-21)", m.fragmentacao_interna() == 11)
    mapa = m.mapa()
    checa("A em offset 0 com bloco 32", mapa[0] == (0, 32, "A"))


def teste_buddy_coalescencia():
    print("teste_buddy_coalescencia")
    m = MemoriaBuddy(256)
    m.alocar("A", 21)
    m.alocar("B", 60)
    m.liberar("A")
    m.liberar("B")
    checa("coalesce total -> [256]", m.blocos_livres() == [256])
    checa("frag interna volta a 0", m.fragmentacao_interna() == 0)


def teste_buddy_extremos():
    print("teste_buddy_extremos")
    m = MemoriaBuddy(4)
    m.alocar("A", 1)
    checa("buddy size 1: blocos livres [1,2]", m.blocos_livres() == [1, 2])
    checa("buddy size 1: contiguos [3]", m.livres_contiguos() == [3])

    m2 = MemoriaBuddy(8)
    m2.alocar("A", 8)
    checa("buddy size==total: sem livres", m2.blocos_livres() == [])
    checa("buddy size==total: frag 0", m2.fragmentacao_interna() == 0)
    m2.liberar("A")
    checa("buddy size==total: OUT restaura [8]", m2.blocos_livres() == [8])


def teste_buddy_fragmentacao():
    print("teste_buddy_fragmentacao")
    m = MemoriaBuddy(8)
    for pid in "ABCD":
        m.alocar(pid, 2)
    checa("buddy cheio", m.blocos_livres() == [])
    checa("IN(E,2) em buddy cheio -> insuficiente", not alocar_ok(m, "E", 2))
    m.liberar("A")
    m.liberar("C")
    checa("dois blocos 2 nao coalescem", m.blocos_livres() == [2, 2])
    checa("frag externa 0.5 (buracos em 0 e 4)", m.fragmentacao_externa() == 0.5)
    checa("IN(F,4) -> insuficiente (frag. do buddy)", not alocar_ok(m, "F", 4))
    m.liberar("B")
    checa("regiao contigua 0..6: frag externa 0", m.fragmentacao_externa() == 0.0)


def teste_potencia2():
    print("teste_potencia2")
    for n in (1, 2, 4, 8, 16, 256, 1024):
        checa(f"eh_potencia2({n})", eh_potencia2(n))
    for n in (0, 3, 6, 100, -8):
        checa(f"not eh_potencia2({n})", not eh_potencia2(n))
    erro = False
    try:
        MemoriaBuddy(100)
    except ValueError:
        erro = True
    checa("MemoriaBuddy(100) rejeitado", erro)


def teste_buddy_bloco_minimo():
    print("teste_buddy_bloco_minimo")
    m = MemoriaBuddy(64, bloco_minimo=4)
    m.alocar("A", 1)
    checa("nunca cria bloco < 4", m.blocos_livres() == [4, 8, 16, 32])
    checa("frag interna 3 (4-1)", m.fragmentacao_interna() == 3)
    m.alocar("B", 4)
    m.liberar("A")
    m.liberar("B")
    checa("coalesce total com bloco minimo", m.blocos_livres() == [64])
    rejeitado = False
    try:
        MemoriaBuddy(64, bloco_minimo=3)
    except ValueError:
        rejeitado = True
    checa("bloco minimo nao-potencia-de-2 rejeitado", rejeitado)


def teste_parser():
    print("teste_parser")
    casos = [
        ("IN(A, 10)", ("IN", "A", 10)),
        ("in( a ,3)", ("IN", "a", 3)),
        ("IN A 10", ("IN", "A", 10)),
        ("IN A, 10", ("IN", "A", 10)),
        ("OUT(B)", ("OUT", "B", None)),
        ("out b", ("OUT", "b", None)),
        ("| 256 |", ("MEM", None, 256)),
        ("128", ("MEM", None, 128)),
        ("# comentario", None),
        ("", None),
        ("lixo qualquer", ("?", "lixo qualquer", None)),
    ]
    for entrada, esperado in casos:
        checa(f"parse_linha({entrada!r}) == {esperado}",
              parse_linha(entrada) == esperado)


def main():
    testes = [
        teste_worst_enunciado,
        teste_circular,
        teste_fragmentacao_externa,
        teste_casos_de_erro,
        teste_buddy_arredondamento,
        teste_buddy_figura,
        teste_buddy_coalescencia,
        teste_buddy_extremos,
        teste_buddy_fragmentacao,
        teste_potencia2,
        teste_buddy_bloco_minimo,
        teste_parser,
    ]
    for t in testes:
        t()
        print()
    if _falhas:
        print(f"==> {_falhas} verificacao(oes) FALHARAM")
        sys.exit(1)
    print("==> Todos os testes passaram.")
    sys.exit(0)


if __name__ == "__main__":
    main()
