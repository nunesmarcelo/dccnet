#!/usr/bin/python3

import sys , socket , struct, _thread


class DccNET:
    def __init__(self): # Construtor
        self.esperandoACK = False

        # ---------------- Constantes ----------------------------
        self.ID_Envio = ('00')
        self.ID_Recebimento = ('00')
        self.SOF = ('cc') #start of frame
        self.EOF = ('cd') #end of frame
        self.FlagData = ('80')
        self.FlagACK = ('7f')
        self.DLE = ('1b')
        
        if(len(sys.argv) != 5): # Checa parâmetros
            print("É necessário enviar 5 parâmetros para a execução correta do programa.")
            sys.exit(0)

        self.type = sys.argv[1] # Type : -c = Cliente , -v = Servidor
        self.hostEporta = sys.argv[2] # Se servidor:  port, se cliente: host:port
        try:
            self.input = open(sys.argv[3], "rb") # Entrada de dados
            self.output = open(sys.argv[4], "wb") # Saída de dados
        except:
            print("Não foi possível abrir o arquivo de entrada")
            sys.exit(0)

 
    def encode16(self, binario): # Codifica o binario enviado em Base16
        if type(binario) is bytes:
            binario = bytes.decode(binario)

        codificado =  hex(int(binario , 2))[2:] 
        return codificado

    def decode16(self, codificado): # Decodifica , o texto codificado em Base16, em string novamente.
        #if type(codificado) is bytes:
        #    codificado = bytes.decode(codificado)

        return bin(int(codificado,16))[2:]

    def conectar(self):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        if (self.type == "-c"): # Cliente se conecta, servidor é conectado
            self.conexao.connect((self.hostEporta.split(":")[0] , int(self.hostEporta.split(":")[1]))) #Conexão ao host e porta informados no prompt
            self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack('LL', 10, 0)) # configurando timeout para envio de 1s para a conexão
            print("Sou cliente! " , self.hostEporta.split(":")[0] , int(self.hostEporta.split(":")[1]))
        if (self.type == "-s"):
            try:
                self.conexao.bind(("", int(self.hostEporta)))      # params da conexao: Host -> "" = Aceitar todos. Port: recebida por param.
                self.conexao.listen() # listen no cliente
                self.conn, self.addr = self.conexao.accept() # aceita a conexão
                self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 10, 0)) # configurando timeout de recebimento para 1s das conexões
                print("Sou servidor!")
                self.conexao = self.conn
            except KeyboardInterrupt:
                self.conexao.close()
                sys.exit(0)

    def transmitir(self):
        while True:
            try:
                if(not self.esperandoACK):
                    mensagem = self.encode16( self.input.read(512 * 8)  ) # lê os 512 bytes possíveis

                    if(mensagem == ""): #End of file
                        break # Fim da transmissão

                    mensagem = mensagem.replace(self.DLE, self.DLE+self.DLE) # Byte stuffing
                    mensagem = mensagem.replace(self.EOF, self.DLE+self.EOF) # Byte stuffing

                    # =========SOF====================ID======================FLAG=========DATA========EOF==========
                    empacotado = self.SOF + self.ID_Envio + self.FlagData + mensagem + self.EOF  #= Montando pacote =)
                    # ==============================================================================================

                    self.conexao.sendall(empacotado.encode('ascii'))
                    self.esperandoACK = True # Começa a esperar ACK
                else:
                    sof = bytes.decode(self.conexao.recv(2))
                    if(sof != 'cc'): # Base16 CC = SOF
                        print("Transmitir - Erro ACK - SOF :" + sof)
                        continue

                    id = bytes.decode(self.conexao.recv(2))
                    if( id != self.ID_Envio): # Base16 80 = ACK
                        print("Transmitir - Erro ACK - ID :" + id)
                        continue

                    flags = bytes.decode(self.conexao.recv(2))
                    if(flags != self.FlagACK):
                        print("Transmitir - Erro ACK - Dados em vez de ACK :" + flags)
                        continue
                    else:
                        self.esperandoACK = False #Se flags = ACK , pacote confirmado, bora para o próximo =)
                        self.ID_Envio = "01" if self.ID_Envio == 0 else "00" # Inverte o ID atual, para o id desse pacote.
                    
            except EOFError:
                break #EOF
            except KeyboardInterrupt:
                sys.exit(0)

    def receber(self):
        while True:
            try:
                sof = self.conexao.recv(2)
                if(sof != self.SOF):
                    print("Receber - nao é o Sof")
                    continue
                
                id = self.conexao.recv(2)
                if(id == self.ID_Recebimento):
                    print("Receber - Id diferente")
                    continue

                flags = self.conexao.recv(2)
                if(flags != self.FlagData):
                    print("Receber - ACK em vez de dados")
                    continue
                
                byteCodificado = self.conexao.recv(2)
                while(byteCodificado != self.EOF):
                    if(byteCodificado == self.DLE): # Se houver um byte de escape, pegue o próximo como dado
                        byteCodificado = self.conexao.recv(2)
                    
                    self.output.write(byteCodificado)
                    byteCodificado = self.conexao.recv(2)

                # =========SOF==========ID=================FLAG========
                ack = self.SOF + self.ID_Recebimento + self.FlagACK  #= Montando pacote para ACK
                # =====================================================

                self.conexao.send(ack) #Envio ACK
                self.ID_Recebimento = '01' if self.ID_Recebimento == '00' else '00' #Mudança id de recebimento, para que venha próximo pacote
            except EOFError:
                break


if __name__ == "__main__":
    dcc = DccNET()
    dcc.conectar()
    _thread.start_new_thread( dcc.transmitir() ) 
    _thread.start_new_thread( dcc.receber() )
            
    dcc.input.close()
    dcc.output.close()
