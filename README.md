# RenoApp (Core Orchestrator)

## Introducción
RenoApp es un framework base construido sobre Django diseñado para actuar como un orquestador central de aplicaciones. En lugar de desarrollar funcionalidades monolíticas directamente en el núcleo, este proyecto permite que múltiples aplicaciones (micro-apps o plugins) se integren de forma dinámica y automatizada.

## Objetivo
El objetivo principal de RenoApp es emular una arquitectura modular similar a la de ERPs robustos (como Odoo), pero ofreciendo una **Experiencia de Desarrollo (DX) amigable y moderna**. 

Cada aplicación dentro del ecosistema de RenoApp:
- Se desarrolla como un repositorio o módulo independiente.
- Es descubierta e instalada dinámicamente al colocarse en la carpeta `apps/`.
- Se configura a sí misma a través de un manifiesto `__app__.json` que define sus rutas, dependencias y configuraciones.
- Se mantiene completamente aislada y desacoplada del código base central.

Este diseño permite que los equipos de desarrollo puedan escalar funcionalidades rápidamente sin tocar el núcleo (Core), reduciendo cuellos de botella y facilitando el mantenimiento a largo plazo.
