#!/usr/bin/python3

import base64 , sys , socket , struct, _thread


class DccNET:
    def __init__(self): # Construtor
        self.esperandoACK = False
        self.ID = 0
        self.SOF = self.encode16('0xcd') # self.decode16('0xcc') #start of frame
        self.EOF = self.encode16('0xcc') # self.decode16('0xcd') #end of frame
        self.FlagData = ('0x80')
        self.FlagACK = ('0x7f')
        
        if(len(sys.argv) != 5): # Checa parâmetros
            print("É necessário enviar 5 parâmetros para a execução correta do programa.")
            sys.exit(0)

        self.type = sys.argv[1] # Type : -c = Cliente , -v = Servidor
        self.hostEporta = sys.argv[2] # Se servidor:  port, se cliente: host:port
        try:
            self.input = open(sys.argv[3], "r") # Entrada de dados
            self.output = open(sys.argv[4], "w") # Saída de dados
        except:
            print("Não foi possível abrir o arquivo de entrada")
            sys.exit(0)

 


    def encode16(self, texto): # Codifica , usando a classe base64 , o texto enviado em Base16
        #codificado = base64.b16encode(texto.encode('utf-8'))
        codificado = texto.encode().hex()
        return codificado

    def decode16(self, codificado): # Decodifica , usando a classe base64 , o texto codificado em Base16, em string novamente.
        #decodificado = base64.b16decode(codificado)
        decodificado = bytes.fromhex(codificado)
        return bytes.decode(decodificado)

    def conectar(self):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        if (self.type == "-c"): # Cliente se conecta, servidor é conectado
            self.conexao.connect((self.hostEporta.split(":")[0] , int(self.hostEporta.split(":")[1]))) #Conexão ao host e porta informados no prompt
            self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack('LL', 10, 0)) # configurando timeout para envio de 1s para a conexão
            
        if (self.type == "-s"):
            try:
                self.conexao.bind(("", int(self.hostEporta)))      # params da conexao: Host -> "" = Aceitar todos. Port: recebida por param.
                self.conexao.listen() # listen no cliente
                self.conn, self.addr = self.conexao.accept() # aceita a conexão
                self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 10, 0)) # configurando timeout de recebimento para 1s das conexões
                
            except KeyboardInterrupt:
                self.conexao.close()
                sys.exit(0)

    def transmitir(self):
        if(not self.esperandoACK):
            mensagem = self.prepararMensagem( self.input.read(512) ) # lê os 512 bytes possíveis
            enviado = self.SOF + ("1" if self.ID == 0 else "0") + self.FlagData + mensagem + self.EOF

    #def receber(self):
        
                
    def prepararMensagem(self, mensagem):
        codificada = self.encode16(mensagem)
        for byte in mensagem:
            print(byte)
            

    def transmitirEReceber(self):
        while True:
            try:
                _thread.start_new_thread( self.transmitir() ) 
                #self.receber()
            except EOFError:
                break #EOF   
        self.input.close()
        self.output.close()

if __name__ == "__main__":
    dcc = DccNET()
    dcc.conectar()
    dcc.transmitirEReceber()
