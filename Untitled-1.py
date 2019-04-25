# input1 = open('in-server.txt', "rb") # Entrada de dados
# input2 = open('out-server.txt' , "rb")
# j = 0
# for i in range (50000):
#     leitura1 = input1.read(1)
#     leitura2 = input2.read(1)

#     print(leitura1)
#     print(leitura2)
#     print(i)
#     print("-" * 50)

#     if not leitura1 or not leitura2:
#         j+=1

#     if j == 10:
#         break

from threading import Timer

def timeout():
    print("Game over")

# duration is in seconds
t = Timer(10, timeout)
t.start()
print("Veio antes")
