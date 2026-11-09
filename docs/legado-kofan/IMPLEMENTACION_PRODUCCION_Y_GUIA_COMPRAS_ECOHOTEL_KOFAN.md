# 🚀 Documento Técnico de Implementación y Guía de Compras
## Proyecto: **Ecohotel Kofán**

**Institución:** SENA  
**Ficha:** 2997671  
**Fase del proyecto:** Despliegue final a producción  
**Arquitectura:** `FastAPI + Vue 3 + MongoDB Atlas`  
**Fecha:** 11 de abril de 2026

---

## 1. Objetivo del documento

Este documento define la estrategia técnica para poner **Ecohotel Kofán** en producción y presenta una **guía de compras** para el cliente final (hotel), con enfoque en continuidad operativa, bajo costo de mantenimiento y compatibilidad con la interfaz web del sistema.

El sistema está compuesto por:

- **Frontend:** Vue 3 + Vite, desplegable como sitio estático.
- **Backend:** FastAPI, autenticación JWT, subida de archivos, servicios REST.
- **Base de datos:** MongoDB Atlas (`kofan_hospedaje_db`).
- **Archivos estáticos:** imágenes y comprobantes almacenados en el backend (`/static/uploads`).

---

# 2. Requisitos de Infraestructura (Servidor)

## 2.1 Supuestos de carga

Para este análisis se considera el siguiente escenario de producción:

- Hasta **100 reservas simultáneas** en momentos pico.
- Acceso concurrente de:
  - recepción,
  - administración,
  - clientes web,
  - consulta de galería y catálogo.
- Subida ocasional de imágenes y comprobantes de pago.
- MongoDB operando externamente en **Atlas**, por lo cual el servidor de aplicación no aloja la base de datos.

> **Conclusión técnica:** el backend no requiere una máquina extremadamente grande, pero sí una instancia **estable**, con buena conectividad, SSD y margen para archivos estáticos, logs y picos de tráfico.

## 2.2 Recomendación de VPS / Hosting backend

### Opción recomendada para producción real

| Recurso | Recomendación mínima | Recomendación ideal |
|---|---:|---:|
| CPU | `2 vCPU` | `4 vCPU` |
| RAM | `4 GB` | `8 GB` |
| Almacenamiento | `80 GB SSD` | `160 GB NVMe/SSD` |
| Transferencia | `1 TB/mes` | `2 TB/mes o más` |
| SO | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Red | IPv4 pública + firewall | IPv4 + firewall + snapshots |

### Capacidad sugerida para 100 reservas simultáneas

| Escenario | Especificación | Observación |
|---|---|---|
| **Piloto / baja carga** | `2 vCPU / 4 GB / 80 GB SSD` | Adecuado para validaciones, pruebas y operación ligera |
| **Producción recomendada** | `4 vCPU / 8 GB / 160 GB SSD` | Recomendado para el hotel con uso diario y picos de reservas |
| **Crecimiento futuro** | `4-8 vCPU / 16 GB` | Si se agregan más sedes, reportes más pesados o integraciones nuevas |

## 2.3 Comparativa sugerida de proveedores

| Proveedor | Plan sugerido | Rango estimado | Ventajas | Observación |
|---|---|---:|---|---|
| **DigitalOcean** | Droplet Premium `4 vCPU / 8 GB` | **USD 48-56/mes** | Simple, estable, buen costo-beneficio | **Recomendado** |
| **AWS Lightsail** | `4 vCPU / 8 GB` | **USD 40-60/mes** | Integración cloud y escalabilidad | Más técnico de administrar |
| **Render** | Web Service `2-4 GB` | **USD 25-85/mes** | Despliegue simple | Menor control que un VPS |
| **Hetzner** | CX/CP equivalente | **USD 20-40/mes** | Muy buen precio | Data center fuera de LATAM |

### Recomendación final

Para **Ecohotel Kofán**, el mejor equilibrio entre costo, control y facilidad de mantenimiento es:

- **Backend:** VPS en **DigitalOcean** o **AWS Lightsail**
- **Frontend:** **Netlify** o **Vercel**
- **Base de datos:** **MongoDB Atlas**
- **Dominio + DNS:** **Cloudflare**

---

# 3. Estrategia de Despliegue (Deployment)

## 3.1 Arquitectura de producción recomendada

```text
Usuario web
   ↓
Frontend Vue (Netlify / Vercel)
   ↓ HTTPS
API FastAPI (Docker en VPS)
   ↓ TLS / IP allowlist
MongoDB Atlas
```

## 3.2 Despliegue del Backend con Docker

### Paso 1. Preparar el servidor VPS

Instalar en Ubuntu:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw
sudo systemctl enable docker
sudo systemctl start docker
```

### Paso 2. Crear `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Paso 3. Crear `docker-compose.yml`

```yaml
version: '3.9'
services:
  ecohotel-api:
    build:
      context: .
    container_name: ecohotel-api
    restart: always
    env_file:
      - ./backend/.env.production
    ports:
      - "8000:8000"
    volumes:
      - ./backend/static/uploads:/app/backend/static/uploads
```

### Paso 4. Variables de entorno del backend

Archivo sugerido: `backend/.env.production`

```env
MONGO_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/kofan_hospedaje_db
SECRET_KEY=<generar_clave_larga_y_segura>
APP_ENV=production
ALLOWED_ORIGINS=https://ecohotelkofan.com,https://www.ecohotelkofan.com
```

> ⚠️ **Recomendación crítica de seguridad:** si durante desarrollo las credenciales de Atlas o la clave JWT estuvieron visibles en archivos del proyecto, deben **rotarse** antes del lanzamiento.

### Paso 5. Levantar el contenedor

```bash
docker compose up -d --build
```

### Paso 6. Configurar Nginx como reverse proxy

```nginx
server {
    server_name api.ecohotelkofan.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activación de SSL:

```bash
sudo certbot --nginx -d api.ecohotelkofan.com
```

---

## 3.3 Despliegue del Frontend en Netlify o Vercel

### Paso 1. Compilación del frontend

```bash
npm install
npm run build
```

### Paso 2. Variables de entorno del frontend

Archivo sugerido: `frontend/.env.production`

```env
VITE_API_URL=https://api.ecohotelkofan.com
VITE_BACKEND_URL=https://api.ecohotelkofan.com
```

> **Importante:** actualmente el proyecto usa tanto `VITE_API_URL` como `VITE_BACKEND_URL` en distintos componentes. En producción conviene definir **ambas** para evitar inconsistencias.

### Paso 3. Configurar el hosting estático

| Servicio | Configuración recomendada |
|---|---|
| **Netlify** | Build command: `npm run build` / Publish directory: `dist` |
| **Vercel** | Framework preset: `Vite` / Output: `dist` |

### Paso 4. Conectar dominio

- `ecohotelkofan.com` → frontend
- `api.ecohotelkofan.com` → backend

---

## 3.4 Configuración de producción recomendada

### Seguridad

- Cambiar `SECRET_KEY` por una clave fuerte de al menos **32-64 caracteres**.
- Restringir orígenes CORS a los dominios reales del hotel.
- Habilitar firewall (`ufw`) para puertos `22`, `80` y `443`.
- No exponer MongoDB al público; usar solo MongoDB Atlas con usuarios restringidos.
- Activar autenticación de dos factores en cuentas cloud y Atlas.

### Operación

- Mantener los archivos subidos en volumen persistente.
- Implementar logs del contenedor y revisión semanal.
- Reinicio automático del contenedor con `restart: always`.

---

# 4. Sugerencias de Compra (Hardware y Servicios)

## 4.1 Hardware para recepción del hotel

La interfaz del sistema es web, moderna y liviana; por tanto no requiere hardware empresarial costoso. Sí se recomienda equipo **confiable**, SSD y buena conectividad.

### Opción A. PC recomendada para recepción

| Componente | Especificación sugerida |
|---|---|
| Procesador | Intel Core i3 / Ryzen 3 / Intel N100 |
| RAM | **8 GB mínimo**, ideal **16 GB** |
| Disco | SSD `256 GB` o `512 GB` |
| Pantalla | 21" a 24" Full HD |
| Sistema operativo | Windows 11 Pro o Ubuntu LTS |
| Navegador | Chrome o Edge actualizados |

### Opción B. Tablet para movilidad o atención ligera

| Componente | Especificación sugerida |
|---|---|
| Pantalla | `10" a 11"` |
| RAM | `4-6 GB` |
| Almacenamiento | `128 GB` |
| Sistema | Android 13+ o iPadOS vigente |
| Conectividad | WiFi dual band |

> **Recomendación práctica:** para recepción fija, se recomienda más una **PC o mini PC con monitor**. La tablet es útil como equipo complementario, no como estación principal.

## 4.2 Suministros de oficina recomendados

| Elemento | Recomendación | Uso en el sistema | Rango estimado |
|---|---|---|---:|
| **Impresora térmica 80 mm** | Epson TM-T20III / XPrinter XP-Q80 | Recibos, comprobantes e impresión rápida desde PDF/HTML | **COP 350.000 - 900.000** |
| **Impresora A4** | HP LaserJet o Epson EcoTank | Facturas completas y documentos administrativos | **COP 650.000 - 1.300.000** |
| **UPS / respaldo de energía** | 1000-1500 VA | Protección ante cortes de energía en Putumayo | **COP 350.000 - 900.000** |
| **Router estable** | TP-Link / MikroTik dual band | Conectividad interna para recepción y administración | **COP 180.000 - 450.000** |
| **Disco externo** | 1 TB USB 3.0 | Copias de respaldo locales mensuales | **COP 220.000 - 320.000** |

### Recomendación especial para energía

Dado el contexto regional, se recomienda adquirir un **UPS de al menos 1200 VA** para proteger:

- PC de recepción
- Router / módem
- impresora térmica (si aplica)

Esto evita interrupciones durante el registro de reservas y el cierre de caja.

## 4.3 Dominios y SSL

| Servicio | Recomendación | Costo estimado |
|---|---|---:|
| Dominio `.com` | `ecohotelkofan.com` | **USD 12 - 18/año** |
| Dominio `.co` | `ecohotelkofan.co` | **USD 25 - 35/año** |
| SSL | **Let's Encrypt** o SSL integrado de Cloudflare/Netlify | **Gratis** |
| DNS / CDN | Cloudflare | **Gratis** o Pro desde **USD 20/mes** |

> **Recomendación:** comprar ambos dominios (`.com` y `.co`) si el presupuesto lo permite, dejando uno como principal y el otro redirigido.

---

# 5. Presupuesto estimado

## 5.1 Presupuesto de servicios digitales mensuales

| Concepto | Opción recomendada | Estimado mensual |
|---|---|---:|
| VPS backend | DigitalOcean / Lightsail `4 vCPU + 8 GB` | **USD 40 - 56** |
| MongoDB Atlas | M10 o equivalente | **USD 57 - 95** |
| Frontend hosting | Netlify / Vercel | **USD 0 - 20** |
| DNS / CDN | Cloudflare | **USD 0 - 20** |
| Backups / snapshots | según proveedor | **USD 5 - 15** |

### Estimado mensual total

- **Escenario austero:** `USD 97 - 122/mes`
- **Escenario recomendado:** `USD 125 - 191/mes`

## 5.2 Presupuesto de compra inicial en hardware

| Elemento | Rango estimado COP |
|---|---:|
| PC o mini PC recepción | **1.400.000 - 2.500.000** |
| Monitor Full HD | **450.000 - 750.000** |
| Impresora térmica | **350.000 - 900.000** |
| UPS 1200-1500 VA | **350.000 - 900.000** |
| Router dual band | **180.000 - 450.000** |
| Disco externo 1 TB | **220.000 - 320.000** |

### Estimado total de compra inicial

- **Rango sugerido:** **COP 2.950.000 a COP 5.820.000**

---

# 6. Plan de Capacitación y Mantenimiento

## 6.1 Cronograma de capacitación (4 sesiones)

| Sesión | Tema | Duración | Participantes | Resultado esperado |
|---|---|---:|---|---|
| **1** | Ingreso al sistema, navegación y seguridad básica | 2 horas | Recepción + administración | Personal accede correctamente y entiende roles |
| **2** | Registro de reservas, validación de pagos y atención al huésped | 2 horas | Recepción | Flujo completo de reserva sin asistencia técnica |
| **3** | Gestión administrativa: usuarios, habitaciones, galería y configuración | 2 horas | Administrador | Uso autónomo del panel de administración |
| **4** | Contingencias, backups, cierre de jornada y soporte básico | 2 horas | Encargado del hotel + apoyo administrativo | Operación segura y respuesta ante incidentes |

### Material sugerido para capacitación

- Manual PDF con capturas del sistema
- Video corto de 5-10 minutos por módulo
- Lista impresa de procedimientos de contingencia
- Credenciales de prueba y entorno controlado

---

## 6.2 Plan de backups semanales (MongoDB Atlas)

### Política recomendada

| Frecuencia | Acción |
|---|---|
| **Diaria** | Verificar integridad del servicio y uso de almacenamiento |
| **Semanal** | Ejecutar backup lógico completo de MongoDB |
| **Mensual** | Probar restauración en entorno de prueba |
| **Trimestral** | Revisar retención, costos y crecimiento de datos |

### Procedimiento semanal sugerido

1. Programar el respaldo los **domingos a las 2:00 a. m.**
2. Ejecutar exportación lógica:

```bash
mongodump --uri="$MONGO_URI" --gzip --archive=/backups/kofan_$(date +%Y%m%d).gz
```

3. Conservar:
   - **4 copias semanales**
   - **3 copias mensuales**
4. Subir los respaldos a:
   - Google Drive institucional, o
   - bucket S3 / almacenamiento cloud privado
5. Respaldar también la carpeta de archivos:

```bash
/backend/static/uploads
```

> **Clave:** no basta con respaldar MongoDB; también deben respaldarse las imágenes, comprobantes y archivos subidos por los usuarios.

---

# 7. Checklist para el día del lanzamiento 🚦

## 7.1 Lista de verificación técnica

- [ ] Dominio principal comprado y configurado
- [ ] Subdominio `api.` apuntando al VPS
- [ ] Certificados SSL activos
- [ ] Variables de entorno de producción cargadas
- [ ] `SECRET_KEY` cambiada por una clave segura
- [ ] Credenciales de MongoDB rotadas y protegidas
- [ ] Contenedor Docker funcionando correctamente
- [ ] Frontend publicado en Netlify/Vercel
- [ ] Conexión frontend ↔ backend validada en producción
- [ ] CORS restringido al dominio final
- [ ] Prueba de login exitosa
- [ ] Prueba de reserva exitosa
- [ ] Prueba de actualización administrativa exitosa
- [ ] Prueba de galería y carga de imágenes exitosa
- [ ] Backup inicial ejecutado y almacenado
- [ ] UPS instalado y probado
- [ ] Impresora configurada y probada

## 7.2 Lista de verificación operativa

- [ ] Recepcionista capacitado
- [ ] Administrador capacitado
- [ ] Usuario de soporte definido
- [ ] Manual básico entregado al hotel
- [ ] Contacto de soporte post-lanzamiento disponible
- [ ] Horario de monitoreo del primer día definido

---

# 8. Recomendación final de implementación

Para el lanzamiento de **Ecohotel Kofán**, se recomienda la siguiente combinación:

### Arquitectura recomendada final
- **Frontend:** Netlify o Vercel
- **Backend:** Docker en VPS Ubuntu (`4 vCPU / 8 GB / 160 GB SSD`)
- **Base de datos:** MongoDB Atlas
- **Dominio y DNS:** Cloudflare
- **Recepción:** PC con 8-16 GB RAM + UPS + impresora térmica

### Beneficios de esta configuración
- Bajo costo operativo comparado con infraestructura tradicional
- Facilidad de mantenimiento y escalado
- Mejor seguridad con SSL y separación de capas
- Continuidad operativa para el hotel incluso en condiciones de conectividad variables

---

## 9. Cierre

Este documento constituye una base práctica para la puesta en producción del sistema **Ecohotel Kofán**, permitiendo al cliente comprender:

- qué infraestructura necesita,
- cómo se realiza el despliegue,
- qué compras son recomendables,
- y cómo sostener la operación mediante capacitación y mantenimiento preventivo.

Si se desea, este documento puede complementarse con un **anexo de costos reales cotizados en Colombia** y una **matriz de riesgos del lanzamiento**.
