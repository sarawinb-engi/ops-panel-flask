
def F2C(tempf):
    return (tempf - 32) * (5 / 9)

def C2F(tempc):
    return (tempc * 9 / 5) + 32

def m3h2gpm(m3h):
    return m3h * 4.4028675393

def lpers2gpm(ls):
    return ls * 15.850323141

def cTon(btuhr):
    return btuhr / 12000

def chiller(gpm, tempR, tempS):
    Btuhr = 500 * gpm * (tempR - tempS)
    return Btuhr, cTon(Btuhr)

def cooling(ls, tempR, tempS):
    Btuhr = 500 * ls * (tempR - tempS)
    return Btuhr, cTon(Btuhr)
