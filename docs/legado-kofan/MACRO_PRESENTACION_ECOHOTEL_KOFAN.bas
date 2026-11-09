Attribute VB_Name = "EcohotelKofanPresentation"
Option Explicit

Sub GenerarPresentacionEcohotelKofan()
    Dim pres As Presentation
    Dim rutaGuardado As String

    Set pres = Application.Presentations.Add

    AgregarPortada pres, _
        "Ecohotel Kofán", _
        "Documentación técnica del sistema" & vbCrLf & _
        "FastAPI + Vue.js + MongoDB" & vbCrLf & _
        "SENA - Ficha 2997671"

    AgregarSlideTexto pres, _
        "Arquitectura General", _
        "• Frontend SPA con Vue 3 + Vite" & vbCrLf & _
        "• Backend API REST con FastAPI" & vbCrLf & _
        "• Persistencia en MongoDB Atlas (kofan_hospedaje_db)" & vbCrLf & _
        "• Autenticación JWT con control de roles" & vbCrLf & _
        "• Metodología de trabajo: Scrumban"

    AgregarSlideTexto pres, _
        "Mapeo de Rutas", _
        "• /auth/login → Login.vue → POST /auth/login" & vbCrLf & _
        "• /auth/register → Register.vue → POST /register/" & vbCrLf & _
        "• /app/bookings → BookingsView.vue → GET /api/reservas/mis-reservas" & vbCrLf & _
        "• /admin/rooms → RoomsManager.vue → /rooms/*" & vbCrLf & _
        "• /admin/users → UsersManager.vue → /users/*" & vbCrLf & _
        "• /admin/gallery → GalleryManager.vue → /gallery/*"

    AgregarSlideTexto pres, _
        "Módulo: Usuarios", _
        "Funciones principales:" & vbCrLf & _
        "• Registro y autenticación de clientes" & vbCrLf & _
        "• Gestión de perfil propio" & vbCrLf & _
        "• Administración de usuarios por rol" & vbCrLf & vbCrLf & _
        "Ruta técnica:" & vbCrLf & _
        "• Frontend: Register.vue, Login.vue, SettingsView.vue, UsersManager.vue" & vbCrLf & _
        "• Backend: /register, /auth/login, /users" & vbCrLf & _
        "• MongoDB: colección users"

    AgregarSlideTexto pres, _
        "Módulo: Reservas", _
        "Funciones principales:" & vbCrLf & _
        "• Creación de reservas por cliente e invitado" & vbCrLf & _
        "• Consulta de historial de reservas" & vbCrLf & _
        "• Confirmación, check-in y check-out" & vbCrLf & _
        "• Edición de detalles y generación de factura" & vbCrLf & vbCrLf & _
        "Ruta técnica:" & vbCrLf & _
        "• Frontend: RoomCalendarModal.vue, BookingsView.vue, BookingsManager.vue" & vbCrLf & _
        "• Backend: /api/reservas/*, /invoices/*" & vbCrLf & _
        "• MongoDB: bookings, invoices, notifications"

    AgregarSlideTexto pres, _
        "Módulo: Habitaciones", _
        "Funciones principales:" & vbCrLf & _
        "• Alta, edición y retiro de habitaciones" & vbCrLf & _
        "• Carga y eliminación de imágenes" & vbCrLf & _
        "• Consulta de disponibilidad y fechas ocupadas" & vbCrLf & _
        "• Registro de movimientos operativos" & vbCrLf & vbCrLf & _
        "Ruta técnica:" & vbCrLf & _
        "• Frontend: Catalog.vue, RoomsManager.vue" & vbCrLf & _
        "• Backend: /rooms/* y /rooms/logs/history" & vbCrLf & _
        "• MongoDB: rooms y room_logs"

    AgregarSlideTexto pres, _
        "Módulo: Inventario / Operación", _
        "Funciones principales:" & vbCrLf & _
        "• Control de espacios activos e inactivos" & vbCrLf & _
        "• Parámetros del hotel: horarios, moneda, contacto" & vbCrLf & _
        "• Seguimiento de ocupación y trazabilidad" & vbCrLf & vbCrLf & _
        "Ruta técnica:" & vbCrLf & _
        "• Frontend: RoomsManager.vue, DashboardView.vue, config.vue" & vbCrLf & _
        "• Backend: /dashboard, /config, /rooms" & vbCrLf & _
        "• MongoDB: settings, rooms, room_logs"

    AgregarSlideTexto pres, _
        "Módulo: Galería", _
        "Funciones principales:" & vbCrLf & _
        "• Publicación de imágenes institucionales" & vbCrLf & _
        "• Filtrado por categorías" & vbCrLf & _
        "• Carga y eliminación desde el panel administrativo" & vbCrLf & vbCrLf & _
        "Ruta técnica:" & vbCrLf & _
        "• Frontend: PhotosGallery.vue, GalleryManager.vue" & vbCrLf & _
        "• Backend: /gallery/*" & vbCrLf & _
        "• MongoDB: colección gallery"

    AgregarSlideTexto pres, _
        "Conclusiones Técnicas", _
        "• La solución implementa una arquitectura modular y mantenible" & vbCrLf & _
        "• Vue gestiona la experiencia de usuario y FastAPI centraliza reglas de negocio" & vbCrLf & _
        "• MongoDB ofrece persistencia flexible para reservas, usuarios y medios" & vbCrLf & _
        "• El proyecto es apto para sustentación técnica bajo lineamientos SENA"

    rutaGuardado = Environ("USERPROFILE") & "\Documents\Presentacion_Ecohotel_Kofan.pptx"
    pres.SaveAs rutaGuardado

    MsgBox "Presentación generada correctamente en: " & rutaGuardado, vbInformation, "Ecohotel Kofán"
End Sub

Private Sub AgregarPortada(ByVal pres As Presentation, ByVal titulo As String, ByVal subtitulo As String)
    Dim sld As Slide
    Set sld = pres.Slides.Add(pres.Slides.Count + 1, ppLayoutTitle)

    sld.Shapes.Title.TextFrame.TextRange.Text = titulo
    sld.Shapes(2).TextFrame.TextRange.Text = subtitulo
End Sub

Private Sub AgregarSlideTexto(ByVal pres As Presentation, ByVal titulo As String, ByVal cuerpo As String)
    Dim sld As Slide
    Set sld = pres.Slides.Add(pres.Slides.Count + 1, ppLayoutText)

    sld.Shapes.Title.TextFrame.TextRange.Text = titulo
    sld.Shapes(2).TextFrame.TextRange.Text = cuerpo
End Sub