import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Form, Input, message, Select, Space, Switch, Typography } from "antd";
import { ReloadOutlined, SaveOutlined } from "@ant-design/icons";

import { leaveAuditApi } from "@/api/leaveAuditApi";
import type { LeaveAuditConfigGuidance, PromptConfigItem } from "@/types/leaveAudit";

const { Paragraph, Text, Title } = Typography;

const RECOGNITION_TYPE_OPTIONS = [
  "*",
  "diagnosis_proof",
  "medical_record",
  "marriage_certificate",
  "birth_certificate",
  "only_child_certificate",
  "custody_relationship_certificate",
  "hukou_booklet",
  "train_ticket",
  "boarding_pass",
  "passport",
  "china_id",
];

const PROMPT_TYPE_OPTIONS = [
  "field_extraction",
  "verification",
  "review_summary",
  "qa_assistant",
];

interface PromptFormValues {
  recognition_type: string;
  prompt_type: string;
  prompt_text: string;
  enabled: boolean;
}

function promptKey(config: Pick<PromptConfigItem, "recognition_type" | "prompt_type">): string {
  return `${config.recognition_type}::${config.prompt_type}`;
}

function configToForm(config: PromptConfigItem | undefined): PromptFormValues {
  return {
    recognition_type: config?.recognition_type ?? "diagnosis_proof",
    prompt_type: config?.prompt_type ?? "field_extraction",
    prompt_text: config?.prompt_text ?? "",
    enabled: config?.enabled ?? true,
  };
}

function uniqueOptions(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).map((value) => ({ label: value, value }));
}

export function PromptConfigPage() {
  const [configs, setConfigs] = useState<PromptConfigItem[]>([]);
  const [selectedKey, setSelectedKey] = useState("diagnosis_proof::field_extraction");
  const [guidance, setGuidance] = useState<LeaveAuditConfigGuidance | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm<PromptFormValues>();

  const selectedConfig = useMemo(
    () => configs.find((item) => promptKey(item) === selectedKey),
    [configs, selectedKey],
  );

  const recognitionTypeOptions = useMemo(
    () => uniqueOptions([...RECOGNITION_TYPE_OPTIONS, ...configs.map((item) => item.recognition_type)]),
    [configs],
  );

  const promptTypeOptions = useMemo(
    () => uniqueOptions([...PROMPT_TYPE_OPTIONS, ...configs.map((item) => item.prompt_type)]),
    [configs],
  );

  const refresh = async () => {
    setLoading(true);
    try {
      const response = await leaveAuditApi.getConfig();
      setConfigs(response.prompt_configs);
      setGuidance(response.guidance);
      const nextKey = response.prompt_configs.find((item) => promptKey(item) === selectedKey)
        ? selectedKey
        : response.prompt_configs[0]
          ? promptKey(response.prompt_configs[0])
          : "diagnosis_proof::field_extraction";
      setSelectedKey(nextKey);
      form.setFieldsValue(configToForm(response.prompt_configs.find((item) => promptKey(item) === nextKey)));
    } catch (error) {
      message.error(error instanceof Error ? error.message : "读取提示词配置失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    form.setFieldsValue(configToForm(selectedConfig));
  }, [form, selectedConfig]);

  const save = async () => {
    const values = await form.validateFields();
    const nextConfig: PromptConfigItem = {
      recognition_type: values.recognition_type.trim(),
      prompt_type: values.prompt_type.trim(),
      prompt_text: values.prompt_text,
      enabled: values.enabled,
    };
    if (!nextConfig.recognition_type || !nextConfig.prompt_type) {
      message.error("识别类型和提示词类型不能为空");
      return;
    }
    const nextKey = promptKey(nextConfig);
    const nextConfigs = [...configs.filter((item) => promptKey(item) !== nextKey), nextConfig];
    setLoading(true);
    try {
      const response = await leaveAuditApi.updatePromptConfigs(nextConfigs);
      setConfigs(response.prompt_configs);
      setSelectedKey(nextKey);
      message.success("提示词配置已保存");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "保存提示词配置失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="leave-audit-workbench">
      <div className="leave-audit-header">
        <div>
          <Text className="leave-audit-eyebrow">Configuration</Text>
          <Title level={2}>识别类型提示词配置</Title>
          <Paragraph>按识别插件配置字段抽取、审核口径和复核辅助提示词。Dify 解析会读取 field_extraction。</Paragraph>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void refresh()} loading={loading}>刷新</Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={() => void save()} loading={loading}>保存</Button>
        </Space>
      </div>

      {guidance?.prompt_config?.length ? (
        <Alert type="info" showIcon message="配置引导" description={guidance.prompt_config.join("；")} />
      ) : null}

      <Card className="leave-audit-toolbar-card">
        <Form form={form} layout="vertical">
          <Form.Item label="选择已有提示词">
            <Select
              value={selectedKey}
              onChange={setSelectedKey}
              options={configs.map((item) => ({
                label: `${item.recognition_type} / ${item.prompt_type}`,
                value: promptKey(item),
              }))}
              placeholder="尚无配置，可直接填写下方表单新增"
            />
          </Form.Item>
          <Form.Item name="recognition_type" label="识别类型" rules={[{ required: true, message: "请输入识别类型" }]}>
            <Select showSearch options={recognitionTypeOptions} placeholder="diagnosis_proof" />
          </Form.Item>
          <Form.Item name="prompt_type" label="提示词类型" rules={[{ required: true, message: "请输入提示词类型" }]}>
            <Select showSearch options={promptTypeOptions} placeholder="field_extraction" />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="prompt_text" label="提示词内容">
            <Input.TextArea
              rows={12}
              spellCheck={false}
              placeholder="例如：只抽取病假证明相关字段。必须优先识别 patient_name、issue_date、rest_start_date、rest_end_date。不要把医生姓名当成患者姓名。"
            />
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
