
# =============================================================================
#  💊 RECORDATORIO DE MEDICAMENTOS
#  Versión : 2.0
#  Autor   : Proyecto Personal Python 3
# =============================================================================

import json
import os
import sys
import time
import threading
import importlib.util
from datetime import datetime, timedelta






ARCHIVO_USUARIOS   = "usuarios.json"      # guarda todas las cuentas
ARCHIVO_DATOS      = "medicamentos.json"  # cambia según el usuario activo
INTERVALO_REVISION = 30                   # segundos entre revisiones


MEDICAMENTOS        = []
USUARIO_ACTIVO      = ""   
hilo_recordatorio   = None
recordatorio_activo = False


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def separador(caracter="─", ancho=52):
    print(caracter * ancho)


def pausar():
    input("\n  Presione ENTER para continuar...")


def encabezado(titulo: str):
    limpiar_pantalla()
    separador("═")
    print(f"  💊  {titulo.upper()}")
    separador("═")
    print()


def cargar_usuarios() -> dict:
    if os.path.exists(ARCHIVO_USUARIOS):
        try:
            with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def guardar_usuarios(usuarios: dict):
    try:
        with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except IOError as error:
        print(f"\n  ⚠️  No se pudo guardar usuarios: {error}")


def usuario_existe(nombre: str) -> bool:
    usuarios = cargar_usuarios()
    return nombre.lower() in [u.lower() for u in usuarios.keys()]


def validar_contrasena(contrasena: str) -> tuple:
    if not contrasena:
        return False, "La contraseña no puede estar vacía."
    if len(contrasena) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."
    return True, ""


def registrar_usuario() -> bool:
    encabezado("Crear Cuenta Nueva")
    print("  Complete los datos para registrarse.\n")
    print("  (Escriba 'cancelar' en cualquier campo para volver)\n")

    while True:
        usuario = input("  👤  Nombre de usuario : ").strip()
        if usuario.lower() == "cancelar":
            return False
        if not usuario:
            print("  ⚠️  El nombre no puede estar vacío.\n")
            continue
        if usuario_existe(usuario):
            print(f"  ⚠️  El usuario '{usuario}' ya existe. Elije otro.\n")
            continue
        break

    nombre_completo = input("  🔤  Su nombre (ej: Sebastián Rentería)  : ").strip()
    if nombre_completo.lower() == "cancelar":
        return False
    if not nombre_completo:
        nombre_completo = usuario

    while True:
        contrasena = input("  🔒  Contraseña (mín. 4 caracteres) : ").strip()
        if contrasena.lower() == "cancelar":
            return False

        valida, motivo = validar_contrasena(contrasena)
        if not valida:
            print(f"  ⚠️  {motivo}\n")
            continue

        confirmar = input("  🔒  Confirma tu contraseña          : ").strip()
        if contrasena != confirmar:
            print("  ⚠️  Las contraseñas no coinciden. Intenta de nuevo.\n")
            continue
        break

    # ── Guardar la cuenta ─────────────────────────────────────────────────────
    usuarios         = cargar_usuarios()
    archivo_personal = f"medicamentos_{usuario.lower()}.json"

    usuarios[usuario] = {
        "contrasena"     : contrasena,
        "nombre_completo": nombre_completo,
        "archivo_datos"  : archivo_personal,
        "fecha_registro" : datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    guardar_usuarios(usuarios)

    print()
    separador()
    print("  ✅  ¡Cuenta creada exitosamente!\n")
    print(f"      Usuario : {usuario}")
    print(f"      Nombre  : {nombre_completo}")
    separador()
    pausar()
    return True


# ── Iniciar sesión ────────────────────────────────────────────────────────────

def iniciar_sesion() -> bool:
    global USUARIO_ACTIVO, ARCHIVO_DATOS

    encabezado("Iniciar Sesión")
    print("  (Escriba 'cancelar' para volver)\n")

    usuario = input("  👤  Usuario    : ").strip()
    if usuario.lower() == "cancelar":
        return False

    contrasena = input("  🔒  Contraseña : ").strip()
    if contrasena.lower() == "cancelar":
        return False

    usuarios = cargar_usuarios()

    usuario_key = None
    for key in usuarios:
        if key.lower() == usuario.lower():
            usuario_key = key
            break

    if usuario_key is None:
        print("\n  ❌  Usuario no encontrado.")
        pausar()
        return False

    if usuarios[usuario_key]["contrasena"] != contrasena:
        print("\n  ❌  Contraseña incorrecta.")
        pausar()
        return False

    USUARIO_ACTIVO = usuarios[usuario_key]["nombre_completo"]
    ARCHIVO_DATOS  = usuarios[usuario_key]["archivo_datos"]

    print(f"\n  ✅  ¡Bienvenido, {USUARIO_ACTIVO}!")
    time.sleep(1.2)
    return True


def pantalla_acceso() -> bool:
    while True:
        limpiar_pantalla()
        separador("═")
        print("  💊  RECORDATORIO DE MEDICAMENTOS  v2.0")
        separador("═")
        print()
        print("  Gestione sus medicamentos de forma sencilla.")
        print()
        separador("=")
        print()
        print("  [S]  Ya tengo una cuenta  →  Iniciar sesión")
        print("  [R]  Soy nuevo            →  Crear cuenta")
        print("  [C]  Salir del programa")
        print()
        separador("═")

        opcion = input("\n  ¿Ya tiene una cuenta? (S / R / C) : ").strip().upper()

        if opcion == "S":
            if iniciar_sesion():
                return True

        elif opcion == "R":
            if registrar_usuario():
                print("\n  Ahora inicie sesión con su nueva cuenta.")
                pausar()

        elif opcion == "C":
            return False

        else:
            print("\n  ⚠️  Opción no válida. Escriba S, R o C.")
            time.sleep(1.5)


def guardar_medicamentos():
    """Guarda MEDICAMENTOS en el archivo personal del usuario activo."""
    try:
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
            json.dump(MEDICAMENTOS, f, ensure_ascii=False, indent=4)
    except IOError as error:
        print(f"\n  ⚠️  No se pudo guardar: {error}")


def cargar_medicamentos():
    global MEDICAMENTOS
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
                MEDICAMENTOS = json.load(f)
            print(f"  ✅  {len(MEDICAMENTOS)} medicamento(s) cargado(s).")
        except (json.JSONDecodeError, IOError):
            print("  ⚠️  Archivo dañado. Comenzando desde cero.")
            MEDICAMENTOS = []
    else:
        MEDICAMENTOS = []

def validar_hora(hora_texto: str) -> bool:
    """Devuelve True si la hora tiene formato HH:MM válido."""
    try:
        datetime.strptime(hora_texto.strip(), "%H:%M")
        return True
    except ValueError:
        return False


def validar_frecuencia(frecuencia_texto: str) -> bool:
    try:
        return 1 <= int(frecuencia_texto.strip()) <= 24
    except ValueError:
        return False


def nombre_med_existe(nombre: str) -> bool:
    """Devuelve True si ya hay un medicamento con ese nombre."""
    return any(m["nombre"].lower() == nombre.lower() for m in MEDICAMENTOS)


def calcular_horarios(hora_inicio: str, frecuencia: int) -> list:
    """Genera la lista de horarios del día según la frecuencia."""
    horarios    = []
    hora_actual = datetime.strptime(hora_inicio, "%H:%M")
    vistos      = set()

    while True:
        hora_str = hora_actual.strftime("%H:%M")
        if hora_str in vistos or len(horarios) >= 24:
            break
        vistos.add(hora_str)
        horarios.append(hora_str)
        hora_actual += timedelta(hours=frecuencia)

    return horarios

def registrar_medicamento():
    encabezado("Registrar Medicamento")
    print("  (Escriba 'cancelar' en cualquier campo para volver)\n")

    while True:
        nombre = input("  🔤  Nombre del medicamento : ").strip()
        if nombre.lower() == "cancelar":
            return
        if not nombre:
            print("  ⚠️  El nombre no puede estar vacío.\n")
            continue
        if nombre_med_existe(nombre):
            print(f"  ⚠️  '{nombre}' ya existe. Use un nombre diferente.\n")
            continue
        break

    dosis = input("  💉  Dosis (ej: 500mg, o ENTER para omitir) : ").strip()
    if dosis.lower() == "cancelar":
        return
    if not dosis:
        dosis = "Sin dosis especificada"

    while True:
        hora_texto = input("  🕐  Hora de toma (HH:MM, ej: 08:00)       : ").strip()
        if hora_texto.lower() == "cancelar":
            return
        if validar_hora(hora_texto):
            break
        print("  ⚠️  Formato incorrecto. Use HH:MM (ej: 08:00).\n")

    while True:
        frec_texto = input("  🔁  Frecuencia en horas (1-24)             : ").strip()
        if frec_texto.lower() == "cancelar":
            return
        if validar_frecuencia(frec_texto):
            frecuencia = int(frec_texto)
            break
        print("  ⚠️  Ingrese un número entre 1 y 24.\n")

    horarios = calcular_horarios(hora_texto, frecuencia)

    MEDICAMENTOS.append({
        "nombre"     : nombre,
        "dosis"      : dosis,
        "hora_inicio": hora_texto,
        "frecuencia" : frecuencia,
        "horarios"   : horarios,
        "activo"     : True
    })
    guardar_medicamentos()

    print()
    separador()
    print("  ✅  ¡Medicamento registrado!\n")
    print(f"      Nombre   : {nombre}")
    print(f"      Dosis    : {dosis}")
    print(f"      Horarios : {', '.join(horarios)}")
    separador()
    pausar()


def mostrar_medicamentos():
    """Muestra la lista completa de medicamentos del usuario activo."""
    encabezado("Mis Medicamentos")

    if not MEDICAMENTOS:
        print("  📭  No hay medicamentos registrados.\n")
        print("      Use la opción 1 para agregar el primero.")
        pausar()
        return

    print(f"  Total: {len(MEDICAMENTOS)} medicamento(s)\n")

    for i, med in enumerate(MEDICAMENTOS, start=1):
        estado = "✅ Activo" if med.get("activo", True) else "⏸️  Inactivo"
        separador("─")
        nombre = med.get("nombre", "[Sin nombre]").upper()
        print(f"  [{i}]  {nombre}  —  {estado}")
        separador("─")
        dosis = med.get("dosis", "[Sin información]")
        hora_inicio = med.get("hora_inicio", "[Sin información]")
        frecuencia = med.get("frecuencia", "[Sin información]")
        horarios = med.get("horarios", [])
        print(f"       💉 Dosis       : {dosis}")
        print(f"       🕐 Hora inicio : {hora_inicio}")
        print(f"       🔁 Frecuencia  : cada {frecuencia} hora(s)")
        if horarios:
            print(f"       📋 Horarios    : {', '.join(horarios)}")
        else:
            print(f"       📋 Horarios    : [Sin información]")
        print()

    pausar()


def eliminar_medicamento():
    encabezado("Eliminar Medicamento")

    if not MEDICAMENTOS:
        print("  📭  No hay medicamentos para eliminar.")
        pausar()
        return

    for i, med in enumerate(MEDICAMENTOS, start=1):
        nombre = med.get("nombre", "[Sin nombre]")
        dosis = med.get("dosis", "[Sin dosis]")
        hora = med.get("hora_inicio", "[Sin hora]")
        print(f"  [{i}]  {nombre}  —  {dosis}  —  {hora}")

    print("\n[0]  Cancelar")
    separador()

    while True:
        try:
            seleccion = int(input("\n  Ingrese el número: ").strip())
        except ValueError:
            print("  ⚠️  Solo números.")
            continue
        if seleccion == 0:
            return
        if 1 <= seleccion <= len(MEDICAMENTOS):
            break
        print(f"  ⚠️  Número fuera de rango (1-{len(MEDICAMENTOS)}).")

    elegido = MEDICAMENTOS[seleccion - 1]
    nombre_med = elegido.get("nombre", "[Sin nombre]")
    print(f"\n  ¿Seguro que desea eliminar '{nombre_med}'?")

    if input("  Escriba SI para confirmar: ").strip().upper() == "SI":
        nombre_elim = elegido.get("nombre", "[Sin nombre]")
        MEDICAMENTOS.pop(seleccion - 1)
        guardar_medicamentos()
        print(f"\n  🗑️  '{nombre_elim}' eliminado correctamente.")
    else:
        print("\n  ❌  Cancelado. No se hicieron cambios.")

    pausar()

def mostrar_alerta_terminal(medicamento: dict):
    """ Se imprime la alerta visual con estrellas."""
    hora_actual = datetime.now().strftime("%H:%M")
    print("\n")
    separador("★", 52)
    print("  ⏰ ¡RECORDATORIO DE MEDICAMENTO!")
    separador("★", 52)
    print("\n 💊 Es hora de tomar su medicamento\n")
    nombre = medicamento.get("nombre", "[Sin nombre]")
    dosis = medicamento.get("dosis", "[Sin dosis]")
    print(f"  🔤 Medicamento : {nombre}")
    print(f"  💉 Dosis       : {dosis}")
    print(f"  🕐 Hora        : {hora_actual}")
    separador("★", 52)
    print()


def verificar_recordatorios():
    """Compara la hora actual (HH:MM) con los horarios de cada
    medicamento activo. Si coincide, dispara alerta y notificación."""

    hora_ahora = datetime.now().strftime("%H:%M")
    for med in MEDICAMENTOS:
        if not med.get("activo", True):
            continue
        if hora_ahora in med.get("horarios", []):
            mostrar_alerta_terminal(med)


def bucle_recordatorios():
    """Corre en el hilo de segundo plano.
    Llama a verificar_recordatorios() cada INTERVALO_REVISION segundos.
    Usa sleep(1) en bucle para poder detenerse rápidamente."""
    global recordatorio_activo
    print(f"\n  🔔  Recordatorios activos. Revisando cada {INTERVALO_REVISION}s...\n")
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
        print("  📭  No hay medicamentos. Registre uno primero.")
        pausar()
        return

    if recordatorio_activo and hilo_recordatorio and hilo_recordatorio.is_alive():
        print("  ✅  Los recordatorios ya están activos.\n")
        print(f"      Revisión cada {INTERVALO_REVISION} segundos.")
        pausar()
        return

    print("  Medicamentos que serán monitoreados:\n")
    for med in MEDICAMENTOS:
        if med.get("activo", True):
            print(f"  💊  {med['nombre']}  →  {', '.join(med['horarios'])}")

    recordatorio_activo = True
    hilo_recordatorio   = threading.Thread(
        target=bucle_recordatorios, daemon=True
    )
    hilo_recordatorio.start()

    separador()
    print("¡Recordatorios ACTIVADOS correctamente!")
    separador()
    pausar()


def detener_recordatorios():
    global recordatorio_activo
    recordatorio_activo = False


def estado_recordatorios() -> str:
    """Devuelve el indicador visual del estado actual del sistema."""
    if recordatorio_activo and hilo_recordatorio and hilo_recordatorio.is_alive():
        return "🟢 ACTIVOS"
    return "🔴 INACTIVOS"

def menu_principal() -> str:
    while True:
        limpiar_pantalla()
        separador("═")
        print(f"  💊  BIENVENIDO, {USUARIO_ACTIVO.upper()}")
        separador("═")
        print(f"  🕐  Hora          : {datetime.now().strftime('%H:%M  —  %d/%m/%Y')}")
        print(f"  📋  Medicamentos  : {len(MEDICAMENTOS)} registrado(s)")
        print(f"  🔔  Recordatorios : {estado_recordatorios()}")
        separador("─")
        print()
        print("     MENÚ PRINCIPAL")
        print()
        print("  [1]  📝  Registrar medicamento")
        print("  [2]  👁️  Ver mis medicamentos")
        print("  [3]  🔔  Iniciar recordatorios")
        print("  [4]  🗑️   Eliminar medicamento")
        print("  [5]  🔒  Cerrar sesión")
        print("  [6]  🚪  Salir del programa")
        print()
        separador("═")

        opcion = input("\n  ¿Qué desea hacer? Ingrese el número: ").strip()

        if   opcion == "1":
            registrar_medicamento()
        elif opcion == "2":
            mostrar_medicamentos()
        elif opcion == "3":
            iniciar_recordatorios()
        elif opcion == "4":
            eliminar_medicamento()
        elif opcion == "5":
            detener_recordatorios()
            print(f"\n  👋  Sesión cerrada. ¡Hasta luego, {USUARIO_ACTIVO}!")
            time.sleep(1.2)
            return "cerrar_sesion"
        elif opcion == "6":
            salir_programa()
            return "salir"
        else:
            print("\n  ⚠️  Opción inválida. Elija entre 1 y 6.")
            time.sleep(1.5)

def salir_programa():
    detener_recordatorios()
    guardar_medicamentos()
    limpiar_pantalla()
    separador("═")
    print("  💊  RECORDATORIO DE MEDICAMENTOS")
    separador("═")
    print()
    nombre = USUARIO_ACTIVO if USUARIO_ACTIVO else "usuario"
    print(f"  👋  ¡Hasta luego, {nombre}!")
    print()
    print("  Recuerde siempre tomar sus medicamentos a tiempo.")
    print("  ¡Cuídese mucho! 🌟")
    print()
    separador("═")
    print()

def main():
    """
    Flujo completo del programa:

        1. Verifica Python >= 3.6
        2. Muestra el estado de las librerías opcionales
        3. Bucle externo:
               a. pantalla_acceso()  → login o registro
               b. Si el usuario eligió salir → termina
               c. Si el login fue exitoso → carga medicamentos → menú
               d. Si elige 'Cerrar sesión' → vuelve al paso a
               e. Si elige 'Salir'         → termina
    """
    if sys.version_info < (3, 6):
        print("⚠️  Se requiere Python 3.6 o superior.")
        sys.exit(1)

    limpiar_pantalla()
    separador("═")
    print("  💊  RECORDATORIO DE MEDICAMENTOS  v2.0")
    separador("═")
    print()
    separador("─")
    input("  Presione ENTER para continuar...")

    while True:
        sesion_ok = pantalla_acceso()

        if not sesion_ok:
            limpiar_pantalla()
            separador("═")
            print("  💊  ¡Hasta luego!")
            print("\n  Recuerde tomar sus medicamentos a tiempo. 🌟")
            separador("═")
            print()
            break
        
        cargar_medicamentos()

        resultado = menu_principal()

        if resultado == "salir":
            break
        
if __name__ == "__main__":
    main()

