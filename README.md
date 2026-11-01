# minecraft-plugins

Lista de plugins de mi servidor Paper y un script que los deja al día con un comando.

El repo **no guarda los `.jar`**: solo la lista ([`plugins.txt`](plugins.txt)). El script descarga cada plugin desde [Modrinth](https://modrinth.com), elige la versión para la versión de Minecraft del servidor, comprueba el hash SHA-512 y reemplaza el `.jar` viejo. Los viejos se guardan en `plugins-respaldo/<fecha>/` junto a la carpeta `plugins`, por si hay que volver atrás.

## Uso

Instalación (una vez, dentro del servidor):

```bash
apt install -y git python3
git clone https://github.com/ex6tense/minecraft-plugins /opt/minecraft-plugins
```

Actualizar (hace `git pull` del repo y luego actualiza los plugins):

```bash
python3 /opt/minecraft-plugins/actualizar.py
```

Después, reinicia el servidor para que cargue los plugins nuevos.

Opciones:

| Opción | Para qué |
|---|---|
| `-n` / `--simular` | Muestra qué cambiaría, sin tocar nada |
| `--dir RUTA` | Carpeta `plugins` del servidor (por defecto la de la instancia de AMP) |
| `--mc 26.3` | Fuerza la versión de Minecraft si no se detecta sola (se lee de `version_history.json`) |
| `--sin-pull` | No hace `git pull` antes |

Si un plugin todavía no tiene versión para tu Minecraft exacto, se instala la más nueva de la misma serie (por ejemplo 26.2 en un servidor 26.3) y el script lo avisa.

## Añadir o quitar un plugin

Edita [`plugins.txt`](plugins.txt): una línea por plugin con su *slug* de Modrinth (lo que va después de `modrinth.com/plugin/`) y los patrones de los `.jar` que reemplaza. Para quitar uno, comenta su línea con `#` y borra su `.jar` de la carpeta `plugins`.

## Cambios respecto a lo que tenía

- **ProTPA → TPA** (`tpaa`): ProTPA dejó de actualizarse en 1.21.7.
- **DeathChest → AxGraves**: DeathChest perdió los datos de los cofres al pasar a 26.x.
- **Sleeper → regla de juego**: Minecraft ya lo trae: `gamerule players_sleeping_percentage 1` (basta con que duerma uno).
- InteractionVisualizer y Damage Indicator quedan como opcionales; CoreProtect está en la lista, comentado, para registrar quién rompe o abre qué.

## Modpack para los jugadores

El chat de voz necesita un mod en cada cliente. El pack (`.mrpack`) lo instala todo de una vez: Minecraft 26.3, Fabric Loader, Fabric API, Simple Voice Chat y Sodium. Además deja el servidor `mc.ex6tenseiscool.co.in` ya añadido en la lista, con su paquete de recursos aceptado.

Para jugar:

1. Instala un launcher que importe `.mrpack`:
   - Cuenta **premium**: [Modrinth App](https://modrinth.com/app) o [Prism Launcher](https://prismlauncher.org).
   - Cuenta **no premium**: [PrismLauncher-Cracked](https://github.com/Diegiwg/PrismLauncher-Cracked/releases) (descárgalo solo de ahí). En **Cuentas → Añadir offline** usa el mismo nombre que está en la whitelist.
2. Descarga el pack: [ex6tense-26.3.mrpack](https://github.com/ex6tense/minecraft-plugins/raw/main/dist/ex6tense-26.3.mrpack).
3. En el launcher: **Añadir instancia → Importar** y elige el `.mrpack`.
4. Abre la instancia y entra al servidor. En el juego, **V** abre la configuración de voz.

Para regenerarlo cuando cambie la versión del servidor o salgan versiones nuevas de los mods:

```bash
python3 generar_pack.py --mc 26.3
```

Sobrescribe el archivo en `dist/`; haz commit y push para que el enlace de descarga sirva la versión nueva.

## Pruebas

```bash
python3 test_actualizar.py
```
