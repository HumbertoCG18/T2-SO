# Simulador de gerenciamento de memoria - TP2.

import argparse
import re
import sys

from memoria_variavel import MemoriaVariavel, EspacoInsuficiente as FaltaVar
from memoria_buddy import MemoriaBuddy, EspacoInsuficiente as FaltaBuddy, eh_potencia2

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MSG_SEM_ESPACO = "ESPAÇO INSUFICIENTE DE MEMÓRIA"

_RE_IN = re.compile(r"IN\s*\(\s*([^,\s)]+)\s*,\s*(\d+)\s*\)", re.IGNORECASE)
_RE_OUT = re.compile(r"OUT\s*\(\s*([^,\s)]+)\s*\)", re.IGNORECASE)
_RE_IN2 = re.compile(r"^IN\s+([^\s,()]+)\s*,?\s*(\d+)\s*$", re.IGNORECASE)
_RE_OUT2 = re.compile(r"^OUT\s+([^\s,()]+)\s*$", re.IGNORECASE)
_RE_MEM = re.compile(r"\|?\s*(\d+)\s*\|?$")


def parse_linha(linha):
    linha = linha.strip()
    if not linha or linha.startswith("#"):
        return None
    m = _RE_IN.search(linha)
    if m:
        return ("IN", m.group(1), int(m.group(2)))
    m = _RE_OUT.search(linha)
    if m:
        return ("OUT", m.group(1), None)
    m = _RE_IN2.match(linha)
    if m:
        return ("IN", m.group(1), int(m.group(2)))
    m = _RE_OUT2.match(linha)
    if m:
        return ("OUT", m.group(1), None)
    m = _RE_MEM.fullmatch(linha)
    if m:
        return ("MEM", None, int(m.group(1)))
    return ("?", linha, None)


def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8-sig") as f:
        return f.readlines()


def detectar_memoria(linhas):
    for raw in linhas:
        ev = parse_linha(raw)
        if ev and ev[0] == "MEM":
            return ev[2]
    return None


def barra(mapa, total, largura=48):
    if total <= 0:
        return ""
    chars = []
    for pos in range(largura):
        addr = pos * total // largura
        ocupado = False
        for inicio, tam, pid in mapa:
            if inicio <= addr < inicio + tam:
                ocupado = pid is not None
                break
        chars.append("#" if ocupado else ".")
    return "[" + "".join(chars) + "]"


def fmt_segmentos(mapa):
    partes = []
    for _, tam, pid in mapa:
        partes.append(f"[{pid}:{tam}]" if pid is not None else f"({tam})")
    return "".join(partes)


def fmt_livres(blocos):
    if not blocos:
        return "| (memoria cheia) |"
    return "| " + " | ".join(str(b) for b in blocos) + " |"


def imprimir_estado(mem, eh_buddy):
    mapa = mem.mapa()
    livres = mem.livres_contiguos()
    print(f"    Mapa  : {barra(mapa, mem.total)}")
    print(f"    Segm. : {fmt_segmentos(mapa)}")
    print(f"    Livres: {fmt_livres(livres)}   "
          f"({len(livres)} bloco(s) contiguo(s) livre(s), total {sum(livres)})")
    if eh_buddy:
        buddy = mem.blocos_livres()
        print(f"    Buddy livres: {fmt_livres(buddy)}")
        print(f"    Fragmentacao interna total: {mem.fragmentacao_interna()}")


def executar(mem, linhas, eh_buddy, passo):
    FaltaEspaco = FaltaBuddy if eh_buddy else FaltaVar
    tipo = "Sistema Buddy" if eh_buddy else f"Particoes variaveis ({mem.politica}-fit)"
    print("=" * 60)
    print(f"  Esquema: {tipo}")
    print(f"  Memoria total: {mem.total}")
    if eh_buddy and mem.bloco_minimo > 1:
        print(f"  Bloco minimo: {mem.bloco_minimo}")
    print("=" * 60)
    print("\n[0] Estado inicial")
    imprimir_estado(mem, eh_buddy)

    n = 0
    for raw in linhas:
        ev = parse_linha(raw)
        if ev is None or ev[0] == "MEM":
            continue
        if ev[0] == "?":
            print(f"  [aviso] linha ignorada: {ev[1]!r}")
            continue

        n += 1
        if ev[0] == "IN":
            _, pid, tam = ev
            print(f"\n[{n}] IN({pid}, {tam})")
            try:
                mem.alocar(pid, tam)
            except FaltaEspaco:
                print(f"    >>> {MSG_SEM_ESPACO} (processo '{pid}' nao alocado)")
            except ValueError as e:
                print(f"    [aviso] {e}")
        else:
            _, pid, _ = ev
            print(f"\n[{n}] OUT({pid})")
            try:
                mem.liberar(pid)
            except ValueError as e:
                print(f"    [aviso] {e}")

        imprimir_estado(mem, eh_buddy)
        if passo:
            try:
                input("    -- Enter para o proximo passo --")
            except EOFError:
                passo = False

    print("\n" + "=" * 60)
    print("  Fim da simulacao.")
    print("=" * 60)


def pedir_inteiro(prompt, padrao=None, validar=None):
    while True:
        bruto = input(prompt).strip()
        if not bruto and padrao is not None:
            return padrao
        try:
            valor = int(bruto)
        except ValueError:
            print("    Valor invalido. Tente novamente.")
            continue
        if validar and not validar(valor):
            print("    Valor invalido. Tente novamente.")
            continue
        return valor


def menu_interativo():
    if not sys.stdin.isatty():
        print("Entrada nao interativa detectada (sem terminal).")
        print("Use o modo por linha de comando, por exemplo:")
        print("  python main.py --tipo variavel --politica worst "
              "--memoria 16 --arquivo ../entradas/exemplo_variavel.txt")
        print("  python main.py --tipo buddy --memoria 256 "
              "--arquivo ../entradas/exemplo_buddy.txt")
        return
    print("\n=== Simulador de Gerenciamento de Memoria (TP2) ===")
    print("  1) Particoes variaveis")
    print("  2) Sistema Buddy")
    opc = input("Escolha o esquema [1/2]: ").strip()
    eh_buddy = opc == "2"

    politica = "worst"
    if not eh_buddy:
        print("  1) Worst-Fit")
        print("  2) Circular-Fit")
        p = input("Escolha a politica [1/2]: ").strip()
        politica = "circular" if p == "2" else "worst"

    caminho = input("Arquivo de requisicoes: ").strip().strip('"')
    linhas = ler_arquivo(caminho)
    mem_arq = detectar_memoria(linhas)

    validar = eh_potencia2 if eh_buddy else (lambda v: v > 0)
    prompt = "Tamanho da memoria (potencia de 2)" if eh_buddy else "Tamanho da memoria"
    if mem_arq is not None:
        prompt += f" [Enter = {mem_arq} do arquivo]"
    tamanho = pedir_inteiro(prompt + ": ", padrao=mem_arq, validar=validar)
    if not eh_buddy and not eh_potencia2(tamanho):
        print(f"    [aviso] {tamanho} nao e potencia de 2 (ok para particoes variaveis).")

    bloco_min = 1
    if eh_buddy:
        bloco_min = pedir_inteiro(
            "Bloco minimo do buddy (potencia de 2) [Enter = 1]: ",
            padrao=1, validar=lambda v: eh_potencia2(v) and v <= tamanho)

    passo = input("Modo passo a passo? [s/N]: ").strip().lower().startswith("s")

    mem = (MemoriaBuddy(tamanho, bloco_min) if eh_buddy
           else MemoriaVariavel(tamanho, politica))
    executar(mem, linhas, eh_buddy, passo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", choices=["variavel", "buddy"])
    ap.add_argument("--politica", choices=["worst", "circular"], default="worst")
    ap.add_argument("--memoria", type=int)
    ap.add_argument("--bloco-min", type=int, default=1)
    ap.add_argument("--arquivo")
    ap.add_argument("--passo", action="store_true")
    args = ap.parse_args()

    if not args.tipo or not args.arquivo:
        menu_interativo()
        return

    linhas = ler_arquivo(args.arquivo)
    tamanho = args.memoria if args.memoria is not None else detectar_memoria(linhas)
    if tamanho is None:
        sys.exit("Erro: informe o tamanho da memoria com --memoria ou no arquivo.")
    if tamanho <= 0:
        sys.exit(f"Erro: tamanho da memoria ({tamanho}) deve ser positivo.")

    eh_buddy = args.tipo == "buddy"
    if eh_buddy and not eh_potencia2(tamanho):
        sys.exit(f"Erro: Sistema Buddy exige memoria potencia de 2 (recebido {tamanho}).")
    if not eh_buddy and not eh_potencia2(tamanho):
        print(f"[aviso] {tamanho} nao e potencia de 2 (ok para particoes variaveis).")
    if eh_buddy and not eh_potencia2(args.bloco_min):
        sys.exit(f"Erro: bloco minimo deve ser potencia de 2 (recebido {args.bloco_min}).")
    mem = (MemoriaBuddy(tamanho, args.bloco_min) if eh_buddy
           else MemoriaVariavel(tamanho, args.politica))
    executar(mem, linhas, eh_buddy, args.passo)


if __name__ == "__main__":
    main()
