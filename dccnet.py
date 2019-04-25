#!/usr/bin/python3

import sys , socket  , binascii , struct , textwrap
from threading import Timer

class DccNET:
    def __init__(self): # Construtor
        self.esperandoACK = False
        self.terminouEnviar = False
        self.i = 0
        self.pacotesRecebidos = 0

        # ---------------- Constantes - Trabalhadas já em Base16 ----------------------------
        self.ID_Envio = ('00') # ID de controle para envios
        self.ID_Recebimento = ('00') # ID de controle para recebimentos
        self.SOF = ('cc') # Start of Frame
        self.EOF = ('cd') # End of Frame
        self.FlagData = ('7f') # Flag para controle do tipo de pacote "Dados"
        self.FlagACK = ('80') # Flag para controle  do tipo de pacote "Confirmação"
        self.DLE = ('1b') # Usado no preenchimento de dados - ajuda a "pular" EOF's no meio de dados
        # ---------------------------------------------------------------------------------
        
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

    # ------------------------------------------ Codifica os bytes enviados em Base16 ------------------------------------------------------
    def encode16(self, leitura):
        codificado = str(hex(int.from_bytes(leitura , 'little')))[2:]
        codificado = "0" + codificado if len(codificado) == 1 else codificado
        return codificado

    # ------------------------------------------ Decodifica os bytes codificados em Base16 -------------------------------------------------
    def decode16(self, codificado):
        decodificado = int("0x"+codificado , 16).to_bytes( 1, 'little' )
        return decodificado

    # ------------------------------------------ Criação do socket para conexão ------------------------------------------------------------
    def conectar(self):
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        if (self.type == "-c"): # Cliente se conecta
            try:
                self.conexao.connect((self.hostEporta.split(":")[0] , int(self.hostEporta.split(":")[1]))) #Conexão ao host e porta informados no prompt
            except:
                print("-" * 20 + "Falha na conexão com o servidor " + "-" *20)
                sys.exit(1)
            
        if (self.type == "-s"): # Servidor é conectado
            try:
                self.conexao.bind(("", int(self.hostEporta))) # params da conexao: Host -> "" = Aceitar todos. Port: recebida por param.
                self.conexao.listen() # listen no cliente
                self.conn, self.addr = self.conexao.accept() # aceita a conexão
                self.conexao = self.conn # Conexão fica sendo a que for aceita (para usar mesmos comandos entre cliente/servidor a partir daqui)
            except:
                print("-" * 20 + "Falha na conexão com o cliente " + "-" * 20)

    # -------------------------------------------- Função que faz as chamadas para transmissão e recebimento ------------------------------
    def transmitirEreceber(self):
        while True:
            try:
                # --------------------------- Envio ------------------------------------
                if(not self.esperandoACK and not self.terminouEnviar): # Se livre e não terminou de enviar, envie
                    pacoteEnviado = self.enviaPacote()
                    #esperar 1s e reenviar pacoteEnviado, enquanto não receber ACK dele.
                    #self.retransmitir = Timer(1, reenviarPacote , pacoteEnviado)
                    #self.retransmitir.start()
                
                # --------------------------- Recebimento ------------------------------

                id , flags , checksum , dados  = self.recebePacote() # Recebe o pacote

                # --------------- Verifica checksum - se der erro: joga fora pacote, senão: continua recebendo ---------------------
                # print("id: " , id)
                # print("flags: " , flags)
                # print("dados: " , dados , " - tamanho: " , len(dados))
                # print("recebido: " , checksum)
                # print("Calculado: " , self.calc_checksum( id,flags, dados ))
                # print( "checksum: " , self.calc_checksum( id,flags, dados, checksum ))
                # print("-" * 50)
                if (self.calc_checksum( id,flags, dados, checksum ) != "0000") : #retorna "0" se checksum tiver correto
                    # print("pacote jogado fora!! ********************************************************************")
                    # print("id:" , id)
                    # print("flags: ",flags)
                    # print("dados: " , dados)
                    # print("checksum antes: " , checksum)
                    # print("checksum depois envio:" , self.calc_checksum( id,flags, dados ))
                    # print("Soma checksums::" , self.calc_checksum( id,flags, dados, checksum ))
                    continue # Passa para a próxima execução (receber outro pacote), se este pacote vier com falha no checksum
                
                if(flags == self.FlagACK): # Se for um ACK - pacote confirmado, bora para o próximo =)
                    if id == self.ID_Envio: # Se o ACK recebido for o do id esperado, confirme-o, senão (retransmissão de ack) , não faça nada
                        self.esperandoACK = False
                        self.ID_Envio = "01" if self.ID_Envio == "00" else "00" # Inverte o ID atual, para o id desse pacote.
                        self.imprimir("Recebido: CONFIRMAÇÃO " + str(self.i) , "recebimento")
                        #self.retransmitir.stop() # para a retransmissão
        
                if(flags == self.FlagData): # Se for um pacote de dados
                    if( id == self.ID_Recebimento): # Se o ID for o esperado, comece a receber o pacote
                        for chave in range(0 , len(dados) , 2):
                            self.output.write( self.decode16( dados[chave] + dados[chave+1] )) # Escreva a saída no arquivo de output

                    # Envia ACK - Se id == esperado atualiza id e envia ACK, senão retransmita ack para transmissor se atualizar
                    self.enviaACK(id) 

            except KeyboardInterrupt:
                self.imprimir("CTRL+C - Programa finalizado.")
                sys.exit(0)
            except socket.error:
                print("  ")
                print("             -----------------------------------")
                print("             - Conexão fechada pelo outro lado -")
                print("             -----------------------------------")
                #print(e)
                sys.exit(0)
            except Exception as e:
                print(e)
                sys.exit(0)

    # -------------------------------------------- Envio de novo pacote -------------------------------------------------------------------
    def enviaPacote(self):
        contador = 512 #Tamanho máximo dos dados , por padrão
        byteLido = self.input.read(1) # lê os 512 bytes possíveis de um pacote
        mensagem = ""
        mensagemSemDLE = "" #Usada para o cálculo do checksum
        bla = ""
        while (contador > 0 and byteLido ):
            byteCodificado = self.encode16(byteLido)

            if byteCodificado == self.DLE or byteCodificado == self.EOF: #Byte Stuffing
                mensagem += self.DLE
                contador -= 1
            
            mensagem += byteCodificado
            mensagemSemDLE += byteCodificado
            bla += byteCodificado + "|"
            contador -= 1 
            if contador > 0:
                byteLido = self.input.read(1)

        if not byteLido: # Fim da leitura do arquivo de entrada (input)
            #self.input.close()
            self.terminouEnviar = True

        # --------------- Cálculo do checksum para enviar junto do pacote ---------------------
        checksum = self.calc_checksum(self.ID_Envio , self.FlagData , mensagemSemDLE)

        if(len(checksum) > 4):
            print("Checksum len:" , len(checksum) , " - ", checksum)
            sys.exit(0)

        # print("Antes de enviar:")
        # print("id: " , self.ID_Envio)
        # print("flag: " , self.FlagData)
        # print("dados: " , bla , " - tamanho: " , len(mensagemSemDLE))
        # print("checksum calculado: ", checksum)
        # print("-" * 50)

        # --------------- Fim cálculo checksum ------------------------------------------------

        # =========SOF====================ID======================FLAG=========DATA========EOF==========
        empacotado = self.SOF + self.ID_Envio + self.FlagData + checksum + mensagem + self.EOF  #= Montando pacote =)
        # ==============================================================================================
        
        self.i += 1
        self.imprimir( ("Transmitido: PACOTE " + str(self.i)) , "envio")

        self.conexao.sendall( empacotado.encode() ) # envia o pacote!
        self.esperandoACK = True # Começa a esperar ACK

        if self.terminouEnviar:
            self.imprimir("FIM ENVIO")

        return empacotado

    # ---------------------------------- Efetua a Leitura de um pacote - para checksum, não o armazena -----------------------------------
    def recebePacote(self): 
        # Recebe o SOF do pacote a ser lido - Se recv trouxer algo que não seja um SOF, leia até chegar no próximo SOF
        sof = bytes.decode( self.conexao.recv(2) ) 
        if( sof != self.SOF):
            print("Falha SOF: " + sof)
            self.recebePacote()    

        # Recebe o ID do pacote a ser lido -  Se recv trouxer algo que não seja 00 nem 01, problema! leia próximo pacote.
        id = bytes.decode( self.conexao.recv(2) ) 
        if id != '00' and id != '01': 
            print("Falha id: " + id)
            self.recebePacote()
        
        # Recebe a Flag do pacote a ser lido - Se recv trouxer algo que não seja a FlagACK nem FlagData, problema! leia próximo pacote.
        flags = bytes.decode( self.conexao.recv(2) )
        if flags != self.FlagACK and flags != self.FlagData: 
            print("Falha flags: " + flags)
            self.recebePacote()

        # Recebe o Checksum do pacote a ser lido
        
        checksum = bytes.decode( self.conexao.recv(4))

        # Se for um pacote de confirmação, leia EOF e retorne sem dados
        if(flags == self.FlagACK): 
            # Leitura End of Frame
            eof = bytes.decode ( self.conexao.recv(2) ) 
            return id, flags , checksum , None

        # Se o flag aponta que vem dados, leia os dados
        if(flags == self.FlagData): 
            byteLido = bytes.decode(self.conexao.recv(2)) # Lê o primeiro byte de dados
            dados = "" # Variável que armazena o hexadecimal com a saída
            dadosBla = ""
            while( byteLido ): #Enquanto não chegar o fim do pacote ou o byteLido não for vazio
                if( byteLido == self.DLE ): # Se houver um byte de escape, pegue o próximo como dado
                    byteLido = bytes.decode(self.conexao.recv(2))
                    dados += byteLido #armazena os dados recebidos
                    dadosBla += byteLido + "|"
                    byteLido = bytes.decode( self.conexao.recv(2) )
                    continue

                if( byteLido == self.EOF): # Condição de parada.. quando chegar um EOF preencha ele no pacote , e pare
                    eof = byteLido
                    print("Bla: " , dadosBla)
                    break
                dados += byteLido #armazena os dados recebidos
                dadosBla += byteLido + "|"
                byteLido = bytes.decode( self.conexao.recv(2) )

            # Como a flag é de dados, após a leitura correta destes, é possível retornar o pacote completo
            return id , flags , checksum , dados


    # ---------------------------------------- Método para transmissão e retransmissão de ACK --------------------------------------------------
    def enviaACK(self, id):

        # --------------- Cálculo do checksum para enviar junto do pacote ---------------------
        checksum = self.calc_checksum(id, self.FlagACK , None)

        # =========SOF==========ID============FLAG============EOF======
        ack = self.SOF     +    id    +   self.FlagACK  + checksum +   self.EOF  #= Montando pacote para ACK
        # ==============================================================

        self.conexao.sendall( ack.encode() ) #Envio ACK

        if id == self.ID_Recebimento: # Se id recebido for igual ao esperado , mude o esperado, se não (retransmissão) não precisa mudar
            self.ID_Recebimento = "01" if self.ID_Recebimento == "00"  else "00" #Mudança id de recebimento, para que venha próximo pacote
            self.pacotesRecebidos += 1 
        
        self.imprimir( ("Recebido: PACOTE " +  str(self.pacotesRecebidos)) , "recebimento") #Imprime saída
        self.imprimir( ("Transmitido: ACK " +  str(self.pacotesRecebidos)) , "envio") #Imprime saída

    # ---------------------------------------- Método usado apenas para gerar impressão padronizada -------------------------------------------
    def imprimir(self , texto , seta = None): 
        print("  ")
        if seta == "recebimento":
            print("               " , "-".ljust( (len(texto) + 6) , '-'))
            print("    <-------    - " , texto , " -")
            print("               " , "-".ljust( (len(texto) + 6) , '-'))

        if seta == "envio":     
            print("               " , "-".ljust( (len(texto) + 6) , '-'))
            print("                - " , texto ," -  ------->")
            print("               " , "-".ljust( (len(texto) + 6) , '-'))
        
        if not seta:
            print("               " , "-".ljust( (len(texto) + 6) , '-'))
            print("                - " , texto ," -")
            print("               " , "-".ljust( (len(texto) + 6) , '-'))
    
    # ----------------------------------------- Calculo do checksum + conferência --------------------------------------------------------------
    def calc_checksum (self , id, flag, dados = None, checksum="0000"):
        #Declaração dos Constantes

        DIVISOR_CHECKSUM = 65536 #Maior número que pode ser representado com 2 bytes (2¹⁶)
        SOF = "cc"
        EOF = "cd"
        pacote = SOF + id + flag
        if dados is not None: pacote += dados #Monta o pacote a ser codificado
        pacote += EOF

        #soma deve ser feita com inteiros de 16 bits,
        #é adicionado 8 bits '0's caso o pacote contenha um número impar de bytes
        if len(pacote) % 4 == 2: pacote += '00'
        soma = 0 #Variável auxiliar para receber a soma dos bytes no pacote
        for aux_data in textwrap.wrap(pacote,4):
            soma += int(aux_data,16)
            carry = int(soma / DIVISOR_CHECKSUM)#Verifica se existe carrys a serem somados

        soma += int(checksum,16)#chacksum é somado apos o cálculo do pacote
        return hex(((soma % DIVISOR_CHECKSUM) + carry) ^ 0xFFFF)[2:].zfill(4) #Retorna o complemento de 1 do pacote
# ----------------------------------------- Fim da classe DccNET ------------------------------------------------------------------------------

if __name__ == "__main__":
    dcc = DccNET() # Instancia a classe
    dcc.conectar() # Conecta com o Cliente/Servidor remoto
    dcc.transmitirEreceber() # Inicia o processo de transmitir seus pacotes e receber pacotes do outro
            
