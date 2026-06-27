# Simulador de Gerenciamento de Memória

Trabalho Prático 2 da disciplina de Sistemas Operacionais. Simula a alocação
contígua de memória usando dois esquemas:

- Particionamento variável, com política Worst-Fit ou Circular-Fit;
- Sistema Buddy, com divisão e coalescência em potências de 2.

A cada requisição lida de um arquivo, o programa mostra o estado da memória, os
blocos contíguos livres e, no caso do buddy, a fragmentação interna.

## Requisitos

Python 3.7 ou superior. Não usa bibliotecas externas.

```
python --version
```

## Estrutura

```
src/
  main.py               programa principal (menu, leitura do arquivo, saída)
  memoria_variavel.py   Worst-Fit e Circular-Fit
  memoria_buddy.py      Sistema Buddy
entradas/               arquivos de requisições de exemplo
tests/test_simulador.py testes automatizados
MANUAL.pdf   manual do usuário
```

## Como executar

Pela pasta `src`:

```
cd src
python main.py
```

O modo interativo pergunta o esquema, a política (se variável), o arquivo, o
tamanho da memória e se quer visualizar passo a passo.

Também dá para passar tudo por linha de comando:

```
python main.py --tipo variavel --politica worst --memoria 16 --arquivo ../entradas/exemplo_variavel.txt
python main.py --tipo buddy --memoria 256 --arquivo ../entradas/exemplo_buddy.txt
```

## Arquivo de requisições

Um comando por linha:

```
IN(A, 10)    aloca 10 para o processo A
OUT(A)       libera o processo A
```

O tamanho da memória pode vir como primeira linha (`256` ou `| 256 |`) ou ser
informado na execução. Linhas começando com `#` são ignoradas. Quando uma
alocação não cabe, o programa avisa `ESPAÇO INSUFICIENTE DE MEMÓRIA` e segue.

## Testes

```
python tests/test_simulador.py
```

## Mais detalhes

Ver `MANUAL.pdf`.
