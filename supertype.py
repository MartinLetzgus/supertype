# -*- coding: utf-8 -*-

#Need to import this library to support array type
from array import array

# Returns the name of the object if it is supported.
# Returns an empty string else
def supported_object(obj):
    if type(obj) not in (tuple, list, array):
        return ""
    if(type(obj) == tuple):
        return "tuple"
    if(type(obj) == list):
        return "list"
    if(type(obj) == array):
        return "array"

#Function that generates the string if the object is supported
def generate_string(obj, cont):
    output = supported_object(obj)
    output += " of " 
    output += str(len(obj))
    if(len(obj) < 2):
        output += " element "
    else:
        output += " elements "
    output += "containing"
    if cont != []:
        output += " " + str(set(cont))
    else:
        output += " : "
    return output


def supertype(obj,indent=0):
    if supported_object(obj) != "":
        cont=[]
        i=0
        while (i<len(obj)) and supported_object(obj[i]) == "":
            i+=1
        if i >= len(obj):
            for j in obj:
                cont.append(supertype(j,indent+1))
        cont = generate_string(obj, cont)
        if i< len(obj):   
            for j in obj:
                cont+='\n'+'    '*(indent+1)+'-'+str(supertype(j,indent+1))            
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