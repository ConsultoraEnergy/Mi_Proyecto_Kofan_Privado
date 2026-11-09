# 🌿 Manual de Usuario
## **Ecohotel Kofán**

**Dirigido a:** personal administrativo y de recepción  
**Versión:** 1.0  
**Fecha:** 11 de abril de 2026

---

## Bienvenida

¡Bienvenido al sistema **Ecohotel Kofán**!  
Este manual fue elaborado para ayudarle a usar la plataforma de forma clara, rápida y tranquila, incluso si tiene conocimientos básicos de tecnología.

El sistema permite:

- consultar el estado general del hotel,
- registrar y administrar reservas,
- realizar **Check-in** y **Check-out**,
- actualizar habitaciones y fotografías,
- cambiar datos de contacto y configuración general.

> **Consejo:** use este manual como guía de apoyo durante la jornada. Está organizado por temas para encontrar rápido lo que necesita.

---

# 1. Guía de Inicio Rápido

## 1.1 Cómo ingresar al sistema

1. Abra el navegador de internet (preferiblemente **Google Chrome** o **Microsoft Edge**).
2. Ingrese a la dirección del sistema:

```text
https://ecohotelkofan.com/auth/login
```

> Si el sistema aún está en pruebas, use la URL entregada por el desarrollador o administrador técnico.

3. En la pantalla de acceso, escriba:
   - **Correo Electrónico**
   - **Contraseña**
4. Haga clic en el botón **Ingresar**.

Si los datos son correctos, el sistema lo llevará automáticamente al panel principal.

---

## 1.2 Qué encontrará en el Dashboard

El **Dashboard** es la pantalla principal del panel administrativo. Allí puede ver de forma rápida el estado del hotel.

### Indicadores principales

- **Ingresos del Mes**: muestra el valor acumulado de ingresos registrados en el periodo.
- **Huéspedes Hoy**: indica cuántas personas están actualmente en las instalaciones.
- **Ocupación**: porcentaje de habitaciones ocupadas frente al total disponible.
- **Check-ins hoy**: cantidad de llegadas esperadas o registradas.
- **Check-outs hoy**: cantidad de salidas programadas o cerradas.
- **Reservas activas**: reservas pendientes, confirmadas o en curso.

### Alertas y avisos

En el panel también se puede consultar el historial de avisos o actividad reciente. Allí verá mensajes como:

- próximas llegadas,
- cambios de estado en reservas,
- movimientos registrados por administración.

Si observa una alerta importante, revise de inmediato el módulo **Reservas**.

---

# 2. Gestión de Reservas (el corazón del sistema)

Este módulo es el más importante para recepción, ya que permite registrar huéspedes, controlar su llegada y salida, y generar la cuenta en PDF.

## 2.1 Cómo crear una reserva desde el calendario interactivo

### Ruta sugerida
**Menú lateral → Habitaciones**

### Paso a paso

1. Ingrese al panel **Habitaciones**.
2. Busque la habitación deseada.
3. Haga clic en el botón **Calendario**.
4. Se abrirá una ventana con el calendario interactivo.
5. Seleccione:
   - la **fecha de entrada**,
   - la **fecha de salida**.

> Los días marcados en rojo no están disponibles.

6. Haga clic en **Continuar**.
7. Complete los datos del huésped:
   - **Nombre del cliente**
   - **Correo electrónico**
   - **Celular**
   - **Monto total**
   - **Observaciones** (si aplica)
8. Confirme la acción para registrar la reserva.

### Recomendación
Antes de guardar, confirme con el huésped:
- número de noches,
- valor total,
- datos de contacto.

---

## 2.2 Cómo confirmar una reserva

### Ruta sugerida
**Menú lateral → Reservas**

Cuando una reserva está pendiente de validación:

1. Abra el módulo **Reservas**.
2. Ubique la reserva en la pestaña **Pendientes** o **Próximas**.
3. Revise la información del cliente.
4. Haga clic en **Confirmar Pago** o en el botón de confirmación correspondiente.
5. Verifique que el estado cambie a **Confirmada**.

---

## 2.3 Cómo realizar el Check-in

El **Check-in** se hace cuando el huésped llega al hotel.

### Paso a paso

1. Abra el módulo **Reservas**.
2. Busque la reserva del huésped.
3. Haga clic en **Hacer Check-in**.
4. En la ventana emergente, revise y complete:
   - **Nombre completo / Razón social**
   - **Tipo de documento**
   - **Número de documento**
   - **Celular**
   - **Correo electrónico**
   - **Acompañantes** (si vienen más personas)
   - **Consumos extra** (si aplica)
5. Verifique las fechas de estadía.
6. Confirme el proceso guardando los datos.

### Resultado esperado
- la reserva cambia a estado **Ocupada / En casa**,
- el sistema crea automáticamente la **cuenta de cobro**.

---

## 2.4 Cómo realizar el Check-out

El **Check-out** se hace cuando el huésped finaliza su estadía.

### Paso a paso

1. Vaya al módulo **Reservas**.
2. Busque la reserva que está en estado **Ocupada / En casa**.
3. Revise si hay consumos pendientes.
4. Haga clic en **Hacer Check-out**.
5. El sistema cerrará la estancia y dejará lista la cuenta final.

### Recomendación
Antes del Check-out, confirme:
- fecha final correcta,
- total de cobro,
- consumos adicionales registrados.

---

## 2.5 Cómo editar una reserva existente

Si necesita actualizar información del huésped o agregar consumos:

1. Ingrese al módulo **Reservas**.
2. Ubique la reserva correspondiente.
3. Haga clic en **Editar Detalles o Agregar Consumos**.
4. Realice los cambios necesarios en:
   - datos del titular,
   - acompañantes,
   - fecha de salida,
   - consumos extra.
5. Haga clic en **Guardar**.

El sistema actualizará la información y, si ya existe cuenta abierta, sincronizará los valores.

---

## 2.6 Cómo generar la factura o cuenta en PDF

1. Ingrese al módulo **Reservas**.
2. Busque la reserva finalizada o con cuenta disponible.
3. Haga clic en **Ver Estado de Cuenta / Factura**.
4. Se abrirá una ventana con el resumen del cobro.
5. Haga clic en **Descargar PDF**.

El archivo se guardará automáticamente en el equipo y podrá imprimirse o enviarse al huésped.

> **Nota importante:** la cuenta de cobro se habilita después del **Check-in**.

---

# 3. Administración de Habitaciones

## 3.1 Cómo cambiar el estado de una habitación

### Ruta sugerida
**Menú lateral → Habitaciones**

En el sistema, las habitaciones pueden reflejar distintos escenarios operativos:

- **Disponible**: se puede reservar normalmente.
- **Ocupada**: ya tiene un huésped con Check-in activo.
- **Mantenimiento**: debe bloquearse temporalmente para que no reciba nuevas reservas.

### Para poner una habitación en mantenimiento

1. Vaya a **Habitaciones**.
2. Haga clic en **Editar habitación**.
3. Busque el campo **Estado**.
4. Seleccione **En Mantenimiento (Bloqueada)**.
5. Guarde los cambios.

### Para volverla a dejar disponible

1. Abra de nuevo la habitación en **Editar**.
2. Cambie el estado a **Disponible / Activa**.
3. Haga clic en **Guardar**.

> El estado de **ocupada** suele estar ligado al proceso de **Check-in** de una reserva.

---

## 3.2 Cómo subir o actualizar fotos de habitaciones

### Para agregar una nueva habitación con fotos

1. Ingrese a **Habitaciones**.
2. Haga clic en **Registrar Habitación**.
3. Complete los datos:
   - **Número de habitación**
   - **Nombre**
   - **Precio**
   - **Capacidad**
   - **Tipo**
   - **Distribución de camas**
4. Cargue las imágenes en el cargador de fotos.
5. Presione **Guardar**.

### Para cambiar o agregar fotos a una habitación existente

1. Busque la habitación en el listado.
2. Haga clic en **Editar**.
3. Agregue nuevas imágenes o elimine las que ya no se usarán.
4. Guarde los cambios.

### Recomendaciones para las fotos

- Use imágenes claras y bien iluminadas.
- Evite archivos demasiado pesados.
- Suba máximo las fotos realmente necesarias para mostrar bien el espacio.

---

# 4. Panel de Configuración

### Ruta sugerida
**Menú lateral → Configuración**

Este panel permite ajustar los datos generales del hotel.

## 4.1 Qué puede cambiar aquí

- **Nombre del hospedaje**
- **Correo de contacto**
- **Teléfono principal**
- **Dirección física**
- **Hora de Check-in**
- **Hora de Check-out**
- **Moneda base**
- **Impuesto / IVA (%)**
- **Redes sociales**
- **Número de WhatsApp**
- **Logo del hotel**

## 4.2 Cómo guardar cambios

1. Abra **Configuración**.
2. Ubique la sección que desea editar:
   - **Esencia del hotel**
   - **Operación diaria**
   - **Canales de contacto**
3. Cambie los campos necesarios.
4. Haga clic en **Guardar cambios del hotel**.

Si todo salió bien, el sistema mostrará un mensaje de confirmación.

---

## 4.3 Sobre los precios de temporada

Actualmente, el sistema permite cambiar fácilmente el **precio por habitación** desde el módulo **Habitaciones**.

### Para actualizar el precio

1. Ingrese a **Habitaciones**.
2. Haga clic en **Editar** sobre la habitación deseada.
3. Cambie el valor en el campo **Precio**.
4. Guarde los cambios.

> Si el hotel maneja temporadas alta, media o baja, se recomienda que el administrador defina internamente cuándo cambiar estos valores para mantener una tarifa correcta.

---

# 5. Preguntas Frecuentes (FAQ) y Solución de Problemas

## 5.1 ¿Qué hacer si el sistema no carga?

Siga estos pasos en orden:

1. Verifique que haya conexión a internet.
2. Recargue la página con la tecla **F5** o el botón del navegador.
3. Cierre y vuelva a abrir el navegador.
4. Intente ingresar nuevamente al sistema.
5. Si el problema continúa, comuníquese con soporte técnico.

---

## 5.2 ¿Qué hacer si no puedo iniciar sesión?

Revise lo siguiente:

- que el **correo electrónico** esté bien escrito,
- que la **contraseña** no tenga errores de digitación,
- que no esté activado el bloqueo de mayúsculas (**Caps Lock**).

Si sigue sin poder entrar, contacte al administrador del sistema.

---

## 5.3 ¿Cómo recuperar la contraseña?

En la versión actual del sistema, la recuperación de contraseña se realiza con apoyo del administrador o del encargado técnico.

### Procedimiento recomendado

1. Informe el inconveniente al responsable del sistema.
2. Verifique su identidad.
3. Solicite el restablecimiento o asignación de una nueva contraseña temporal.
4. Inicie sesión nuevamente con la clave entregada.

> **Sugerencia operativa:** cambiar la contraseña temporal tan pronto como se recupere el acceso.

---

## 5.4 ¿Qué hago si no aparece la factura en PDF?

Revise primero:

- si el huésped ya tiene **Check-in** realizado,
- si la reserva tiene una cuenta abierta,
- si el navegador permite descargas.

Luego:
1. cierre la ventana,
2. vuelva a abrir **Ver Estado de Cuenta / Factura**,
3. pulse otra vez **Descargar PDF**.

---

## 5.5 ¿Qué hago si una habitación no aparece disponible?

Puede deberse a tres causas:

- tiene una reserva activa,
- está marcada como **En Mantenimiento**,
- fue desactivada temporalmente.

Revise el módulo **Habitaciones** y confirme su estado antes de ofrecerla.

---

# 6. Buenas prácticas de uso

Para una operación tranquila y ordenada, se recomienda:

- revisar el **Dashboard** al iniciar la jornada,
- confirmar cada reserva antes de hacer cambios,
- registrar acompañantes y consumos en el momento oportuno,
- cerrar correctamente el **Check-out** al final de la estancia,
- evitar compartir contraseñas entre empleados,
- cerrar sesión al terminar el turno usando el botón **Salir**.

---

# 7. Cierre

El sistema **Ecohotel Kofán** fue diseñado para que la recepción y la administración puedan trabajar de forma organizada, amable y eficiente.

Si en algún momento surge una duda, este manual puede servir como apoyo rápido.  
Y si el hotel lo requiere, este documento puede ampliarse después con:

- capturas de pantalla,
- versión impresa,
- versión para capacitación interna.

---

## 📞 Soporte interno sugerido

**Responsable del sistema:** Administrador / soporte técnico  
**Canal de ayuda:** WhatsApp o correo institucional del hotel
