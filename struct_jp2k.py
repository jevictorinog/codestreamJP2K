import time   # measuring the time process
import sys    # To read arguments from system command line

def int4(code, i):
    return code[i]*2**24 + code[i+1]*2**16 + code[i+2]*2**8 + code[i+3]

def int2(code, i):
    return code[i]*2**8 + code[i+1]

def wint2(arr, position, number):
    arr[position] = (number >> 8) & 0xFF
    arr[position + 1] = number & 0xFF

def wint4(arr, position, number):
    arr[position + 0] = (number >> 24) & 0xFF
    arr[position + 1] = (number >> 16) & 0xFF
    arr[position + 2] = (number >> 8)  & 0xFF
    arr[position + 3] = number & 0xFF

SOC =  79;   SIZ =  81;   COD =  82;   QCD =  92;   QCC =  93;
COC =  83;   RGN =  94;   POC =  95;   CRG =  99;   COM = 100;
TLM =  85;   PLM =  87;   PLT =  88;   PPM =  96;   PPT =  97;
SOT = 144;   SOP = 145;   EPH = 146;   SOD = 147;   EOC = 217;

progression = {0:'LRCP', 1:'RLCP', 2:'RPCL', 3:'PCRL', 4:'CPRL'}
qstyle      = {0:'exp', 1:'scalar_derived', 2:'scalar_expounded'}

marks = [SOC, SIZ, COD, QCD, QCC, COC, RGN, POC, CRG, COM, TLM, PLM, PLT, PPM, PPT, SOT, SOP, EPH, SOD, EOC]

# B02C7986 código único de asesoría de protección s.a.

if len(sys.argv) < 2:
    filename = input('Ingrese el nombre del archivo jp2: ')
else :
    filename = sys.argv[1]
if filename == '':  filename = '083_078_2021_he.jp2'

imfile   = open(filename, 'rb')
code     = imfile.read(100000)

imfile.close()
print('byte stream size: {:,}'.format(len(code)))

# parse SIZ segment   0x51   d_81
def parseSizeJP2K(code, j):
    lsiz  = int2(code, j+0)    # lsiz: size segment
    rsiz  = int2(code, j+2)    # rsiz: segment capabilities (0 usualy)
    xsiz  = int4(code, j+4)    # xsiz: image width
    ysiz  = int4(code, j+8)    # ysiz: image height
    x0siz = int4(code, j+12)   # xsiz: image horizontal origin
    y0siz = int4(code, j+16)   # ysiz: image vertical origin
    xTsiz = int4(code, j+20)   # xsiz: image tile width
    yTsiz = int4(code, j+24)   # ysiz: image tile height
    xosiz = int4(code, j+28)   # xsiz: image horizontal offset
    yosiz = int4(code, j+32)   # ysiz: image vertical offset
    csiz  = int2(code, j+36)   # csiz: number of components
    ntiles = ((xsiz - xosiz + xTsiz - 1) // xTsiz) * ((ysiz - yosiz + yTsiz - 1) // yTsiz)
    print('[%6d]'%j, 'SIZ')
    print(f'\t  segment_length:    {lsiz}')
    print(f'\t  image dimensions:  {xsiz}x{ysiz}')
    print(f'\t  Tile dimensions:   {xTsiz}x{yTsiz}')
    print(f'\t  Offset image:      {xosiz}x{yosiz}')
    print(f'\t  num of components: {csiz}')
    print(f'\t  num of Tiles:      {ntiles}')
    return lsiz, xTsiz, yTsiz

# parse COD segment  0x52   d_82
def parseCodeJP2K(code, xt, yt, j):
    lcod  = int2(code, j)      # lcod: segment size
    scod  = code[j+2]          # scod: code style defaults: flags for ROI and precinct matrix
    prog  = code[j+3]          # prog: progression order: 0:LRCP, 1:RLCP, 2:RPCL, 3:PCRL, 4:CPRL
    lays  = int2(code, j+4)    # lays: number of quality layers
    mctb  = code[j+6]          # mctb: multiple component trasnformation byte:  RGB to YCbCr
    levs  = code[j+7]          # levs: Number of decomposition levels, resolutions
    cbwd  = code[j+8]          # code block width dimensions in log2 factor
    cbht  = code[j+9]          # code block height dimensions in log2 factor
    cbs   = code[j+10]         # code block style parameters
    wavl  = code[j+11]         # wavelet trasnfomation type:  0:9-7, 32:5-3
    cur   = levs
    res_info = []
    for i in range(levs+1):
        precsz = code[j+12+i]  # precinct size in log2 factor
        resW   = int(xt / (2**cur))
        resH   = int(yt / (2**cur))
        precW  = 2**(precsz & 15)
        precH  = 2**((precsz & 240) >> 4)
        nPrecX = resW // precW if resW // precW >= 1 else 1
        nPrecY = resH // precH if resH // precH >= 1 else 1
        res_info.append([precsz, resH, resW, precH, precW, nPrecX, nPrecY])
        cur -= 1
    print('[%6d]'%j, 'COD')
    print(f'\t  segment length:    {lcod}')
    print(f'\t  style code:        {scod}')
    print(f'\t  progression:       {prog}:{progression[prog]}')
    print(f'\t  num of layers:     {lays}')
    print(f'\t  num of resolutions:{levs}')
    for pr in res_info:
        print('\t\t Code prec:', format(pr[0], '02X'), '  \tres:', '%4d'%pr[1], '%4d'%pr[2], ' \tsize:', '%4d'%pr[3], '%4d'%pr[4], '\tnprec:', '%2d'%pr[5], '%2d'%pr[6])
    print(f'\t  code_block_size:   {2**cbwd}x{2**cbht}')
    print(f'\t  wavelet_type:      {wavl}')
    print(f'\t  color_transform:   {mctb}')
    return lcod

# parse QCD segment  0x5C   d_92
def parseQcdJP2K(code, res, j):
    lqcd  = int2(code, j)      # lcod: segment size
    sqcd  = code[j+2]          # sqcd: quantization style: bits{7-5} 0:exp, 1:scalar_derived, 2:scalar_expounded; and bits{4-0} step precision
    st    = (sqcd & 0xE0) >> 5
    prcs  = sqcd % 0x1F
    qcode = bytearray(code[j+3:j+lqcd])
    styl  = (sqcd & 0xE0) >> 5
    print('[%6d]'%j, 'QCD')
    print(f'\t  segment len:{lqcd}, quant style:{qstyle[st]}, precision:{prcs}')
    print('\t  code: ',  ' '.join(format(q, '02X') for q in qcode))
    return lqcd

# parse QCC segment  0x5D  d_93
def parseQccJP2K(code, res, j):
    lqcc  = int2(code, j)      # lqcc: segment size
    cqcc  = code[j+2]          # cqcc: number of component quantization
    sqcc  = code[j+3]          # sqcc: quantization style: bits{7-5} 0:exp, 1:scalar_derived, 2:scalar_expounded; and bits{4-0} step precision
    st    = (sqcc & 0xE0) >> 5
    prcs  = sqcc % 0x1F
    qcode = bytearray(code[j+4:j+lqcc])
    print('[%6d]'%j, 'QCC')
    print(f'\t  segment len:{lqcc}, component:{cqcc}, quant_style:{qstyle[st]}, precision:{prcs}')
    print('\t  code: ',  ' '.join(format(q, '02X') for q in qcode))
    return lqcc

# parse SOT segment  0x90  d_144
def parseSotJP2K(code, j):
    lsot  = int2(code, j)      # lsot: segment size
    isot  = int2(code, j+2)    # isot: tile index number
    psot  = int4(code, j+4)    # psot: total tile length
    tpsot = code[j+8]          # tpsot: index of first tile part
    ntsot = code[j+9]          # ntsot: number of tile parts

    print('[%6d]'%j, f'SOT len:{lsot}, ndx:{isot}, Total_Tile_length:', '{:,}'.format(psot))
    #for i in range(j+10, j+psot):
    #    if code[i] == 0xFF and code[i+1] in marks[10:15]:
    #        print(i,'\t', ' '.join(format(q, '02X') for q in code[i:i+30]))

    return lsot

# parse SOT segment  0x90  d_144
def parseSotAllJP2K(code, j):
    while j < len(code):
        if code[j-2] == 0xFF and code[j-1] == SOT:    ## SOT: Tile segment
            lsot  = int2(code, j)                     # lsot: segment size
            isot  = int2(code, j+2)                   # isot: tile index number
            psot  = int4(code, j+4)                   # psot: total tile length
            tpsot = code[j+8]                         # tpsot: index of first tile part
            ntsot = code[j+9]                         # ntsot: number of tile parts
            if j>100000000 and isot<120:
                print('[%6d]'%j, f'SOT len:{lsot}, ndx:{isot}, \tTotal_Tile_length:', '{:,}'.format(psot))
            aSot.append(j)
            j = j + lsot
        else:
            j = j + 1
    return len(aSot)

def countSopSegments(code, j):
    sop_cnt = 0
    while j < len(code):
        if code[j] == 0xFF and code[j+1] == SOP:    ## SOP: Code block segment
            nsop = int2(code, j+4)
            if sop_cnt != nsop: print('problem SOP count', nsop, sop_cnt)
            sop_cnt += 1
        if code[j] == 0xFF and (code[j+1] == SOT or code[j+1] == EOC): break
        j = j +1
    print('Pakets count =', sop_cnt)

# Documentation in: https://www.sciencedirect.com/topics/computer-science/jpeg2000
# parse TLM segment (tile part length in the main header) 0x55  d_85
def parseTlmJP2K(code, j):
    ltlm  = int2(code, j+0)    # ltlm: size segment
    ztlm  = code[j+2]          # ztlm: index relative to other TLM marker segments in the header
    stlm  = code[j+3]          # stlm: size of ttlm and ptlm parameters
    lim   = j+ltlm
    print('[%6d]'%j, f'TLM\n\t  segment len:{ltlm}, ndx:{ztlm}, size reg:{stlm} end pointer: {lim}')
    pntr  = lim
    while j < lim:
        if stlm == 0x60:
            ttlm  = int2(code, j+4)   # ttlm: tile number of i-th tile part
            ptlm  = int4(code, j+6)   # ptlm: length in bytes from beginning of SOT marker to end of data for the i-th tile-part
            if ttlm >540 and ttlm<550: print(f'\t\t  {j}\tTile N°: {ttlm}\tlength: {ptlm}, pos: {pntr}\t', ' '.join(format(q, '02X') for q in code[pntr:pntr+24]))
            ncode = bytearray(code[pntr:(pntr+ptlm+2)])
            f2 = open('tiles_cut/t%04d.dat'%ttlm, 'wb')
            f2.write(ncode)
            f2.close()
            pntr += ptlm
            j += 6
    return ltlm

# parse PLM segment (packet length in main header) 0x57 d_87
def parsePlmJP2K(code, j):
    lplm  = int2(code, j+0)    # lplm: size segment
    zplm  = code[j+2]          # zplm: index relative to other PLM marker segments in the header
    nplm  = code[j+3]          # nplm: number of bytes of iplm information for i-th tile part
    iplm  = code[j+4]          # iplm: length the j-th packet in the i-th tile part

# parse PLT segment (packet length in tile header) 0x58  d_88
def parsePltJP2K(code, j):
    lplt  = int2(code, j+0)    # lplt: size segment
    zplt  = code[j+2]          # zplt: index relative to other PLT marker segments in the header
    iplt  = code[j+4]          # iplt: length the i-th packet

# parse PPM segment (packet header in main header) 0x60  d_96
def parsePpmJP2K(code, j):
    lppm  = int2(code, j+0)    # lppm: size segment
    zppm  = code[j+2]          # zppm: index relative to other PPM marker segments in the header
    nppm  = int4(code, j+3)    # nppm: number of bytes of ippm information for i-th tile part, one value for each tile part
    ippm  = code[j+7]          # ippm: Packet header for every packet in order in the tile-part. The component number, layer and resolution determined from method of progression or POD. One value for each packet in the tile-part

# parse PPT segment  (packet header in tile part) 0x61  d_97
def parsePptJP2K(code, j):
    lppt  = int2(code, j+0)    # lppt: size segment
    zppt  = code[j+2]          # zppt: index relative to other PPM marker segments in the header
    ippt  = code[j+3]          # ippt: Packet header for every packet in order in the tile-part. The component number, layer and resolution determined from method of progression or POD. One value for each packet in the tile-part


# parse COM segment 0x64  d_100
def parseComJP2K(code, j):
    lcom  = int2(code, j)      # lcom: segment size
    rcom  = int2(code, j+2)    # rcom: type of comment 0:general use,  1:binary data
    cad = code[j+4:j+lcom]
    print('[%6d]'%j, f'COM len:{lcom}, type:{rcom}, \ttext:"{cad.decode("utf-8")}"')
    return lcom

def textcode(code, ini, end):
    for i in range(ini, end):
        if code[i] > 31 and code[i] < 129:
            print(chr(code[i]), end='')
        elif code[i] == 10: print()
        elif code[i] ==  9: print('\t', end='')
        elif code[i] <  32: pass
        else: print('!%d'%code[i], end='')
    print()

def transHeader(code):
    pass

def imageRequest(code, x1, y1, res, lay, precROI):
    ALL = -1
    comp = ALL
    c1 = True if code == ALL else False
    c2 = True if lay  == ALL else False
    c3 = True if res  == ALL else False
    c4 = True if comp == ALL else False
    dx, numPrecX = 0, 0
    missing = []
    packs = []

    imgInfo = code
    resolutions = res+1
    layers = lay+1
    tiles = 0
    components = 2
    lstPcks = []
    if x1 > 0 or y1 > 0 :
        pass
        #coord2Prec(x1, y1, res)

    num = 0
    numTiles = imgInfo.tx * imgInfo.ty
    numRes = imgInfo.numLev + 1

    for t in range(numTiles):
        for l in range(imgInfo.numLay):
            for r in range(numRes):
                for c in range(imgInfo.numCmp):
                    numPrec = imgInfo.numPrecX[r] * imgInfo.numPrecY[r]
                    for p in range(numPrec):
                        if (t <= tiles or c1) and (l <= layers or c2) and (r <= resolutions or c3) and (c <= components or c4):
                            lgral = (t // imgInfo.tx) * imgInfo.numPrecX[r] + p // imgInfo.numPrecX[r]
                            cgral = (t % imgInfo.tx) * imgInfo.numPrecX[r] + p % imgInfo.numPrecX[r]
                            pg = imgInfo.numPrecX[r] * imgInfo.tx * lgral + cgral
                            if pg >= precROI[r].tl and pg <= precROI[r].br:
                                numPrecX = imgInfo.numPrecX[r] * imgInfo.tx
                                dx = precROI[r].tr - precROI[r].tl
                                startLine = precROI[r].tl + (pg - precROI[r].tl) // numPrecX * numPrecX
                                if pg >= startLine and pg <= startLine + dx:
                                    packs.append(num)
                                    if lstPcks[num] is None:
                                        missing.append(num)
                        num += 1

    mpacks = [missing[i] for i in range(len(missing))]

    return mpacks
# parse JP2K image file
j = 0
aSot = []
while j < len(code):
    if code[j] == 0xFF and code[j+1] == SOC:    ##  start codestream
        print('[%6d]'%j, 'SOC')
        init = j
        j += 1
    elif code[j] == 0xFF and code[j+1] == SIZ:  ##  size params
        k, xt, yt =  parseSizeJP2K(code, j+2)
        j += k+1
    elif code[j] == 0xFF and code[j+1] == COD:  ##  code params
        j += parseCodeJP2K(code, xt, yt, j+2) + 1
    elif code[j] == 0xFF and code[j+1] == QCD:  ##  quantization params
        j += parseQcdJP2K(code, 4, j+2) + 1
        ended = j
    elif code[j] == 0xFF and code[j+1] == QCC:  ##  component quantization params
        j += parseQccJP2K(code, 4, j+2) + 1
        ended = j
    elif code[j] == 0xFF and code[j+1] == COM:  ##  Comment segment
        j += parseComJP2K(code, j+2) + 1
    elif code[j] == 0xFF and code[j+1] == TLM:  ##  Tile-part lenght in main header
        j += parseTlmJP2K(code, j+2) + 1
    elif code[j] == 0xFF and code[j+1] == SOT:  ##  Tile segment start
        print('---Tile segments---')
        parseSotJP2K(code, j+2)
        break
    j += 1

print(len(aSot), aSot)
print('Main header:', init, ended)
main_header = bytearray(code[init:ended])

#print('Tile %2d'%i, end='\t')
#countSopSegments(code, aSot[0])

#parseSotAllJP2K(code,10290)
#textcode(code, 0, 1473)


#for i in range(5):
#    h = i*60 + 1473
#    print(' '.join(format(q, '02X') for q in code[h:h+60]))
#print('--'*20)
#for i in range(5):
#    h = i*60 + 0
#    print(' '.join(format(q, '02X') for q in ncode[h:h+60]))
#
#print(' '.join(format(q, '02X') for q in ncode[-20:]))
