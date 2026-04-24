import type { DemoRequestConfig, MockScenario } from "@/types";

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
    ocr_backend: "mock",
    vlm_backend: "mock",
    leave_type: "SICK",
    applicant_name: "张三",
    leave_start_date: "2026-04-01",
    leave_end_date: "2026-04-03",
    fieldOverrides: {
      patient_name: "张三",
      rest_start_date: "2026-04-01",
      rest_end_date: "2026-04-03",
      issue_date: "2026-04-01",
    },
    sampleFileUrl: "/samples/paddle_sample_doc_00006737.jpg",
    sampleFilename: "diagnosis-proof.jpg",
    sampleContentType: "image/jpeg",
  };
}

async function buildBaseDemoFormData(config: DemoRequestConfig): Promise<FormData> {
  const response = await fetch(config.sampleFileUrl);
  if (!response.ok) {
    throw new Error(`failed to load sample file: ${config.sampleFileUrl}`);
  }

  const blob = await response.blob();
  const file = new File([blob], config.sampleFilename, { type: config.sampleContentType });
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

export async function buildAnalyzeDemoFormData(scenario: MockScenario): Promise<FormData> {
  const config = getScenarioRequestConfig(scenario);
  return buildBaseDemoFormData(config);
}

export async function buildVerifyDemoFormData(scenario: MockScenario): Promise<FormData> {
  const config = getScenarioRequestConfig(scenario);
  const formData = await buildBaseDemoFormData(config);

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
