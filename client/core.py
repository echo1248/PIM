# -*- coding: utf-8 -*-
# File   @ core.py
# Create @ 2019/3/1 15:22
# Author @ 819070918@qq.com

import socket


def send(client, data):
    server = ("127.0.0.1", 8000)
    client.sendto(data, server)


def recv(client):
    return client.recv(1024)


def main():

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send(client, "hello pim!")
    recv(client)


if __name__ == '__main__':
    main()
