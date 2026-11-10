<script setup>
/**
 * Política de tratamiento de datos personales (Ley 1581 de 2012, Decreto 1377 de 2013
 * compilado en el Decreto 1074 de 2015). La enlazan las casillas de consentimiento del
 * registro y de la reserva.
 *
 * Los datos del responsable (razón social, NIT, contacto) salen de los ajustes del sitio.
 * El texto es una plantilla base: debe validarla el asesor legal del hotel antes de publicar.
 */
import { computed } from "vue";
import { useConfigStore } from "@/stores/config";

// Cambiar al publicar una nueva versión de la política.
const POLICY_VERSION = "1.0";
const POLICY_EFFECTIVE_DATE = "9 de noviembre de 2026";

const configStore = useConfigStore();
const d = computed(() => configStore.data);

const responsable = computed(() => d.value.legal_name || configStore.hotelName);
const domicilio = computed(() =>
  [d.value.address, d.value.city, d.value.country].filter(Boolean).join(", ")
);
const canalContacto = computed(() => d.value.contact_email || "el correo de contacto publicado en este sitio");
</script>

<template>
  <main class="policy-page">
    <section class="policy-hero">
      <div class="container text-center">
        <span class="policy-kicker">Ley 1581 de 2012 · Habeas Data</span>
        <h1 class="policy-title">Política de tratamiento de datos personales</h1>
        <p class="policy-meta mb-0">
          Versión {{ POLICY_VERSION }} · Vigente desde el {{ POLICY_EFFECTIVE_DATE }}
        </p>
      </div>
    </section>

    <section class="py-5">
      <div class="container policy-container">
        <nav class="policy-toc shadow-soft mb-5" aria-label="Contenido de la política">
          <h2 class="h6 fw-bold mb-3">Contenido</h2>
          <ol class="mb-0">
            <li><a href="#responsable">Responsable del tratamiento</a></li>
            <li><a href="#datos">Datos que recolectamos</a></li>
            <li><a href="#finalidades">Finalidades del tratamiento</a></li>
            <li><a href="#menores">Datos de niñas, niños y adolescentes</a></li>
            <li><a href="#derechos">Derechos del titular</a></li>
            <li><a href="#procedimiento">Consultas y reclamos</a></li>
            <li><a href="#encargados">Encargados y transmisión de datos</a></li>
            <li><a href="#seguridad">Seguridad de la información</a></li>
            <li><a href="#conservacion">Conservación de los datos</a></li>
            <li><a href="#vigencia">Vigencia y cambios</a></li>
          </ol>
        </nav>

        <article class="policy-body">
          <p class="lead-intro">
            En {{ configStore.hotelName }} respetamos tu privacidad. Esta política explica qué datos personales
            recolectamos, para qué los usamos y cómo puedes ejercer tus derechos como titular, en cumplimiento de la
            Ley Estatutaria 1581 de 2012, el Decreto 1377 de 2013 (compilado en el Decreto Único 1074 de 2015) y
            demás normas que los modifiquen o complementen.
          </p>

          <h2 id="responsable">1. Responsable del tratamiento</h2>
          <ul class="policy-facts">
            <li><strong>Razón social:</strong> {{ responsable }}</li>
            <li v-if="d.tax_id"><strong>NIT:</strong> {{ d.tax_id }}</li>
            <li v-if="domicilio"><strong>Domicilio:</strong> {{ domicilio }}</li>
            <li v-if="d.contact_email">
              <strong>Correo electrónico:</strong>
              <a :href="`mailto:${d.contact_email}`">{{ d.contact_email }}</a>
            </li>
            <li v-if="d.phone"><strong>Teléfono:</strong> {{ d.phone }}</li>
          </ul>
          <p>
            La administración del hotel es el área encargada de atender las consultas, reclamos y solicitudes
            relacionadas con tus datos personales, a través de {{ canalContacto }}.
          </p>

          <h2 id="datos">2. Datos que recolectamos</h2>
          <p>Solo pedimos los datos necesarios para prestarte el servicio de hospedaje:</p>
          <ul>
            <li>
              <strong>Al crear tu cuenta:</strong> nombre completo, tipo de persona, tipo y número de documento,
              correo electrónico, teléfono, país y ciudad. Tu contraseña se guarda cifrada con un algoritmo de
              resumen irreversible; nadie en el hotel puede leerla.
            </li>
            <li>
              <strong>Al hacer una reserva:</strong> nombre, correo, teléfono, tipo y número de documento,
              fechas de estadía, observaciones y el comprobante de pago del anticipo (que puede contener datos
              bancarios).
            </li>
            <li>
              <strong>Sobre tus acompañantes:</strong> nombre, tipo y número de documento y parentesco. Al
              registrarlos declaras que cuentas con su autorización, o con la de su representante legal si son
              menores de edad.
            </li>
            <li>
              <strong>Durante tu estadía:</strong> fechas de ingreso y salida, consumos y pagos registrados en tu
              cuenta de huésped.
            </li>
            <li>
              <strong>Datos técnicos:</strong> una cookie necesaria para mantener tu sesión iniciada y la fecha en
              que aceptaste esta política. No usamos cookies publicitarias.
            </li>
          </ul>
          <p>
            No solicitamos datos sensibles (salud, origen étnico, orientación política o religiosa, datos
            biométricos, entre otros). Si nos los compartes de forma voluntaria en las observaciones, por ejemplo
            una condición médica o alimentaria para atenderte mejor, los usaremos solo para ese fin. No estás
            obligado a suministrarlos.
          </p>

          <h2 id="finalidades">3. Finalidades del tratamiento</h2>
          <ul>
            <li>Gestionar tu cuenta, tus reservas y tu estadía (verificación del pago, confirmación, ingreso y salida).</li>
            <li>Enviarte comunicaciones sobre tu reserva: confirmaciones, cambios, recordatorios y avisos de vencimiento.</li>
            <li>Verificar tu correo electrónico, restablecer tu contraseña y proteger tu cuenta.</li>
            <li>Llevar la cuenta de huésped con tus consumos y pagos, y cumplir obligaciones contables y tributarias.</li>
            <li>
              Cumplir obligaciones legales del sector hotelero, como el registro de huéspedes ante las autoridades
              de turismo y el reporte de huéspedes extranjeros a Migración Colombia.
            </li>
            <li>Atender tus peticiones, quejas y reclamos.</li>
            <li>Elaborar estadísticas internas de ocupación con datos agregados que no te identifican.</li>
          </ul>
          <p>
            No vendemos, alquilamos ni cedemos tus datos a terceros con fines comerciales. Si en el futuro
            quisiéramos enviarte promociones, te pediremos una autorización separada que podrás revocar en
            cualquier momento.
          </p>

          <h2 id="menores">4. Datos de niñas, niños y adolescentes</h2>
          <p>
            Solo tratamos datos de menores de edad cuando viajan como acompañantes y únicamente para cumplir el
            registro de huéspedes exigido por la ley, respetando su interés superior y sus derechos fundamentales.
            Estos datos los suministra el adulto responsable de la reserva, quien declara actuar como su
            representante legal o con su autorización.
          </p>

          <h2 id="derechos">5. Derechos del titular</h2>
          <p>Como titular de los datos tienes derecho a:</p>
          <ul>
            <li>Conocer, actualizar y rectificar tus datos personales.</li>
            <li>Solicitar prueba de la autorización que nos otorgaste.</li>
            <li>Ser informado sobre el uso que les hemos dado a tus datos.</li>
            <li>
              Presentar quejas ante la Superintendencia de Industria y Comercio (SIC) por infracciones a la ley,
              una vez hayas agotado el trámite de consulta o reclamo ante nosotros.
            </li>
            <li>
              Revocar la autorización y solicitar la supresión de tus datos, salvo cuando exista un deber legal o
              contractual de conservarlos.
            </li>
            <li>Acceder gratuitamente a tus datos personales.</li>
          </ul>
          <p>
            Puedes consultar y actualizar tus datos en cualquier momento desde tu perfil en el sitio. Estos
            derechos también pueden ejercerlos tus causahabientes, tu representante o apoderado, acreditando esa
            calidad.
          </p>

          <h2 id="procedimiento">6. Consultas y reclamos</h2>
          <p>
            Envía tu solicitud a {{ canalContacto }} indicando tu nombre completo, tu número de documento, la
            descripción de lo que pides, una dirección o correo para responderte y, si es un reclamo, los
            documentos que quieras hacer valer.
          </p>
          <ul>
            <li>
              <strong>Consultas:</strong> se responden en un máximo de diez (10) días hábiles desde su recibo. Si
              no es posible en ese plazo, te informaremos el motivo y responderemos dentro de los cinco (5) días
              hábiles siguientes.
            </li>
            <li>
              <strong>Reclamos</strong> (corrección, actualización, supresión o incumplimiento): se responden en
              un máximo de quince (15) días hábiles desde el día siguiente a su recibo, prorrogables hasta por
              ocho (8) días hábiles más, previo aviso. Si el reclamo está incompleto, te pediremos completarlo
              dentro de los cinco (5) días siguientes; si pasan dos (2) meses sin que lo hagas, se entenderá que
              desististe.
            </li>
          </ul>

          <h2 id="encargados">7. Encargados y transmisión de datos</h2>
          <p>
            Para operar el sitio usamos proveedores de servicios tecnológicos (alojamiento de la base de datos y
            de archivos en la nube, y envío de correo electrónico), que actúan como encargados del tratamiento.
            Algunos de ellos pueden almacenar la información en servidores ubicados fuera de Colombia. En esos
            casos exigimos que traten los datos solo siguiendo nuestras instrucciones, para las finalidades de
            esta política y con medidas de seguridad adecuadas.
          </p>
          <p>
            También podemos entregar datos a autoridades públicas cuando lo exija la ley o una orden de autoridad
            competente.
          </p>

          <h2 id="seguridad">8. Seguridad de la información</h2>
          <p>
            Aplicamos medidas técnicas y administrativas para proteger tus datos: conexiones cifradas,
            contraseñas almacenadas con algoritmos de resumen seguros, acceso al panel administrativo restringido
            por rol y permisos, y comprobantes de pago guardados en un almacenamiento privado que solo puede
            consultar el personal autorizado.
          </p>

          <h2 id="conservacion">9. Conservación de los datos</h2>
          <p>
            Conservamos tus datos mientras tengas una cuenta activa o una relación comercial con el hotel, y
            después durante el tiempo necesario para cumplir obligaciones legales, contables y tributarias o para
            atender reclamaciones. Cumplido ese plazo, los suprimimos o anonimizamos. Si desactivas tu cuenta, no
            podrás volver a usarla, pero los datos de reservas y cuentas de huésped que la ley nos obliga a
            conservar se mantendrán durante el plazo exigido.
          </p>

          <h2 id="vigencia">10. Vigencia y cambios</h2>
          <p>
            Esta política rige desde el {{ POLICY_EFFECTIVE_DATE }} y las bases de datos estarán vigentes mientras
            el hotel desarrolle su actividad. Si hacemos cambios sustanciales, los publicaremos en esta página y te
            avisaremos por correo antes de aplicarlos y, cuando la ley lo requiera, te pediremos una nueva
            autorización.
          </p>
        </article>
      </div>
    </section>
  </main>
</template>

<style scoped>
.policy-hero {
  background: linear-gradient(135deg, var(--k-forest) 0%, var(--k-forest-soft) 100%);
  color: var(--k-cream);
  padding: 130px 20px 70px;
}

.policy-kicker {
  display: inline-block;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--k-apple-light);
  margin-bottom: 12px;
}

.policy-title {
  font-weight: 700;
  font-size: clamp(1.7rem, 4vw, 2.6rem);
  margin-bottom: 14px;
}

.policy-meta {
  opacity: 0.85;
  font-size: 0.95rem;
}

.policy-container {
  max-width: 860px;
}

.policy-toc {
  background: var(--k-offwhite);
  border: 1px solid var(--k-border);
  border-radius: 16px;
  padding: 24px 28px;
  color: var(--k-text);
}

.policy-toc ol {
  columns: 2;
  column-gap: 32px;
  padding-left: 1.2rem;
}

.policy-toc li {
  margin-bottom: 6px;
  break-inside: avoid;
}

.policy-toc a,
.policy-body a {
  color: var(--k-forest-soft);
}

.policy-body {
  color: var(--k-text);
  line-height: 1.75;
}

.policy-body h2 {
  color: var(--k-forest);
  font-size: 1.3rem;
  font-weight: 700;
  margin: 2.5rem 0 1rem;
  /* Evita que la barra de navegación fija tape el título al saltar desde el índice. */
  scroll-margin-top: 100px;
}

.policy-body ul {
  padding-left: 1.2rem;
}

.policy-body li {
  margin-bottom: 8px;
}

.lead-intro {
  font-size: 1.05rem;
}

.policy-facts {
  list-style: none;
  padding: 18px 22px !important;
  background: var(--k-apple-soft);
  border-radius: 12px;
}

.policy-facts li:last-child {
  margin-bottom: 0;
}

@media (max-width: 576px) {
  .policy-toc ol {
    columns: 1;
  }
}
</style>
