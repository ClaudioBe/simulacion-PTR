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
# PARÁMETROS DE LA SIMULACIÓN Y CLIMA
# ======================================================

clima = "seco"  # "seco" o "lluvia"
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
    
    calle_x_min = ANCHO // 2 - 125
    calle_x_max = ANCHO // 2 + 125
    calle_y_min = ALTO // 2 - 125
    calle_y_max = ALTO // 2 + 125

    intentos = 0
    while len(posiciones_arboles) < 22 and intentos < 200:
        tx = random.randint(40, ANCHO - 40)
        ty = random.randint(40, ALTO - 40)
        
        fuera_h = (ty < calle_y_min - 30) or (ty > calle_y_max + 30)
        fuera_v = (tx < calle_x_min - 30) or (tx > calle_x_max + 30)
        
        if fuera_h and fuera_v:
            demasiado_cerca = False
            for ax, ay, ar in posiciones_arboles:
                if math.hypot(tx - ax, ty - ay) < 65:
                    demasiado_cerca = True
                    break
            if not demasiado_cerca:
                radio = random.randint(22, 35)
                posiciones_arboles.append((tx, ty, radio))
        intentos += 1

def crear_fondo_estatico():
    """Dibuja e inicializa el fondo estático con texturas y carreteras."""
    global fondo_estatico
    fondo_estatico = pygame.Surface((ANCHO, ALTO))
    
    fondo_estatico.fill(PASTO_COLOR)
    
    for _ in range(35000):
        rx = random.randint(0, ANCHO - 1)
        ry = random.randint(0, ALTO - 1)
        
        calle_x_min = ANCHO // 2 - 120
        calle_x_max = ANCHO // 2 + 120
        calle_y_min = ALTO // 2 - 120
        calle_y_max = ALTO // 2 + 120
        
        if (rx < calle_x_min or rx > calle_x_max) and (ry < calle_y_min or ry > calle_y_max):
            fondo_estatico.set_at((rx, ry), PASTO_DETALLE)

    color_asfalto = CALLE_MOJADA if clima == "lluvia" else CALLE_COLOR
    
    pygame.draw.rect(fondo_estatico, color_asfalto, (0, ALTO//2 - 120, ANCHO, 240))
    pygame.draw.rect(fondo_estatico, color_asfalto, (ANCHO//2 - 120, 0, 240, ALTO))
    
    for _ in range(28000):
        rx = random.randint(0, ANCHO - 1)
        ry = random.randint(ALTO//2 - 120, ALTO//2 + 119)
        c = fondo_estatico.get_at((rx, ry))
        variation = random.randint(-8, 8)
        nr = max(0, min(255, c.r + variation))
        ng = max(0, min(255, c.g + variation))
        nb = max(0, min(255, c.b + variation))
        fondo_estatico.set_at((rx, ry), (nr, ng, nb))

        rx = random.randint(ANCHO//2 - 120, ANCHO//2 + 119)
        ry = random.randint(0, ALTO - 1)
        c = fondo_estatico.get_at((rx, ry))
        variation = random.randint(-8, 8)
        nr = max(0, min(255, c.r + variation))
        ng = max(0, min(255, c.g + variation))
        nb = max(0, min(255, c.b + variation))
        fondo_estatico.set_at((rx, ry), (nr, ng, nb))

    for y in range(ALTO//2 - 110, ALTO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 165, y, 35, 10))
    for y in range(ALTO//2 - 110, ALTO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 130, y, 35, 10))
    for x in range(ANCHO//2 - 110, ANCHO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 - 165, 10, 35))
    for x in range(ANCHO//2 - 110, ANCHO//2 + 110, 20):
        pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 + 130, 10, 35))

    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 180, ALTO//2, 8, 120))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 172, ALTO//2 - 120, 8, 120))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2, ALTO//2 - 180, 120, 8))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 120, ALTO//2 + 172, 120, 8))

    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (0, ALTO//2 - 3, ANCHO, 2))
    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (0, ALTO//2 + 1, ANCHO, 2))
    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (ANCHO//2 - 3, 0, 2, ALTO))
    pygame.draw.rect(fondo_estatico, LINEA_AMARILLA, (ANCHO//2 + 1, 0, 2, ALTO))

    pygame.draw.rect(fondo_estatico, color_asfalto, (ANCHO//2 - 120, ALTO//2 - 120, 240, 240))
    for _ in range(5000):
        rx = random.randint(ANCHO//2 - 120, ANCHO//2 + 119)
        ry = random.randint(ALTO//2 - 120, ALTO//2 + 119)
        c = fondo_estatico.get_at((rx, ry))
        variation = random.randint(-8, 8)
        nr = max(0, min(255, c.r + variation))
        ng = max(0, min(255, c.g + variation))
        nb = max(0, min(255, c.b + variation))
        fondo_estatico.set_at((rx, ry), (nr, ng, nb))

    for x in range(0, ANCHO, 50):
        if x < ANCHO//2 - 180 or x > ANCHO//2 + 180:
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 + 58, 20, 4))
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (x, ALTO//2 - 62, 20, 4))

    for y in range(0, ALTO, 50):
        if y < ALTO//2 - 180 or y > ALTO//2 + 180:
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 58, y, 4, 20))
            pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 62, y, 4, 20))

    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 380, ALTO//2 + 58, 200, 4))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 180, ALTO//2 - 62, 200, 4))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 + 58, ALTO//2 - 380, 4, 200))
    pygame.draw.rect(fondo_estatico, LINEA_BLANCA, (ANCHO//2 - 62, ALTO//2 + 180, 4, 200))

    for tx, ty, radio in posiciones_arboles:
        draw_circle_alpha(fondo_estatico, (10, 25, 10, 90), (tx + 8, ty + 8), radio)
        pygame.draw.circle(fondo_estatico, (100, 60, 20), (tx, ty), max(4, radio // 5))
        pygame.draw.circle(fondo_estatico, (34, 139, 34), (tx, ty), radio)
        pygame.draw.circle(fondo_estatico, (46, 175, 46), (tx - 3, ty - 3), int(radio * 0.8))
        pygame.draw.circle(fondo_estatico, (60, 200, 60), (tx - 5, ty - 5), int(radio * 0.55))

# ======================================================
# CLASE SEMÁFORO
# ======================================================

class Semaforo:
    def __init__(self):
        self.horizontal = "verde"
        self.vertical = "rojo"
        self.timer = int(duracion_semaforo_segundos * 60)
        self.amarillo_duration = int(min(75, duracion_semaforo_segundos * 0.20 * 60))

    def actualizar(self):
        self.timer -= 1
        self.amarillo_duration = int(min(75, duracion_semaforo_segundos * 0.20 * 60))

        if self.horizontal == "verde" and self.timer <= self.amarillo_duration:
            self.horizontal = "amarillo"
        if self.vertical == "verde" and self.timer <= self.amarillo_duration:
            self.vertical = "amarillo"

        if self.timer <= 0:
            if self.horizontal in ["verde", "amarillo"]:
                self.horizontal = "rojo"
                self.vertical = "verde"
            else:
                self.horizontal = "verde"
                self.vertical = "rojo"
            self.timer = int(duracion_semaforo_segundos * 60)

    def dibujar(self):
        sem_configs = [
            (ANCHO//2 - 150, ALTO//2 + 150, "vertical", self.horizontal, "DERECHA"),
            (ANCHO//2 + 150, ALTO//2 - 150, "vertical", self.horizontal, "IZQUIERDA"),
            (ANCHO//2 - 150, ALTO//2 - 150, "horizontal", self.vertical, "ABAJO"),
            (ANCHO//2 + 150, ALTO//2 + 150, "horizontal", self.vertical, "ARRIBA")
        ]

        for x, y, orientacion, estado, nombre in sem_configs:
            pygame.draw.rect(pantalla, GRIS_POSTE, (x - 4, y - 4, 8, 8))
            
            if orientacion == "vertical":
                w, h = 24, 60
                caja_rect = pygame.Rect(x - w//2, y - h//2, w, h)
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
                c_rojo = ROJO_ENCENDIDO if estado == "rojo" else ROJO_APAGADO
                c_amar = AMARILLO_ENCENDIDO if estado == "amarillo" else AMARILLO_APAGADO
                c_verd = VERDE_ENCENDIDO if estado == "verde" else VERDE_APAGADO
                
                luces = [
                    (c_rojo, (x - 18, y)),
                    (c_amar, (x, y)),
                    (c_verd, (x + 18, y))
                ]
                
            pygame.draw.rect(pantalla, NEGRO, caja_rect, border_radius=4)
            pygame.draw.rect(pantalla, GRIS_OSCURO, caja_rect, width=2, border_radius=4)
            
            for color, pos in luces:
                pygame.draw.circle(pantalla, color, pos, 7)
                if color in [ROJO_ENCENDIDO, AMARILLO_ENCENDIDO, VERDE_ENCENDIDO]:
                    draw_circle_alpha(pantalla, (color[0], color[1], color[2], 55), pos, 15)

# ======================================================
# ZONA DE INTERSECCIÓN
# ======================================================

zona_interseccion = pygame.Rect(ANCHO//2 - 120, ALTO//2 - 120, 240, 240)

# ======================================================
# PARTICULAS DE SALPICADURAS DE AGUA (LLUVIA)
# ======================================================

particulas_salpicadura = []

def actualizar_y_dibujar_salpicaduras():
    """Actualiza y dibuja las salpicaduras de los neumáticos en la calle mojada."""
    global particulas_salpicadura
    nuevas_particulas = []
    for p in particulas_salpicadura:
        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 1
        
        if p[4] > 0:
            alfa = int(120 * (p[4] / p[5]))
            draw_circle_alpha(pantalla, (200, 200, 255, alfa), (int(p[0]), int(p[1])), random.randint(1, 3))
            nuevas_particulas.append(p)
            
    particulas_salpicadura = nuevas_particulas

def spawn_salpicadura(x, y, direccion):
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
        else:
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
        self.ancho = datos["ancho"]
        self.alto = datos["alto"]
        
        vel_rango = datos["velocidad"]
        vel_random = random.uniform(vel_rango[0], vel_rango[1])
            
        self.velocidad_base_max = vel_random
        self.velocidad_max = vel_random
        self.velocidad = vel_random
        self.acel_max = datos["acel"]
        self.decel_max = datos["decel"]

        self.x = x
        self.y = y
        self.direccion = direccion
        
        self.carril_actual = carril_index
        self.carril_target = carril_index
        self.tiempo_cambio = 0
        self.y_inicio = y
        self.x_inicio = x
        
        self.decel_activa = False
        self.velocidad_anterior = vel_random
        
        self.wiper_angle = 0
        self.wiper_direction = 1

    def obtener_rect(self):
        if self.direccion in ["derecha", "izquierda"]:
            return pygame.Rect(self.x, self.y, self.ancho, self.alto)
        else:
            return pygame.Rect(self.x, self.y, self.alto, self.ancho)

    def obtener_coordenadas_carril(self, direccion, carril_idx):
        if direccion == "derecha":
            carriles_derecha = [ALTO//2 + 25, ALTO//2 + 75]
            return carriles_derecha[carril_idx]
        elif direccion == "izquierda":
            carriles_izquierda = [ALTO//2 - 55, ALTO//2 - 105]
            return carriles_izquierda[carril_idx]
        elif direccion == "abajo":
            carriles_abajo = [ANCHO//2 + 25, ANCHO//2 + 75]
            return carriles_abajo[carril_idx]
        else:
            carriles_arriba = [ANCHO//2 - 55, ANCHO//2 - 105]
            return carriles_arriba[carril_idx]

    def evaluar_cambio_carril(self, vehiculos):
        if self.tiempo_cambio > 0:
            return

        dist_interseccion = 1000
        if self.direccion == "derecha":
            dist_interseccion = (ANCHO//2 - 180) - (self.x + self.ancho)
        elif self.direccion == "izquierda":
            dist_interseccion = self.x - (ANCHO//2 + 180)
        elif self.direccion == "abajo":
            dist_interseccion = (ALTO//2 - 180) - (self.y + self.ancho)
        elif self.direccion == "arriba":
            dist_interseccion = self.y - (ALTO//2 + 180)

        if dist_interseccion < 220 or dist_interseccion < -80:
            return

        vehiculo_adelante = self.buscar_vehiculo_adelante(vehiculos)
        incentivo = False
        if vehiculo_adelante:
            dist = self.obtener_distancia_a(vehiculo_adelante)
            if dist < 160 and vehiculo_adelante.velocidad < self.velocidad_max * 0.85:
                incentivo = True

        if not incentivo:
            return

        carril_alternativo = 1 - self.carril_actual
        seguro = True
        
        vehiculos_destino = []
        for otro in vehiculos:
            if otro == self or otro.direccion != self.direccion:
                continue
            if otro.carril_actual == carril_alternativo or otro.carril_target == carril_alternativo:
                vehiculos_destino.append(otro)

        cerca_adelante = None
        cerca_atras = None
        min_dist_adelante = 99999
        min_dist_atras = 99999

        for otro in vehiculos_destino:
            dist = self.obtener_distancia_relativa(otro)
            if dist > 0:
                if dist < min_dist_adelante:
                    min_dist_adelante = dist
                    cerca_adelante = otro
            else:
                abs_dist = abs(dist)
                if abs_dist < min_dist_atras:
                    min_dist_atras = abs_dist
                    cerca_atras = otro

        safe_gap_front = 90.0
        safe_gap_back = 90.0

        if cerca_adelante and min_dist_adelante < safe_gap_front:
            seguro = False
        if cerca_atras and min_dist_atras < safe_gap_back:
            if cerca_atras.velocidad > self.velocidad + 1:
                seguro = False
            seguro = seguro and (min_dist_atras > safe_gap_back + (cerca_atras.velocidad * 10))

        if seguro:
            self.carril_target = carril_alternativo
            self.tiempo_cambio = 45
            if self.direccion in ["derecha", "izquierda"]:
                self.y_inicio = self.y
            else:
                self.x_inicio = self.x

    def obtener_distancia_relativa(self, otro):
        if self.direccion == "derecha":
            return otro.x - self.x
        elif self.direccion == "izquierda":
            return self.x - otro.x
        elif self.direccion == "abajo":
            return otro.y - self.y
        else:
            return self.y - otro.y

    def obtener_distancia_a(self, otro):
        if self.direccion == "derecha":
            return otro.x - (self.x + self.ancho)
        elif self.direccion == "izquierda":
            return self.x - (otro.x + otro.ancho)
        elif self.direccion == "abajo":
            return otro.y - (self.y + self.ancho)
        else:
            return self.y - (otro.y + otro.ancho)

    def buscar_vehiculo_adelante(self, vehiculos):
        coche_lider = None
        min_dist = 999999
        
        for otro in vehiculos:
            if otro == self or otro.direccion != self.direccion:
                continue
                
            mismo_carril = False
            if self.tiempo_cambio > 0:
                mismo_carril = (otro.carril_actual == self.carril_target or otro.carril_target == self.carril_target)
            else:
                mismo_carril = (otro.carril_actual == self.carril_actual or otro.carril_target == self.carril_actual)
            
            dist_lateral = 0
            if self.direccion in ["derecha", "izquierda"]:
                dist_lateral = abs(otro.y - self.y)
            else:
                dist_lateral = abs(otro.x - self.x)
                
            mismo_carril = mismo_carril or (dist_lateral < 36)

            if mismo_carril:
                dist = self.obtener_distancia_relativa(otro)
                if dist > 0:
                    net_dist = self.obtener_distancia_a(otro)
                    if net_dist < min_dist:
                        min_dist = net_dist
                        coche_lider = otro
                        
        return coche_lider

    def mover(self, semaforo, vehiculos):
        w_factor = 0.75 if clima == "lluvia" else 1.0
        self.velocidad_max = self.velocidad_base_max * w_factor * velocidad_multiplicador
        self.velocidad_anterior = self.velocidad

        if self.tiempo_cambio > 0:
            self.tiempo_cambio -= 1
            progress = (45 - self.tiempo_cambio) / 45
            smooth_progress = 3 * progress**2 - 2 * progress**3
            coord_dest = self.obtener_coordenadas_carril(self.direccion, self.carril_target)
            
            if self.direccion in ["derecha", "izquierda"]:
                self.y = self.y_inicio + (coord_dest - self.y_inicio) * smooth_progress
            else:
                self.x = self.x_inicio + (coord_dest - self.x_inicio) * smooth_progress
                
            if self.tiempo_cambio == 0:
                self.carril_actual = self.carril_target
        else:
            if self.direccion in ["derecha", "izquierda"]:
                self.y = self.obtener_coordenadas_carril(self.direccion, self.carril_actual)
            else:
                self.x = self.obtener_coordenadas_carril(self.direccion, self.carril_actual)

        if pygame.time.get_ticks() % 15 == 0:
            self.evaluar_cambio_carril(vehiculos)

        lider = self.buscar_vehiculo_adelante(vehiculos)
        lider_dist = 999999
        lider_speed = 0
        if lider:
            lider_dist = self.obtener_distancia_a(lider)
            lider_speed = lider.velocidad

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

        if not crossed_stop_line:
            dist_to_light = 99999
            if self.direccion == "derecha":
                dist_to_light = stop_line - (self.x + self.ancho)
            elif self.direccion == "izquierda":
                dist_to_light = self.x - stop_line
            elif self.direccion == "abajo":
                dist_to_light = stop_line - (self.y + self.ancho)
            elif self.direccion == "arriba":
                dist_to_light = self.y - stop_line

            frenar_en_semaforo = False
            if luz_activa == "rojo":
                frenar_en_semaforo = True
            elif luz_activa == "amarillo":
                dist_frenado_seguro = (self.velocidad ** 2) / (2 * self.decel_max) + 20
                if dist_to_light > dist_frenado_seguro:
                    frenar_en_semaforo = True

            if frenar_en_semaforo:
                if dist_to_light < lider_dist:
                    lider_dist = max(5.0, dist_to_light)
                    lider_speed = 0

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

        if mi_rect_futuro.colliderect(zona_interseccion) and not self.obtener_rect().colliderect(zona_interseccion):
            for otro in vehiculos:
                if otro.direccion in ["derecha", "izquierda"] and self.direccion in ["abajo", "arriba"]:
                    if otro.obtener_rect().colliderect(zona_interseccion):
                        lider_dist = 15.0
                        lider_speed = 0
                        break
                elif otro.direccion in ["abajo", "arriba"] and self.direccion in ["derecha", "izquierda"]:
                    if otro.obtener_rect().colliderect(zona_interseccion):
                        lider_dist = 15.0
                        lider_speed = 0
                        break

        s0 = 35.0
        T_frames = 20.0
        a = self.acel_max
        b = self.decel_max
        v = self.velocidad
        v0 = self.velocidad_max

        acel = a * (1.0 - (v / v0) ** 4) if v0 > 0 else 0

        if lider_dist < 1000:
            s = max(2.0, lider_dist)
            dv = v - lider_speed
            s_star = s0 + v * T_frames + (v * dv) / (2 * ((a * b) ** 0.5))
            s_star = max(s0, s_star)
            interaction = (s_star / s) ** 2
            acel -= a * interaction

        acel = max(-1.6, acel)
        self.velocidad = max(0.0, min(v0, self.velocidad + acel))

        if self.direccion == "derecha":
            self.x += self.velocidad
        elif self.direccion == "izquierda":
            self.x -= self.velocidad
        elif self.direccion == "abajo":
            self.y += self.velocidad
        else:
            self.y -= self.velocidad

        self.decel_activa = (self.velocidad < self.velocidad_anterior - 0.04) or (self.velocidad < 0.1)

        if clima == "lluvia" and self.velocidad > 0.5:
            if self.direccion == "derecha":
                spawn_salpicadura(self.x, self.y + self.alto//2, self.direccion)
            elif self.direccion == "izquierda":
                spawn_salpicadura(self.x + self.ancho, self.y + self.alto//2, self.direccion)
            elif self.direccion == "abajo":
                spawn_salpicadura(self.x + self.alto//2, self.y, self.direccion)
            else:
                spawn_salpicadura(self.x + self.alto//2, self.y + self.ancho, self.direccion)

        if clima == "lluvia":
            self.wiper_angle += 8 * self.wiper_direction
            if abs(self.wiper_angle) > 55:
                self.wiper_direction *= -1

    def dibujar(self):
        w = self.ancho
        h = self.alto
        
        if self.direccion in ["abajo", "arriba"]:
            w = self.alto
            h = self.ancho

        draw_rect_alpha(pantalla, (0, 0, 0, 70), (self.x + 4, self.y + 4, w, h), border_radius=6)

        if clima == "lluvia":
            glow_color = (255, 255, 200, 35)
            cone_length = 120
            
            if self.direccion == "derecha":
                puntos = [(self.x + w, self.y + 6), (self.x + w + cone_length, self.y - 25), (self.x + w + cone_length, self.y + h + 25), (self.x + w, self.y + h - 6)]
            elif self.direccion == "izquierda":
                puntos = [(self.x, self.y + 6), (self.x - cone_length, self.y - 25), (self.x - cone_length, self.y + h + 25), (self.x, self.y + h - 6)]
            elif self.direccion == "abajo":
                puntos = [(self.x + 6, self.y + h), (self.x - 25, self.y + h + cone_length), (self.x + w + 25, self.y + h + cone_length), (self.x + w - 6, self.y + h)]
            else:
                puntos = [(self.x + 6, self.y), (self.x - 25, self.y - cone_length), (self.x + w + 25, self.y - cone_length), (self.x + w - 6, self.y)]
                
            cone_surf = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            pygame.draw.polygon(cone_surf, glow_color, puntos)
            pantalla.blit(cone_surf, (0, 0))

        pygame.draw.rect(pantalla, self.color, (self.x, self.y, w, h), border_radius=6)
        pygame.draw.rect(pantalla, (max(0, self.color[0]-40), max(0, self.color[1]-40), max(0, self.color[2]-40)), (self.x, self.y, w, h), width=2, border_radius=6)

        color_vidrio = (170, 215, 240)
        
        if self.direccion == "derecha":
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 16, self.y + 3, 6, h - 6), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 8, self.y + 4, 4, h - 8), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 16, self.y + 2, w - 36, 2))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 16, self.y + h - 4, w - 36, 2))
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + w - 6, self.y + 5, 4, h - 10), border_radius=1)
        elif self.direccion == "izquierda":
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 10, self.y + 3, 6, h - 6), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 12, self.y + 4, 4, h - 8), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 20, self.y + 2, w - 36, 2))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 20, self.y + h - 4, w - 36, 2))
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + 2, self.y + 5, 4, h - 10), border_radius=1)
        elif self.direccion == "abajo":
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 3, self.y + h - 16, w - 6, 6), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 4, self.y + 8, w - 8, 4), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 2, self.y + 16, 2, h - 36))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 4, self.y + 16, 2, h - 36))
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + 5, self.y + h - 6, w - 10, 4), border_radius=1)
        else:
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 3, self.y + 10, w - 6, 6), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 4, self.y + h - 12, w - 8, 4), border_radius=2)
            pygame.draw.rect(pantalla, color_vidrio, (self.x + 2, self.y + 20, 2, h - 36))
            pygame.draw.rect(pantalla, color_vidrio, (self.x + w - 4, self.y + 20, 2, h - 36))
            pygame.draw.rect(pantalla, GRIS_OSCURO, (self.x + 5, self.y + 2, w - 10, 4), border_radius=1)

        color_rueda = (30, 30, 30)
        if self.direccion in ["derecha", "izquierda"]:
            pygame.draw.rect(pantalla, color_rueda, (self.x + 8, self.y - 2, 11, 4), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 18, self.y - 2, 11, 4), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + 8, self.y + h - 2, 11, 4), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 18, self.y + h - 2, 11, 4), border_radius=1)
        else:
            pygame.draw.rect(pantalla, color_rueda, (self.x - 2, self.y + 8, 4, 11), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x - 2, self.y + h - 18, 4, 11), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 2, self.y + 8, 4, 11), border_radius=1)
            pygame.draw.rect(pantalla, color_rueda, (self.x + w - 2, self.y + h - 18, 4, 11), border_radius=1)

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
        else:
            pygame.draw.rect(pantalla, c_freno, (self.x + 3, self.y + h - 2, 5, 2))
            pygame.draw.rect(pantalla, c_freno, (self.x + w - 8, self.y + h - 2, 5, 2))

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
        else:
            pygame.draw.circle(pantalla, c_faro, (self.x + 4, self.y), 2)
            pygame.draw.circle(pantalla, c_faro, (self.x + w - 4, self.y), 2)

        if self.tiempo_cambio > 0:
            parpadeo_on = (pygame.time.get_ticks() // 220) % 2 == 0
            if parpadeo_on:
                giro_menor = self.carril_target < self.carril_actual
                if self.direccion in ["derecha", "izquierda"]:
                    girando_arriba = giro_menor if self.direccion == "derecha" else not giro_menor
                    y_luces = self.y if girando_arriba else self.y + h - 2
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (self.x + 3, y_luces + 1), 2)
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (self.x + w - 3, y_luces + 1), 2)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (self.x + 3, y_luces + 1), 5)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (self.x + w - 3, y_luces + 1), 5)
                else:
                    girando_izquierda = giro_menor if self.direccion == "abajo" else not giro_menor
                    x_luces = self.x if girando_izquierda else self.x + w - 2
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (x_luces + 1, self.y + 3), 2)
                    pygame.draw.circle(pantalla, NARANJA_GIRO, (x_luces + 1, self.y + h - 3), 2)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (x_luces + 1, self.y + 3), 5)
                    draw_circle_alpha(pantalla, (255, 140, 0, 100), (x_luces + 1, self.y + h - 3), 5)

        if clima == "lluvia":
            w_color = (10, 10, 10)
            rads = math.radians(self.wiper_angle)
            wiper_len = 10
            
            if self.direccion == "derecha":
                px, py = self.x + w - 11, self.y + h//2
                dx = int(wiper_len * math.cos(rads))
                dy = int(wiper_len * math.sin(rads))
                pygame.draw.line(pantalla, w_color, (px, py), (px + dx, py + dy), 2)
            elif self.direccion == "izquierda":
                px, py = self.x + 11, self.y + h//2
                dx = int(wiper_len * math.cos(rads))
                dy = int(wiper_len * math.sin(rads))
                pygame.draw.line(pantalla, w_color, (px, py), (px - dx, py + dy), 2)
            elif self.direccion == "abajo":
                px, py = self.x + w//2, self.y + h - 11
                dx = int(wiper_len * math.sin(rads))
                dy = int(wiper_len * math.cos(rads))
                pygame.draw.line(pantalla, w_color, (px, py), (px + dx, py + dy), 2)
            else:
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
    global vehiculos
    global gotas
    global semaforo
    global particulas_salpicadura

    vehiculos = []
    particulas_salpicadura = []
    
    generar_posiciones_arboles()
    crear_fondo_estatico()

    for c_idx in [0, 1]:
        y_carril = ALTO//2 + 25 if c_idx == 0 else ALTO//2 + 75
        for i in range(7):
            x = -150 - i * random.randint(180, 290)
            vehiculos.append(Vehiculo(x, y_carril, "derecha", c_idx))

    for c_idx in [0, 1]:
        y_carril = ALTO//2 - 55 if c_idx == 0 else ALTO//2 - 105
        for i in range(7):
            x = ANCHO + 150 + i * random.randint(180, 290)
            vehiculos.append(Vehiculo(x, y_carril, "izquierda", c_idx))

    for c_idx in [0, 1]:
        x_carril = ANCHO//2 + 25 if c_idx == 0 else ANCHO//2 + 75
        for i in range(6):
            y = -150 - i * random.randint(200, 310)
            vehiculos.append(Vehiculo(x_carril, y, "abajo", c_idx))

    for c_idx in [0, 1]:
        x_carril = ANCHO//2 - 55 if c_idx == 0 else ANCHO//2 - 105
        for i in range(6):
            y = ALTO + 150 + i * random.randint(200, 310)
            vehiculos.append(Vehiculo(x_carril, y, "arriba", c_idx))

    gotas = []
    if clima == "lluvia":
        for _ in range(400):
            gotas.append([
                random.randint(0, ANCHO),
                random.randint(0, ALTO),
                random.randint(10, 15)
            ])

    semaforo = Semaforo()

# ======================================================
# MENÚ
# ======================================================

def menu():
    global clima

    boton_seco = pygame.Rect(ANCHO//2 - 200, 320, 400, 70)
    boton_lluvia = pygame.Rect(ANCHO//2 - 200, 420, 400, 70)
    boton_iniciar = pygame.Rect(ANCHO//2 - 200, 560, 400, 70)

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
        pantalla.fill((22, 28, 36))

        for c in autos_menu:
            c["x"] += c["speed"]
            if c["x"] > ANCHO + 100:
                c["x"] = -100
                c["y"] = random.randint(0, ALTO)
            
            draw_rect_alpha(pantalla, (c["color"][0], c["color"][1], c["color"][2], 30), 
                            (int(c["x"]), c["y"], c["w"], c["h"]), border_radius=5)

        title_shadow = font_large.render("SIMULADOR DE TRÁFICO", True, (10, 15, 20))
        title_text = font_large.render("SIMULADOR DE TRÁFICO", True, BLANCO)
        pantalla.blit(title_shadow, (ANCHO//2 - 228, 142))
        pantalla.blit(title_text, (ANCHO//2 - 230, 140))
        
        subtitle_text = font_small.render("Mejoras de Superficie, Clima y Físicas de Tránsito Inteligente", True, (150, 170, 190))
        pantalla.blit(subtitle_text, (ANCHO//2 - 225, 190))

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
        
        texto_seco = font.render("Clima Seco", True, BLANCO)
        pantalla.blit(texto_seco, (ANCHO//2 - 50, 340))

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
        pantalla.blit(texto_lluvia, (ANCHO//2 - 68, 440))

        color_inicio = (38, 143, 65)
        if boton_iniciar.collidepoint(mouse):
            color_inicio = (46, 179, 81)
            
        pygame.draw.rect(pantalla, color_inicio, boton_iniciar, border_radius=12)
        if boton_iniciar.collidepoint(mouse):
            pygame.draw.rect(pantalla, BLANCO, boton_iniciar, width=2, border_radius=12)
            
        texto_inicio = font.render("INICIAR SIMULACIÓN", True, BLANCO)
        pantalla.blit(texto_inicio, (ANCHO//2 - 100, 580))

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
                if boton_iniciar.collidepoint(mouse):
                    return

# ======================================================
# AUXILIARES DE SPAWN
# ======================================================

def intentar_spawnear_vehiculo():
    direcciones = ["derecha", "izquierda", "abajo", "arriba"]
    dir_random = random.choice(direcciones)
    carril_random = random.choice([0, 1])
    
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
        else:
            x = ANCHO//2 - 55 if carril_random == 0 else ANCHO//2 - 105
            y = ALTO + random.randint(150, 300)
            
        vehiculos.append(Vehiculo(x, y, dir_random, carril_random))

# Panel de control lateral (Ubicado estratégicamente en la esquina inferior izquierda)
btn_pausa = BotonUI(30, 560, 140, 30, "PAUSAR", (150, 40, 40), (190, 60, 60))
btn_clima_seco = BotonUI(180, 560, 80, 30, "SECO", (60, 68, 80), (80, 90, 110))
btn_clima_lluvia = BotonUI(270, 560, 80, 30, "LLUVIA", (60, 68, 80), (80, 90, 110))

btn_force_change = BotonUI(30, 600, 140, 30, "FORZAR CAMBIO", (40, 110, 200), (50, 130, 230))
btn_reiniciar = BotonUI(180, 600, 170, 30, "REINICIAR SIM.", (38, 143, 65), (46, 179, 81))

btn_menu = BotonUI(30, 640, 320, 30, "VOLVER AL MENÚ PRINCIPAL", (60, 68, 80), (80, 90, 110))

# Ajustes de simulación adicionales
btn_caudal_dec = BotonUI(30, 685, 25, 25, "-", (40, 45, 55), (60, 68, 80))
btn_caudal_inc = BotonUI(60, 685, 25, 25, "+", (40, 45, 55), (60, 68, 80))

btn_vel_dec = BotonUI(150, 685, 25, 25, "-", (40, 45, 55), (60, 68, 80))
btn_vel_inc = BotonUI(180, 685, 25, 25, "+", (40, 45, 55), (60, 68, 80))

btn_dur_dec = BotonUI(270, 685, 25, 25, "-", (40, 45, 55), (60, 68, 80))
btn_dur_inc = BotonUI(300, 685, 25, 25, "+", (40, 45, 55), (60, 68, 80))

# Iniciar simulación
menu()
reiniciar_simulacion()

# ======================================================
# BUCLE PRINCIPAL DE LA SIMULACIÓN (UNIFICADO)
# ======================================================
while True:
    clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = False

    # 1. Eventos de Entrada
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

    # 2. Controladores de clic en la interfaz
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
            gotas = []
            for _ in range(400):
                gotas.append([random.randint(0, ANCHO), random.randint(0, ALTO), random.randint(10, 15)])
                
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

    # 3. Lógica Física e Interna (solo si no está pausado)
    if not pausado:
        semaforo.actualizar()
        actualizar_y_dibujar_salpicaduras()
        
        for v in vehiculos:
            v.mover(semaforo, vehiculos)
            
        if clima == "lluvia":
            for gota in gotas:
                gota[1] += gota[2]
                if gota[1] > ALTO:
                    gota[0] = random.randint(0, ANCHO)
                    gota[1] = -15
                    gota[2] = random.randint(10, 15)

        # Re-aparcamiento de vehículos que salen del mapa
        vehiculos_nuevos = []
        for v in vehiculos:
            fuera = False
            if v.direccion == "derecha" and v.x > ANCHO + 120: fuera = True
            elif v.direccion == "izquierda" and v.x < -120: fuera = True
            elif v.direccion == "abajo" and v.y > ALTO + 120: fuera = True
            elif v.direccion == "arriba" and v.y < -120: fuera = True
                
            if fuera:
                if len(vehiculos) - (len(vehiculos) - len(vehiculos_nuevos)) <= target_vehiculos:
                    v.carril_actual = random.choice([0, 1])
                    v.carril_target = v.carril_actual
                    v.velocidad = v.velocidad_max
                    if v.direccion == "derecha": v.x = -random.randint(150, 450)
                    elif v.direccion == "izquierda": v.x = ANCHO + random.randint(150, 450)
                    elif v.direccion == "abajo": v.y = -random.randint(150, 450)
                    else: v.y = ALTO + random.randint(150, 450)
                    vehiculos_nuevos.append(v)
            else:
                vehiculos_nuevos.append(v)
        vehiculos = vehiculos_nuevos

        if len(vehiculos) < target_vehiculos and pygame.time.get_ticks() % 15 == 0:
            intentar_spawnear_vehiculo()

    # 4. Renderizado Completo de Gráficos
    pantalla.blit(fondo_estatico, (0, 0))
    
    # Efecto de asfalto mojado si llueve
    if clima == "lluvia":
        draw_rect_alpha(pantalla, (0, 0, 0, 30), (0, ALTO//2 - 120, ANCHO, 240))
        draw_rect_alpha(pantalla, (0, 0, 0, 30), (ANCHO//2 - 120, 0, 240, ALTO))

    semaforo.dibujar()

    for v in vehiculos:
        v.dibujar()

    if clima == "lluvia":
        for gota in gotas:
            pygame.draw.line(pantalla, (170, 180, 240, 180), (gota[0], gota[1]), (gota[0] + 3, gota[1] + 12), 1)

    # 5. Interfaz de Usuario e HUD
    # Panel superior de estadísticas
    draw_rect_alpha(pantalla, (20, 25, 35, 200), (10, 10, 310, 105), border_radius=8)
    pygame.draw.rect(pantalla, (80, 90, 110), (10, 10, 310, 105), width=1, border_radius=8)

    clima_txt = "Lluvioso (Vel. reducida 25%)" if clima == "lluvia" else "Seco (Vel. nominal)"
    pantalla.blit(font_small.render(f"Clima: {clima_txt}", True, (230, 240, 255)), (22, 18))
    
    vels = [v.velocidad * 6 for v in vehiculos if 0 < v.x < ANCHO and 0 < v.y < ALTO]
    avg_vel = sum(vels)/len(vels) if vels else 0.0
    detenidos = sum(1 for v in vehiculos if v.velocidad < 0.2 and 0 < v.x < ANCHO and 0 < v.y < ALTO)
    c_level = "Alta" if detenidos > 6 else ("Moderada" if detenidos > 2 else "Baja")
    c_color = ROJO_ENCENDIDO if c_level == "Alta" else (AMARILLO_ENCENDIDO if c_level == "Moderada" else VERDE_ENCENDIDO)

    pantalla.blit(font_small.render(f"Velocidad Promedio: {avg_vel:.1f} km/h", True, BLANCO), (22, 40))
    pantalla.blit(font_small.render(f"Vehículos Detenidos: {detenidos}", True, BLANCO), (22, 62))
    pantalla.blit(font_small.render("Congestión:", True, BLANCO), (22, 84))
    pantalla.blit(font_small.render(c_level, True, c_color), (115, 84))

    # Panel inferior translúcido para agrupar los botones interactivos
    draw_rect_alpha(pantalla, (20, 25, 35, 200), (10, 540, 340, 185), border_radius=8)
    pygame.draw.rect(pantalla, (80, 90, 110), (10, 540, 340, 185), width=1, border_radius=8)

    # Dibujar botones del panel
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
    pantalla.blit(font_small.render(f"Sem: {duracion_semaforo_segundos:.0f}s", True, BLANCO), (330, 688))

    # Luces indicadoras de los semáforos en la esquina superior derecha
    col_h = VERDE_ENCENDIDO if semaforo.horizontal == "verde" else (AMARILLO_ENCENDIDO if semaforo.horizontal == "amarillo" else ROJO_ENCENDIDO)
    col_v = VERDE_ENCENDIDO if semaforo.vertical == "verde" else (AMARILLO_ENCENDIDO if semaforo.vertical == "amarillo" else ROJO_ENCENDIDO)
    
    draw_rect_alpha(pantalla, (20, 25, 35, 200), (ANCHO - 220, 10, 210, 80), border_radius=8)
    pygame.draw.rect(pantalla, (80, 90, 110), (ANCHO - 220, 10, 210, 80), width=1, border_radius=8)
    
    pantalla.blit(font_small.render("Semáforo H (Est/Oest):", True, BLANCO), (ANCHO - 208, 18))
    pygame.draw.circle(pantalla, col_h, (ANCHO - 35, 26), 6)
    pantalla.blit(font_small.render("Semáforo V (Nort/Sur):", True, BLANCO), (ANCHO - 208, 48))
    pygame.draw.circle(pantalla, col_v, (ANCHO - 35, 56), 6)

    pygame.display.flip()