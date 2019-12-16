
from socket import *
import asyncio
import pickle
import pymongo
from datetime import datetime

all_connections = []
all_addresses = []
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["PsMonitor"]
mycol = mydb["Agents"]


async def echo_server(address, loop):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(address)
    sock.listen(1)
    sock.setblocking(False)
    for c in all_connections:
        c.close()
    del all_connections[:]
    del all_addresses[:]
    while True:
        # client,addr=sock.accept()
        client, addr = await loop.sock_accept(sock)

        all_connections.append(client)
        all_addresses.append(address)
        print('connection from', all_addresses[0])
        loop.create_task(get_data(client, loop))

    # t=threading.Thread(Target=echo_handler,args=(client,))
    # t.start()







async def get_data(client, loop):
    while True:
        # data=client.recv(1024)
        try:
            data = await loop.sock_recv(client, 1024)
            data=pickle.loads(data)
        except:

            print('No Connection from client ',client)
        now = datetime.now()  # current date and time
        effective_date = now.strftime("%m/%d/%Y")
        effective_time=now.strftime("%H:%M:%S")

        all_agents=mycol.find({})
        if not data:
            break
        # client.sendall(b'Got :'+data)
        myquery = {"HostName": data["HostName"]}
        print(myquery)
        mydoc = mycol.find(myquery)
        mydoc = [x for x in mydoc]
        if mydoc:
            serachquery = {"HostName": data["HostName"]}
            updatequery={ "$set": { "CPU": data["CPU"],"Effective_date":effective_date,"Effective_time":effective_time ,'Enabled':'YES'} }
            x = mycol.update_one(serachquery, updatequery)
            print('updated data is ', x)

        else:
            x=mycol.insert_one(data)
            print('inserted data is ',x)
        #print('sending back '+data)
        #await loop.sock_sendall(client, b'Got :' + data.encode())
    print('connection closing for {}'.format(client))
    client.close()
    print('Connection Closed for ', client)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(echo_server(('', 25000), loop))

