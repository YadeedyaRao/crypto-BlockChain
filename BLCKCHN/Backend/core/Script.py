from BLCKCHN.Backend.util.util import int_to_little_endian, encode_varint
from BLCKCHN.Backend.core.EllepticCurve.op import OP_CODE_FUNCTIONS
class Script:
    def __init__(self, cmds = None):
        if cmds is None :
            self.cmds = []
        else:
            self.cmds = cmds
    #p2pkh -> pay to public key hash

    def __add__(self, other):
        return Script(self.cmds + other.cmds)

    def serialize(self):
        result = b''
        #go through each cmd
        for cmd in self.cmds:
            #if the cmd is an integer its an opcode
            if type(cmd) == int:
                #all opcodes are less than 256 => 1 byte
                #turn thr cmd into a single byte integer using int_to_little_endian
                result += int_to_little_endian(cmd, 1)
            else:
                #otherwise its an element
                #get the length in bytes
                length = len(cmd)
                #fir large lengths, we have to use a pushdata opcode
                if length < 75:
                    #turn the length into a single byte integer
                    if length < 75:
                        #turn the length into a single byte integer
                        result += int_to_little_endian(length, 1)
                    elif length > 75 and length < 0x100:
                        # 76 is pushdata1
                        result += int_to_little_endian(76, 1)
                        result += int_to_little_endian(length, 1)
                    elif length >= 0x100 and length <= 520:
                        #77 is pushdata2
                        result += int_to_little_endian(77, 1)
                        result += int_to_little_endian(length, 1)
                    else:
                        raise ValueError('too long an cmd')   
                result += cmd
        #get the length of the whole thing
        total = len(result)
        #encode_varunt the total length of the result and prepend
        return encode_varint(total) + result

    def evaluate(self, z):
        cmds = self.cmds[:]
        stack = []

        while len(cmds) > 0:
            cmd = cmds.pop(0)

            if type(cmd) == int: # opcode
                operation = OP_CODE_FUNCTIONS[cmd]

                if cmd == 172:
                    if not operation(stack, z):
                        print("Error in signature verififcation")
                        return False
                
                elif not operation(stack):
                    print("Error in signature verififcation")
                    return False
            else:# data element
                stack.append(cmd)
        return True


    @classmethod
    def p2pkh_script(cls, h160):
        """Takes a hash160 and returns the p2pkh scriptPublickey"""
        #opcodes and elements
        return Script([0x76, 0xa9, h160, 0x88, 0xac])
    