'''
Prérequis expérimentaux : Lors de la collecte des données, l'axe x du téléphone est perpendiculaire à la direction de la gravité.

1. Modèle
Liste des paramètres (3 paramètres) :
Matrice d'accélération linéaire (accélération sur l'axe x, accélération sur l'axe y, accélération sur l'axe z) ;
Matrice d'accélération gravitationnelle (accélération gravitationnelle sur l'axe x, accélération gravitationnelle sur l'axe y, accélération gravitationnelle sur l'axe z) ;
Matrice de quaternions (quaternion x, quaternion y, quaternion z, quaternion w).

2. Types de paramètres du modèle :
numpy.ndarray
'''

import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


#IMU DATA is provided through the model described as follows
class Modele(object):
    def __init__(self, lineaire, gravite, rotation):
        self.lineaire = lineaire #Lineare acceleration Matrix. 
        self.gravite = gravite #Gravity acceleration Matrix.
        self.rotation = rotation #Angular acceleration Matrix. 

    '''
        Conversion des quaternions en angles d'Euler
    '''
    def quaternion2euler(self):
        rotation = self.rotation
        x = rotation[:, 0]
        y = rotation[:, 1]
        z = rotation[:, 2]
        w = rotation[:, 3]
        pitch = np.arcsin(2*(w*y-z*x))
        roll = np.arctan2(2*(w*x+y*z),1-2*(x*x+y*y))
        yaw = np.arctan2(2*(w*z+x*y),1-2*(z*z+y*y))
        return pitch, roll, yaw
    
    '''
        Obtention de l'angle (theta) entre le système de coordonnées du téléphone et le système de coordonnées terrestre
    '''
    def conversion_coordonnees(self):
        gravite = self.gravite
        lineaire = self.lineaire

        g_y = gravite[:, 1]
        g_z = gravite[:, 2]

        a_vertical = lineaire[:, 1]*np.cos(theta) + lineaire[:, 2]*np.sin(theta)

        return a_vertical
    
    '''
        Fonction de détection des pas

        Type de marche :
        normal : Mode de marche normal
        abnormal : Mode de marche de localisation fusionnée (intervalles de marche supérieurs à 1s)

        Valeur de retour :
        steps
        Tableau de dictionnaires, chaque dictionnaire stocke la position du pic (index) et la valeur d'accélération totale à ce point (acceleration)
    '''
    def compteur_pas(self, frequence=100, type_marche='normal'):
        offset = frequence/100
        g = 9.794
        a_vertical = self.conversion_coordonnees()
        glissement = 40 * offset
        frequence = 100 * offset
        min_acceleration = 0.2 * g
        max_acceleration = 2 * g
        min_interval = 0.4
        steps = []
        peak = {'index': 0, 'acceleration': 0}

        for i, v in enumerate(a_vertical):
            if v >= peak['acceleration'] and v >= min_acceleration and v <= max_acceleration:
                peak['acceleration'] = v
                peak['index'] = i
            if i%slide == 0 and peak['index'] != 0:
                steps.append(peak)
                peak = {'index': 0, 'acceleration': 0}
        
        if len(steps)>0:
            lastStep = steps[0]
            dirty_points = []
            for key, step_dict in enumerate(steps):
                if key == 0:
                    continue
                if step_dict['index']-lastStep['index'] < min_interval*frequence:
                    if step_dict['acceleration'] <= lastStep['acceleration']:
                        dirty_points.append(key)
                    else:
                        lastStep = step_dict
                        dirty_points.append(key-1)
                else:
                    lastStep = step_dict
            
            counter = 0
            for key in dirty_points:
                del steps[key-counter]
                counter = counter + 1
        
        return steps
    
    def pas_longueur(self, max_acceleration):
        return np.power(max_acceleration, 1/4) * 0.5

    def pas_orientation(self):
        _, _, lacet = self.quaternion2euler()
        for i,v in enumerate(lacet):
            lacet[i] = -v
        return lacet
    
    '''
        Position relative de chaque trajectoire de marche
        Retourne les coordonnées prédites
    '''
    def position_pdr(self, frequence=100, type_marche='normal', offset=0, position_initiale=(0, 0)):
        lacet = self.pas_orientation()
        steps = self.compteur_pas(frequence=frequence, type_marche=type_marche)
        position_x = []
        position_y = []
        x = position_initiale[0]
        y = position_initiale[1]
        position_x.append(x)
        position_y.append(y)
        strides = []
        angle = [offset]
        for v in steps:
            index = v['index']
            length = self.pas_longueur(v['acceleration'])
            strides.append(length)
            theta = lacet[index] + offset
            angle.append(theta)
            x = x + length*np.sin(theta)
            y = y + length*np.cos(theta)
            position_x.append(x)
            position_y.append(y)
        return position_x, position_y, strides + [0], angle

    '''
        Affiche le graphique de détection des pas
        type_marche :
            - normal : Mode de marche normal
            - abnormal : Mode de marche de localisation fusionnée (intervalles de marche supérieurs à 1s)
    '''
    def afficher_pas(self, frequence=100, type_marche='normal'):
        a_vertical = self.conversion_coordonnees()
        steps = self.compteur_pas(frequence=frequence, type_marche=type_marche)

        index_test = []
        value_test = []
        for v in steps:
            index_test.append(v['index'])
            value_test.append(v['acceleration'])

        textstr = '='.join(('pas', str(len(steps))))
        _, ax = plt.subplots()
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        plt.plot(a_vertical)
        plt.scatter(index_test, value_test, color='r')
        plt.xlabel('échantillons')
        plt.ylabel("accélération verticale")
        plt.show()

    '''
        Affiche un nuage de points de distribution de données, utilisé pour évaluer la distribution du bruit pour un type de données particulier, généralement une distribution gaussienne.
    '''
    def afficher_gaussienne(self, donnees, ajustement):
        essuyer = 150
        donnees = donnees[essuyer:len(donnees)-essuyer]
        division = 100
        acc_min = np.min(donnees)
        acc_max = np.max(donnees)
        intervalle = (acc_max-acc_min)/division
        compteur = [0]*division
        index = []

        for k in range(division):
            index.append(acc_min+k*intervalle)

        for v in donnees:
            for k in range(division):
                if v>=(acc_min+k*intervalle) and v<(acc_min+(k+1)*intervalle):
                    compteur[k] = compteur[k]+1
        
        textstr = '\n'.join((
            r'$max=%.3f$' % (acc_max, ),
            r'$min=%.3f$' % (acc_min, ),
            r'$moyenne=%.3f$' % (np.mean(donnees), )))
        _, ax = plt.subplots()
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        plt.scatter(index, compteur, label='distribution')

        if ajustement==True:
            longueur = math.ceil((acc_max-acc_min)/intervalle)
            compteurArr = longueur * [0]
            for value in donnees:
                key = int((value - acc_min) / intervalle)
                if key >=0 and key <longueur:
                    compteurArr[key] += 1
            moyenne_normale = np.mean(donnees)
            sigma_normale = np.std(donnees)
            x_normale = np.linspace(acc_min, acc_max, 100)
            y_normale = norm.pdf(x_normale, moyenne_normale, sigma_normale)
            y_normale = y_normale * np.max(compteurArr) / np.max(y_normale)
            ax.plot(x_normale, y_normale, 'r-', label='ajustement')

        plt.xlabel('accélération')
        plt.ylabel('échantillons totaux')
        plt.legend()
        plt.show()

    '''
        Affiche les variations d'accélération sur les trois axes
    '''
    def afficher_donnees(self, type_donnees):
        if type_donnees=='lineaire':
            lineaire = self.lineaire
            x = lineaire[:,0]
            y = lineaire[:,1]
            z = lineaire[:,2]
            index = range(len(x))
            
            ax1 = plt.subplot(3,1,1) 
            ax2 = plt.subplot(3,1,2) 
            ax3 = plt.subplot(3,1,3) 
            plt.sca(ax1)
            plt.title('x')
            plt.scatter(index,x)
            plt.sca(ax2)
            plt.title('y')
            plt.scatter(index,y)
            plt.sca(ax3)
            plt.title('z')
            plt.scatter(index,z)
            plt.show()
        elif type_donnees=='gravite':
            gravite = self.gravite
            x = gravite[:,0]
            y = gravite[:,1]
            z = gravite[:,2]
            index = range(len(x))
            
            ax1 = plt.subplot(3,1,1) 
            ax2 = plt.subplot(3,1,2) 
            ax3 = plt.subplot(3,1,3) 
            plt.sca(ax1)
            plt.title('x')
            plt.scatter(index,x)
            plt.sca(ax2)
            plt.title('y')
            plt.scatter(index,y)
            plt.sca(ax3)
            plt.title('z')
            plt.scatter(index,z)
            plt.show()
        else: 
            rotation = self.rotation
            x = rotation[:,0]
            y = rotation[:,1]
            z = rotation[:,2]
            w = rotation[:,3]
            index = range(len(x))
            
            ax1 = plt.subplot(4,1,1) 
            ax2 = plt.subplot(4,1,2) 
            ax3 = plt.subplot(4,1,3) 
            ax4 = plt.subplot(4,1,4) 
            plt.sca(ax1)
            plt.title('x')
            plt.scatter(index,x)
            plt.sca(ax2)
            plt.title('y')
            plt.scatter(index,y)
            plt.sca(ax3)
            plt.title('z')
            plt
