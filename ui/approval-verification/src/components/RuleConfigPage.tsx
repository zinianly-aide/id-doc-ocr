import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Form, Input, message, Select, Space, Switch, Typography } from "antd";
import { ReloadOutlined, SaveOutlined } from "@ant-design/icons";

import { leaveAuditApi } from "@/api/leaveAuditApi";
import type { LeaveAuditConfigGuidance, RuleConfigItem } from "@/types/leaveAudit";

const { Paragraph, Text, Title } = Typography;

interface RuleFormValues {
  leave_type: string;
  prompt_text: string;
  rules_json: string;
  enabled: boolean;
}

function configToForm(config: RuleConfigItem | undefined): RuleFormValues {
  return {
    leave_type: config?.leave_type ?? "MARRIAGE",
    prompt_text: config?.prompt_text ?? "",
    rules_json: JSON.stringify(config?.rules ?? [], null, 2),
    enabled: config?.enabled ?? true,
  };
}

export function RuleConfigPage() {
  const [configs, setConfigs] = useState<RuleConfigItem[]>([]);
  const [selectedLeaveType, setSelectedLeaveType] = useState("MARRIAGE");
  const [guidance, setGuidance] = useState<LeaveAuditConfigGuidance | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm<RuleFormValues>();

  const selectedConfig = useMemo(
    () => configs.find((item) => item.leave_type === selectedLeaveType),
    [configs, selectedLeaveType],
  );

  const refresh = async () => {
    setLoading(true);
    try {
      const response = await leaveAuditApi.getConfig();
      setConfigs(response.rule_configs);
      setGuidance(response.guidance);
      const nextLeaveType = response.rule_configs.find((item) => item.leave_type === selectedLeaveType)?.leave_type
        ?? response.rule_configs[0]?.leave_type
        ?? "MARRIAGE";
      setSelectedLeaveType(nextLeaveType);
      form.setFieldsValue(configToForm(response.rule_configs.find((item) => item.leave_type === nextLeaveType)));
    } catch (error) {
      message.error(error instanceof Error ? error.message : "读取规则配置失败");
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
    let rules: Array<Record<string, unknown>>;
    try {
      const parsed = JSON.parse(values.rules_json || "[]");
      if (!Array.isArray(parsed)) {
        throw new Error("rules must be an array");
      }
      rules = parsed as Array<Record<string, unknown>>;
    } catch (error) {
      message.error(error instanceof Error ? `规则 JSON 无效：${error.message}` : "规则 JSON 无效");
      return;
    }

    const nextConfig: RuleConfigItem = {
      leave_type: values.leave_type.trim().toUpperCase(),
      prompt_text: values.prompt_text,
      rules,
      enabled: values.enabled,
    };
    const nextConfigs = [...configs.filter((item) => item.leave_type !== nextConfig.leave_type), nextConfig];
    setLoading(true);
    try {
      const response = await leaveAuditApi.updateRuleConfigs(nextConfigs);
      setConfigs(response.rule_configs);
      setSelectedLeaveType(nextConfig.leave_type);
      message.success("规则配置已保存");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "保存规则配置失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="leave-audit-workbench">
      <div className="leave-audit-header">
        <div>
          <Text className="leave-audit-eyebrow">Configuration</Text>
          <Title level={2}>提示词与校验规则配置</Title>
          <Paragraph>配置不同假别的审核提示词和规则 JSON，系统审核时会从 DB 读取这些配置。</Paragraph>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void refresh()} loading={loading}>刷新</Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={() => void save()} loading={loading}>保存</Button>
        </Space>
      </div>

      {guidance?.rule_config?.length ? (
        <Alert type="info" showIcon message="配置引导" description={guidance.rule_config.join("；")} />
      ) : null}

      <Card className="leave-audit-toolbar-card">
        <Form form={form} layout="vertical">
          <Form.Item label="选择已有假别">
            <Select
              value={selectedLeaveType}
              onChange={setSelectedLeaveType}
              options={configs.map((item) => ({ label: item.leave_type, value: item.leave_type }))}
            />
          </Form.Item>
          <Form.Item name="leave_type" label="假别编码" rules={[{ required: true, message: "请输入假别编码" }]}>
            <Input placeholder="MARRIAGE" />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="prompt_text" label="提示词">
            <Input.TextArea rows={4} placeholder="写清楚该假别材料需要抽取什么字段、怎么判断风险。" />
          </Form.Item>
          <Form.Item name="rules_json" label="规则 JSON" rules={[{ required: true, message: "请输入规则 JSON" }]}>
            <Input.TextArea rows={14} spellCheck={false} />
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
