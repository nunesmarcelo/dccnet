#!/usr/bin/python3

import base64 , sys , socket , struct


class DccNET:
    def __init__(self): # Construtor
        if(len(sys.argv) != 5): # Checa parâmetros
            print("É necessário enviar 5 parâmetros para a execução correta do programa.")
            sys.exit(0)

        self.type = sys.argv[1] # Type : -c = Cliente , -v = Servidor
        self.hostEporta = sys.argv[2] # Se servidor:  port, se cliente: host:port
        self.input = sys.argv[3] # Entrada de dados
        self.output = sys.argv[4] # Saída de dados

    def encode16(self, texto): # Codifica , usando a classe base64 , o texto enviado em Base16
        codificado = texto.encode('utf-8')
        return base64.b16encode(codificado)

    def decode16(self, codificado): # Decodifica , usando a classe base64 , o texto codificado em Base16, em string novamente.
        decodificado = base64.b16decode(codificado)
        return bytes.decode(decodificado)

    def conectar(self):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) 

        if (self.type == "-c"): # Cliente se conecta, servidor é conectado
            self.conexao.connect((self.hostEporta.split(":")[0] , self.hostEporta.split(":")[1])) #Conexão ao host e porta informados no prompt
            self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack('LL', 15, 0)) # configurando timeout para envio de 15s para a conexão

        if (self.type == "-s"):
            try:
                self.conexao.bind(("", self.hostEporta))      # params da conexao: Host -> "" = Aceitar todos. Port: recebida por param.
                self.conexao.listen() # listen no cliente
                self.conn, self.addr = self.conexao.accept() # aceita a conexão
                self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 15, 0)) # configurando timeout de recebimento para 15s das conexões

            except KeyboardInterrupt:
                self.conexao.close()
                sys.exit(0)
           
    def executar(self):
        self.conectar()

        while True:
            try:
                leitura = input()
            except:
                break #EOF
                

if __name__ == "__main__":
    dcc = DccNET()
    