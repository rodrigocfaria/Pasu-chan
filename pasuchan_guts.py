from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol import KDF
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
import os
import json
from copy import deepcopy
from bisect import insort_right
#from sortedcollection import SortedCollection
from random import choice

# class IncrementalSearch(mp.Process):

#     def __init__(self, q_get = None, q_put = None):

#         mp.Process.__init__(self)

#         if q_get != None and q_put != None:
#                 self.q_put = q_put
#                 self.q_get = q_get
#                 self.search = SearchTools()
#                 self.database = Database()

#         else:
#             raise Exception('You should put both queues.')

#     def run(self):

#         while 1:

#             try:
#                 search_parameters = self.q_get.get()

#             except queue.Empty:
#                 pass

#             else:
#                 input_text = search_parameters['search_term']
#                 search_by = search_parameters['search_by']
#                 data = self.database.database_read()
#                 sorted_data = self.database.sort_dict(data, search_by)
#                 search_gen = self.search.binary_search_gen(sorted_data, input_text, search_by)

#                 for i in search_gen:
#                     self.q_put.put(i)   

def binary_search_gen(dict_to_be_searched, search_term, key):
    ''''dict_to_be_sorted' must be, well, a dict. 'key' is the key to search in dict. Remember:
    this method returns a fucking generator. Use it in the right way.'''

    if len(dict_to_be_searched) == 0:
        yield 'SEARCH_NOT_FOUND'

    else:
        indexes = search_bisect(dict_to_be_searched, search_term, key)

        if indexes == None:
            yield 'SEARCH_NOT_FOUND'

        else:
            for i in range(indexes[0], indexes[1] + 1):
                yield dict_to_be_searched[i]    

#Modified from python examples in their docs.
def search_bisect(dict_to_be_searched, term, key, low = 0, high = None):
    '''This method returns the indexes of first match and last match inside a ORDERED dict. Anything
    between them, inclusive them, is a match for the term searched.'''

    if low < 0:
        raise ValueError('low must be non-negative')
    if high == None:
        high = len(dict_to_be_searched) - 1
    
    length = len(dict_to_be_searched)
    term = term.lower()

    while low < high:
        mid = (low + high) // 2
        if term <= dict_to_be_searched[mid][key].lower():
            high = mid
        else:
            low = mid + 1
    
    if dict_to_be_searched[low][key].lower().startswith(term) == True: 
        first_match = low
    else:
        return None

    low = first_match
    high = length
    while low < high:
        mid = (low + high) // 2
        if dict_to_be_searched[mid][key].lower().startswith(term) == True:
            low = mid + 1
        else:
            high = mid
    last_match = low - 1

    return [first_match, last_match] 

def insert_bisect(dict_to_be_searched, term, key, low = 0, high = None):

    if low < 0:
        raise ValueError('low must be non-negative')
    if high == None:
        high = len(dict_to_be_searched)

    term = term.lower()
    
    while low < high:
        mid = (low + high) // 2
        if term < dict_to_be_searched[mid][key].lower():
            high = mid
        else:
            low = mid + 1
    
    return low

def create_file(filename):
    try:
        f = open(filename, 'w')
        f.close()
    except:
        return 'CREATE_ERROR'

def load_file(filename):
    if os.stat(filename).st_size == 0:
        return 'FILE_EMPTY'
    else:
        with open(filename, 'r') as f:
            try:
                aux = json.load(f)
                for i in range(0,len(aux)):
                    aux[i]['index'] = i
                return aux
            except:
                return 'JSON_ERROR'
        

def update_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def encrypt(masterpassword, plaintext):
    mastersalt = os.urandom(32)
    key = KDF.PBKDF2(masterpassword, mastersalt, dkLen = 32, count = 500000)
    cipher_obj = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher_obj.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    iv = cipher_obj.iv
    return {'ciphertext': b64encode(ciphertext).decode('utf-8'),
            'iv': b64encode(iv).decode('utf-8'), 
            'mastersalt': b64encode(mastersalt).decode('utf-8')}

def decrypt(masterpassword, cipher_dict):
    key = KDF.PBKDF2(masterpassword, b64decode(cipher_dict['mastersalt'].encode('utf-8')), dkLen = 32, count = 500000)
    cipher_obj = AES.new(key, AES.MODE_CBC, b64decode(cipher_dict['iv'].encode('utf-8')))
    plaintext = cipher_obj.decrypt(b64decode(cipher_dict['ciphertext'].encode('utf-8')))
    plaintext = unpad(plaintext, AES.block_size).decode('utf-8')
    return plaintext

def decrypt_names(masterpassword, encdata):
    unencdata = deepcopy(encdata)
    for i in range(0,len(encdata)):
        unenc_name = decrypt(masterpassword, encdata[i]['name'])
        unencdata[i]['name'] = unenc_name
    # indexdata(encdata, unencdata)
    unencdata.sort(key = lambda x: x['name'])
    return unencdata

# def resetindex(encdata, unencdata):
#     for i in range(0,len(encdata)):
#         encdata[i]['index'] = i
#         unencdata[i]['index'] = i

def add_entry(masterpassword, filename, encdata, unencdata, entry):
    encentry = {}
    for i, j in zip(['name', 'login', 'password'], entry):
        encentry[i] = encrypt(masterpassword, j)
    encentry['index'] = len(encdata)
    encdata.append(encentry)
    update_file(filename, encdata)

    unencentry = deepcopy(encentry)
    unencentry['name'] = entry[0]
    index = insert_bisect(unencdata, entry[0], 'name')
    unencdata.insert(index, unencentry)

def remove_entry(filename, encdata, unencdata, name):
    for i in range(0,len(unencdata)):
        if name == unencdata[i]['name']:
            removed_index = unencdata[i]['index']
            del unencdata[i]
            break
        
    for i in range(0,len(encdata)):
        if removed_index == encdata[i]['index']:
            del encdata[i]
            break

    for i in range(0,len(unencdata)):
        if unencdata[i]['index'] > removed_index:
            unencdata[i]['index'] -= 1
            
    for i in range(0,len(encdata)):
        if encdata[i]['index'] > removed_index:
            encdata[i]['index'] -= 1

    update_file(filename, encdata)


# # n = 0
# f = 'test.pasu'
# # mp = 'a'
# # pt = [ [choice(['a','b','c','d','e']),'l','h'] for i in range(0,5)]
# # #pt = [['n2','l1','p1'],['n1','l2','p2']]
# encdata = load_file(f)
# unencdata = []

# create_file(f)
# add_entry('tr', f, encdata, unencdata, ['oio1','n','c'])
# print(unencdata)
# add_entry('tr', f, encdata, unencdata, ['odasdio1','n','c'])
# encdata = load_file(f)
# unencdata = decrypt_names(mp,encdata)
# remove_entry(f, encdata, unencdata, 'b')
# print(encdata)
# print(unencdata)














