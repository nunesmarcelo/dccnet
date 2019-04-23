#!/usr/bin/python3

import sys , socket  , binascii , struct


class DccNET:
    def __init__(self): # Construtor
        self.esperandoACK = False
        self.terminouEnviar = False
        self.i = 0
        self.j = 0

        # ---------------- Constantes - Trabalhadas em binário ----------------------------
        self.ID_Envio = ('00') # ID de controle para envios
        self.ID_Recebimento = ('00') # ID de controle para recebimentos
        self.SOF = ('cc') # Start of Frame
        self.EOF = ('cd') # End of Frame
        self.FlagData = ('80') # Flag para controle do tipo de pacote "Dados"
        self.FlagACK = ('7f') # Flag para controle  do tipo de pacote "Confirmação"
        self.DLE = ('1b') # Usado no preenchimento de dados - ajuda a "pular" EOF's no meio de dados
        
        if(len(sys.argv) != 5): # Checa parâmetros
            print("É necessário enviar 5 parâmetros para a execução correta do programa.")
            sys.exit(0)

        self.type = sys.argv[1] # Type : -c = Cliente , -v = Servidor
        self.hostEporta = sys.argv[2] # Se servidor:  port, se cliente: host:port
        try:
            self.input = open(sys.argv[3], "rb") # Entrada de dados
            self.output = open(sys.argv[4], "wb") # Saída de dados
        except:
            print("Não foi possível abrir os arquivos de entrada/saída")
            sys.exit(0)

 
    def encode16(self, leitura): # Codifica o binario enviado em Base16
        codificado = str(hex(int.from_bytes(leitura , 'little')))[2:]
        codificado = "0" + codificado if len(codificado) == 1 else codificado
        return codificado

    def decode16(self, codificado): # Decodifica o binário codificado em Base16
        decodificado = int("0x"+codificado , 16).to_bytes( 1, 'little' )
        return decodificado

    def conectar(self):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) # Criação do socket para conexão
        if (self.type == "-c"): # Cliente se conecta, servidor é conectado
            self.conexao.connect((self.hostEporta.split(":")[0] , int(self.hostEporta.split(":")[1]))) #Conexão ao host e porta informados no prompt
            
        if (self.type == "-s"):
            self.conexao.bind(("", int(self.hostEporta))) # params da conexao: Host -> "" = Aceitar todos. Port: recebida por param.
            self.conexao.listen() # listen no cliente
            self.conn, self.addr = self.conexao.accept() # aceita a conexão
            self.conexao = self.conn # Conexão fica sendo a que for aceita (para usar mesmos comandos a partir daqui)
        
    def transmitirEreceber(self):
        while True:
            try:
                if(not self.esperandoACK and not self.terminouEnviar):
                    self.enviar()
                    #self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack('LL', 1, 0)) # configurando timeout para envio de 1s para a conexão
                    continue
                else:
                    #receber
                    try:
                        sof = bytes.decode( self.conexao.recv(2) ) 
                        if( sof != self.SOF):
                            print("Falha SOF: " + sof)
                            continue
                    except:
                        continue

                    try:
                        id = bytes.decode( self.conexao.recv(2) )
                    except:
                        continue

                    try:
                        flags = bytes.decode( self.conexao.recv(2) )
                        if(flags == self.FlagACK):
                            if( id != self.ID_Envio): # Base16 80 = ACK
                                #print("Falha ID ACK:" , id)
                                continue

                            self.esperandoACK = False #Se flags = ACK , pacote confirmado, bora para o próximo =)
                            self.ID_Envio = "01" if self.ID_Envio == "00" else "00" # Inverte o ID atual, para o id desse pacote.
                            continue
                        if(flags == self.FlagData):
                            
                            if( id != self.ID_Recebimento): # Base16 80 = ACK
                                #print("Falha ID Dados:" , id)
                                continue

                            try:
                                byteLido = bytes.decode(self.conexao.recv(2))
                            except:
                                continue

                            while( byteLido != self.EOF ):
                                if( byteLido == self.DLE ): # Se houver um byte de escape, pegue o próximo como dado
                                    byteLido = bytes.decode(self.conexao.recv(2))
                                
                                self.output.write( self.decode16( byteLido ))

                                try:
                                    #self.conexao.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 2000, 0)) # configurando timeout para envio de 1s para a conexão
                                    #self.conexao.settimeout(1)
                                    byteLido = bytes.decode( self.conexao.recv(2) )
                                #except Exception as e:
                                    #print(e)
                                except:
                                    break
                            # =========SOF==========ID=================FLAG========
                            ack = self.SOF + self.ID_Recebimento + self.FlagACK  #= Montando pacote para ACK
                            # =====================================================

                            self.conexao.send( ack.encode() ) #Envio ACK

                            self.ID_Recebimento = "01" if self.ID_Recebimento == "00" else "00" #Mudança id de recebimento, para que venha próximo pacote
                            self.j += 1 
                            print("Pct recebido: " , self.j)
                            continue
                    except:
                        #print("flag não veio, retransmitir")
                        continue
                   
                    
                    #ERRO.. NÃO VEIO DADOS NEM ACK
                    #print('Falha leitura - não veio dados nem ACK.. linha 118')

            except EOFError:
                print ("eof error - 128")
                break #EOF
            except KeyboardInterrupt:
                sys.exit(0)

    def enviar(self):
        contador = 512 #Tamanho máximo dos dados , por padrão
        byteLido = self.input.read(1) # lê os 512 bytes possíveis de um pacote
        mensagem = ""
        mensagem2 = ""
        while (contador > 0 and byteLido ):
            byteCodificado = self.encode16(byteLido)

            if byteCodificado == self.DLE or byteCodificado == self.EOF: #Byte Stuffing
                mensagem += self.DLE
                mensagem2 += self.DLE
                contador -= 1
            
            mensagem += byteCodificado
            #mensagem2 += byteCodificado + " " + str(byteLido) + "|"
            mensagem2 += byteCodificado  + "|"
            contador -= 1 
            if contador > 0:
                byteLido = self.input.read(1)

        if not byteLido: # Fim da leitura do arquivo de entrada (input)
            #self.input.close()
            self.terminouEnviar = True
            print("-" *20 + "Aqui acabou" + "-" *20)

        # =========SOF====================ID======================FLAG=========DATA========EOF==========
        empacotado = self.SOF + self.ID_Envio + self.FlagData + mensagem + self.EOF  #= Montando pacote =)
        # ==============================================================================================
        self.i += 1
        print("-" * 50)
        print("Mensagem " , self.i ," Dados: ", mensagem2  )
        print('-' * 50)
        self.conexao.sendall( empacotado.encode() ) #Codifica e envia o pacote!
        self.esperandoACK = True # Começa a esperar ACK

        return True



if __name__ == "__main__":
    dcc = DccNET()
    dcc.conectar()
    dcc.transmitirEreceber()
            
