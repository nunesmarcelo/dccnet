input1 = open('grande.jpg', "rb") # Entrada de dados
input2 = open('grande2.jpg' , "rb")
j = 0
for i in range (50000):
    leitura1 = input1.read(512)
    leitura2 = input2.read(512)

    print(leitura1)
    print(leitura2)
    print(i)
    print("-" * 50)

    if not leitura1 or not leitura2:
        j+=1

    if j == 10:
        break
    