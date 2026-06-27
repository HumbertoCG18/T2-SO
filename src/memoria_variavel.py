# Particionamento variavel: politicas Worst-Fit e Circular-Fit.


class EspacoInsuficiente(Exception):
    pass


class Segmento:
    __slots__ = ("inicio", "tamanho", "pid")

    def __init__(self, inicio, tamanho, pid=None):
        self.inicio = inicio
        self.tamanho = tamanho
        self.pid = pid  # None = livre

    @property
    def livre(self):
        return self.pid is None


class MemoriaVariavel:
    POLITICAS = ("worst", "circular")

    def __init__(self, tamanho_total, politica="worst"):
        if politica not in self.POLITICAS:
            raise ValueError("politica deve ser 'worst' ou 'circular'")
        if tamanho_total <= 0:
            raise ValueError("tamanho da memoria deve ser positivo")
        self.total = tamanho_total
        self.politica = politica
        self.segmentos = [Segmento(0, tamanho_total, None)]
        self.cursor = 0  # usado pelo circular-fit

    def alocar(self, pid, tamanho):
        if tamanho <= 0:
            raise ValueError("tamanho do processo deve ser > 0")
        if any(s.pid == pid for s in self.segmentos):
            raise ValueError(f"processo '{pid}' ja esta alocado")

        idx = self._escolher(tamanho)
        if idx is None:
            raise EspacoInsuficiente()

        seg = self.segmentos[idx]
        if seg.tamanho == tamanho:
            seg.pid = pid
        else:
            ocupado = Segmento(seg.inicio, tamanho, pid)
            seg.inicio += tamanho
            seg.tamanho -= tamanho
            self.segmentos.insert(idx, ocupado)

        self.cursor = self.segmentos[idx].inicio + tamanho
        return True

    def _escolher(self, tamanho):
        livres = [i for i, s in enumerate(self.segmentos)
                  if s.livre and s.tamanho >= tamanho]
        if not livres:
            return None

        if self.politica == "worst":
            return max(
                livres,
                key=lambda i: (self.segmentos[i].tamanho, -self.segmentos[i].inicio),
            )

        # circular: primeiro bloco que cabe a partir do cursor
        for i in livres:
            if self.segmentos[i].inicio >= self.cursor:
                return i
        return livres[0]

    def liberar(self, pid):
        for s in self.segmentos:
            if s.pid == pid:
                s.pid = None
                self._coalescer()
                return True
        raise ValueError(f"processo '{pid}' nao encontrado")

    def _coalescer(self):
        novos = []
        for s in self.segmentos:
            if novos and novos[-1].livre and s.livre:
                novos[-1].tamanho += s.tamanho
            else:
                novos.append(s)
        self.segmentos = novos

    def mapa(self):
        return [(s.inicio, s.tamanho, s.pid) for s in self.segmentos]

    def blocos_livres(self):
        return [s.tamanho for s in self.segmentos if s.livre]

    livres_contiguos = blocos_livres
