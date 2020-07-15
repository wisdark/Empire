import os
import struct

LANGUAGE = {
    'NONE' : 0,
    'POWERSHELL' : 1,
    'PYTHON' : 2
}

LANGUAGE_IDS = {}
for name, ID in list(LANGUAGE.items()): LANGUAGE_IDS[ID] = name

META = {
    'NONE' : 0,
    'STAGING_REQUEST' : 1,
    'STAGING_RESPONSE' : 2,
    'TASKING_REQUEST' : 3,
    'RESULT_POST' : 4,
    'SERVER_RESPONSE' : 5
}
META_IDS = {}
for name, ID in list(META.items()): META_IDS[ID] = name

ADDITIONAL = {}
ADDITIONAL_IDS = {}
for name, ID in list(ADDITIONAL.items()): ADDITIONAL_IDS[ID] = name

def rc4(key, data):
    """
    RC4 encrypt/decrypt the given data input with the specified key.

    From: http://stackoverflow.com/questions/29607753/how-to-decrypt-a-file-that-encrypted-with-rc4-using-python
    """
    S, j, out = list(range(256)), 0, []
    # This might break python 2.7
    key = bytearray(key)
    # KSA Phase
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    # this might also break python 2.7
    #data = bytearray(data)
    # PRGA Phase
    i = j = 0

    for char in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        if sys.version[0] == "2":
            char = ord(char)
        out.append(chr(char ^ S[(S[i] + S[j]) % 256]).encode('latin-1'))
    #out = str(out)
    tmp = b''.join(out)
    return tmp

def parse_routing_packet(stagingKey, data):
    """
    Decodes the rc4 "routing packet" and parses raw agent data into:

        {sessionID : (language, meta, additional, [encData]), ...}

    Routing packet format:

        +---------+-------------------+--------------------------+
        | RC4 IV  | RC4s(RoutingData) | AESc(client packet data) | ...
        +---------+-------------------+--------------------------+
        |    4    |         16        |        RC4 length        |
        +---------+-------------------+--------------------------+

        RC4s(RoutingData):
        +-----------+------+------+-------+--------+
        | SessionID | Lang | Meta | Extra | Length |
        +-----------+------+------+-------+--------+
        |    8      |  1   |  1   |   2   |    4   |
        +-----------+------+------+-------+--------+

    """

    if data:
        results = {}
        offset = 0

        # ensure we have at least the 20 bytes for a routing packet
        if len(data) >= 20:

            while True:

                if len(data) - offset < 20:
                    break

                RC4IV = data[0+offset:4+offset]
                RC4data = data[4+offset:20+offset]
                routingPacket = rc4(RC4IV+stagingKey.encode('UTF-8'), RC4data)

                sessionID = routingPacket[0:8].decode('UTF-8')


                # B == 1 byte unsigned char, H == 2 byte unsigned short, L == 4 byte unsigned long
                (language, meta, additional, length) = struct.unpack("=BBHL", routingPacket[8:])

                if length < 0:
                    encData = None
                else:
                    encData = data[(20+offset):(20+offset+length)]

                results[sessionID] = (LANGUAGE_IDS.get(language, 'NONE'), META_IDS.get(meta, 'NONE'), ADDITIONAL_IDS.get(additional, 'NONE'), encData)

                # check if we're at the end of the packet processing
                remainingData = data[20+offset+length:]
                if not remainingData or remainingData == '':
                    break

                offset += 20 + length
            return results

        else:
            print("[*] parse_agent_data() data length incorrect: %s" % (len(data)))
            return None

    else:
        print("[*] parse_agent_data() data is None")
        return None


def build_routing_packet(stagingKey, sessionID, meta=0, additional=0, encData=''):
    """
    Takes the specified parameters for an RC4 "routing packet" and builds/returns
    an HMAC'ed RC4 "routing packet".

    packet format:

        Routing Packet:
        +---------+-------------------+--------------------------+
        | RC4 IV  | RC4s(RoutingData) | AESc(client packet data) | ...
        +---------+-------------------+--------------------------+
        |    4    |         16        |        RC4 length        |
        +---------+-------------------+--------------------------+

        RC4s(RoutingData):
        +-----------+------+------+-------+--------+
        | SessionID | Lang | Meta | Extra | Length |
        +-----------+------+------+-------+--------+
        |    8      |  1   |  1   |   2   |    4   |
        +-----------+------+------+-------+--------+

    """

    # binary pack all of the passed config values as unsigned numbers
    #   B == 1 byte unsigned char, H == 2 byte unsigned short, L == 4 byte unsigned long
    if isinstance(sessionID, str):
        sessionID = sessionID.encode('UTF-8')

    data = sessionID + struct.pack("=BBHL", 2, meta, additional, len(encData))
    RC4IV = os.urandom(4)

    if isinstance(data, str):
        data = data.encode('UTF-8')
    if isinstance(stagingKey, str):
        stagingKey = stagingKey.encode('UTF-8')
    if isinstance(RC4IV, str):
        RC4IV = RC4IV.encode('UTF-8')
    if isinstance(encData, str):
        encData = encData.encode('UTF-8')

    key = RC4IV + stagingKey

    if isinstance(key, str):
        key = key.encode('UTF-8')

    rc4EncData = rc4(key, data)

    if isinstance(rc4EncData, str):
        rc4EncData = rc4EncData.encode('UTF-8')
    packet = RC4IV + rc4EncData + encData
    return packet