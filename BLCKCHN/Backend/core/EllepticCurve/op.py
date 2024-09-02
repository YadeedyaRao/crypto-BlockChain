from BLCKCHN.Backend.util.util import hash160
from BLCKCHN.Backend.core.EllepticCurve.EllepticCurve import Sha256Point, Signature
def op_dup(stack):
    if not len(stack): 
        return False
    stack.append(stack[-1])
    return True

def op_equalVerify(stack):
    if len(stack) < 2:
        return False
    element1 = stack.pop()
    element2 = stack.pop()
    if element1 == element2:
        return True
    return False

def op_hash160(stack):
    if len(stack) < 1:
        return False
    element = stack.pop()
    stack.append(hash160(element))
    return True

def op_checkSign(stack, z):
    if len(stack) < 2 : 
        return False
    sec_pubkey = stack.pop()
    der_sign = stack.pop()[:-1] # excluding hash type

    try:
        point = Sha256Point.parse(sec_pubkey)
        sig = Signature.parse(der_sign)
    except Exception as e:
        return False
    
    if point.verify(z, sig):
        stack.append(1)
        return True
    else:
        stack.append(0)
        return False

    

OP_CODE_FUNCTIONS = {
    118 : op_dup, 
    136: op_equalVerify,
    169 : op_hash160,
    172 : op_checkSign,
    }