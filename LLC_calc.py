'''
LLC calculation
'''
from sympy import *
import math
import numpy as np
#unit difinition
n = 1e-9
u = 1e-6
m = 1e-3
k = 1e3
meg = 1e6
Pi = math.pi
#Limited values
Lr_min = 10
Cr_max = 430
Cr_min = 100

class LLC():
    Power_Coefficient = 1.2
    Vd = 0.7
    Ip = 1.1
    Fr = np.arange(70*k,100*k,5*k)
    K = np.arange(3,7,0.5)
    def __init__(self,Vin = 450, Vo_max = 16, Vo_nor = 14.5, Vo_min = 9, Po = 2500, Eff = 0.93):
        self.Vin = Vin
        self.Vo_max = Vo_max
        self.Vo_nor = Vo_nor
        self.Vo_min =Vo_min
        self.Po = Po
        self.Eff = Eff

# M_:volt transmit ratio
        # |           s*Lm // Rac         |
# M_ =    | ----------------------------  |
        # | s*Lm // Rac + s*Lr + 1/(s*Cr) |

    def Power_Split(self,x):
        if self.Vo_min <= x < self.Vo_nor:
            return self.Po*x/self.Vo_nor
        elif self.Vo_nor <= x <= self.Vo_max:
            return self.Po
        else: return -1
        
    def Rload(self,Vo):
        return Vo**2/self.Power_Split(Vo)/self.Eff/self.Power_Coefficient
        
    def calc(self):
        # X = Symbol('X',type = 'true')
        N = round(self.Vin/2/self.Vo_nor*self.Eff)
        print("N: " ,N)
        Rlm = self.Rload(self.Vo_max)
        Rac = 8*Rlm*N*N/(Pi**2)
        print("Rac: %.2f" %Rac)
        # x = np.arange(0.4,0.8,0.01)
        M_max = 2*N*(self.Vo_max+self.Vd)/self.Vin
        M_min = 2*N*(self.Vo_min+self.Vd)/self.Vin
        print("M_max: %.2f" %M_max)
        print("M_min: %.2f" %M_min)
        
        for K in self.K:
            # Q_max = sqrt(1/(self.K*(1-X**2)) - 1/(self.K**2*X**2))
            Q_max = 1/(K*M_max)*np.sqrt(K+M_max**2/(M_max**2-1))
        # #M = -self.K*X/((1/X-self.K*X-X)+1j*(Q*self.K-Q*X**2*self.K))
        # #M = -self.K*X/((1/X-self.K*X-X)+1j*(Q_max*self.K-Q_max*X**2*self.K))
        # M_ = self.K*X/sqrt((1/X-self.K*X-X)**2 + (Q_max*self.K-Q_max*X**2*self.K)**2)
        # # print(M_real)
        # res = solve([M_-M_max],[X])
        # res = res[0][0]
        # print("X_left: %.2f" %res)
        # Q_max  = sqrt(1/(self.K*(1-res**2)) - 1/(self.K**2*res**2))
            print("------------K: %.1f-------------" %K)
            print("Q_max: %.2f" %Q_max)
            for Fr in self.Fr:
                #calculate Freq range

                F_min = Fr/np.sqrt(1+K*(1-1/M_max**2))/k
                F_max = Fr/np.sqrt(abs(1+K*(1-1/M_min)))/k
                print("F_min: %.2fkHz"%F_min)
                print("F_max: %.2fkHz"%F_max)

                #calculate Lr,Lm,Cr
                Q  = 0.95*Q_max
                Lr = Q*Rac/(2*Pi*Fr)*1e6
                Lm = K*Lr
                Cr = 1e9*(2*Pi*Fr*Rac*Q)**-1
                Im = self.Vin/(Lr+Lm)/4/F_max
                # if Lr < Lr_min or Cr < Cr_min or Cr > Cr_max or Im < self.Ip:
                    # continue
                # else:
                print("Lr: %.2fuH, Lm: %.2fuH, Cr: %.2fnF, Im: %.2fA" %(Lr,Lm,Cr,Im))
                
                    
                    # print("Calculation completed!")
        
        return M_min,M_max,Q_max,F_min/Fr,F_max/Fr
        # pass
        
    
if __name__ == '__main__':
    llc = LLC()
    
    llc.calc()
    # y=[]
    # X = np.arange(9,15,1)
    # for x in X:
        # y.append(llc.Power_Split(x))
    # print(llc.Rload(llc.Vo_max))   
    # print(np.arange(0.4,0.8,0.1))