import type { DemoRequestConfig, MockScenario } from "@/types";

const SIMPLE_SAMPLE_CANDIDATES = [
  "/api/demo/samples/simple/diagnosis_generated_001.png",
  "/api/demo/samples/simple/online_prescription_mobile.jpg",
  "/api/demo/samples/simple/medical_care_card_usa_sample.jpg",
  "/api/demo/samples/by-path?path=examples/assets/sick_leave_normal_generated/diagnosis_generated_001.png",
  "/api/demo/samples/by-path?path=examples/assets/sick_leave_public/commons/online_prescription_mobile.jpg",
];

async function resolveSimpleSampleUrl(fallbackUrl: string): Promise<string> {
  for (const candidate of SIMPLE_SAMPLE_CANDIDATES) {
    try {
      const response = await fetch(candidate, { method: "HEAD" });
      if (response.ok) return candidate;
    } catch {
      // ignore and continue fallback probing
    }
  }
  return fallbackUrl;
}

function getScenarioRequestConfig(scenario: MockScenario): DemoRequestConfig {
  if (scenario === "review") {
    return {
      plugin_name: "marriage_certificate",
      ocr_backend: "mock",
      vlm_backend: "mock",
      leave_type: "MARRIAGE",
      applicant_name: "张三",
      related_person_name: "王五",
      related_person_relation: "spouse",
      leave_start_date: "2024-05-20",
      leave_end_date: "2024-05-20",
      fieldOverrides: {
        holder_name: "张三",
        person_a_name: "张三",
        person_b_name: "李四",
        registration_date: "2024-05-20",
      },
      sampleFileUrl: "/samples/paddle_sample_doc_00006737.jpg",
      sampleFilename: "marriage-proof.jpg",
      sampleContentType: "image/jpeg",
    };
  }

  return {
    plugin_name: "diagnosis_proof",
    ocr_backend: "rapidocr",
    vlm_backend: "mock",
    leave_type: "SICK",
    applicant_name: "张三",
    leave_start_date: "2026-03-10",
    leave_end_date: "2026-03-16",
    fieldOverrides: {
      patient_name: "张三",
      rest_start_date: "2026-03-10",
      rest_end_date: "2026-03-16",
      issue_date: "2026-03-10",
    },
    sampleFileUrl: "/samples/diagnosis_generated_001.png",
    sampleFilename: "diagnosis_generated_001.png",
    sampleContentType: "image/png",
  };
}

async function fetchDemoFile(config: DemoRequestConfig): Promise<File> {
  const sampleUrl = await resolveSimpleSampleUrl(config.sampleFileUrl);
  const response = await fetch(sampleUrl);
  if (!response.ok) {
    throw new Error(`failed to load sample file: ${sampleUrl}`);
  }

  const blob = await response.blob();
  return new File([blob], config.sampleFilename, { type: config.sampleContentType });
}

function buildBaseFormData(config: DemoRequestConfig, file: File): FormData {
  const formData = new FormData();
  formData.set("plugin_name", config.plugin_name);
  formData.set("file", file);

  if (config.ocr_backend) formData.set("ocr_backend", config.ocr_backend);
  if (config.vlm_backend) formData.set("vlm_backend", config.vlm_backend);
  if (config.detector_backend) formData.set("detector_backend", config.detector_backend);
  if (config.rectify_backend) formData.set("rectify_backend", config.rectify_backend);

  for (const [key, value] of Object.entries(config.fieldOverrides)) {
    formData.set(key, value);
  }

  return formData;
}

function appendVerifyFields(formData: FormData, config: DemoRequestConfig): FormData {
  if (config.expected_attachment_type) formData.set("expected_attachment_type", config.expected_attachment_type);
  if (config.expected_attachment_types) formData.set("expected_attachment_types", config.expected_attachment_types);
  if (config.leave_type) formData.set("leave_type", config.leave_type);
  if (config.applicant_name) formData.set("applicant_name", config.applicant_name);
  if (config.related_person_name) formData.set("related_person_name", config.related_person_name);
  if (config.related_person_relation) formData.set("related_person_relation", config.related_person_relation);
  if (config.leave_start_date) formData.set("leave_start_date", config.leave_start_date);
  if (config.leave_end_date) formData.set("leave_end_date", config.leave_end_date);
  return formData;
}

export async function buildAnalyzeDemoFormData(scenario: MockScenario): Promise<FormData> {
  const config = getScenarioRequestConfig(scenario);
  const demoFile = await fetchDemoFile(config);
  return buildBaseFormData(config, demoFile);
}

export async function buildVerifyDemoFormData(scenario: MockScenario): Promise<FormData> {
  const config = getScenarioRequestConfig(scenario);
  const demoFile = await fetchDemoFile(config);
  return appendVerifyFields(buildBaseFormData(config, demoFile), config);
}

export function buildAnalyzeSelectedFileFormData(
  scenario: MockScenario,
  selectedFile: File,
): FormData {
  const config = getScenarioRequestConfig(scenario);
  return buildBaseFormData(config, selectedFile);
}

export function buildVerifySelectedFileFormData(
  scenario: MockScenario,
  selectedFile: File,
): FormData {
  const config = getScenarioRequestConfig(scenario);
  return appendVerifyFields(buildBaseFormData(config, selectedFile), config);
}
