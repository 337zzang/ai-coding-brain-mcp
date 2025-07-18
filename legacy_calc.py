def calc(x,y,op):
    if op=='+':
        return x+y
    elif op=='-':
        return x-y
    elif op=='*':
        return x*y
    elif op=='/':
        if y!=0:
            return x/y
        else:
            return None
    else:
        return None
