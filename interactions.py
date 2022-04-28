def angle(input):
    return int(40 + ((100-40) / (1024 - 1)) * (input - 1))

def drawingAngle(input):
    return int(((-40-40) / (100-40)) * (input - 40) + 40)

def doThrottle(en, in1, in2, value=0):    
    if abs(value) < 0.1:
        in1.off()
        in2.off()
        en.value = 0
    elif value < 0:
        in1.on()
        in2.off()
        en.value = abs(value)
    elif value > 0:
        in1.off()
        in2.on()
        en.value = value
        
def camAngle(leftin, rightin, leftstate, rightstate):
    if not leftstate and not rightstate:
        input = (leftin + rightin) / 2
    elif leftstate and not rightstate:
        input = rightin
    elif not leftstate and rightstate:
        input = leftin
    else:
        print("ZeroDivisionError somewhere somehow i dont even know anymore")
        raise ZeroDivisionError
    return int(40 + ((100-40) / (-90-90)) * (input - 90))