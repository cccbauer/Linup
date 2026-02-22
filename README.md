# Linup - Roulette Tracker

App para seguimiento de sesiones de ruleta en Android.

## 🚀 Setup Rápido

```bash
# 1. Dar permisos al script
chmod +x setup.sh

# 2. Ejecutar setup automático
./setup.sh

# 3. Activar entorno virtual
source venv/bin/activate

# 4. Probar localmente (opcional)
flet run main.py

# 5. Compilar APK para Android
flet build apk
```

El APK quedará en: `build/apk/app.apk`

---

## 📱 Instalar en Android

### Opción 1: Con cable USB
```bash
adb install -r build/apk/app.apk
```

### Opción 2: Sin cable
1. Copia `build/apk/app.apk` a tu teléfono (WhatsApp, Drive, etc.)
2. Abre el archivo en el teléfono
3. Activa "Instalar apps de fuentes desconocidas" si te lo pide
4. Instala

---

## 🛠️ Requisitos del Sistema

- **macOS** (cualquier versión reciente)
- **Python 3.10+** (preferible 3.11 o 3.12)
- **Xcode Command Line Tools** (solo la primera vez)

Si no tienes Python:
```bash
brew install python@3.11
```

Si no tienes Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## ⏱️ Tiempos de Compilación

- **Primer build**: 20-40 minutos (descarga Flutter, Android SDK, etc.)
- **Builds siguientes**: 3-8 minutos (usa cache)

---

## 📋 Estructura del Proyecto

```
linup_project/
├── main.py           # Código principal de la app
├── pyproject.toml    # Configuración del proyecto
├── setup.sh          # Script de configuración automática
├── README.md         # Este archivo
└── build/
    └── apk/
        └── app.apk   # APK compilado (después del build)
```

---

## 🐛 Debug de Sugerencias

La app incluye notificaciones de debug para el sistema de sugerencias:

- **Notificación azul**: Muestra cuántos números hay en la ventana
- **Notificación verde**: Confirma que las sugerencias se actualizaron

Si los botones muestran "---" incluso después de 6 números, copia el texto de las notificaciones y reporta el bug.

---

## 🔧 Comandos Útiles

```bash
# Ver logs en tiempo real (con teléfono conectado)
adb logcat | grep -i "python\|flet"

# Limpiar build anterior
rm -rf build/

# Reinstalar en teléfono
adb install -r build/apk/app.apk

# Desinstalar del teléfono
adb uninstall com.linup.linup
```

---

## ✨ Features

✅ Teclado numérico adaptable a cualquier pantalla  
✅ Tabla de bitácora con scroll horizontal  
✅ Historial de sesiones con SQLite  
✅ Cálculo de eficiencia real (P/L %)  
✅ Sistema de sugerencias basado en ventana deslizante  
✅ Feedback visual mejorado en botones  
✅ Responsive (rotación de pantalla)  

---

## 📞 Soporte

Si encuentras bugs o tienes sugerencias, documenta:
1. Qué acción realizaste
2. Qué esperabas que pasara
3. Qué pasó en realidad
4. Screenshot si es posible
5. Texto de las notificaciones de debug (si aplica)
