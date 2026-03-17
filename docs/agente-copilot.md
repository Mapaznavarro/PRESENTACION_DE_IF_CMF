# ¿Por qué aparece "Start 'playwright' MCP server" al usar el agente?

Cuando le pides una tarea al **agente de GitHub Copilot** (Copilot Coding Agent), éste
muestra en pantalla una sección llamada **"Setting up environment"** con tres líneas:

```
Setting up environment
  Start 'playwright' MCP server   >
  Start 'github-mcp-server' MCP server   >
  Start agent firewall   >
```

Esta sección puede generar confusión porque aparece antes de que el agente haga
cualquier trabajo visible. A continuación se explica qué es cada elemento y por qué
están presentes.

---

## ¿Qué es un "MCP server"?

**MCP** significa **Model Context Protocol** (Protocolo de Contexto para Modelos).
Es un estándar abierto que permite a un modelo de lenguaje (como el que usa el agente
de Copilot) conectarse a herramientas externas de forma estructurada.

Cada "MCP server" es un pequeño proceso que corre en segundo plano y expone un
conjunto de herramientas al agente. El agente decide si las usa o no, según la tarea
que reciba.

---

## ¿Para qué sirve cada servidor?

### 1. `playwright` MCP server — servidor de automatización de navegador

[Playwright](https://playwright.dev/) es una biblioteca de automatización de
navegadores web (Chrome, Firefox, Safari). El MCP de Playwright le da al agente la
capacidad de:

| Herramienta | Para qué sirve |
|-------------|----------------|
| Abrir URLs  | Visitar páginas web para leer su contenido actual |
| Tomar capturas de pantalla | Mostrarle al usuario cómo quedó un cambio en una UI |
| Hacer clic / escribir | Interactuar con formularios o aplicaciones web |
| Leer el DOM | Inspeccionar el HTML de una página para extraer datos |

**¿Se usa en este repositorio?**
Para tareas puramente de documentación Markdown (como las de este repositorio) el
agente **generalmente no necesita abrir ningún navegador**. Sin embargo, el servidor
se inicia de todas formas porque:

- El agente no sabe de antemano qué herramientas va a necesitar; las carga todas al
  inicio por si acaso.
- Si en una tarea el agente necesita visitar `cmfchile.cl` para verificar una norma, o
  tomar una captura de pantalla de un resultado, ya tiene el servidor disponible.
- Iniciarlo es barato (milisegundos) y no tiene ningún costo si no se usa.

En resumen: **se inicia por precaución, no porque vaya a abrir el navegador
obligatoriamente en tu tarea**.

---

### 2. `github-mcp-server` MCP server — servidor de acceso a GitHub

Este servidor le da al agente acceso a la API de GitHub. Con él puede:

| Herramienta | Para qué sirve |
|-------------|----------------|
| Leer issues y PRs | Entender el contexto del problema que se le pide resolver |
| Leer commits y ramas | Conocer la historia reciente del repositorio |
| Leer el contenido de archivos (a través de la API) | Complementar el acceso directo al sistema de archivos |
| Buscar código en GitHub | Encontrar ejemplos o referencias en otros repos |

**¿Se usa en este repositorio?**
Sí. Cada vez que le asignas un issue al agente, éste usa el `github-mcp-server` para
leer el texto del issue, sus comentarios, y el estado del PR asociado. Es el servidor
que más se utiliza en este flujo de trabajo.

---

### 3. Agent firewall — cortafuegos del agente

No es un MCP server, sino una capa de seguridad que controla a qué dominios de
internet puede conectarse el agente durante su ejecución. Su propósito es:

- **Evitar filtraciones de datos**: impide que el agente envíe información del
  repositorio a servicios externos no autorizados.
- **Limitar el alcance**: el agente solo puede acceder a dominios de GitHub, npm,
  PyPI, etc., no a cualquier URL arbitraria.
- **Auditoría**: registra qué conexiones se intentan para que el equipo de GitHub
  pueda revisar el comportamiento del agente.

---

## Resumen visual

```
┌─────────────────────────────────────────────────────────┐
│                   Agente de Copilot                     │
│                                                         │
│  ┌─────────────────┐  ┌──────────────────┐              │
│  │  playwright MCP │  │ github-mcp-server│              │
│  │  (navegador web)│  │  (API de GitHub) │              │
│  └────────┬────────┘  └────────┬─────────┘              │
│           │                   │                         │
│           └──────────┬────────┘                         │
│                      │                                  │
│              ┌───────▼────────┐                         │
│              │ Agent firewall │                         │
│              │  (seguridad)   │                         │
│              └───────┬────────┘                         │
│                      │                                  │
│                   Internet                              │
└─────────────────────────────────────────────────────────┘
```

---

## ¿Qué pasa si el agente no usa Playwright en mi tarea?

El servidor se inicia, espera posibles instrucciones del modelo, y al final de la
tarea se detiene. Si el agente nunca le envió ninguna instrucción, Playwright nunca
abrió ningún navegador ni consumió recursos apreciables.

Puedes comprobarlo expandiendo la línea `Start 'playwright' MCP server >` en la
interfaz: si no aparece ninguna herramienta de navegador entre los pasos del agente
(como `browser_navigate`, `browser_take_screenshot`, etc.), es que no se usó.

---

## ¿Puedo desactivar Playwright para este repositorio?

El conjunto de MCP servers que se inician es una configuración del agente de GitHub
Copilot, no del repositorio en sí. No existe hoy en día un archivo de configuración
dentro del repositorio que permita deshabilitar servidores MCP individuales. Esa
opción podría estar disponible en el futuro a través de la configuración de la
organización o del repositorio en GitHub.

---

## Referencias

- [Documentación de MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Playwright – automatización de navegadores](https://playwright.dev/)
- [GitHub Copilot Coding Agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent)
