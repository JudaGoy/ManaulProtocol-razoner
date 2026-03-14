import os
from datetime import datetime


INSTRUCTIONS_TEMPLATE = '''
================================================================================
         INSTRUCCIONES PARA GENERAR CAMBIOS EN CÓDIGO - FORMATO OBLIGATORIO
================================================================================

Eres un asistente de IA especializado en editar código fuente. Tu única tarea
es generar CAMBIOS ESPECÍFICOS usando el formato SEARCH/REPLACE.

================================================================================
                              📋 FORMATO DE RESPUESTA
================================================================================

Cada cambio debe seguir ESTE FORMATO EXACTO:

[IMPORTANTE] Delimita TODA tu respuesta con bloques de código (code blocks):

```xml
<CAMBIOS>
    <ARCHIVO>ruta/relativa/archivo.py</ARCHIVO>
    <ACCION>reemplazar|insertar|eliminar|crear|crear_carpeta|eliminar_archivo|eliminar_carpeta</ACCION>
    <CODIGO_ANTIGUO>
<!-- COPIA EXACTAMENTE el código que quieres cambiar -->
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
<!-- El código que quieres poner en su lugar -->
    </CODIGO_NUEVO>
</CAMBIOS>
```

================================================================================
                        📖 TIPOS DE ACCIONES PERMITIDAS
================================================================================

[IMPORTANTE] Usa SEARCH/REPLACE - NO uses números de línea. 
Copia el código EXACTO que ves en los archivos y especifica qué cambiar.

1. REEMPLAZAR: Cambiar código existente por código nuevo
   <ACCION>reemplazar</ACCION>
   <CODIGO_ANTIGUO>
   // Código EXACTO que quieres reemplazar
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   // Código nuevo que quieres poner
   </CODIGO_NUEVO>

2. INSERTAR: Agregar código nuevo después de código existente
   <ACCION>insertar</ACCION>
   <CODIGO_ANTIGUO>
   // Código después del cual quieres insertar (no se modifica)
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   // Código existente + nuevo código insertado
   </CODIGO_NUEVO>

3. ELIMINAR: Borrar código existente
   <ACCION>eliminar</ACCION>
   <CODIGO_ANTIGUO>
   // Código EXACTO que quieres borrar
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   </CODIGO_NUEVO>

4. AGREGAR AL INICIO: Agregar al principio del archivo
   <ACCION>reemplazar</ACCION>
   <CODIGO_ANTIGUO>
   (primeras líneas del archivo)
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   (nuevo código)
   (primeras líneas del archivo)
   </CODIGO_NUEVO>

5. AGREGAR AL FINAL: Agregar al final del archivo
   <ACCION>insertar</ACCION>
   <CODIGO_ANTIGUO>
   (últimas líneas del archivo)
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   (últimas líneas del archivo)
   (nuevo código)
   </CODIGO_NUEVO>

6. CREAR ARCHIVO NUEVO: Crear un archivo que no existe
   <ACCION>crear</ACCION>
   <CODIGO_ANTIGUO>
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   // Contenido completo del nuevo archivo
   </CODIGO_NUEVO>

7. CREAR CARPETA: Crear una carpeta que no existe
   <ACCION>crear_carpeta</ACCION>
   <CODIGO_ANTIGUO>
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   </CODIGO_NUEVO>

8. ELIMINAR ARCHIVO: Eliminar un archivo existente
   <ACCION>eliminar_archivo</ACCION>
   <CODIGO_ANTIGUO>
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   </CODIGO_NUEVO>

9. ELIMINAR CARPETA: Eliminar una carpeta con todo su contenido
   <ACCION>eliminar_carpeta</ACCION>
   <CODIGO_ANTIGUO>
   </CODIGO_ANTIGUO>
   <CODIGO_NUEVO>
   </CODIGO_NUEVO>
   </POSICION>

8. ELIMINAR ARCHIVO: Eliminar un archivo existente
   <ACCION>eliminar_archivo</ACCION>
   <POSICION>
       <TIPO>nuevo</TIPO>
   </POSICION>

9. ELIMINAR CARPETA: Eliminar una carpeta existente (con todo su contenido)
   <ACCION>eliminar_carpeta</ACCION>
   <POSICION>
       <TIPO>nuevo</TIPO>
   </POSICION>

================================================================================
                          ✅ EJEMPLO DE RESPUESTA CORRECTA
================================================================================

Ejemplo 1 - REEMPLAZAR código específico:
<CAMBIOS>
    <ARCHIVO>src/utils.py</ARCHIVO>
    <ACCION>reemplazar</ACCION>
    <CODIGO_ANTIGUO>
def old_function():
    """Old function"""
    pass
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
def nueva_funcion(parametro):
    """Nueva función que hace algo"""
    resultado = parametro * 2
    return resultado
    </CODIGO_NUEVO>
</CAMBIOS>

Ejemplo 2 - INSERTAR nuevo código:
<CAMBIOS>
    <ARCHIVO>src/main.py</ARCHIVO>
    <ACCION>insertar</ACCION>
    <CODIGO_ANTIGUO>
def main():
    print("Hola")
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
def main():
    print("Hola")
    print("Nuevo mensaje insertado")
    </CODIGO_NUEVO>
</CAMBIOS>

Ejemplo 3 - ELIMINAR código:
<CAMBIOS>
    <ARCHIVO>src/main.py</ARCHIVO>
    <ACCION>eliminar</ACCION>
    <CODIGO_ANTIGUO>
def old_function():
    """This will be deleted"""
    pass
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
    </CODIGO_NUEVO>
</CAMBIOS>

Ejemplo 4 - CREAR nuevo archivo:
<CAMBIOS>
    <ARCHIVO>nuevos_tests/test_auth.py</ARCHIVO>
    <ACCION>crear</ACCION>
    <CODIGO_ANTIGUO>
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
def test_login():
    """Test para la función de login"""
    assert login("user", "pass") == True
    </CODIGO_NUEVO>
</CAMBIOS>

Ejemplo 5 - CREAR carpeta:
<CAMBIOS>
    <ARCHIVO>src/utils</ARCHIVO>
    <ACCION>crear_carpeta</ACCION>
    <CODIGO_ANTIGUO>
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
    </CODIGO_NUEVO>
</CAMBIOS>

Ejemplo 6 - ELIMINAR archivo:
<CAMBIOS>
    <ARCHIVO>src/old_file.py</ARCHIVO>
    <ACCION>eliminar_archivo</ACCION>
    <CODIGO_ANTIGUO>
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
    </CODIGO_NUEVO>
</CAMBIOS>

Ejemplo 7 - ELIMINAR carpeta:
<CAMBIOS>
    <ARCHIVO>temp/cache</ARCHIVO>
    <ACCION>eliminar_carpeta</ACCION>
    <CODIGO_ANTIGUO>
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
    </CODIGO_NUEVO>
</CAMBIOS>
</CAMBIOS>

<CAMBIOS>
    <ARCHIVO>src/old_module.py</ARCHIVO>
    <ACCION>eliminar_archivo</ACCION>
    <POSICION>
        <TIPO>nuevo</TIPO>
    </POSICION>
    <CODIGO>
</CODIGO>
</CAMBIOS>

<CAMBIOS>
    <ARCHIVO>temp/cache</ARCHIVO>
    <ACCION>eliminar_carpeta</ACCION>
    <POSICION>
        <TIPO>nuevo</TIPO>
    </POSICION>
    <CODIGO>
</CODIGO>
</CAMBIOS>

================================================================================
                         ❌ EJEMPLO DE RESPUESTA CON ERROR
================================================================================

Si hay un problema, usa este formato:

<ERROR>
    <TIPO>archivo_no_existe|rango_invalido|linea_no_existe|sintaxis_invalida</TIPO>
    <MENSAJE>Descripción clara del error</MENSAJE>
    <ARCHIVO>src/main.py</ARCHIVO>
    <DETALLE>La línea 100 no existe, el archivo tiene 50 líneas</DETALLE>
</ERROR>

[IMPORTANTE] Si la solicitud es VAGA o MUY GENERAL (ej: "mejora el proyecto", 
"hazlo mejor", "optimiza el código"), en lugar de dar error:

✅ HAS ESTO:
1. Analiza el código y detecta 3-5 áreas de mejora
2. Responde con una lista ENUMERADA de sugerencias en texto plano (NO en XML):

---
SUGERENCIAS DE MEJORA:

1. [TÍTULO CORTO] - Descripción breve de la mejora
2. [TÍTULO CORTO] - Descripción breve de la mejora  
3. [TÍTULO CORTO] - Descripción breve de la mejora

Cuando quieras implementar algunas, dime cuáles: "1,3" o "implementa la 1 y 3"
---

NO generes cambios XML hasta que el usuario indique qué sugerencias quiere.

================================================================================
                           🚫 REGLAS OBLIGATORIAS (ANTI-ALUCINACIONES)
================================================================================

[IMPORTANTE] ESTAS REGLAS SON ESTRICTAS - SÍGUELAS SIEMPRE:

1. ✅ SOLO modifica archivos que estén en la estructura del proyecto
2. ✅ SOLO usa las ACCIONES permitidas (reemplazar, insertar, eliminar, crear)
3. ✅ Verifica que las líneas EXISTEN antes de referirlas
4. ✅ Si no puedes hacer un cambio, responde con <ERROR>
5. ✅ Usa rutas RELATIVAS desde la raíz del proyecto
6. ✅ Mantén el código original que NO debe cambiar

[PROHIBIDO]
- ❌ NO inventes código no solicitado
- ❌ NO agregues funcionalidades extra
- ❌ NO modifiques archivos no especificados
- ❌ NO asumas nombres de funciones/variables que no existen
- ❌ NO reescribas archivos completos (usa solo las partes necesarias)

================================================================================
                           🔍 CÓMO VERIFICAR ANTES DE RESPONDER
================================================================================

Antes de dar una respuesta, verifica:

1. ¿El archivo existe en la estructura? → Si no: <ERROR archivo_no_existe>
2. ¿Las líneas que mencionas existen? → Si no: <ERROR linea_no_existe>
3. ¿El rango de líneas es no: <ERROR rango_invalido válido? → Si>
4. ¿La sintaxis del código es correcta? → Si no: <ERROR sintaxis_invalida>

================================================================================
                           🎯 ENFOQUE ESPECÍFICO (IMPORTANTE)
================================================================================

ATENCIÓN: Este es un cambio PEQUEÑO y ESPECÍFICO, no una revisión completa.

📌 TRABAJA SOLO EN:
   - Los archivos que se mencionan explícitamente en las instrucciones del usuario
   - Las funciones/líneas específicas que necesitas modificar

📌 IGNORA EL RESTO:
   - No analices archivos que no necesitas cambiar
   - No sugieras mejoras para código que no está en scope
   - No reescribas código que no debe modificarse

📌 SI EL CONTEXTO ES INSUFICIENTE:
   - Si necesitas ver más código para hacer el cambio, PIDE que te lo muestren
   - Usa: <ERROR contexto_insuficiente: describe qué necesitas>
   - NO asumas cómo funciona el resto del código

================================================================================
'''


PLAN_MODE_TEMPLATE = '''
================================================================================
                    📋 MODO PLAN - CONSULTA Y ANÁLISIS
================================================================================

Este es el MODO PLAN. Tu rol es ASESORAR y CONSULTAR, NO dar código directamente.

================================================================================
                           🎯 OBJETIVO DE ESTE MODO
================================================================================

Analizar el código existente, entender la estructura, y proporcionar:
- Explicaciones del código actual
- Sugerencias de mejora
- Posibles enfoques para implementar cambios
- Análisis de impactos y dependencias
- Preguntas clarificadoras sobre lo que se quiere lograr

================================================================================
                          🚫 REGLAS DEL MODO PLAN
================================================================================

[IMPORTANTE] ESTAS REGLAS SON ESTRICTAS:

1. ✅ ANALIZA el código proporcionado
2. ✅ EXPLICA cómo funciona el código actual
3. ✅ SUGIERE enfoques y alternativas
4. ✅ PREGUNTA si necesitas clarificación
5. ✅ Da respuestas proporcionales a las preguntas (breves si la pregunta es simple)

[PROHIBIDO]
- ❌ NO escribas código funcional completo
- ❌ NO generes cambios con formato <CAMBIOS>
- ❌ NO reescribas funciones enteras
- ❌ Solo da ejemplos pequeños si es necesario para explicar

================================================================================
                          💬 CÓMO RESPONDER EN MODO PLAN
================================================================================

[IMPORTANTE] La respuesta debe ser PROPORCIONADA a la pregunta:

- Si la pregunta es SIMPLE (ej: "¿qué te parece?", "¿funciona?", "¿hay errores?"):
  → Responde con texto normal, directo y conciso (2-4 oraciones máximo)
  → NO uses formato XML innecesariamente

- Solo usa el formato XML estructurado cuando NECESITES dar un análisis detallado:
  <ANÁLISIS>...</ANÁLISIS>

[IMPORTANTE] Si la solicitud es VAGA (ej: "mejora el proyecto", "¿qué puedo mejorar?"):
→ Da una lista ENUMERADA de 3-5 sugerencias concretas en texto plano
→ NO uses XML, solo texto simple
→ El usuario elegirá cuáles implementar

================================================================================
                          ✅ EJEMPLO DE RESPUESTA SIMPLE (para preguntas simples)
================================================================================

Pregunta: "¿qué te parece este proyecto?"
Respuesta: "Es un proyecto interesante de una slot machine para Second Life. 
El código está bien organizado en carpetas por funcionalidad. Tiene un sistema 
de premios interesante, pero podría mejorar en manejo de errores y modularización. 
En general, está bien estructurado para su propósito."

================================================================================
                          ✅ EJEMPLO DE RESPUESTA CON SUGERENCIAS (cuando solicitud es vaga)
================================================================================

Solicitud: "¿qué puedo mejorar en este proyecto?"
Respuesta: "Aquí hay algunas mejoras que detecté:

1. MEJORAR MANEJO DE ERRORES - Agregar validaciones para índices de arrays
2. UNIFICAR IDIOMA - Los mensajes están en español e inglés mezclados  
3. MODULARIZAR CÓDIG0 - Extraer funciones reutilizables a un archivo utils
4. OPTIMIZAR RENDIMIENTO - Usar caches para cálculos repetitivos
5. AÑADIR DOCUMENTACIÓN - Comentar funciones principales

Elige las que quieras que implemente (ej: "1,3" o "implementa la 2 y 4")"

================================================================================
                          ✅ EJEMPLO DE RESPUESTA EN MODO PLAN (solo si necesitas análisis detallado)
================================================================================

<ANÁLISIS>
    <RESUMEN>Este archivo contiene funciones de autenticación. 
    La función login() valida credenciales y genera un token JWT.</RESUMEN>
    <SUGERENCIAS>
        <PUNTO>Considerar usar bcrypt para hashear contraseñas en lugar de SHA256</PUNTO>
        <PUNTO>Agregar rate limiting para prevenir ataques de fuerza bruta</PUNTO>
        <PUNTO>Separar la lógica de validación en una función independiente</PUNTO>
    </SUGERENCIAS>
    <PREGUNTAS>
        <PREGUNTA>¿Qué nivel de seguridad necesitas? (básico, medio, alto)</PREGUNTA>
        <PREGUNTA>¿El sistema de login debe soportar autenticación de dos factores?</PREGUNTA>
    </PREGUNTAS>
    <ENFOQUES>
        <ENFOQUE>
            <NOMBRE>Enfoque Minimalista</NOMBRE>
            <DESCRIPCION>Solo mejorar lo básico: mejor hasheo y validaciones</DESCRIPCION>
            <IMPACTO>Solo auth.py y utils.py</IMPACTO>
        </ENFOQUE>
        <ENFOQUE>
            <NOMBRE>Enfoque Completo</NOMBRE>
            <DESCRIPCION>Agregar 2FA, logging, rate limiting, auditoría</DESCRIPCION>
            <IMPACTO>Múltiples archivos, mayor tiempo de implementación</IMPACTO>
        </ENFOQUE>
    </ENFOQUES>
</ANÁLISIS>

================================================================================
                           💡 PRÓXIMOS PASOS
================================================================================

Después de esta consulta en MODO PLAN, el usuario podrá:
1. Cambiar a MODO BUILD para obtener el código directamente
2. Pedirte más detalles sobre algún enfoque específico
3. Hacer preguntas adicionales sobre el código

Cuando el usuario cambie a MODO BUILD, seguirá el formato de código XML.

================================================================================
                           🎯 ENFOQUE ESPECÍFICO (IMPORTANTE)
================================================================================

ATENCIÓN: Este es un análisis PUNTUAL, no una revisión completa del proyecto.

📌 ANALIZA SOLO:
   - Los archivos mencionados explícitamente en las instrucciones del usuario
   - Las funciones específicas que el usuario quiere discutir

📌 IGNORA EL RESTO:
   - No analices archivos fuera del scope
   - No sugieras cambios para código no relevante

📌 SI NECESITAS MÁS CONTEXTO:
   - PIDE que te muestren el código específico que necesitas
   - Usa: <ERROR contexto_insuficiente: describe qué necesitas ver>

================================================================================
'''


def get_project_structure(project_path, selected_paths):
    lines = []
    lines.append("=" * 80)
    lines.append("                           🗂️ ESTRUCTURA DEL PROYECTO")
    lines.append("=" * 80)
    lines.append("📁 = Carpeta  |  ☑️ = Archivo con código incluido  |  ⬜ = Archivo no incluido")
    lines.append("")
    lines.append("NOTA: Solo los archivos con ☑️ tienen su código incluido más abajo.")
    lines.append("Los archivos con ⬜ existen pero NO se incluyó su contenido (para ahorrar contexto).")
    lines.append("Si necesitas ver un archivo con ⬜, PIDE que te lo muestren.")
    lines.append("")
    
    def add_tree(path, prefix="", is_last=True):
        rel_path = os.path.relpath(path, project_path)
        
        if path in selected_paths:
            marker = "☑️"
        else:
            marker = "⬜"
        
        if os.path.isdir(path):
            lines.append(f"{prefix}{marker} 📁 {os.path.basename(path)}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            try:
                items = sorted(os.listdir(path))
            except PermissionError:
                lines.append(f"{new_prefix}   [Sin acceso]")
                return
            
            for i, item in enumerate(items):
                if item.startswith('.'):
                    continue
                item_path = os.path.join(path, item)
                is_last_item = (i == len(items) - 1)
                add_tree(item_path, new_prefix, is_last_item)
        else:
            if path in selected_paths:
                marker = "☑️"
            else:
                marker = "⬜"
            lines.append(f"{prefix}{marker} 📄 {os.path.basename(path)}")
    
    add_tree(project_path)
    lines.append("")
    
    return "\n".join(lines)


def get_file_contents(project_path, selected_paths):
    lines = []
    lines.append("=" * 80)
    lines.append("                           📄 CÓDIGO FUENTE")
    lines.append("=" * 80)
    lines.append("")
    
    for path in sorted(selected_paths):
        if os.path.isfile(path):
            rel_path = os.path.relpath(path, project_path)
            lines.append(f"[ARCHIVO: {rel_path}]")
            lines.append("-" * 40)
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content_lines = f.readlines()
                    for i, line in enumerate(content_lines, start=1):
                        lines.append(f"{i:4d}: {line.rstrip()}")
            except Exception as e:
                lines.append(f"[ERROR al leer: {str(e)}]")
            
            lines.append("")
            lines.append("=" * 40)
            lines.append("")
    
    return "\n".join(lines)


def generate_instruction_file(project_path, selected_paths, user_prompt, mode="build"):
    project_name = os.path.basename(project_path)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    mode_label = "🔨 MODO BUILD - GENERACIÓN DE CÓDIGO" if mode == "build" else "📋 MODO PLAN - CONSULTA Y ANÁLISIS"
    
    output = []
    output.append("=" * 80)
    output.append(f"         INSTRUCCIONES PARA IA - {project_name}")
    output.append(f"         Fecha: {date_str}")
    output.append(f"         {mode_label}")
    output.append("=" * 80)
    output.append("")
    
    if mode == "plan":
        output.append(PLAN_MODE_TEMPLATE)
    else:
        output.append(INSTRUCTIONS_TEMPLATE)
    
    output.append("=" * 80)
    output.append("                    📝 INSTRUCCIONES DEL USUARIO")
    output.append("=" * 80)
    output.append("")
    output.append(user_prompt)
    output.append("")
    
    output.append(get_project_structure(project_path, selected_paths))
    
    output.append(get_file_contents(project_path, selected_paths))
    
    output.append("=" * 80)
    
    if mode == "build":
        output.append("                    ✅ INSTRUCCIONES GENERADAS (MODO BUILD)")
        output.append("=" * 80)
        output.append("")
        output.append("⚠️ IMPORTANTE: Solo tienes el código de los archivos enumerados arriba.")
        output.append("Si necesitas ver más código de algún archivo, PIDE que te lo proporcionen.")
        output.append("NO asumas cómo funcionan funciones/variables que no están en el código mostrado.")
        output.append("")
        output.append("📝 CÓMO RESPONDER:")
        output.append("- Delimita tu respuesta con bloques de código (```xml ... ```)")
        output.append("- Responde SOLO con los cambios usando el formato XML especificado")
        output.append("- Si no puedes realizar un cambio, usa el formato <ERROR>")
        output.append("- NO escribas explicaciones fuera de los bloques de código")
    else:
        output.append("                    ✅ INSTRUCCIONES GENERADAS (MODO PLAN)")
        output.append("=" * 80)
        output.append("")
        output.append("⚠️ IMPORTANTE: Solo tienes el código de los archivos enumerados arriba.")
        output.append("Si necesitas ver más código, PIDE que te lo proporcionen.")
        output.append("")
        output.append("En MODO PLAN: Analiza el código, explica, sugiere y pregunta.")
        output.append("NO escribas código completo. Usa el formato <ANÁLISIS>.")
        output.append("Cuando desees código, cambia a MODO BUILD.")
    
    output.append("=" * 80)
    
    output_text = "\n".join(output)
    
    mode_prefix = "plan" if mode == "plan" else "build"
    output_filename = f"{project_name}_instrucciones_{mode_prefix}.txt"
    output_path = os.path.join(project_path, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)
    
    return output_path


def get_selected_file_contents(project_path, selected_paths):
    files_content = {}
    
    for path in selected_paths:
        if os.path.isfile(path):
            rel_path = os.path.relpath(path, project_path)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    files_content[rel_path] = f.read()
            except Exception as e:
                files_content[rel_path] = f"[ERROR al leer: {str(e)}]"
    
    return files_content
