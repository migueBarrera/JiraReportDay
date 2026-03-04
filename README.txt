# Jira Report App

Esta herramienta genera reportes de horas de Jira y muestra gráficos diarios.

## Requisitos
- Tener Python 3 instalado en el sistema.
- Copiar el .env.default y usar de nombre .env y setear la URL, nombre de usuario por defecto y codigo del proyecto

## Cómo ejecutar

### En Mac / Linux:
1. Abre una terminal en esta carpeta.
2. Dale permisos de ejecución al script (solo la primera vez):
   chmod +x start.sh
3. Ejecuta:
   ./start.sh

### En Windows:
1. Haz doble clic en el archivo `start.bat`.

El script se encargará automáticamente de:
- Crear un entorno virtual (carpeta `venv`).
- Instalar las librerías necesarias.
- Abrir la aplicación en tu navegador.
