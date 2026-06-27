# Sistema Buddy: alocacao em potencias de 2 com coalescencia.


class EspacoInsuficiente(Exception):
    pass


def proxima_potencia2(n):
    if n <= 1:
        return 1
    return 1 << (n - 1).bit_length()


def eh_potencia2(n):
    return n > 0 and (n & (n - 1)) == 0


class MemoriaBuddy:
    def __init__(self, tamanho_total, bloco_minimo=1):
        if not eh_potencia2(tamanho_total):
            raise ValueError("tamanho da memoria deve ser potencia de 2")
        if not eh_potencia2(bloco_minimo):
            raise ValueError("bloco minimo deve ser potencia de 2")
        if bloco_minimo > tamanho_total:
            raise ValueError("bloco minimo nao pode exceder a memoria total")
        self.total = tamanho_total
        self.bloco_minimo = bloco_minimo
        self.ordem_max = tamanho_total.bit_length() - 1
        self.ordem_min = bloco_minimo.bit_length() - 1
        self.livres = {o: set() for o in range(self.ordem_min, self.ordem_max + 1)}
        self.livres[self.ordem_max].add(0)
        self.alocados = {}  # pid -> (offset, tamanho_bloco, tamanho_pedido)

    def alocar(self, pid, tamanho):
        if tamanho <= 0:
            raise ValueError("tamanho do processo deve ser > 0")
        if pid in self.alocados:
            raise ValueError(f"processo '{pid}' ja esta alocado")

        bloco = max(proxima_potencia2(tamanho), self.bloco_minimo)
        if bloco > self.total:
            raise EspacoInsuficiente()
        ordem = bloco.bit_length() - 1

        j = ordem
        while j <= self.ordem_max and not self.livres[j]:
            j += 1
        if j > self.ordem_max:
            raise EspacoInsuficiente()

        offset = self.livres[j].pop()
        while j > ordem:
            j -= 1
            companheiro = offset + (1 << j)
            self.livres[j].add(companheiro)

        self.alocados[pid] = (offset, bloco, tamanho)
        return True

    def liberar(self, pid):
        if pid not in self.alocados:
            raise ValueError(f"processo '{pid}' nao encontrado")
        offset, bloco, _ = self.alocados.pop(pid)
        ordem = bloco.bit_length() - 1

        while ordem < self.ordem_max:
            buddy = offset ^ (1 << ordem)
            if buddy in self.livres[ordem]:
                self.livres[ordem].discard(buddy)
                offset = min(offset, buddy)
                ordem += 1
            else:
                break
        self.livres[ordem].add(offset)
        return True

    def fragmentacao_interna(self):
        return sum(bloco - pedido for (_, bloco, pedido) in self.alocados.values())

    def _blocos_livres_ordenados(self):
        livres = []
        for ordem, offsets in self.livres.items():
            for off in offsets:
                livres.append((off, 1 << ordem))
        livres.sort()
        return livres

    def blocos_livres(self):
        return [tam for _, tam in self._blocos_livres_ordenados()]

    def livres_contiguos(self):
        regioes = []
        for off, tam in self._blocos_livres_ordenados():
            if regioes and regioes[-1][0] + regioes[-1][1] == off:
                regioes[-1] = (regioes[-1][0], regioes[-1][1] + tam)
            else:
                regioes.append((off, tam))
        return [tam for _, tam in regioes]

    def mapa(self):
        blocos = [(off, tam, pid)
                  for pid, (off, tam, _) in self.alocados.items()]
        for ordem, offsets in self.livres.items():
            for off in offsets:
                blocos.append((off, 1 << ordem, None))
        blocos.sort()
        return blocos
