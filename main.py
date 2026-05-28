import pygame
import random
import sys

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

font = pygame.font.SysFont("Arial", 28)

# ======================================================
# COLORES
# ======================================================

PASTO = (50, 130, 50)
CALLE = (60, 60, 60)
LINEA = (240, 240, 240)

BLANCO = (255,255,255)
NEGRO = (20,20,20)

ROJO = (220,50,50)
VERDE = (50,220,50)

# ======================================================
# TIPOS DE VEHÍCULOS
# ======================================================

TIPOS = {

    "auto": {
        "color": (0,120,255),
        "ancho": 50,
        "alto": 28,
        "velocidad": (3,5)
    },

    "camion": {
        "color": (220,120,20),
        "ancho": 90,
        "alto": 35,
        "velocidad": (2,3)
    },

    "colectivo": {
        "color": (230,220,0),
        "ancho": 110,
        "alto": 38,
        "velocidad": (2,3)
    }
}

# ======================================================
# CLIMA
# ======================================================

clima = "seco"

# ======================================================
# MENÚ
# ======================================================

def menu():

    global clima

    boton_seco = pygame.Rect(500, 300, 400, 70)
    boton_lluvia = pygame.Rect(500, 400, 400, 70)
    boton_iniciar = pygame.Rect(500, 550, 400, 70)

    while True:

        mouse = pygame.mouse.get_pos()

        pantalla.fill((30,30,30))

        titulo = font.render(
            "SIMULADOR DE TRAFICO",
            True,
            BLANCO
        )

        pantalla.blit(titulo, (430,150))

        # =========================================
        # BOTÓN SECO
        # =========================================

        color_seco = (80,80,80)

        if boton_seco.collidepoint(mouse):
            color_seco = (120,120,120)

        pygame.draw.rect(
            pantalla,
            color_seco,
            boton_seco,
            border_radius=10
        )

        texto = font.render(
            "Clima seco",
            True,
            BLANCO
        )

        pantalla.blit(texto, (620,320))

        # =========================================
        # BOTÓN LLUVIA
        # =========================================

        color_lluvia = (80,80,80)

        if boton_lluvia.collidepoint(mouse):
            color_lluvia = (120,120,120)

        pygame.draw.rect(
            pantalla,
            color_lluvia,
            boton_lluvia,
            border_radius=10
        )

        texto = font.render(
            "Lluvia",
            True,
            BLANCO
        )

        pantalla.blit(texto, (650,420))

        # =========================================
        # BOTÓN INICIAR
        # =========================================

        color_inicio = (40,140,40)

        if boton_iniciar.collidepoint(mouse):
            color_inicio = (60,180,60)

        pygame.draw.rect(
            pantalla,
            color_inicio,
            boton_iniciar,
            border_radius=10
        )

        texto = font.render(
            "INICIAR",
            True,
            BLANCO
        )

        pantalla.blit(texto, (640,570))

        # =========================================
        # TEXTO CLIMA
        # =========================================

        texto = font.render(
            f"Clima seleccionado: {clima}",
            True,
            (255,220,0)
        )

        pantalla.blit(texto, (500,500))

        pygame.display.flip()

        # =========================================
        # EVENTOS
        # =========================================

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
# SEMÁFORO
# ======================================================

class Semaforo:

    def __init__(self):

        self.horizontal = "verde"
        self.vertical = "rojo"

        self.timer = 300

    def actualizar(self):

        self.timer -= 1

        # =====================================
        # HORIZONTAL VERDE -> AMARILLO
        # =====================================

        if (
            self.horizontal == "verde"
            and self.timer <= 60
        ):

            self.horizontal = "amarillo"

        # =====================================
        # VERTICAL VERDE -> AMARILLO
        # =====================================

        if (
            self.vertical == "verde"
            and self.timer <= 60
        ):

            self.vertical = "amarillo"

        # =====================================
        # CAMBIO TOTAL
        # =====================================

        if self.timer <= 0:

            if self.horizontal in ["verde", "amarillo"]:

                self.horizontal = "rojo"
                self.vertical = "verde"

            else:

                self.horizontal = "verde"
                self.vertical = "rojo"

            self.timer = 300

    def dibujar(self):

        # ===============================
        # HORIZONTAL
        # ===============================

        if self.horizontal == "verde":
            color_h = VERDE

        elif self.horizontal == "amarillo":
            color_h = (255,220,0)

        else:
            color_h = ROJO

        # ===============================
        # VERTICAL
        # ===============================

        if self.vertical == "verde":
            color_v = VERDE

        elif self.vertical == "amarillo":
            color_v = (255,220,0)

        else:
            color_v = ROJO

        pygame.draw.circle(
            pantalla,
            color_h,
            (ANCHO//2 + 150, ALTO//2 - 150),
            25
        )

        pygame.draw.circle(
            pantalla,
            color_v,
            (ANCHO//2 - 150, ALTO//2 + 150),
            25
        )

# ======================================================
# INTERSECCIÓN
# ======================================================

zona_interseccion = pygame.Rect(
    ANCHO//2 - 120,
    ALTO//2 - 120,
    240,
    240
)

# ======================================================
# VEHÍCULO
# ======================================================

class Vehiculo:

    def __init__(self, x, y, direccion):

        tipo = random.choice(list(TIPOS.keys()))

        datos = TIPOS[tipo]

        self.tipo = tipo

        self.color = datos["color"]

        self.ancho = datos["ancho"]
        self.alto = datos["alto"]

        velocidad = random.uniform(
            datos["velocidad"][0],
            datos["velocidad"][1]
        )

        if clima == "lluvia":
            velocidad *= 0.7

        self.velocidad_max = velocidad
        self.velocidad = velocidad

        self.x = x
        self.y = y

        self.direccion = direccion

    # ==================================================
    # RECT REAL
    # ==================================================

    def obtener_rect(self):

        if self.direccion == "horizontal":

            return pygame.Rect(
                self.x,
                self.y,
                self.ancho,
                self.alto
            )

        else:

            return pygame.Rect(
                self.x,
                self.y,
                self.alto,
                self.ancho
            )

    # ==================================================
    # MOVIMIENTO
    # ==================================================

    def mover(self, vehiculo_adelante, semaforo, vehiculos):

        self.velocidad = self.velocidad_max

    # =========================================
    # DISTANCIA ENTRE AUTOS DEL MISMO CARRIL
    # =========================================

        if vehiculo_adelante:

            mi_rect = self.obtener_rect()

            rect_adelante = vehiculo_adelante.obtener_rect()

            if self.direccion == "horizontal":
                mi_rect.width += 80
            else:
                mi_rect.height += 80

            if mi_rect.colliderect(rect_adelante):

                self.velocidad = 0
                return

    # =========================================
    # SEMÁFOROS
    # =========================================

        if self.direccion == "horizontal":

            zona_frenado = ANCHO//2 - 180

            if (
                self.x + self.ancho >= zona_frenado
                and self.x < zona_frenado
            ):

                if semaforo.horizontal != "verde":

                    self.velocidad = 0
                    return

        else:

            zona_frenado = ALTO//2 - 180

            if (
                self.y + self.ancho >= zona_frenado
                and self.y < zona_frenado
            ):

                if semaforo.vertical != "verde":

                    self.velocidad = 0
                    return

    # =========================================
    # EVITAR CHOQUES EN LA INTERSECCIÓN
    # =========================================

        siguiente_rect = self.obtener_rect()

        if self.direccion == "horizontal":
            siguiente_rect.x += self.velocidad
        else:
            siguiente_rect.y += self.velocidad

        for otro in vehiculos:
            if otro == self:
                continue

            # solo controlar autos cruzados
            if otro.direccion == self.direccion:
                continue

            rect_otro = otro.obtener_rect()

            if siguiente_rect.colliderect(rect_otro):

                self.velocidad = 0
                return

    # =========================================
    # MOVIMIENTO
    # =========================================

        if self.direccion == "horizontal":
            self.x += self.velocidad

        else:
            self.y += self.velocidad

    # ==================================================
    # DIBUJAR
    # ==================================================

    def dibujar(self):

        ancho = self.ancho
        alto = self.alto

        if self.direccion == "vertical":

            ancho = self.alto
            alto = self.ancho

        # cuerpo
        pygame.draw.rect(
            pantalla,
            self.color,
            (self.x, self.y, ancho, alto),
            border_radius=6
        )

        # vidrio
        pygame.draw.rect(
            pantalla,
            (180,220,255),
            (
                self.x + 10,
                self.y + 5,
                ancho - 20,
                alto - 10
            ),
            border_radius=4
        )

        # ruedas
        pygame.draw.rect(
            pantalla,
            NEGRO,
            (self.x + 5, self.y - 2, 10, 6)
        )

        pygame.draw.rect(
            pantalla,
            NEGRO,
            (self.x + ancho - 15, self.y - 2, 10, 6)
        )

        pygame.draw.rect(
            pantalla,
            NEGRO,
            (self.x + 5, self.y + alto - 4, 10, 6)
        )

        pygame.draw.rect(
            pantalla,
            NEGRO,
            (
                self.x + ancho - 15,
                self.y + alto - 4,
                10,
                6
            )
        )

# ======================================================
# CARRILES
# ======================================================

carriles = [
    ALTO//2 - 70,
    ALTO//2 - 10
]

carriles_verticales = [
    ANCHO//2 - 70,
    ANCHO//2 - 10
]

# ======================================================
# VARIABLES
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

    vehiculos = []

    # horizontales

    for carril in carriles:

        for i in range(8):

            x = -i * random.randint(170,280)

            vehiculos.append(
                Vehiculo(
                    x,
                    carril,
                    "horizontal"
                )
            )

    # verticales

    for carril in carriles_verticales:

        for i in range(6):

            y = -i * random.randint(220,340)

            vehiculos.append(
                Vehiculo(
                    carril,
                    y,
                    "vertical"
                )
            )

    # lluvia

    gotas = []

    if clima == "lluvia":

        for i in range(250):

            gotas.append([
                random.randint(0, ANCHO),
                random.randint(0, ALTO)
            ])

    semaforo = Semaforo()

# ======================================================
# INICIO
# ======================================================

menu()
reiniciar_simulacion()

# ======================================================
# LOOP PRINCIPAL
# ======================================================

while True:

    clock.tick(FPS)

    # ==================================================
    # EVENTOS
    # ==================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                menu()
                reiniciar_simulacion()

    # ==================================================
    # FONDO
    # ==================================================

    pantalla.fill(PASTO)

    # horizontal
    pygame.draw.rect(
        pantalla,
        CALLE,
        (0, ALTO//2 - 120, ANCHO, 240)
    )

    # vertical
    pygame.draw.rect(
        pantalla,
        CALLE,
        (ANCHO//2 - 120, 0, 240, ALTO)
    )

    # líneas horizontales
    for i in range(0, ANCHO, 60):

        pygame.draw.rect(
            pantalla,
            LINEA,
            (i, ALTO//2 - 2, 30, 4)
        )

    # líneas verticales
    for i in range(0, ALTO, 60):

        pygame.draw.rect(
            pantalla,
            LINEA,
            (ANCHO//2 - 2, i, 4, 30)
        )

    # ==================================================
    # SEMÁFORO
    # ==================================================

    semaforo.actualizar()
    semaforo.dibujar()

    # ==================================================
    # INTERSECCIÓN OCUPADA
    # ==================================================

    interseccion_ocupada = False

    for vehiculo in vehiculos:

        rect = vehiculo.obtener_rect()

        if zona_interseccion.colliderect(rect):

            interseccion_ocupada = True
            break

    # ==================================================
    # HORIZONTALES
    # ==================================================

    for carril in carriles:

        vehiculos_carril = [

            v for v in vehiculos

            if (
                v.direccion == "horizontal"
                and v.y == carril
            )
        ]

        vehiculos_carril.sort(
            key=lambda v: v.x
        )

        for i in range(len(vehiculos_carril)):

            vehiculo = vehiculos_carril[i]

            vehiculo_adelante = None

            if i < len(vehiculos_carril) - 1:

                vehiculo_adelante = vehiculos_carril[i + 1]

            vehiculo.mover(
                vehiculo_adelante,
                semaforo,
                vehiculos
            )

    # ==================================================
    # VERTICALES
    # ==================================================

    for carril in carriles_verticales:

        vehiculos_carril = [

            v for v in vehiculos

            if (
                v.direccion == "vertical"
                and v.x == carril
            )
        ]

        vehiculos_carril.sort(
            key=lambda v: v.y
        )

        for i in range(len(vehiculos_carril)):

            vehiculo = vehiculos_carril[i]

            vehiculo_adelante = None

            if i < len(vehiculos_carril) - 1:

                vehiculo_adelante = vehiculos_carril[i + 1]

            vehiculo.mover(
                vehiculo_adelante,
                semaforo,
                vehiculos
            )

    # ==================================================
    # DIBUJAR VEHÍCULOS
    # ==================================================

    for vehiculo in vehiculos:
        vehiculo.dibujar()

    # ==================================================
    # REAPARECER
    # ==================================================

    for vehiculo in vehiculos:

        if vehiculo.direccion == "horizontal":

            if vehiculo.x > ANCHO + 400:

                vehiculo.x = random.randint(-900, -300)

        else:

            if vehiculo.y > ALTO + 500:

                vehiculo.y = random.randint(-900, -300)

    # ==================================================
    # LLUVIA
    # ==================================================

    if clima == "lluvia":

        for gota in gotas:

            pygame.draw.line(
                pantalla,
                (170,170,255),
                (gota[0], gota[1]),
                (gota[0]+2, gota[1]+10),
                1
            )

            gota[1] += 12

            if gota[1] > ALTO:

                gota[0] = random.randint(0, ANCHO)
                gota[1] = 0

    # ==================================================
    # TEXTOS
    # ==================================================

    texto = font.render(
        f"Clima: {clima}",
        True,
        BLANCO
    )

    pantalla.blit(texto, (20,20))

    texto2 = font.render(
        f"H: {semaforo.horizontal} | V: {semaforo.vertical}",
        True,
        BLANCO
    )

    pantalla.blit(texto2, (20,60))

    # ==================================================
    # UPDATE
    # ==================================================

    pygame.display.flip()