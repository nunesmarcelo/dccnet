import textwrap

def calc_checksum (id, flag, dados = None, checksum="0000000000000000"):
    #Declaração dos Constantes

    DIVISOR_CHECKSUM = 65536 #Maior número que pode ser representado com 2 bytes (2¹⁶)
    SOF = "11001100"
    EOF = "11001101"
    pacote = SOF + id + flag
    if dados is not None: pacote += dados #Monta o pacote a ser codificado
    pacote += EOF

    #soma deve ser feita com inteiros de 16 bits,
    #é adicionado 8 bits '0's caso o pacote contenha um número impar de bytes
    if len(pacote) % 16 == 8: pacote += '00000000'
    soma = 0 #Variável auxiliar para receber a soma dos bytes no pacote
    for aux_data in textwrap.wrap(pacote,16):
        soma += int(aux_data,2)
        carry = int(soma / DIVISOR_CHECKSUM)#Verifica se existe carrys a serem somados

    soma += int(checksum,2)#chacksum é somado apos o cálculo do pacote
    return bin(((soma % DIVISOR_CHECKSUM) + carry) ^ 0xFFFF)[2:] #Retorna o complemento de 1 do pacote


print("Valor do checksum: ", calc_checksum("00000000", "01111111", None))
