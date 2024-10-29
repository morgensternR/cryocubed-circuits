import numpy as np
import matplotlib.pyplot as plt 

#Get Data
pwm1 = np.loadtxt(fr'current_list_pwm1.txt', delimiter= ' ')
pwm05 = np.loadtxt(fr'current_list_pwm0-5.txt', delimiter= ' ')
pwm025 = np.loadtxt(fr'current_list_pwm0-25.txt', delimiter= ' ')


# plot lines 
plt.plot(pwm1[:,0], pwm1[:,1], label = "PWM = 1") 
plt.plot(pwm05[:,0], pwm05[:,1], label = "PWM = 0.5") 
plt.plot(pwm025[:,0], pwm025[:,1], label = "PWM = 0.25") 
plt.legend() 
plt.title("Current vs CTRL Value (at different PWM'd outputs) ")
plt.xlabel('CTRL Value')
plt.ylabel('ISMON Measured Current (mA)')
plt.yticks(range(0, 1000, 100))
plt.xticks(np.linspace(0,1, 11))

plt.show()