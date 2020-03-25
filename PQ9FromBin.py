import sys
import struct
import math
import hashlib
import crc8

BLOCK_SIZE = 32
MD5_SIZE = 16
VERSION_SIZE = (8*2)

SERVICE_NUMBER = 18
PAYLOAD_SIZE_OFFSET = 3
ACKNOWLEDGE = 13

def setup(partials,md5,blocks,iterations,rest,bin_file):
    #rewind file
    bin_file.seek(0,0)

    #create md5 coder
    m = hashlib.md5()

    temp = 0
    for i in range(0,iterations):
        #print("Processing block nr: "+str(i)+" | ", end="")  
        temp = bin_file.read(BLOCK_SIZE)
        blocks[i] = temp
        m.update(temp)
        val = crc8.crc8()
        for q in temp:
            val.update(bytes([q]))
        crc = val.digest()
        #print(" - "+str(crc))
        partials[i] = crc

    if rest > 0:
        #print("Processing block nr: "+str(iterations)+" | ", end="")  
        temp = bin_file.read(rest)
        temp = temp + bytes((BLOCK_SIZE-rest)*[255])
        blocks[iterations] = temp
        m.update(temp)
        val = crc8.crc8()
        for q in temp:
            val.update(bytes([q]))
        crc = val.digest()
        #print(" - "+str(crc))
        partials[iterations] = crc

    md5.append(m.digest())
    #rewind file
    bin_file.seek(0,0)

if __name__ == "__main__":
    SourceFile = sys.argv[1]
    DestinationFile = SourceFile.strip('.bin') + ".pq9"
    stringData = SourceFile.split('_')
    
    VersionNumber = stringData[-2]
    SlotNumber = stringData[-1].split('.')[0]
    print("Source : "+stringData[0]+" | Version : "+VersionNumber+" | Slot : "+SlotNumber)
    fi = open(SourceFile, 'rb')
    fo = open(DestinationFile, 'wb')

    # Get binary size by going through the file
    fi.seek(0, 2)
    size = fi.tell()
    print("Size : "+str(size))
    fi.seek(0, 0)

    iterations = math.floor(size / BLOCK_SIZE)
    rest = size % BLOCK_SIZE
    if (rest > 0):
        num_blocks = iterations + 1 
    else:
        num_blocks = iterations

    print("Number of Blocks: " +str(num_blocks))

    partials = num_blocks * [0]
    datablocks = num_blocks * [0]
    md5 = []

    setup(partials,md5,datablocks,iterations,rest,fi)
    md5 = md5[0]

    #print(md5)

    #Erase Slot Command:
    fo.write(bytes(str(SERVICE_NUMBER)+" 1 8 "+SlotNumber+"\n", 'ascii'))
    fo.write(bytes(str(SERVICE_NUMBER)+" 2 8 13"+"\n", 'ascii'))

    #Start OTA
    fo.write(bytes(str(SERVICE_NUMBER)+" 1 0 "+SlotNumber+"\n", 'ascii'))

    #Send MetaData
    fo.write(bytes(str(SERVICE_NUMBER)+" 1 1 ", 'ascii'))
    for i in range(0,MD5_SIZE):
        fo.write(bytes(str(md5[i]), 'ascii'))
        fo.write(bytes(" ", 'ascii'))
    #print(VersionNumber)
    for i in range(0,8):
        a = VersionNumber[2*i:(2*i)+2]
        fo.write(bytes(str(int(a, 16)), 'ascii'))
        fo.write(bytes(str(" "), 'ascii'))

    vnum_bytes = struct.pack('>H', num_blocks)

    fo.write(bytes(str(vnum_bytes[1]), 'ascii'))
    fo.write(bytes(str(" "), 'ascii'))
    fo.write(bytes(str(vnum_bytes[0]), 'ascii'))
    fo.write(bytes(str("\n"), 'ascii'))


    #Send CRCs
    count = 0
    crcBlocks = math.floor(num_blocks/BLOCK_SIZE)
    for i in range(0,crcBlocks):
        fo.write(bytes(str(SERVICE_NUMBER)+" 1 3 ", 'ascii'))
        count_bytes = struct.pack('>H', count)

        fo.write(bytes(str(count_bytes[1]), 'ascii'))
        fo.write(bytes(str(" "), 'ascii'))
        fo.write(bytes(str(count_bytes[0]), 'ascii'))
        fo.write(bytes(str(" "), 'ascii'))

        for j in range(0,BLOCK_SIZE):
            fo.write(bytes(str((partials[BLOCK_SIZE*i+j][0] )), 'ascii'))
            fo.write(bytes(str(" "), 'ascii'))
        fo.write(bytes(str("\n"), 'ascii'))
        count +=BLOCK_SIZE

    if(num_blocks % BLOCK_SIZE > 0):
        fo.write(bytes(str(SERVICE_NUMBER)+" 1 3 ", 'ascii'))
        count_bytes = struct.pack('>H', count)

        fo.write(bytes(str(count_bytes[1]), 'ascii'))
        fo.write(bytes(str(" "), 'ascii'))
        fo.write(bytes(str(count_bytes[0]), 'ascii'))
        fo.write(bytes(str(" "), 'ascii'))

        for j in range(0,num_blocks % BLOCK_SIZE):
            fo.write(bytes(str((partials[BLOCK_SIZE*crcBlocks+j][0] )), 'ascii'))
            fo.write(bytes(str(" "), 'ascii'))
        fo.write(bytes(str("\n"), 'ascii'))
        count += num_blocks % BLOCK_SIZE

    #Send Blocks
    count = 0
    for i in range(0,num_blocks):
        fo.write(bytes(str(SERVICE_NUMBER)+" 1 5 ", 'ascii'))
        count_bytes = struct.pack('>H', count)

        fo.write(bytes(str(count_bytes[1]), 'ascii'))
        fo.write(bytes(str(" "), 'ascii'))
        fo.write(bytes(str(count_bytes[0]), 'ascii'))
        fo.write(bytes(str(" "), 'ascii'))

        for j in range(0,BLOCK_SIZE):
            #print(datablocks[i][j])
            fo.write(bytes(str((datablocks[i][j])), 'ascii'))
            fo.write(bytes(str(" "), 'ascii'))
        fo.write(bytes(str("\n"), 'ascii'))
        count += 1

    #Start OTA
    fo.write(bytes(str(SERVICE_NUMBER)+" 1 7"+"\n", 'ascii'))

    