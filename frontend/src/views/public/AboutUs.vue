<script setup>
import { computed } from "vue";
import { useConfigStore } from "@/stores/config";
import {
  ABOUT_CAROUSEL,
  ABOUT_DEFAULTS,
  ABOUT_FAQS,
  ABOUT_IMPACT,
  ABOUT_STORY,
  ABOUT_VALUES,
} from "@/content/publicContent";
import AboutHero from "@/components/about/AboutHero.vue";
import MissionVision from "@/components/about/MissionVision.vue";
import AboutStory from "@/components/about/AboutStory.vue";
import ValuesGrid from "@/components/about/ValuesGrid.vue";
import FaqAccordion from "@/components/about/FaqAccordion.vue";
import ImpactSection from "@/components/about/ImpactSection.vue";
import ImageMarquee from "@/components/about/ImageMarquee.vue";

const configStore = useConfigStore();
const hotelName = computed(() => configStore.hotelName);

// Los textos institucionales editables desde el panel tienen prioridad sobre los de respaldo.
const tagline = computed(() => configStore.data.tagline || ABOUT_DEFAULTS.tagline);
const description = computed(
  () => configStore.data.about_description || ABOUT_DEFAULTS.description(hotelName.value),
);
const mission = computed(() => configStore.data.mission || ABOUT_DEFAULTS.mission);
const vision = computed(() => configStore.data.vision || ABOUT_DEFAULTS.vision);

const faqs = computed(() =>
  ABOUT_FAQS.map((faq) => ({
    question: faq.question,
    answer: faq.answer({ depositPercent: configStore.data.deposit_percent }),
  })),
);
</script>

<template>
  <main class="about-page">
    <AboutHero :hotel-name="hotelName" :tagline="tagline" />
    <MissionVision :mission="mission" :vision="vision" />
    <AboutStory :title="ABOUT_STORY.title" :text="description" :image="ABOUT_STORY.image" :image-alt="hotelName" />
    <ValuesGrid :values="ABOUT_VALUES" />
    <FaqAccordion :faqs="faqs" />
    <ImpactSection
      :label="ABOUT_IMPACT.label"
      :title="ABOUT_IMPACT.title"
      :description="ABOUT_IMPACT.description(hotelName)"
      :commitments="ABOUT_IMPACT.commitments"
      :metrics="ABOUT_IMPACT.metrics"
    />
    <ImageMarquee :images="ABOUT_CAROUSEL" />
  </main>
</template>
