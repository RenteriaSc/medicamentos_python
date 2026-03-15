# =============================================================================
#  💊 RECORDATORIO DE MEDICAMENTOS 
# =============================================================================
#  Versión    : 1.0
#  Descripción: Programa de terminal para registrar medicamentos y recibir
#               recordatorios automáticos con notificaciones del sistema.
#  INSTALACIÓN DE DEPENDENCIAS (ejecutar antes de usar el programa):

import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta

# ── Verificamos disponibilidad de librerías opcionales ──────────────────────────────────
import importlib.util

SCHEDULE_DISPONIBLE = importlib.util.find_spec("schedule") is not None
NOTIFICACIONES_DISPONIBLES = importlib.util.find_spec("plyer") is not None

if SCHEDULE_DISPONIBLE:
    import schedule

if NOTIFICACIONES_DISPONIBLES:
    from plyer import notification

ARCHIVO_DATOS = "medicamentos.json"   
INTERVALO_REVISION = 30               
MEDICAMENTOS = []                     
hilo_recordatorio = None              
recordatorio_activo = False           

def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")

def separador(caracter="─", ancho=50):
    print(caracter * ancho)

def pausar():
    input("\n  Presione ENTER para continuar...")

def encabezado(titulo: str):
    limpiar_pantalla()
    separador("═")
    print(f"  💊  {titulo.upper()}")
    separador("═")
    print()

def guardar_medicamentos():
    try:
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as archivo:
            json.dump(MEDICAMENTOS, archivo, ensure_ascii=False, indent=4)
    except IOError as error:
        print(f"\n  ⚠️  No se pudo guardar el archivo: {error}")

def cargar_medicamentos():
    global MEDICAMENTOS
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
                MEDICAMENTOS = json.load(archivo)
            print(f"  ✅  Se cargaron {len(MEDICAMENTOS)} medicamento(s) guardado(s).")
        except (json.JSONDecodeError, IOError):
            print("  ⚠️  El archivo de datos estaba dañado. Comenzando desde cero.")
            MEDICAMENTOS = []
    else:
        MEDICAMENTOS = []

def validar_hora(hora_texto: str) -> bool:
    try:
        datetime.strptime(hora_texto.strip(), "%H:%M")
        return True
    except ValueError:
        return False


def validar_frecuencia(frecuencia_texto: str) -> bool:
    try:
        valor = int(frecuencia_texto.strip())
        return 1 <= valor <= 24
    except ValueError:
        return False


def nombre_ya_existe(nombre: str) -> bool:
    return any(m["nombre"].lower() == nombre.lower() for m in MEDICAMENTOS)

def registrar_medicamento():
    print("  Por favor, ingrese los datos del medicamento.\n")
    print("  (Escriba 'cancelar' en cualquier momento para volver al menú)\n")

    while True:
        nombre = input("  🔤  Nombre del medicamento : ").strip()
        if nombre.lower() == "cancelar":
            return
        if not nombre:
            print("  ⚠️  El nombre no puede estar vacío. Intente de nuevo.\n")
            continue
        if nombre_ya_existe(nombre):
            print(f"  ⚠️  Ya existe '{nombre}'. Use un nombre diferente.\n")
            continue
        break

    dosis = input("  💉  Dosis (ej: 500mg, dejar vacío si no aplica): ").strip()
    if dosis.lower() == "cancelar":
        return
    if not dosis:
        dosis = "Sin dosis especificada"

    while True:
        hora_texto = input("  🕐  Hora de toma (formato 24h) : ").strip()
        if hora_texto.lower() == "cancelar":
            return
        if validar_hora(hora_texto):
            break
        print("  ⚠️  Formato incorrecto. Use HH:MM (ejemplo: 08:00 o 14:30).\n")

    while True:
        frecuencia_texto = input("  🔁  Frecuencia en horas (ej: 8 = cada 8 horas): ").strip()
        if frecuencia_texto.lower() == "cancelar":
            return
        if validar_frecuencia(frecuencia_texto):
            frecuencia = int(frecuencia_texto)
            break
        print("  ⚠️  Ingrese un número entre 1 y 24.\n")

    horarios = calcular_horarios(hora_texto, frecuencia)
    nuevo_medicamento = {
        "nombre"     : nombre,
        "dosis"      : dosis,
        "hora_inicio": hora_texto,
        "frecuencia" : frecuencia,
        "horarios"   : horarios,          
        "activo"     : True               
    }

    MEDICAMENTOS.append(nuevo_medicamento)
    guardar_medicamentos()
    print()
    separador()
    print(f"  ✅  ¡Medicamento registrado con éxito!\n")
    print(f"      Medicamento : {nombre}")
    print(f"      Dosis       : {dosis}")
    print(f"      Horarios    : {', '.join(horarios)}")
    separador()

    pausar()


def calcular_horarios(hora_inicio: str, frecuencia: int) -> list:
    horarios = []
    hora_actual = datetime.strptime(hora_inicio, "%H:%M")

    while True:
        horarios.append(hora_actual.strftime("%H:%M"))
        hora_actual += timedelta(hours=frecuencia)
        if hora_actual.strftime("%H:%M") == hora_inicio or len(horarios) >= 24:
            break

    return horarios


def mostrar_medicamentos():
    encabezado("Medicamentos Registrados")

    if not MEDICAMENTOS:
        print("  📭  No hay medicamentos registrados todavía.\n")
        print("  Use la opción 1 del menú para agregar un medicamento.")
        pausar()
        return

    print(f"  Total de medicamentos: {len(MEDICAMENTOS)}\n")

    for indice, med in enumerate(MEDICAMENTOS, start=1):
        estado = "✅ Activo" if med["activo"] else "⏸️  Inactivo"
        separador("─")
        print(f"  [{indice}]  {med['nombre'].upper()}  —  {estado}")
        separador("─")
        print(f"       💉 Dosis       : {med['dosis']}")
        print(f"       🕐 Hora inicio : {med['hora_inicio']}")
        print(f"       🔁 Frecuencia  : cada {med['frecuencia']} hora(s)")
        print(f"       📋 Horarios    : {', '.join(med['horarios'])}")
        print()

    pausar()


def eliminar_medicamento():
    encabezado("Eliminar Medicamento")

    if not MEDICAMENTOS:
        print("  📭  No hay medicamentos registrados para eliminar.")
        pausar()
        return

    print("  Seleccione el número del medicamento que desea eliminar:\n")
    for i, med in enumerate(MEDICAMENTOS, start=1):
        print(f"  [{i}]  {med['nombre']}  —  {med['dosis']}  —  {med['hora_inicio']}")

    print(f"\n  [0]  Cancelar y volver al menú")
    separador()

    while True:
        try:
            seleccion = int(input("\n  Ingrese el número: ").strip())
        except ValueError:
            print("  ⚠️  Por favor ingrese solo números.")
            continue

        if seleccion == 0:
            return
        if 1 <= seleccion <= len(MEDICAMENTOS):
            break
        print(f"  ⚠️  Número fuera de rango. Elija entre 1 y {len(MEDICAMENTOS)}.")

    medicamento_elegido = MEDICAMENTOS[seleccion - 1]

    print(f"\n  ¿Está seguro que desea eliminar '{medicamento_elegido['nombre']}'?")
    confirmacion = input("  Escriba SI para confirmar: ").strip().upper()

    if confirmacion == "SI":
        nombre_eliminado = medicamento_elegido["nombre"]
        MEDICAMENTOS.pop(seleccion - 1)
        guardar_medicamentos()
        print(f"\n  🗑️  '{nombre_eliminado}' eliminado correctamente.")
    else:
        print("\n  ❌  Eliminación cancelada. No se hicieron cambios.")

    pausar()

def enviar_notificacion(nombre: str, dosis: str):
    if NOTIFICACIONES_DISPONIBLES:
        try:
            notification.notify(
                title   = "💊 Recordatorio de Medicamento",
                message = f"Es hora de tomar: {nombre}\nDosis: {dosis}",
                app_name= "Recordatorio de Medicamentos",
                timeout = 10   
            )
        except Exception:
            pass  


def mostrar_alerta_terminal(medicamento: dict):
    hora_actual = datetime.now().strftime("%H:%M")
    print("\n")
    separador("★", 50)
    print("  ⏰  ¡RECORDATORIO DE MEDICAMENTO! ⏰")
    separador("★", 50)
    print(f"\n  💊  Es hora de tomar su medicamento\n")
    print(f"      🔤 Medicamento : {medicamento['nombre']}")
    print(f"      💉 Dosis       : {medicamento['dosis']}")
    print(f"      🕐 Hora        : {hora_actual}")
    separador("★", 50)
    print()


def verificar_recordatorios():
    hora_ahora = datetime.now().strftime("%H:%M")

    for medicamento in MEDICAMENTOS:
        if not medicamento.get("activo", True):
            continue  

        if hora_ahora in medicamento.get("horarios", []):
            mostrar_alerta_terminal(medicamento)
            enviar_notificacion(medicamento["nombre"], medicamento["dosis"])


def bucle_recordatorios():
    global recordatorio_activo
    print(f"\n  🔔  Recordatorios iniciados. Revisando cada {INTERVALO_REVISION} segundos...")
    print(f"      (El menú sigue disponible mientras los recordatorios están activos)\n")

    while recordatorio_activo:
        verificar_recordatorios()
        for _ in range(INTERVALO_REVISION):
            if not recordatorio_activo:
                break
            time.sleep(1)


def iniciar_recordatorios():
    global hilo_recordatorio, recordatorio_activo

    encabezado("Iniciar Recordatorios")

    if not MEDICAMENTOS:
        print("  📭  No hay medicamentos registrados.")
        print("      Use la opción 1 para agregar un medicamento primero.\n")
        pausar()
        return

    if recordatorio_activo and hilo_recordatorio and hilo_recordatorio.is_alive():
        print("  ✅  Los recordatorios ya están activos y funcionando.\n")
        print(f"      Revisando cada {INTERVALO_REVISION} segundos en segundo plano.")
        pausar()
        return

    print("  Se activarán recordatorios para los siguientes medicamentos:\n")
    for med in MEDICAMENTOS:
        if med.get("activo", True):
            print(f"  💊  {med['nombre']}  →  Horarios: {', '.join(med['horarios'])}")

    print()

    if not NOTIFICACIONES_DISPONIBLES:
        print("  ℹ️  Nota: Las notificaciones del sistema NO están disponibles.")
        print("      Instale 'plyer' con:  pip install plyer\n")

    recordatorio_activo = True
    hilo_recordatorio = threading.Thread(
        target=bucle_recordatorios,
        daemon=True   
    )
    hilo_recordatorio.start()

    separador()
    print("  🟢  ¡Recordatorios ACTIVADOS correctamente!")
    separador()
    pausar()

def detener_recordatorios():
    global recordatorio_activo
    recordatorio_activo = False

def mostrar_estado_recordatorios() -> str:
    if recordatorio_activo and hilo_recordatorio and hilo_recordatorio.is_alive():
        return "🟢 ACTIVOS"
    return "🔴 INACTIVOS"


def menu_principal():
    while True:
        limpiar_pantalla()
        separador("═")
        print("💊   RECORDATORIO DE MEDICAMENTOS   💊")
        separador("=")
        print(f"  🕐  Hora actual    : {datetime.now().strftime('%H:%M  —  %d/%m/%Y')}")
        print(f"  📋  Medicamentos   : {len(MEDICAMENTOS)} registrado(s)")
        print(f"  🔔  Recordatorios  : {mostrar_estado_recordatorios()}")
        separador("─")
        print()
        print("     MENÚ PRINCIPAL")
        print()
        print("  [1]  📝  Registrar medicamento")
        print("  [2]  📋  Ver mis medicamentos")
        print("  [3]  🔔  Iniciar recordatorios automáticos")
        print("  [4]  🗑️   Eliminar medicamento")
        print("  [5]  🚪  Salir del programa")
        print()
        separador("═")

        opcion = input("\n  ¿Qué desea hacer? Ingresa el número: ").strip()

        if opcion == "1":
            registrar_medicamento()

        elif opcion == "2":
            mostrar_medicamentos()

        elif opcion == "3":
            iniciar_recordatorios()

        elif opcion == "4":
            eliminar_medicamento()

        elif opcion == "5":
            salir_programa()
            break

        else:
            print("\n  ⚠️  Opción no válida. Por favor elija un número del 1 al 5.")
            time.sleep(2)


def salir_programa():
    detener_recordatorios()
    guardar_medicamentos()
    limpiar_pantalla()
    separador("=")
    print("💊  RECORDATORIO DE MEDICAMENTOS")
    separador("=")
    print()
    print("¡Hasta luego!")
    print()
    print("Recuerda siempre tomar tus medicamentos a tiempo.")
    print("¡Nos vemos pronto! 🌟")
    print()
    separador("=")
    print()

def main():
    if sys.version_info < (3, 6):
        print("⚠️  Este programa requiere Python 3.6 o superior.")
        sys.exit(1)

    limpiar_pantalla()
    separador("=")
    print("  💊   BIENVENIDO AL RECORDATORIO DE MEDICAMENTOS   💊")
    separador("=")
    print()
    print("  Este programa le ayudará a recordar cuándo tomar sus medicamentos con facilidad.")
    print()

    if SCHEDULE_DISPONIBLE:
        print("  ✅  Librería disponible.")
    else:
        print("  ℹ️  'schedule' no instalado (opcional). pip install schedule")

    if NOTIFICACIONES_DISPONIBLES:
        print("  ✅  Notificaciones activadas.")
    else:
        print("  ℹ️  'plyer' no instalado. Sin notificaciones del sistema.")
        print("      Para activarlas ejecute: pip install plyer")

    print()
    separador("─")


    cargar_medicamentos()

    separador("─")
    print()
    input("  Presione ENTER para ingresar al menú principal...")

    menu_principal()

if __name__ == "__main__":
    main()