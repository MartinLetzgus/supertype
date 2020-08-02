# -*- coding: utf-8 -*-

  

#Fonction qui p
def generate_string(strType, obj, last = False, cont = []):
    output = strType
    output += " of " 
    output += str(len(obj))
    if(len(obj) < 2):
        output += " element "
    else:
        output += " elements "
    output += "containing"
    if last:
        output += " " + str(set(cont))
    else:
        output += " : "
    return output


def supertype(obj,indent=0):
    if type(obj)==list or type(obj)==tuple:
        cont=[]
        i=0
        while (i<len(obj)) and (type(obj[i])!=tuple) and (type(obj[i])!=list):
            i+=1
        if i<len(obj):
            if type(obj)==list:
                cont = generate_parent_string("list", obj)
            else:
                cont = generate_parent_string("tuple", obj)
            for i in obj:
                cont+='\n'+'    '*(indent+1)+'-'+str(supertype(i,indent+1))
        else:
            for i in obj:
                cont.append(supertype(i,indent+1))
            c = set(cont)
            if type(obj)==list:
                cont = generate_parent_string("list", obj, True, cont)
            else:
                cont = generate_parent_string("tuple", obj, True, cont)               
        if(indent==0):
            print(cont)
        else:
            return(cont)
#         elif type(obj)==numpy.ndarray:
#             return('numpy array of shape '+str(obj.shape))
#         #If we want to add specific info about some types (as shape of nunmpy array) we can add elif right here
    else:
        try:
            cont = (str(type(obj))[8:-2]+' of shape '+str(obj.shape))
        except:
            try:
                cont = (str(type(obj))[8:-2]+' of '+str(len(obj))+' element')
                if len(obj)>1:
                    cont+='s'
            except:
                cont = (str(type(obj))[8:-2])
        if(indent==0):
            print(cont)
        else:
            return(cont)
        #The [8:-2] allows us to make "<class 'str'>" into "str"