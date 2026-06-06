import pygame
import random
import sys
import math

# ======================================================
# CONFIGURACIÓN
# ======================================================

ANCHO = 1400
ALTO = 800
FPS = 60

pygame.init()

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Simulador de Tráfico")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 24)
font_large = pygame.font.SysFont("Arial", 36, bold=True)
font_small = pygame.font.SysFont("Arial", 18)

# ======================================================
# COLORES
# ======================================================

PASTO_COLOR = (46, 115, 59)
PASTO_DETALLE = (38, 97, 49)
CALLE_COLOR = (55, 55, 55)
CALLE_MOJADA = (35, 35, 35)
LINEA_BLANCA = (235, 235, 235)
LINEA_AMARILLA = (230, 185, 30)

BLANCO = (255, 255, 255)
NEGRO = (15, 15, 15)
GRIS_POSTE = (100, 100, 100)
GRIS_OSCURO = (40, 40, 40)

ROJO_APAGADO = (80, 20, 20)
ROJO_ENCENDIDO = (255, 40, 40)
AMARILLO_APAGADO = (80, 70, 10)
AMARILLO_ENCENDIDO = (255, 220, 20)
VERDE_APAGADO = (10, 80, 30)
VERDE_ENCENDIDO = (40, 255, 100)
NARANJA_GIRO = (255, 140, 0)

# ======================================================
# PARÁMETROS DE LA SIMULACIÓN, CLIMA Y TIPO DE AVENIDA
# ======================================================

clima = "seco"  # "seco" o "lluvia"
tipo_avenida = "estrecha"   # "estrecha" o "ancha"
pausado = False
target_vehiculos = 10
velocidad_multiplicador = 1.0
duracion_semaforo_segundos = 6.0

# ======================================================
# TIPOS DE VEHÍCULOS
# ======================================================

TIPOS = {
    "auto": {
        "color": (20, 130, 240),
        "ancho": 52,        # longitud del auto
        "alto": 28,         # ancho del auto
        "velocidad": (3.5, 5.0),
        "acel": 0.16,
        "decel": 0.24
    },
    "camion": {
        "color": (220, 110, 15),
        "ancho": 92,
        "alto": 36,
        "velocidad": (2.2, 3.2),
        "acel": 0.08,
        "decel": 0.18
    },
    "colectivo": {
        "color": (210, 190, 10),
        "ancho": 110,
        "alto": 38,
        "velocidad": (2.5, 3.2),
        "acel": 0.09,
        "decel": 0.20
    }
}

# ======================================================
# UTILIDADES DE DIBUJO
# ======================================================

def draw_rect_alpha(surface, color, rect, border_radius=0):
    """Dibuja un rectángulo con soporte para canal alfa (transparencia)."""
    x, y, w, h = rect
    shape_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, (0, 0, w, h), border_radius=border_radius)
    surface.blit(shape_surf, (x, y))

def draw_circle_alpha(surface, color, center, radius):
    """Dibuja un círculo con soporte para canal alfa."""
    cx, cy = center
    shape_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, (cx - radius, cy - radius))
# ======================================================
# CLASE BOTÓN INTERACTIVO DE UI
# ======================================================

class BotonUI:
    def __init__(self, x, y, w, h, texto, color_base, color_hover, color_texto=BLANCO):
        self.rect = pygame.Rect(x, y, w, h)
        self.texto = texto
        self.color_base = color_base
        self.color_hover = color_hover
        self.color_texto = color_texto
        
    def dibujar(self, superficie, mouse_pos):
        color = self.color_hover if self.rect.collidepoint(mouse_pos) else self.color_base
        pygame.draw.rect(superficie, color, self.rect, border_radius=8)
        pygame.draw.rect(superficie, (80, 90, 110), self.rect, width=1, border_radius=8)
        
        # Usar fuente de tamaño de botón
        txt_surf = font_small.render(self.texto, True, self.color_texto)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        superficie.blit(txt_surf, txt_rect)
        
    def clickeado(self, mouse_pos, clicked):
        return clicked and self.rect.collidepoint(mouse_pos)

# ======================================================
# GENERACIÓN PROCEDURAL DEL FONDO (AESTHETICS)
# ======================================================

fondo_estatico = None
posiciones_arboles = []

def generar_posiciones_arboles():
    """Genera posiciones de árboles de forma que no colisionen con las carreteras."""
    global posiciones_arboles
    posiciones_arboles = []
    
    # Zonas seguras para colocar árboles (fuera de las calles)
    # Calles ocupan x: ANCHO//2 - 120 a ANCHO//2 + 120
    # y: ALTO//2 - 120 a ALTO//2 + 120
    calle_x_min = ANCHO // 2 - 125
    calle_x_max = ANCHO // 2 + 125
    calle_y_min = ALTO // 2 - 125
    calle_y_max = ALTO // 2 + 125

    intentos = 0
    while len(posiciones_arboles) < 22 and intentos < 200:
        tx = random.randint(40, ANCHO - 40)
        ty = random.randint(40, ALTO - 40)
        
        # Verificar si está fuera de la carretera
        fuera_h = (ty < calle_y_min - 30) or (ty > calle_y_max + 30)
        fuera_v = (tx < calle_x_min - 30) or (tx > calle_x_max + 30)
        
        if fuera_h and fuera_v:
            # Evitar que estén demasiado pegados
            demasiado_cerca = False
            for ax, ay, ar in posiciones_arboles:
                if math.hypot(tx - ax, ty - ay) < 65:
                    demasiado_cerca = True
                    break
            if not demasiado_cerca:
                radio = random.randint(22, 35)
                posiciones_arboles.append((tx, ty, radio))
        intentos += 1

# ======================================================
# CONFIGURACIÓN DINÁMICA DE AVENIDAS
# ======================================================

def obtener_config_avenida():
    global tipo_avenida

    if tipo_avenida == "ancha":
        return {
            "mitad": 180,
            "carriles": [-135, -90, -45, 45, 90, 135]
        }
    else:
        return {
            "mitad": 120,
            "carriles": [-75, -25, 25, 75]
        }
    
def crear_fondo_estatico():
    config = obtener_config_avenida()
    MITAD_CALLE = config["mitad"]
    """Dibuja e inicializa el fondo estático con texturas y carreteras."""
    global fondo_estatico
    fondo_estatico = pygame.Surface((ANCHO, ALTO))
    
    # 1. Pintar Césped de Fondo
    fondo_estatico.fill(PASTO_COLOR)
    
    # Detalle/Ruido de Césped
    for _ in range(35000):
        rx = random.randint(0, ANCHO - 1)
        ry = random.randint(0, ALTO - 1)
        
        # Verificar que esté en el césped
        calle_x_min = ANCHO // 2 - MITAD_CALLE
        calle_x_max = ANCHO // 2 + MITAD_CALLE
        calle_y_min = ALTO // 2 - MITAD_CALLE
        calle_y_max = ALTO // 2 + MITAD_CALLE
        
        if (rx < calle_x_min or rx > calle_x_max) and (ry < calle_y_min or ry > calle_y_max):
            fondo_estatico.set_at((rx, ry), PASTO_DETALLE)

    # 2. Dibujar Calles (Asfalto)
    color_asfalto = CALLE_MOJADA if clima == "lluvia" else CALLE_COLOR
    
    # Horizontal
    pygame.draw.rect(fondo_estatico, color_asfalto, (0, ALTO//2 - MITAD_CALLE, ANCHO, MITAD_CALLE*2))
    # Vertical
    pygame.draw.rect(fondo_estatico, color_asfalto, (ANCHO//2 - MITAD_CALLE, 0, MITAD_CALLE*2, ALTO))
    
    # Texturizar Asfalto (Puntos de ruido fino en la calle)
    for _ in range(28000):
        # Puntos horizontales
        rx = random.randint(0, ANCHO - 1)
        ry = random.randint(ALTO//2 - MITAD_CALLE, ALTO//2 + 119)
        c = fondo_estatico.get_at((rx, ry))
        variation = random.randint(-8, 8)
        nr = max(0, min(255, c.r + variation))
        ng = max(0, min(255, c.g + variation))
        nb = max(0, min(255, c.b + variation))
        fondo_estatico.set_at((rx, ry), (nr, ng, nb))

        # Puntos verticales
        rx = random.randint(ANCHO//2 - MITAD_CALLE, ANCHO//2 + 119)
        ry = random.randint(0, ALTO - 1)
        c = fondo_estatico.get_at((rx, ry))
        variation = random.randint(-8, 8)
        nr = max(0, min(255, c.r + variation))
        ng = max(0, min(255, c.g + variation))
        nb = max(0, min(255, c.b + variation))
        fondo_estatico.set_at((rx, ry), (nr, ng, nb))

    # 3. Dibujar Sendas Peatonales (Cebras)
    # Horizontal izquierda
    for y in range(ALTO//2 - 110, ALTO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 165, y, 35, 10))
    # Horizontal derecha
    for y in range(ALTO//2 - 110, ALTO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 130, y, 35, 10))
    # Vertical superior
    for x in range(ANCHO//2 - 110, ANCHO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 - 165, 10, 35))
    # Vertical inferior
    for x in range(ANCHO//2 - 110, ANCHO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 + 130, 10, 35))

    # 4. Líneas de parada (Líneas de detención continuas)
    # Derecha (entrando de izquierda a derecha, carril inferior)
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 180, ALTO//2, 8, MITAD_CALLE))
    # Izquierda (entrando de derecha a izquierda, carril superior)
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 172, ALTO//2 - MITAD_CALLE, 8, MITAD_CALLE))
    # Abajo (entrando de arriba a abajo, carril derecho)
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2, ALTO//2 - 180, MITAD_CALLE, 8))
    # Arriba (entrando de abajo a arriba, carril izquierdo)
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - MITAD_CALLE, ALTO//2 + 172, MITAD_CALLE, 8))

    # 5. Línea divisoria central (Doble línea amarilla para separar sentidos de circulación)
    # Doble línea horizontal en el centro de la calle horizontal
    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (0, ALTO//2 - 3, ANCHO, 2))
    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (0, ALTO//2 + 1, ANCHO, 2))
    # Doble línea vertical en el centro de la calle vertical
    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (ANCHO//2 - 3, 0, 2, ALTO))
    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (ANCHO//2 + 1, 0, 2, ALTO))

    # Re-dibujar el cuadrado central de la intersección limpio de líneas amarillas
    pygame.draw.rect(fondo_estatico, color_asfalto, (ANCHO//2 - MITAD_CALLE, ALTO//2 - MITAD_CALLE, MITAD_CALLE*2, MITAD_CALLE*2))
    # Agregar grano al cuadrado central
    for _ in range(5000):
        rx = random.randint(ANCHO//2 - MITAD_CALLE, ANCHO//2 + 119)
        ry = random.randint(ALTO//2 - MITAD_CALLE, ALTO//2 + 119)
        c = fondo_estatico.get_at((rx, ry))
        variation = random.randint(-8, 8)
        nr = max(0, min(255, c.r + variation))
        ng = max(0, min(255, c.g + variation))
        nb = max(0, min(255, c.b + variation))
        fondo_estatico.set_at((rx, ry), (nr, ng, nb))

    # 6. Dibujar Líneas Discontinuas de Carril (Separación de carriles en el mismo sentido)
    # Horizontal izquierdo y derecho (a y = centro +/- 60)
    for x in range(0, ANCHO, 50):
        if x < ANCHO//2 - 180 or x > ANCHO//2 + 180:
            # Hacia la derecha (abajo)
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 + 58, 20, 4))
            # Hacia la izquierda (arriba)
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 - 62, 20, 4))

    # Vertical superior e inferior (a x = centro +/- 60)
    for y in range(0, ALTO, 50):
        if y < ALTO//2 - 180 or y > ALTO//2 + 180:
            # Hacia abajo (derecha)
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 58, y, 4, 20))
            # Hacia arriba (izquierda)
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 62, y, 4, 20))

    # 7. Líneas continuas de prohibido cambiar de carril justo antes del cruce (200 px antes)
    # Carril derecho superior e inferior
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 380, ALTO//2 + 58, 200, 4))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 180, ALTO//2 - 62, 200, 4))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 58, ALTO//2 - 380, 4, 200))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 62, ALTO//2 + 180, 4, 200))

    # 8. Dibujar Árboles con Sombras
    for tx, ty, radio in posiciones_arboles:
        # Sombra del árbol proyectada (negra semi-transparente desplazada al sureste)
        draw_circle_alpha(fondo_estatico, (10, 25, 10, 90), (tx + 8, ty + 8), radio)
        
        # Tronco
        pygame.draw.circle(fondo_estatico, (100, 60, 20), (tx, ty), max(4, radio // 5))
        
        # Copa del árbol (círculos concéntricos verdes de distinto matiz)
        pygame.draw.circle(fondo_estatico, (34, 139, 34), (tx, ty), radio)
        pygame.draw.circle(fondo_estatico, (46, 175, 46), (tx - 3, ty - 3), int(radio * 0.8))
        pygame.draw.circle(fondo_estatico, (60, 200, 60), (tx - 5, ty - 5), int(radio * 0.55))

# ======================================================
# CLASE SEMÁFORO
# ======================================================

class Semaforo:
    def __init__(self):
        # horizontal: derecha/izquierda | vertical: abajo/arriba
        self.horizontal = "verde"
        self.vertical = "rojo"
        self.timer = int(duracion_semaforo_segundos * 60)
        self.amarillo_duration = int(min(75, duracion_semaforo_segundos * 0.20 * 60))

    def actualizar(self):
        self.timer -= 1
        self.amarillo_duration = int(min(75, duracion_semaforo_segundos * 0.20 * 60))

        # Cambio Verde -> Amarillo
        if self.horizontal == "verde" and self.timer <= self.amarillo_duration:
            self.horizontal = "amarillo"
        if self.vertical == "verde" and self.timer <= self.amarillo_duration:
            self.vertical = "amarillo"

        # Cambio total
        if self.timer <= 0:
            if self.horizontal in ["verde", "amarillo"]:
                self.horizontal = "rojo"
                self.vertical = "verde"
            else:
                self.horizontal = "verde"
                self.vertical = "rojo"
            self.timer = int(duracion_semaforo_segundos * 60)

    def dibujar(self):
        # Posición física de los 4 semáforos
        # Cada semáforo tiene un poste, un fondo negro y 3 círculos de color
        # Posiciones: 
        # 1. Semáforo para tráfico DERECHA (lado inferior izquierdo del cruce)
        # 2. Semáforo para tráfico IZQUIERDA (lado superior derecho del cruce)
        # 3. Semáforo para tráfico ABAJO (lado superior izquierdo del cruce)
        # 4. Semáforo para tráfico ARRIBA (lado inferior derecho del cruce)
        
        sem_configs = [
            # (X, Y, Orientacion_Caja, Estado_Luces)
            # 1. Derecha
            (ANCHO//2 - 150, ALTO//2 + 150, "vertical", self.horizontal, "DERECHA"),
            # 2. Izquierda
            (ANCHO//2 + 150, ALTO//2 - 150, "vertical", self.horizontal, "IZQUIERDA"),
            # 3. Abajo
            (ANCHO//2 - 150, ALTO//2 - 150, "horizontal", self.vertical, "ABAJO"),
            # 4. Arriba
            (ANCHO//2 + 150, ALTO//2 + 150, "horizontal", self.vertical, "ARRIBA")
        ]

        for x, y, orientacion, estado, nombre in sem_configs:
            # Dibujar poste metálico
            pygame.draw.rect(pantalla, GRIS_POSTE, (x - 4, y - 4, 8, 8))
            
            # Dimensiones de la caja del semáforo
            if orientacion == "vertical":
                w, h = 24, 60
                caja_rect = pygame.Rect(x - w//2, y - h//2, w, h)
                # Colores de las 3 luces
                c_rojo = ROJO_ENCENDIDO if estado == "rojo" else ROJO_APAGADO
                c_amar = AMARILLO_ENCENDIDO if estado == "amarillo" else AMARILLO_APAGADO
                c_verd = VERDE_ENCENDIDO if estado == "verde" else VERDE_APAGADO
                
                luces = [
                    (c_rojo, (x, y - 18)),
                    (c_amar, (x, y)),
                    (c_verd, (x, y + 18))
                ]
            else:
                w, h = 60, 24
                caja_rect = pygame.Rect(x - w//2, y - h//2, w, h)
                # Colores
                c_rojo = ROJO_ENCENDIDO if estado == "rojo" else ROJO_APAGADO
                c_amar = AMARILLO_ENCENDIDO if estado == "amarillo" else AMARILLO_APAGADO
                c_verd = VERDE_ENCENDIDO if estado == "verde" else VERDE_APAGADO
                
                luces = [
                    (c_rojo, (x - 18, y)),
                    (c_amar, (x, y)),
                    (c_verd, (x + 18, y))
                ]
                
            # Dibujar caja contenedora con borde
            pygame.draw.rect(pantalla, NEGRO, caja_rect, border_radius=4)
            pygame.draw.rect(pantalla, GRIS_OSCURO, caja_rect, width=2, border_radius=4)
            
            # Dibujar focos de luz
            for color, pos in luces:
                pygame.draw.circle(pantalla, color, pos, 7)
                # Efecto de brillo difuminado si la luz está encendida
                if color in [ROJO_ENCENDIDO, AMARILLO_ENCENDIDO, VERDE_ENCENDIDO]:
                    # Hacer un glow de radio 16 con canal alfa
                    draw_circle_alpha(pantalla, (color[0], color[1], color[2], 55), pos, 15)

# ======================================================
# ZONA DE INTERSECCIÓN
# ======================================================

zona_interseccion = pygame.Rect(
    ANCHO//2 - 120,
    ALTO//2 - 120,
    240,
    240
)

# ======================================================
# PARTICULAS DE SALPICADURAS DE AGUA (LLUVIA)
# ======================================================

particulas_salpicadura = []

def actualizar_y_dibujar_salpicaduras():
    """Actualiza y dibuja las salpicaduras de los neumáticos en la calle mojada."""
    global particulas_salpicadura
    nuevas_particulas = []
    for p in particulas_salpicadura:
        # p = [x, y, vx, vy, vida, max_vida]
        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 1  # decrementar vida
        
        if p[4] > 0:
            alfa = int(120 * (p[4] / p[5]))
            draw_circle_alpha(pantalla, (200, 200, 255, alfa), (int(p[0]), int(p[1])), random.randint(1, 3))
            nuevas_particulas.append(p)
            
    particulas_salpicadura = nuevas_particulas

def spawn_salpicadura(x, y, direccion):
    """Genera partículas de spray de neumático en la dirección opuesta al movimiento."""
    if clima != "lluvia":
        return
    for _ in range(2):
        if direccion == "derecha":
            vx = -random.uniform(0.5, 2.0)
            vy = random.uniform(-0.8, 0.8)
        elif direccion == "izquierda":
            vx = random.uniform(0.5, 2.0)
            vy = random.uniform(-0.8, 0.8)
        elif direccion == "abajo":
            vx = random.uniform(-0.8, 0.8)
            vy = -random.uniform(0.5, 2.0)
        else: # arriba
            vx = random.uniform(-0.8, 0.8)
            vy = random.uniform(0.5, 2.0)
            
        vida = random.randint(10, 20)
        particulas_salpicadura.append([x, y, vx, vy, vida, vida])

# ======================================================
# CLASE VEHÍCULO
# ======================================================

class Vehiculo:
    def __init__(self, x, y, direccion, carril_index):
        tipo = random.choice(list(TIPOS.keys()))
        datos = TIPOS[tipo]

        self.tipo = tipo
        self.color = datos["color"]
        self.ancho = datos["ancho"]  # Longitud del auto
        self.alto = datos["alto"]    # Ancho del auto
        
        # Velocidad base
        vel_rango = datos["velocidad"]
        vel_random = random.uniform(vel_rango[0], vel_rango[1])
            
        self.velocidad_base_max = vel_random
        self.velocidad_max = vel_random
        self.velocidad = vel_random
        self.acel_max = datos["acel"]
        self.decel_max = datos["decel"]

        self.x = x
        self.y = y
        self.direccion = direccion  # "derecha", "izquierda", "abajo", "arriba"
        
        # Carriles e índices
        self.carril_actual = carril_index
        self.carril_target = carril_index
        self.tiempo_cambio = 0      # Contador de frames para cambio de carril
        self.y_inicio = y           # Almacena el y/x inicial durante la transición
        self.x_inicio = x           # Almacena el y/x inicial durante la transición
        
        # Intersección e IDM
        self.decel_activa = False   # Se activa para encender luces de freno
        self.velocidad_anterior = vel_random
        
        # Limpiaparabrisas
        self.wiper_angle = 0
        self.wiper_direction = 1

    def obtener_rect(self):
        """Devuelve el rectángulo colisionable actual en base a su x, y reales."""
        if self.direccion in ["derecha", "izquierda"]:
            return pygame.Rect(self.x, self.y, self.ancho, self.alto)
        else:
            return pygame.Rect(self.x, self.y, self.alto, self.ancho)

    def obtener_coordenadas_carril(self, direccion, carril_idx):

        config = obtener_config_avenida()
        offsets = config["carriles"]

        if direccion == "derecha":
            carriles = [
                ALTO//2 + o
                for o in offsets if o > 0
            ]

        elif direccion == "izquierda":
            carriles = [
                ALTO//2 + o
                for o in offsets if o < 0
            ]

        elif direccion == "abajo":
            carriles = [
                ANCHO//2 + o
                for o in offsets if o > 0
            ]

        else:  # arriba
            carriles = [
                ANCHO//2 + o
                for o in offsets if o < 0
            ]

        return carriles[carril_idx]

    def evaluar_cambio_carril(self, vehiculos):
        """Modelo de cambio de carril para sobrepaso y desatascar carriles."""
        if self.tiempo_cambio > 0:
            return # Ya está realizando un cambio

        # No cambiar de carril cerca de la intersección (líneas continuas viales)
        dist_interseccion = 1000
        if self.direccion == "derecha":
            dist_interseccion = (ANCHO//2 - 180) - (self.x + self.ancho)
        elif self.direccion == "izquierda":
            dist_interseccion = self.x - (ANCHO//2 + 180)
        elif self.direccion == "abajo":
            dist_interseccion = (ALTO//2 - 180) - (self.y + self.ancho)
        elif self.direccion == "arriba":
            dist_interseccion = self.y - (ALTO//2 + 180)

        # Si ya pasó la intersección o está a menos de 220px antes de ella, no cambia
        if dist_interseccion < 220 or dist_interseccion < -80:
            return

        # Incentivo para cambiar: si el vehículo de adelante está muy cerca y va lento
        vehiculo_adelante = self.buscar_vehiculo_adelante(vehiculos)
        incentivo = False
        if vehiculo_adelante:
            dist = self.obtener_distancia_a(vehiculo_adelante)
            if dist < 160 and vehiculo_adelante.velocidad < self.velocidad_max * 0.85:
                incentivo = True

        if not incentivo:
            return # No hay necesidad de cambiar

        # Determinar carril alternativo
        carril_alternativo = 1 - self.carril_actual
        coord_destino = self.obtener_coordenadas_carril(self.direccion, carril_alternativo)

        # Evaluar SEGURIDAD en el carril de destino
        seguro = True
        
        # Buscar coches en el carril de destino
        vehiculos_destino = []
        for otro in vehiculos:
            if otro == self or otro.direccion != self.direccion:
                continue
            
            # Verificar si el otro auto está o estará en el carril alternativo
            if otro.carril_actual == carril_alternativo or otro.carril_target == carril_alternativo:
                vehiculos_destino.append(otro)

        # Buscar el más cercano adelante y el más cercano atrás en el carril alternativo
        cerca_adelante = None
        cerca_atras = None
        min_dist_adelante = 99999
        min_dist_atras = 99999

        for otro in vehiculos_destino:
            # Calcular distancia orientada
            dist = self.obtener_distancia_relativa(otro)
            if dist > 0:  # Está adelante
                if dist < min_dist_adelante:
                    min_dist_adelante = dist
                    cerca_adelante = otro
            else:  # Está atrás
                abs_dist = abs(dist)
                if abs_dist < min_dist_atras:
                    min_dist_atras = abs_dist
                    cerca_atras = otro

        # Umbrales de seguridad
        safe_gap_front = 90.0  # px adelante
        safe_gap_back = 90.0   # px atrás

        if cerca_adelante and min_dist_adelante < safe_gap_front:
            seguro = False
        if cerca_atras and min_dist_atras < safe_gap_back:
            # Si el de atrás va mucho más rápido que nosotros, tampoco es seguro
            if cerca_atras.velocidad > self.velocidad + 1:
                seguro = False
            seguro = seguro and (min_dist_atras > safe_gap_back + (cerca_atras.velocidad * 10))

        if seguro:
            # Iniciar cambio de carril
            self.carril_target = carril_alternativo
            self.tiempo_cambio = 45 # Duración de la maniobra (0.75 segundos a 60 fps)
            if self.direccion in ["derecha", "izquierda"]:
                self.y_inicio = self.y
            else:
                self.x_inicio = self.x

    def obtener_distancia_relativa(self, otro):
        """Calcula la distancia orientada a lo largo del eje de movimiento. 
        Positiva si el 'otro' está por delante, negativa si está por detrás."""
        if self.direccion == "derecha":
            return otro.x - self.x
        elif self.direccion == "izquierda":
            return self.x - otro.x
        elif self.direccion == "abajo":
            return otro.y - self.y
        else: # arriba
            return self.y - otro.y

    def obtener_distancia_a(self, otro):
        """Distancia bumper a bumper (neta) entre este coche y otro por delante."""
        if self.direccion == "derecha":
            return otro.x - (self.x + self.ancho)
        elif self.direccion == "izquierda":
            return self.x - (otro.x + otro.ancho)
        elif self.direccion == "abajo":
            return otro.y - (self.y + self.ancho)
        else: # arriba
            return self.y - (otro.y + otro.ancho)

    def buscar_vehiculo_adelante(self, vehiculos):
        """Encuentra el vehículo líder directo en el mismo carril/trayectoria."""
        coche_lider = None
        min_dist = 999999
        
        for otro in vehiculos:
            if otro == self or otro.direccion != self.direccion:
                continue
                
            # Verificar si comparten carril (o están en transición hacia él)
            mismo_carril = False
            if self.tiempo_cambio > 0:
                # Si estamos cambiando, consideramos coches en el carril destino
                mismo_carril = (otro.carril_actual == self.carril_target or otro.carril_target == self.carril_target)
            else:
                # Si no, coches en el carril actual
                mismo_carril = (otro.carril_actual == self.carril_actual or otro.carril_target == self.carril_actual)
            
            # Alternativa física continua: si la distancia lateral es pequeña (< 35px)
            # Esto maneja muy bien las colisiones diagonales durante los cambios de carril
            dist_lateral = 0
            if self.direccion in ["derecha", "izquierda"]:
                dist_lateral = abs(otro.y - self.y)
            else:
                dist_lateral = abs(otro.x - self.x)
                
            mismo_carril = mismo_carril or (dist_lateral < 36)

            if mismo_carril:
                dist = self.obtener_distancia_relativa(otro)
                # Sólo si está físicamente por delante
                if dist > 0:
                    net_dist = self.obtener_distancia_a(otro)
                    if net_dist < min_dist:
                        min_dist = net_dist
                        coche_lider = otro
                        
        return coche_lider

    def mover(self, semaforo, vehiculos):
        # Actualizar velocidad_max dinámicamente según clima y multiplicador
        w_factor = 0.75 if clima == "lluvia" else 1.0
        self.velocidad_max = self.velocidad_base_max * w_factor * velocidad_multiplicador
        
        # Guardar velocidad anterior para control de luces de freno
        self.velocidad_anterior = self.velocidad

        # 1. Gestionar cambio de carril (transición lateral suave)
        if self.tiempo_cambio > 0:
            self.tiempo_cambio -= 1
            progress = (45 - self.tiempo_cambio) / 45
            # Curva de suavizado Hermite
            smooth_progress = 3 * progress**2 - 2 * progress**3
            
            coord_dest = self.obtener_coordenadas_carril(self.direccion, self.carril_target)
            
            if self.direccion in ["derecha", "izquierda"]:
                self.y = self.y_inicio + (coord_dest - self.y_inicio) * smooth_progress
            else:
                self.x = self.x_inicio + (coord_dest - self.x_inicio) * smooth_progress
                
            if self.tiempo_cambio == 0:
                self.carril_actual = self.carril_target
        else:
            # Mantener la posición del carril estable
            if self.direccion in ["derecha", "izquierda"]:
                self.y = self.obtener_coordenadas_carril(self.direccion, self.carril_actual)
            else:
                self.x = self.obtener_coordenadas_carril(self.direccion, self.carril_actual)

        # 2. Evaluar cambio de carril cada 15 frames para no saturar CPU
        if pygame.time.get_ticks() % 15 == 0:
            self.evaluar_cambio_carril(vehiculos)

        # 3. Identificar coche líder físico
        lider = self.buscar_vehiculo_adelante(vehiculos)
        lider_dist = 999999
        lider_speed = 0
        if lider:
            lider_dist = self.obtener_distancia_a(lider)
            lider_speed = lider.velocidad

        # 4. Control de Semáforos e Intersecciones (como vehículo virtual)
        luz_activa = "rojo"
        stop_line = 0
        crossed_stop_line = False

        if self.direccion == "derecha":
            stop_line = ANCHO//2 - 180
            crossed_stop_line = (self.x + self.ancho) > stop_line
            luz_activa = semaforo.horizontal
        elif self.direccion == "izquierda":
            stop_line = ANCHO//2 + 180
            crossed_stop_line = self.x < stop_line
            luz_activa = semaforo.horizontal
        elif self.direccion == "abajo":
            stop_line = ALTO//2 - 180
            crossed_stop_line = (self.y + self.ancho) > stop_line
            luz_activa = semaforo.vertical
        elif self.direccion == "arriba":
            stop_line = ALTO//2 + 180
            crossed_stop_line = self.y < stop_line
            luz_activa = semaforo.vertical

        # Si nos aproximamos a luz roja o amarilla, y NO hemos cruzado la línea
        if not crossed_stop_line:
            # Calcular distancia al semáforo
            dist_to_light = 99999
            if self.direccion == "derecha":
                dist_to_light = stop_line - (self.x + self.ancho)
            elif self.direccion == "izquierda":
                dist_to_light = self.x - stop_line
            elif self.direccion == "abajo":
                dist_to_light = stop_line - (self.y + self.ancho)
            elif self.direccion == "arriba":
                dist_to_light = self.y - stop_line

            # Comportamiento del semáforo:
            # Rojo: Parar obligatoriamente (crea vehículo virtual)
            # Amarillo: Parar si la distancia es suficiente para hacerlo cómodamente, si no, pasar
            frenar_en_semaforo = False
            if luz_activa == "rojo":
                frenar_en_semaforo = True
            elif luz_activa == "amarillo":
                # Distancia mínima estimada para frenado confortable: d = v^2 / (2 * decel)
                dist_frenado_seguro = (self.velocidad ** 2) / (2 * self.decel_max) + 20
                if dist_to_light > dist_frenado_seguro:
                    frenar_en_semaforo = True

            if frenar_en_semaforo:
                # Comportamiento IDM considerando el semáforo como obstáculo estático
                if dist_to_light < lider_dist:
                    lider_dist = max(5.0, dist_to_light)
                    lider_speed = 0

        # 5. Evitar colisiones laterales en la intersección (cruce libre de atascos)
        # Si vamos a entrar en la intersección (distancia < 40px antes)
        # y hay coches perpendiculares cruzando, frenamos
        mi_rect_futuro = self.obtener_rect()
        crawling_dist = 30
        if self.direccion == "derecha":
            mi_rect_futuro.x += crawling_dist
        elif self.direccion == "izquierda":
            mi_rect_futuro.x -= crawling_dist
        elif self.direccion == "abajo":
            mi_rect_futuro.y += crawling_dist
        elif self.direccion == "arriba":
            mi_rect_futuro.y -= crawling_dist

        # Si el coche aún no cruza, pero está por entrar a la intersección
        if mi_rect_futuro.colliderect(zona_interseccion) and not self.obtener_rect().colliderect(zona_interseccion):
            # Buscar si hay vehículos perpendiculares en la intersección
            for otro in vehiculos:
                if otro.direccion in ["derecha", "izquierda"] and self.direccion in ["abajo", "arriba"]:
                    if otro.obtener_rect().colliderect(zona_interseccion):
                        # Obstáculo virtual
                        lider_dist = 15.0
                        lider_speed = 0
                        break
                elif otro.direccion in ["abajo", "arriba"] and self.direccion in ["derecha", "izquierda"]:
                    if otro.obtener_rect().colliderect(zona_interseccion):
                        lider_dist = 15.0
                        lider_speed = 0
                        break

        # 6. Cálculo de Aceleración con el Modelo IDM
        # Parámetros IDM
        s0 = 35.0          # Distancia de seguridad bumper a bumper mínima
        T_frames = 20.0    # Tiempo de reacción en frames (~0.33 seg)
        a = self.acel_max
        b = self.decel_max
        v = self.velocidad
        v0 = self.velocidad_max

        # Ecuación de flujo libre
        acel = a * (1.0 - (v / v0) ** 4) if v0 > 0 else 0

        # Ecuación de interacción (si hay un obstáculo/vehículo delante)
        if lider_dist < 1000:
            s = max(2.0, lider_dist)
            dv = v - lider_speed
            
            # Distancia de seguridad dinámica deseada
            s_star = s0 + v * T_frames + (v * dv) / (2 * ((a * b) ** 0.5))
            s_star = max(s0, s_star)
            
            interaction = (s_star / s) ** 2
            acel -= a * interaction

        # Limitar la desaceleración máxima para evitar movimientos bruscos irreales
        acel = max(-1.6, acel)

        # Aplicar aceleración a la velocidad
        self.velocidad = max(0.0, min(v0, self.velocidad + acel))

        # 7. Actualización de posición espacial
        if self.direccion == "derecha":
            self.x += self.velocidad
        elif self.direccion == "izquierda":
            self.x -= self.velocidad
        elif self.direccion == "abajo":
            self.y += self.velocidad
        else: # arriba
            self.y -= self.velocidad

        # Control visual de luces de freno (si desacelera significativamente)
        self.decel_activa = (self.velocidad < self.velocidad_anterior - 0.04) or (self.velocidad < 0.1)

        # Spawnear salpicaduras de neumático si se mueve y llueve
        if clima == "lluvia" and self.velocidad > 0.5:
            # Coordenadas traseras del neumático
            if self.direccion == "derecha":
                spawn_salpicadura(self.x, self.y + self.alto//2, self.direccion)
            elif self.direccion == "izquierda":
                spawn_salpicadura(self.x + self.ancho, self.y + self.alto//2, self.direccion)
            elif self.direccion == "abajo":
                spawn_salpicadura(self.x + self.alto//2, self.y, self.direccion)
            else:
                spawn_salpicadura(self.x + self.alto//2, self.y + self.ancho, self.direccion)

        # Actualizar limpiaparabrisas
        if clima == "lluvia":
            self.wiper_angle += 8 * self.wiper_direction
            if abs(self.wiper_angle) > 55:
                self.wiper_direction *= -1

    # ==================================================
    # DIBUJAR VEHÍCULO (AESTHETICS PREMIUM)
    # ==================================================

    def dibujar(self):
        w = self.ancho
        h = self.alto
        
        # Ajustar dimensiones de dibujo en base a orientación vertical
        if self.direccion in ["abajo", "arriba"]:
            w = self.alto
            h = self.ancho

        # 1. Dibujar sombra suave proyectada en el suelo
        draw_rect_alpha(pantalla, (0, 0, 0, 70), (self.x + 4, self.y + 4, w, h), border_radius=6)

        # 2. Dibujar Faros Delanteros de Luz (Conos proyectados en la calle si llueve)
        if clima == "lluvia":
            glow_color = (255, 255, 200, 35) # Luz amarilla cálida y transparente
            cone_length = 120
            
            # Polígono del cono de luz
            if self.direccion == "derecha":
                puntos = [
                    (self.x + w, self.y + 6),
                    (self.x + w + cone_length, self.y - 25),
                    (self.x + w + cone_length, self.y + h + 25),
                    (self.x + w, self.y + h - 6)
                ]
            elif self.direccion == "izquierda":
                puntos = [
                    (self.x, self.y + 6),
                    (self.x - cone_length, self.y - 25),
                    (self.x - cone_length, self.y + h + 25),
                    (self.x, self.y + h - 6)
                ]
            elif self.direccion == "abajo":
                puntos = [
                    (self.x + 6, self.y + h),
                    (self.x - 25, self.y + h + cone_length),
                    (self.x + w + 25, self.y + h + cone_length),
                    (self.x + w - 6, self.y + h)
                ]
            else: # arriba
                puntos = [
                    (self.x + 6, self.y),
                    (self.x - 25, self.y - cone_length),
                    (self.x + w + 25, self.y - cone_length),
                    (self.x + w - 6, self.y)
                ]
                
            # Render con alfa del cono
            cone_surf = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            pygame.draw.polygon(cone_surf, glow_color, puntos)
            pantalla.blit(cone_surf, (0, 0))

        # 3. Dibujar carrocería del vehículo
        pygame.draw.rect(pantalla, self.color, (self.x, self.y, w, h), border_radius=6)
        # Borde sutil para darle volumen tridimensional
        pygame.draw.rect(pantalla, (max(0, self.color[0]-40), max(0, self.color[1]-40), max(0, self.color[2]-40)), (self.x, self.y, w, h), width=2, border_radius=6)

        # 4. Dibujar cristales (parabrisas delantero, trasero y ventanas)
        color_vidrio = (170, 215, 240)
        
        if self.direccion == "derecha":
            # Parabrisas delantero (curvo adelante)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 16, self.y + 3, 6, h - 6), border_radius=2)
            # Vidrio trasero
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 8, self.y + 4, 4, h - 8), border_radius=2)
            # Ventanas laterales
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 16, self.y + 2, w - 36, 2))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 16, self.y + h - 4, w - 36, 2))
            # Parrilla/Capó
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + w - 6, self.y + 5, 4, h - 10), border_radius=1)
            
        elif self.direccion == "izquierda":
            # Parabrisas delantero
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 10, self.y + 3, 6, h - 6), border_radius=2)
            # Vidrio trasero
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 12, self.y + 4, 4, h - 8), border_radius=2)
            # Ventanas laterales
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 20, self.y + 2, w - 36, 2))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 20, self.y + h - 4, w - 36, 2))
            # Parrilla
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + 2, self.y + 5, 4, h - 10), border_radius=1)
            
        elif self.direccion == "abajo":
            # Parabrisas delantero
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 3, self.y + h - 16, w - 6, 6), border_radius=2)
            # Vidrio trasero
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 4, self.y + 8, w - 8, 4), border_radius=2)
            # Ventanas laterales
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 2, self.y + 16, 2, h - 36))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 4, self.y + 16, 2, h - 36))
            # Parrilla
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + 5, self.y + h - 6, w - 10, 4), border_radius=1)
            
        else: # arriba
            # Parabrisas delantero
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 3, self.y + 10, w - 6, 6), border_radius=2)
            # Vidrio trasero
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 4, self.y + h - 12, w - 8, 4), border_radius=2)
            # Ventanas laterales
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 2, self.y + 20, 2, h - 36))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 4, self.y + 20, 2, h - 36))
            # Parrilla
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + 5, self.y + 2, w - 10, 4), border_radius=1)

        # 5. Dibujar Ruedas (sobresaliendo un poco de la carrocería)
        # Ruedas laterales ocultas bajo la carrocería o visibles según dirección
        # El código original dibuja ruedas negras en los bordes. Lo mantenemos mejorado:
        color_rueda = (30, 30, 30)
        
        if self.direccion in ["derecha", "izquierda"]:
            # Rueda delantera izq, delantera der, trasera izq, trasera der
            pygame.draw.rect(pantalla, color_rueda, (self.x + 8, self.y - 2, 11, 4), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 18, self.y - 2, 11, 4), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + 8, self.y + h - 2, 11, 4), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 18, self.y + h - 2, 11, 4), border_radius=1)
        else:
            pygame.draw.rect(pantalla, color_rueda, (self.x - 2, self.y + 8, 4, 11), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x - 2, self.y + h - 18, 4, 11), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 2, self.y + 8, 4, 11), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 2, self.y + h - 18, 4, 11), border_radius=1)

        # 6. Dibujar Luces de Freno (Rojo brillante al frenar/detenerse, rojo oscuro si no)
        c_freno = ROJO_ENCENDIDO if self.decel_activa else (130, 0, 0)
        
        if self.direccion == "derecha":
            pygame.draw.rect(pantalla, c_freno, (self.x, self.y + 3, 2, 5))
            pygame.draw.rect(pantalla, c_freno, (self.x, self.y + h - 8, 2, 5))
        elif self.direccion == "izquierda":
            pygame.draw.rect(pantalla, c_freno, (self.x + w - 2, self.y + 3, 2, 5))
            pygame.draw.rect(pantalla, c_freno, (self.x + w - 2, self.y + h - 8, 2, 5))
        elif self.direccion == "abajo":
            pygame.draw.rect(pantalla, c_freno, (self.x + 3, self.y, 5, 2))
            pygame.draw.rect(pantalla, c_freno, (self.x + w - 8, self.y, 5, 2))
        else: # arriba
            pygame.draw.rect(pantalla, c_freno, (self.x + 3, self.y + h - 2, 5, 2))
            pygame.draw.rect(pantalla, c_freno, (self.x + w - 8, self.y + h - 2, 5, 2))

        # 7. Luces delanteras físicas (Faros físicos de los coches)
        c_faro = (255, 255, 230)
        if self.direccion == "derecha":
            pygame.draw.circle(pantalla, c_faro, (self.x + w, self.y + 4), 2)
            pygame.draw.circle(pantalla, c_faro, (self.x + w, self.y + h - 4), 2)
        elif self.direccion == "izquierda":
            pygame.draw.circle(pantalla, c_faro, (self.x, self.y + 4), 2)
            pygame.draw.circle(pantalla, c_faro, (self.x, self.y + h - 4), 2)
        elif self.direccion == "abajo":
            pygame.draw.circle(pantalla, c_faro, (self.x + 4, self.y + h), 2)
            pygame.draw.circle(pantalla, c_faro, (self.x + w - 4, self.y + h), 2)
        else: # arriba
            pygame.draw.circle(pantalla, c_faro, (self.x + 4, self.y), 2)
            pygame.draw.circle(pantalla, c_faro, (self.x + w - 4, self.y), 2)

        # 8. Luces de Giro (Direccionales)
        # Parpadean en naranja si está realizando cambio de carril
        if self.tiempo_cambio > 0:
            parpadeo_on = (pygame.time.get_ticks() // 220) % 2 == 0
            if parpadeo_on:
                # Determinar lado de giro (si va hacia carril target menor o mayor)
                giro_menor = self.carril_target < self.carril_actual
                
                # Ubicaciones de los intermitentes frontales y traseros del lado de giro
                if self.direccion in ["derecha", "izquierda"]:
                    # Si es derecha y giro menor (carril 0, y inferior/más arriba en pantalla)
                    # o izquierda y giro menor (carril 0, y superior/más arriba en pantalla)
                    girando_arriba = giro_menor if self.direccion == "derecha" else not giro_menor
                    y_luces = self.y if girando_arriba else self.y + h - 2
                    
                    # Dibujar intermitente delantero y trasero
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (self.x + 3, y_luces + 1), 2)
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (self.x + w - 3, y_luces + 1), 2)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (self.x + 3, y_luces + 1), 5)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (self.x + w - 3, y_luces + 1), 5)
                else:
                    # Direcciones verticales: abajo y arriba.
                    # Lado de giro es izquierda (menor x) o derecha (mayor x)
                    girando_izquierda = giro_menor if self.direccion == "abajo" else not giro_menor
                    x_luces = self.x if girando_izquierda else self.x + w - 2
                    
                    # Dibujar
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (x_luces + 1, self.y + 3), 2)
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (x_luces + 1, self.y + h - 3), 2)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (x_luces + 1, self.y + 3), 5)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (x_luces + 1, self.y + h - 3), 5)

        # 9. Limpiaparabrisas móviles (en climas de lluvia)
        if clima == "lluvia":
            # Dibujar un pequeño brazo metálico rotativo en el parabrisas
            w_color = (10, 10, 10)
            rads = math.radians(self.wiper_angle)
            wiper_len = 10
            
            # Punto de pivote en la base del parabrisas
            if self.direccion == "derecha":
                px, py = self.x + w - 11, self.y + h//2
                dx = int(wiper_len * math.cos(rads))
                dy = int(wiper_len * math.sin(rads))
                pygame.draw.line(pantalla, w_color, (px, py), (px + dx, py + dy), 2)
            elif self.direccion == "izquierda":
                px, py = self.x + 11, self.y + h//2
                dx = int(wiper_len * math.cos(rads))
                dy = int(wiper_len * math.sin(rads))
                # apuntar al revés
                pygame.draw.line(pantalla, w_color, (px, py), (px - dx, py + dy), 2)
            elif self.direccion == "abajo":
                px, py = self.x + w//2, self.y + h - 11
                dx = int(wiper_len * math.sin(rads))
                dy = int(wiper_len * math.cos(rads))
                pygame.draw.line(pantalla, w_color, (px, py), (px + dx, py + dy), 2)
            else: # arriba
                px, py = self.x + w//2, self.y + 11
                dx = int(wiper_len * math.sin(rads))
                dy = int(wiper_len * math.cos(rads))
                pygame.draw.line(pantalla, w_color, (px, py), (px + dx, py - dy), 2)

# ======================================================
# VARIABLES DE LA SIMULACIÓN
# ======================================================

vehiculos = []
gotas = []
semaforo = None

# ======================================================
# REINICIAR SIMULACIÓN
# ======================================================

def reiniciar_simulacion():
    config = obtener_config_avenida()

    if tipo_avenida == "ancha":
        cantidad_carriles = 3
    else:
        cantidad_carriles = 2
    
    global vehiculos
    global gotas
    global semaforo
    global particulas_salpicadura

    vehiculos = []
    particulas_salpicadura = []
    
    generar_posiciones_arboles()
    crear_fondo_estatico()

    # --- Generación inicial de vehículos en los 4 sentidos (tráfico en doble mano) ---
    
    # 1. Hacia la DERECHA (Carriles inferiores: carril 0 y carril 1)
    # Carril 0: y_carril = ALTO//2 + 25 | Carril 1: y_carril = ALTO//2 + 75
    for c_idx in range(cantidad_carriles):
        y_carril = ALTO//2 + 25 if c_idx == 0 else ALTO//2 + 75
        for i in range(7):
            # Posicionamiento escalonado hacia atrás para arrancar
            x = -150 - i * random.randint(180, 290)
            vehiculos.append(Vehiculo(x, y_carril, "derecha", c_idx))

    # 2. Hacia la IZQUIERDA (Carriles superiores: carril 0 y carril 1)
    # Carril 0: y_carril = ALTO//2 - 55 | Carril 1: y_carril = ALTO//2 - 105
    for c_idx in range(cantidad_carriles):
        y_carril = ALTO//2 - 55 if c_idx == 0 else ALTO//2 - 105
        for i in range(7):
            x = ANCHO + 150 + i * random.randint(180, 290)
            vehiculos.append(Vehiculo(x, y_carril, "izquierda", c_idx))

    # 3. Hacia ABAJO (Carriles derechos: carril 0 y carril 1)
    # Carril 0: x_carril = ANCHO//2 + 25 | Carril 1: x_carril = ANCHO//2 + 75
    for c_idx in range(cantidad_carriles):
        x_carril = ANCHO//2 + 25 if c_idx == 0 else ANCHO//2 + 75
        for i in range(6):
            y = -150 - i * random.randint(200, 310)
            vehiculos.append(Vehiculo(x_carril, y, "abajo", c_idx))

    # 4. Hacia ARRIBA (Carriles izquierdos: carril 0 y carril 1)
    # Carril 0: x_carril = ANCHO//2 - 55 | Carril 1: x_carril = ANCHO//2 - 105
    for c_idx in range(cantidad_carriles):
        x_carril = ANCHO//2 - 55 if c_idx == 0 else ANCHO//2 - 105
        for i in range(6):
            y = ALTO + 150 + i * random.randint(200, 310)
            vehiculos.append(Vehiculo(x_carril, y, "arriba", c_idx))

    # Gotas de lluvia
    gotas = []
    if clima == "lluvia":
        for _ in range(400):  # Más gotas para mayor densidad visual
            gotas.append([
                random.randint(0, ANCHO),
                random.randint(0, ALTO),
                random.randint(10, 15)  # Velocidad de caída
            ])

    semaforo = Semaforo()

# ======================================================
# MENÚ CON ESTÉTICA PREMIUM
# ======================================================

def menu():
    global clima
    global tipo_avenida

    boton_seco = pygame.Rect(ANCHO//2 - 200, 280, 400, 70)
    boton_lluvia = pygame.Rect(ANCHO//2 - 200, 380, 400, 70)
    boton_estrecha = pygame.Rect(ANCHO//2 - 200, 480, 190, 60)
    boton_ancha = pygame.Rect(ANCHO//2 + 10, 480, 190, 60)

    boton_iniciar = pygame.Rect(ANCHO//2 - 200, 560, 400, 70)

    # Generar algunos autos decorativos flotando de fondo en el menú
    autos_menu = []
    for _ in range(12):
        autos_menu.append({
            "x": random.randint(-100, ANCHO),
            "y": random.randint(0, ALTO),
            "color": random.choice([(0,120,255), (220,120,20), (230,220,0), (100,200,80), (240,80,80)]),
            "speed": random.uniform(1.5, 3.5),
            "w": random.randint(45, 80),
            "h": random.randint(25, 35)
        })

    while True:
        mouse = pygame.mouse.get_pos()
        pantalla.fill((22, 28, 36)) # Color oscuro azulado premium

        # BOTÓN ESTRECHA
        color_estrecha = (70, 70, 70)

        if tipo_avenida == "estrecha":
            color_estrecha = (180, 120, 40)

        if boton_estrecha.collidepoint(mouse):
            color_estrecha = (220, 150, 50)

        pygame.draw.rect(pantalla, color_estrecha, boton_estrecha, border_radius=12)

        txt = font.render("Av. Estrecha", True, BLANCO)
        pantalla.blit(txt, (boton_estrecha.x + 25, boton_estrecha.y+18))


        # BOTÓN ANCHA
        color_ancha = (70, 70, 70)

        if tipo_avenida == "ancha":
            color_ancha = (50, 120, 220)

        if boton_ancha.collidepoint(mouse):
            color_ancha = (70, 150, 255)
        pygame.draw.rect(pantalla, color_ancha, boton_ancha, border_radius=12)

        txt = font.render("Av. Ancha", True, BLANCO)
        pantalla.blit(txt, (boton_ancha.x + 35, boton_ancha.y + 18))

        # Dibujar coches decorativos difuminados en el fondo
        for c in autos_menu:
            c["x"] += c["speed"]
            if c["x"] > ANCHO + 100:
                c["x"] = -100
                c["y"] = random.randint(0, ALTO)
            
            # Autos de fondo semi-transparentes
            draw_rect_alpha(pantalla, (c["color"][0], c["color"][1], c["color"][2], 30), 
                            (int(c["x"]), c["y"], c["w"], c["h"]), border_radius=5)

        # Título principal con sombra
        title_shadow = font_large.render("SIMULADOR DE TRÁFICO", True, (30, 15, 20))
        title_text = font_large.render("SIMULADOR DE TRÁFICO", True, BLANCO)
        pantalla.blit(title_shadow, (ANCHO//2 - 222, 142))
        pantalla.blit(title_text, (ANCHO//2 - 222, 140))
        
        subtitle_text = font_small.render("Mejoras de Superficie, Clima y Físicas de Tránsito Inteligente", True, (150, 170, 190))
        pantalla.blit(subtitle_text, (ANCHO//2 - 235, 190))

        # BOTÓN SECO
        color_seco = (60, 68, 80)
        border_seco = 1
        if clima == "seco":
            color_seco = (40, 110, 200)
            border_seco = 3
        if boton_seco.collidepoint(mouse):
            color_seco = (50, 130, 230)
            
        pygame.draw.rect(pantalla, color_seco, boton_seco, border_radius=12)
        if border_seco > 1 or boton_seco.collidepoint(mouse):
            pygame.draw.rect(pantalla, BLANCO, boton_seco, width=2, border_radius=12)
        
        btn_y=300
        texto_seco = font.render("Clima Seco", True, BLANCO)
        pantalla.blit(texto_seco, (ANCHO//2 - 50, btn_y))

        # BOTÓN LLUVIA
        color_lluvia = (60, 68, 80)
        border_lluvia = 1
        if clima == "lluvia":
            color_lluvia = (30, 160, 140)
            border_lluvia = 3
        if boton_lluvia.collidepoint(mouse):
            color_lluvia = (40, 185, 160)
            
        pygame.draw.rect(pantalla, color_lluvia, boton_lluvia, border_radius=12)
        if border_lluvia > 1 or boton_lluvia.collidepoint(mouse):
            pygame.draw.rect(pantalla, BLANCO, boton_lluvia, width=2, border_radius=12)
            
        texto_lluvia = font.render("Clima Lluvioso", True, BLANCO)
        pantalla.blit(texto_lluvia, (ANCHO//2 - 68, btn_y + 100))

        # BOTÓN INICIAR
        color_inicio = (38, 143, 65)
        if boton_iniciar.collidepoint(mouse):
            color_inicio = (46, 179, 81)
            
        pygame.draw.rect(pantalla, color_inicio, boton_iniciar, border_radius=12)
        if boton_iniciar.collidepoint(mouse):
            pygame.draw.rect(pantalla, BLANCO, boton_iniciar, width=2, border_radius=12)
            
        texto_inicio = font.render("INICIAR SIMULACIÓN", True, BLANCO)
        pantalla.blit(texto_inicio, (ANCHO//2 - 100, 580))

        # Pie de página descriptivo
        footer = font_small.render("[Esc] Volver al Menú   |   Físicas Inteligentes IDM activas   |   Doble Mano y Sobrepasos", True, (110, 120, 135))
        pantalla.blit(footer, (ANCHO//2 - 280, 740))

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boton_seco.collidepoint(mouse):
                    clima = "seco"
                if boton_lluvia.collidepoint(mouse):
                    clima = "lluvia"
                if boton_estrecha.collidepoint(mouse):
                    tipo_avenida = "estrecha"
                if boton_ancha.collidepoint(mouse):
                    tipo_avenida = "ancha"
                if boton_iniciar.collidepoint(mouse):
                    return

# ======================================================
# FUNCIONES AUXILIARES DE SPAWN Y BUCLE PRINCIPAL
# ======================================================

def intentar_spawnear_vehiculo():
    """Busca spawnear un vehículo en un carril y dirección libre."""
    direcciones = ["derecha", "izquierda", "abajo", "arriba"]
    dir_random = random.choice(direcciones)
    if tipo_avenida == "ancha":
        carril_random = random.choice([0, 1, 2])
    else:
        carril_random = random.choice([0, 1])
    
    # Chequear si el área de spawn está libre de otros vehículos
    espacio_libre = True
    for v in vehiculos:
        if v.direccion == dir_random and (v.carril_actual == carril_random or v.carril_target == carril_random):
            if dir_random == "derecha" and v.x < 120:
                espacio_libre = False
            elif dir_random == "izquierda" and v.x > ANCHO - 120:
                espacio_libre = False
            elif dir_random == "abajo" and v.y < 120:
                espacio_libre = False
            elif dir_random == "arriba" and v.y > ALTO - 120:
                espacio_libre = False
                
    if espacio_libre:
        if dir_random == "derecha":
            x = -random.randint(150, 300)
            y = ALTO//2 + 25 if carril_random == 0 else ALTO//2 + 75
        elif dir_random == "izquierda":
            x = ANCHO + random.randint(150, 300)
            y = ALTO//2 - 55 if carril_random == 0 else ALTO//2 - 105
        elif dir_random == "abajo":
            x = ANCHO//2 + 25 if carril_random == 0 else ANCHO//2 + 75
            y = -random.randint(150, 300)
        else: # arriba
            x = ANCHO//2 - 55 if carril_random == 0 else ANCHO//2 - 105
            y = ALTO + random.randint(150, 300)
            
        vehiculos.append(Vehiculo(x, y, dir_random, carril_random))

# Inicialización de botones del panel lateral interactivo (HUD integrado)
panel_y = 550
panel_x=75
btn_ancha = BotonUI(panel_x+ 2, panel_y +100, 140, 30, "AV. Ancha", (150, 40, 40), (190, 60, 60))
btn_estrecha = BotonUI(panel_x+ 162, panel_y +100, 140, 30, "Av. Estrecha", (150, 40, 40), (190, 60, 60))
btn_pausa = BotonUI(panel_x, panel_y, 140, 30, "PAUSAR", (150, 40, 40), (190, 60, 60))
btn_clima_seco = BotonUI(panel_x + 160, panel_y, 75, 30, "SECO", (60, 68, 80), (80, 90, 110))
btn_clima_lluvia = BotonUI(panel_x + 245, panel_y, 75, 30, "LLUVIA", (60, 68, 80), (80, 90, 110))

btn_force_change = BotonUI(panel_x, panel_y+50, 140, 30, "FORZAR CAMBIO", (40, 110, 200), (50, 130, 230))
btn_reiniciar = BotonUI(panel_x + 160, panel_y+50, 160, 30, "REINICIAR SIM.", (38, 143, 65), (46, 179, 81))

btn_menu = BotonUI(ANCHO - 400, panel_y+100, 320, 30, "VOLVER AL MENÚ PRINCIPAL", (60, 68, 80), (80, 90, 110))

# Ajustables


btn_caudal_dec = BotonUI(105, panel_y + 150, 25, 25, "-", (40, 45, 55), (60, 68, 80))
btn_caudal_inc = BotonUI(135, panel_y + 150, 25, 25, "+", (40, 45, 55), (60, 68, 80))

btn_vel_dec = BotonUI(215, panel_y + 150, 25, 25, "-", (40, 45, 55), (60, 68, 80))
btn_vel_inc = BotonUI(245, panel_y + 150, 25, 25, "+", (40, 45, 55), (60, 68, 80))

btn_dur_dec = BotonUI(315, panel_y + 150, 25, 25, "-", (40, 45, 55), (60, 68, 80))
btn_dur_inc = BotonUI(345, panel_y + 150, 25, 25, "+", (40, 45, 55), (60, 68, 80))

# Iniciar simulación
menu()
reiniciar_simulacion()

while True:
    clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = False

    # 1. Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                menu()
                reiniciar_simulacion()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_clicked = True

    # 2. Controlar Clics de Botones del Panel
    if btn_pausa.clickeado(mouse_pos, mouse_clicked):
        pausado = not pausado
        
    if btn_clima_seco.clickeado(mouse_pos, mouse_clicked):
        if clima != "seco":
            clima = "seco"
            crear_fondo_estatico()
            gotas = []
            
    if btn_clima_lluvia.clickeado(mouse_pos, mouse_clicked):
        if clima != "lluvia":
            clima = "lluvia"
            crear_fondo_estatico()
            # Generar lluvia
            gotas = []
            for _ in range(400):
                gotas.append([
                    random.randint(0, ANCHO),
                    random.randint(0, ALTO),
                    random.randint(10, 15)
                ])
                
    if btn_force_change.clickeado(mouse_pos, mouse_clicked):
        if semaforo.horizontal in ["verde", "amarillo"]:
            semaforo.horizontal = "rojo"
            semaforo.vertical = "verde"
        else:
            semaforo.horizontal = "verde"
            semaforo.vertical = "rojo"
        semaforo.timer = int(duracion_semaforo_segundos * 60)
        
    if btn_reiniciar.clickeado(mouse_pos, mouse_clicked):
        reiniciar_simulacion()
        
    if btn_menu.clickeado(mouse_pos, mouse_clicked):
        menu()
        reiniciar_simulacion()
        
    if btn_caudal_dec.clickeado(mouse_pos, mouse_clicked):
        target_vehiculos = max(8, target_vehiculos - 2)
        
    if btn_caudal_inc.clickeado(mouse_pos, mouse_clicked):
        target_vehiculos = min(60, target_vehiculos + 2)
        
    if btn_vel_dec.clickeado(mouse_pos, mouse_clicked):
        velocidad_multiplicador = max(0.2, velocidad_multiplicador - 0.2)
        
    if btn_vel_inc.clickeado(mouse_pos, mouse_clicked):
        velocidad_multiplicador = min(3.0, velocidad_multiplicador + 0.2)
        
    if btn_dur_dec.clickeado(mouse_pos, mouse_clicked):
        duracion_semaforo_segundos = max(2.0, duracion_semaforo_segundos - 1.0)
        
    if btn_dur_inc.clickeado(mouse_pos, mouse_clicked):
        duracion_semaforo_segundos = min(20.0, duracion_semaforo_segundos + 1.0)

    # 3. Lógica física (solo si no está pausado)
    if not pausado:
        # Actualizar semáforos
        semaforo.actualizar()
        
        # Actualizar salpicaduras
        actualizar_y_dibujar_salpicaduras()
        
        # Mover vehículos
        for v in vehiculos:
            v.mover(semaforo, vehiculos)
            
        # Lluvia cayendo
        if clima == "lluvia":
            for gota in gotas:
                gota[1] += gota[2]
                if gota[1] > ALTO:
                    gota[0] = random.randint(0, ANCHO)
                    gota[1] = -15
                    gota[2] = random.randint(10, 15)

    # 4. Control de cantidad (caudal) de vehículos
    # Eliminar autos excedentes que salen de pantalla
    vehiculos_nuevos = []
    for v in vehiculos:
        fuera = False
        if v.direccion == "derecha" and v.x > ANCHO + 120:
            fuera = True
        elif v.direccion == "izquierda" and v.x < -120:
            fuera = True
        elif v.direccion == "abajo" and v.y > ALTO + 120:
            fuera = True
        elif v.direccion == "arriba" and v.y < -120:
            fuera = True
            
        if fuera:
            # Respawnear sólo si no excedemos la cantidad objetivo
            if len(vehiculos) - (len(vehiculos) - len(vehiculos_nuevos)) <= target_vehiculos:
                v.carril_actual = random.choice([0, 1])
                v.carril_target = v.carril_actual
                v.velocidad = v.velocidad_max
                if v.direccion == "derecha":
                    v.x = -random.randint(150, 450)
                elif v.direccion == "izquierda":
                    v.x = ANCHO + random.randint(150, 450)
                elif v.direccion == "abajo":
                    v.y = -random.randint(150, 450)
                else: # arriba
                    v.y = ALTO + random.randint(150, 450)
                vehiculos_nuevos.append(v)
            # De lo contrario, se elimina (no se añade a la lista)
        else:
            vehiculos_nuevos.append(v)
    vehiculos = vehiculos_nuevos

    # Si faltan vehículos para el objetivo, spawnear nuevos de forma espaciada
    if not pausado and len(vehiculos) < target_vehiculos and pygame.time.get_ticks() % 15 == 0:
        intentar_spawnear_vehiculo()

    # 5. Dibujar Fondo y Carretera
    pantalla.blit(fondo_estatico, (0, 0))
        # Oscurecimiento de calles (para dar efecto mojado)
        # Re-dibujamos calles semi-transparentes oscuras encima de las del fondo
    draw_rect_alpha(pantalla, (0, 0, 0, 30), (0, ALTO//2 - 120, ANCHO, 240))
    draw_rect_alpha(pantalla, (0, 0, 0, 30), (ANCHO//2 - 120, 0, 240, ALTO))

    # 3. Actualizar semáforos y dibujarlos
    semaforo.actualizar()
    semaforo.dibujar()

    # 4. Actualizar partículas de salpicadura de agua
    actualizar_y_dibujar_salpicaduras()

    # 5. Mover y actualizar vehículos
    # Recorremos y movemos todos los vehículos con el modelo de físicas IDM y cambio de carril
    for v in vehiculos:
        v.mover(semaforo, vehiculos)

    # 6. Dibujar vehículos en pantalla
    for v in vehiculos:
        v.dibujar()

    # 7. Reaparecer vehículos fuera del mapa (Ciclo continuo e infinito)
    # Al salir, se reposicionan al extremo contrario con velocidades aleatorias para dinamismo
    for v in vehiculos:
        if v.direccion == "derecha" and v.x > ANCHO + 120:
            v.x = -random.randint(150, 450)
            v.carril_actual = random.choice([0, 1])
            v.carril_target = v.carril_actual
            v.velocidad = v.velocidad_max
        elif v.direccion == "izquierda" and v.x < -120:
            v.x = ANCHO + random.randint(150, 450)
            v.carril_actual = random.choice([0, 1])
            v.carril_target = v.carril_actual
            v.velocidad = v.velocidad_max
        elif v.direccion == "abajo" and v.y > ALTO + 120:
            v.y = -random.randint(150, 450)
            v.carril_actual = random.choice([0, 1])
            v.carril_target = v.carril_actual
            v.velocidad = v.velocidad_max
        elif v.direccion == "arriba" and v.y < -120:
            v.y = ALTO + random.randint(150, 450)
            v.carril_actual = random.choice([0, 1])
            v.carril_target = v.carril_actual
            v.velocidad = v.velocidad_max

    # 8. Clima Lluvia (Efecto visual de gotas cayendo)
    if clima == "lluvia":
        for gota in gotas:
            # Gotas como líneas azules semi-transparentes cayendo en diagonal
            pygame.draw.line(
                pantalla,
                (170, 180, 240, 180),
                (gota[0], gota[1]),
                (gota[0] + 3, gota[1] + 12),
                1
            )
            # Caída física
            gota[1] += gota[2]
            # Si toca el suelo, reaparece arriba
            if gota[1] > ALTO:
                gota[0] = random.randint(0, ANCHO)
                gota[1] = -15
                gota[2] = random.randint(10, 15)

    # 9. Panel de Información Superior (HUD Moderno)
    # Dibujar panel translúcido
    draw_rect_alpha(pantalla, (20, 25, 35, 200), (10, 10, 310, 105), border_radius=8)
    pygame.draw.rect(pantalla, (80, 90, 110), (10, 10, 310, 105), width=1, border_radius=8)

    # Textos informativos
    clima_txt = "Lluvioso (Vel. reducida 25%)" if clima == "lluvia" else "Seco (Vel. nominal)"
    pantalla.blit(font_small.render(f"Clima: {clima_txt}", True, (230, 240, 255)), (22, 18))
    
    # Calcular velocidad promedio de los autos en pantalla
    vels = [v.velocidad * (60/10) for v in vehiculos if v.x > 0 and v.x < ANCHO and v.y > 0 and v.y < ALTO] # Escala px/frame a km/h ficticia
    avg_vel = sum(vels)/len(vels) if vels else 0.0
    
    # Contar cuántos autos están parados (velocidad < 0.2) para medir congestión
    detenidos = sum(1 for v in vehiculos if v.velocidad < 0.2 and v.x > 0 and v.x < ANCHO and v.y > 0 and v.y < ALTO)
    c_level = "Alta" if detenidos > 6 else ("Moderada" if detenidos > 2 else "Baja")
    c_color = ROJO_ENCENDIDO if c_level == "Alta" else (AMARILLO_ENCENDIDO if c_level == "Moderada" else VERDE_ENCENDIDO)

    pantalla.blit(font_small.render(f"Velocidad Promedio: {avg_vel:.1f} km/h", True, BLANCO), (22, 40))
    pantalla.blit(font_small.render(f"Vehículos Detenidos: {detenidos}", True, BLANCO), (22, 62))
    
    pantalla.blit(font_small.render("Congestión:", True, BLANCO), (22, 84))
    pantalla.blit(font_small.render(c_level, True, c_color), (115, 84))

    # Panel inferior translúcido para agrupar los botones interactivos
    draw_rect_alpha(pantalla, (20, 25, 35, 200), (65, 540, 340, 185), border_radius=8)
    pygame.draw.rect(pantalla, (80, 90, 110), (65, 540, 340, 185), width=1, border_radius=8)

    # Dibujar botones del panel
    btn_ancha.dibujar(pantalla, mouse_pos)
    btn_estrecha.dibujar(pantalla, mouse_pos)
    btn_pausa.dibujar(pantalla, mouse_pos)
    btn_clima_seco.dibujar(pantalla, mouse_pos)
    btn_clima_lluvia.dibujar(pantalla, mouse_pos)
    btn_force_change.dibujar(pantalla, mouse_pos)
    btn_reiniciar.dibujar(pantalla, mouse_pos)
    btn_menu.dibujar(pantalla, mouse_pos)
    
    btn_caudal_dec.dibujar(pantalla, mouse_pos)
    btn_caudal_inc.dibujar(pantalla, mouse_pos)
    btn_vel_dec.dibujar(pantalla, mouse_pos)
    btn_vel_inc.dibujar(pantalla, mouse_pos)
    btn_dur_dec.dibujar(pantalla, mouse_pos)
    btn_dur_inc.dibujar(pantalla, mouse_pos)

    # Etiquetas de texto para los botones +/-
    pantalla.blit(font_small.render(f"Autos: {target_vehiculos}", True, BLANCO), (90, 688))
    pantalla.blit(font_small.render(f"Vel: {velocidad_multiplicador:.1f}x", True, BLANCO), (210, 688))
    pantalla.blit(font_small.render(f"Sem: {duracion_semaforo_segundos:.0f}s", True, BLANCO), (310, 688))


    # Control de Semáforo en HUD
    # Estado H y V
    col_h = VERDE_ENCENDIDO if semaforo.horizontal == "verde" else (AMARILLO_ENCENDIDO if semaforo.horizontal == "amarillo" else ROJO_ENCENDIDO)
    col_v = VERDE_ENCENDIDO if semaforo.vertical == "verde" else (AMARILLO_ENCENDIDO if semaforo.vertical == "amarillo" else ROJO_ENCENDIDO)
    
    draw_rect_alpha(pantalla, (20, 25, 35, 200), (ANCHO - 220, 10, 210, 80), border_radius=8)
    pygame.draw.rect(pantalla, (80, 90, 110), (ANCHO - 220, 10, 210, 80), width=1, border_radius=8)
    
    pantalla.blit(font_small.render("Semáforo H (Est/Oest):", True, BLANCO), (ANCHO - 208, 18))
    pygame.draw.circle(pantalla, col_h, (ANCHO - 35, 26), 6)
    
    pantalla.blit(font_small.render("Semáforo V (Nort/Sur):", True, BLANCO), (ANCHO - 208, 48))
    pygame.draw.circle(pantalla, col_v, (ANCHO - 35, 56), 6)

    # Actualizar pantalla
    pygame.display.flip()
