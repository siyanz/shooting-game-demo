import socket

UDP_IP = socket.gethostbyname(socket.gethostname())
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

left_hand = 40003
right_hand = 40004

print "Computer ID %s" % UDP_IP


def play_FE(a):
    port = int(a[0])
    intensity = float(a[1])
    duration = float(a[2])
    frequency = float(a[3])

    ramp = 0.2 * duration
    SOA = 0.28 + duration + 60.7

    msg = ("%f %f %f %f %f %f ;\n" % (intensity, ramp, duration+ramp, frequency, SOA, duration+ramp+SOA))

    print "Port %d: FE with frequency %d Hz at intensity %f with duration %d" % (port, frequency, intensity, duration)

    sock.sendto(msg, (UDP_IP, port))

while True:
    data, addr = sock.recvfrom(512) # buffer size is 1024 bytes

    if data:
        array = data.split(';')
        play_FE(array)




