#S19 File Analysis
#By Quito, M.
#This is a small module which can be used to analyze the structure of
#an S19 file for personal study and reference.

###############
#	Functions
###############

#Returns a count for records of the S[N] type, where N is any number from 0 through 9.
class S19:
    def __init__(self, s19_file=None, block_size=0xFF):
        self.module = []
        self.block_size = block_size
        
        if s19_file is None:
            import os
            for root, dirs, files in os.walk('../lib'):
                for f in files:
                    if os.path.splitext(f)[-1] == '.s19':
                        s19_file = os.path.join(root,f)
        self.parse(s19_file)
        pass
    
    def parse(self,file):
        with open(file,'r') as s19:
            #Breakdown S19 records into list.
            s19 = s19.read()
            g='\r\n'
            if g in s19:
                h=s19.split(g)
            else:
                h=s19.split('\n')
        try:
            #Check CheckSum
            for i in h:
                if 'S0' in i or 'S1' in i or 'S2' in i or 'S3' in i:
                    Sum = self.Checksum(i)
                    _Sum = int(self._checksum(i),16)
                    if Sum != _Sum:
                        print('CheckSum error')
                        return

            #Transform s record to Module and block
            cnt = 0
            module_idx = 0
            for i in h:
                # first valid record
                if 'S1' in i or 'S2' in i or 'S3' in i:
                    if cnt == 0:
                        addr, addr_Len = self._addr_extract(i)
                        data_Len = self.bytecount(i) - addr_Len - 1
                        print('addr, data_Len =%s, %d'%(addr,data_Len))
                        addr = int(addr,16)
                        addr_next = addr + data_Len
                        self.module.append(S19_Module(addr,data_Len,self._data_extract(i)))
                        cnt = 1
                        continue
                    # except first, afterward record
                    if cnt == 1 :
                        addr, addr_Len = self._addr_extract(i)
                        data_Len = self.bytecount(i) - addr_Len - 1
                        print('addr, data_Len =%s, %d'%(addr,data_Len))
                        addr = int(addr,16)
                        if addr == addr_next:
                            #address is consecutive
                            addr_next = addr + data_Len
                            self.module[module_idx].length += data_Len
                            self.module[module_idx].data += self._data_extract(i)
                        else:
                            #address is not consecutive, append another module
                            self.module.append(S19_Module(addr,data_Len,self._data_extract(i)))
                            module_idx += 1
            print('S19 module Parse OK!')
            
            for m in self.module:
#                 print('module.data:%s'%m.data)
                print('module.length:%x'%m.length)
                print('module.address:%x'%m.address)
                m.blockParser(self.block_size)
                n = 0
                for b in m.block:
                    print('block[%d] address:%x'%(n,b.address))
                    print('block[%d] length:%x'%(n,b.length))
#                     print('block[%d] data:%s'%(n,b.data))
                    n += 1
            print('S19 Block Parse OK!')
            

        except:
            print('parser error!')
    
    #Calculate Record Checksum
    def Checksum(self, record):
        Sum = 0
        addr, addr_Len = self._addr_extract(record)
        n = 0
        while n < (addr_Len*2):
            Sum += int(addr[n:n+2],16)
            n += 2
        Sum += self.bytecount(record)
        data = self._data_extract(record)
        data_len = len(data)
        if data_len%2 is not 0:
            print("Record data num is not even")
            return None
        n = 0
        while n < data_len:
            Sum += int(data[n:n+2],16)
#                         print(hex(int(data[n:n+2],16)))
            n += 2
        #CheckSum    
        Sum = 0xFF-Sum&0xFF
        return Sum
                    
    def _s_count(self, record_list, N):
        c=0				#count var initalized at 0
        r=record_list 	#local var for the list of records
        l=len(r) 		#length of the record list (the S19 file)
        s= "S"+str(N)		#Depending on value of N, a string equal to S0, S1, .., S8, or S9
        for i in range(0, l-1):	#iterates for each member of the list
            t= s in r[i]		#Is S[N] found in the current row? True if yes, False if no.
            if t==True:			
                c+=1 			#increment by 1 for each record of S[N] found
        return c
    
    #Returns a list of 10 elements, where the first element is equal to the number of S0
    #records in the S19 file, the 2nd element equal to the number of S1 records, and so on
    #until S9.
    
    def s_totals(self, record_list):
        r=record_list	#local var for the list of records
        S=self._zerolist(10)	#initialize empty list.
        for i in range(0,9):
            S[i]=self._s_count(r,i)		#count how many of S[N] type records in the S19 file.
        return S
    
    #A printed breakdown of the type of S records found in the S19 file. Omits S type records
    #that are not found in the file.
    
    def print_totals(self, S):
        for i in range(0,9):
            if S[i]!=0:
                print(str(S[i])+'\tS'+str(i)+' records.')
        return
    
    #Initialize a list of zeroes of length N.
    
    def _zerolist(self, N):
        l=[0]*N
        return l
    
    #Extracts the bytecount byte from the selected record R. See S19_Chart for illustration of
    #different byte fields for each record.
    
    def _bytecount_byte(self, R):
        r=R[2:4]
        return r
    
    #Converts the bytecount byte from hex to decimal value.
    
    def bytecount(self, s):
        b=self._bytecount_byte(s)
        r=int(b,16)
        return r
    
    #Extracts the checksum byte from the selected record R.
    
    def _checksum(self, R):
        r=R[-2:]
        return r
    
    #Extracts the data fields from the selected record R
    
    def _data_extract(self, R):
        adc=R[4:] 			#address, data, checksum
        if 'S0' in R or 'S1' in R:
            s=R[8:-2]
        if 'S2' in R:
            s=R[10:-2]
        if 'S3' in R or 'S7' in R:
            s=R[12:-2]
        return s
    
    #Extracts the address fields from the selecter record R.
    
    def _addr_extract(self, R):
        adc=R[4:] #address, data, checksum
        if 'S0' in R or 'S1' in R:
            s=R[4:8]
            l = 2
        if 'S2' in R:
            s=R[4:10]
            l = 3
        if 'S3' in R or 'S7' in R:
            s=R[4:12]
            l = 4
        return s,l
    
    #Extracts the address fields for all records in the records list.
    #Returns a list of the address fields.
    
    def addr_extract_whole(self, record_list):
        r=record_list
        l=len(record_list)
        S=self._zerolist(l)
        print('---------------Addr----------------')
        for i in range(0,l-1):
            S[i],tmp=self._addr_extract(r[i])
            print('S[%d]: %s'%(i,S[i]))
        return S
    
    #Extracts the data fields for all records in the records list.
    #Returns a list of the data fields.
    
    def data_extract_whole(self, record_list):
        r=record_list
        l=len(record_list)
        S=self._zerolist(l)
        print('---------------Data----------------')
        for i in range(0,l-1):
            S[i]=self._data_extract(r[i])
            print('S[%d]: %s'%(i,S[i]))
        return S
    
    #Saves the extracted data fields list to file.
    
    def dump_data(self, g):
        q=self.data_extract_whole(g)
        data=open('_data.txt','w')
        for x in q:
            data.write("%s\n" % x)
        return
    
    #Saves the extracted address fields list to file.
    
    def dump_addresses(self, g):
        q=self.addr_extract_whole(g)
        data=open('_addresses.txt','w')
        for x in q:
            data.write("%s\n" % x)
        return

class S19_block:
    def __init__(self, addr, len, data):
        self.address    =   addr
        self.length     =   len
        self.data       =   data
        pass
    
"""
Split module to block

:param data: Module data
:type data: list[ascii char]

:param bl: block data length, by default set to 0xF7, 8 bytes aligned
:type bl: int

"""
class S19_Module(S19_block):
    def __init__(self, addr, len, data):
        super(S19_Module, self).__init__(addr, len, data)
        self.block      =   []
        pass
    
    def blockParser(self, block_size):
        import math
        block_num = math.ceil(self.length / block_size)
        addr = self.address
        p = 0
        for n in range(block_num):
            if p < (self.length - block_size)*2:
                self.block.append(S19_block(addr,block_size,self.data[p:p+2*block_size]))
            else:
                self.block.append(S19_block(addr,self.length-(p//2),self.data[p:]))
            addr += block_size
            p += 2*block_size
        pass

#####################
#	Main Program	
#####################
if __name__ == "__main__":  
    s = S19(block_size=0xF7)