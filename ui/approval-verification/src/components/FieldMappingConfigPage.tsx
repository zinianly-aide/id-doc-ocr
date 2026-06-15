import { useEffect, useState } from "react";
import { Alert, Button, Card, Input, message, Space, Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { ReloadOutlined, SaveOutlined } from "@ant-design/icons";

import { leaveAuditApi } from "@/api/leaveAuditApi";
import type { FieldMappingItem, LeaveAuditConfigGuidance } from "@/types/leaveAudit";

const { Paragraph, Text, Title } = Typography;

function candidatesToText(candidates: string[]): string {
  return candidates.join(", ");
}

function textToCandidates(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function FieldMappingConfigPage() {
  const [mappings, setMappings] = useState<FieldMappingItem[]>([]);
  const [guidance, setGuidance] = useState<LeaveAuditConfigGuidance | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const response = await leaveAuditApi.getConfig();
      setMappings(response.field_mappings);
      setGuidance(response.guidance);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "读取字段映射失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const updateCandidates = (canonicalField: string, value: string) => {
    setMappings((current) =>
      current.map((item) =>
        item.canonical_field === canonicalField ? { ...item, candidates: textToCandidates(value) } : item,
      ),
    );
  };

  const save = async () => {
    setLoading(true);
    try {
      const response = await leaveAuditApi.updateFieldMappings(mappings);
      setMappings(response.field_mappings);
      message.success("字段映射已保存");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "保存字段映射失败");
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<FieldMappingItem> = [
    {
      title: "内部字段",
      dataIndex: "canonical_field",
      width: 220,
      render: (value: string) => <Text code>{value}</Text>,
    },
    {
      title: "候选字段（逗号或换行分隔）",
      dataIndex: "candidates",
      render: (_value, row) => (
        <Input.TextArea
          rows={2}
          value={candidatesToText(row.candidates)}
          onChange={(event) => updateCandidates(row.canonical_field, event.target.value)}
        />
      ),
    },
  ];

  return (
    <div className="leave-audit-workbench">
      <div className="leave-audit-header">
        <div>
          <Text className="leave-audit-eyebrow">Configuration</Text>
          <Title level={2}>字段映射配置</Title>
          <Paragraph>配置 OCR/解析结果字段名到审核内部字段的候选顺序，例如把 name 加入 applicant_name。</Paragraph>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void refresh()} loading={loading}>刷新</Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={() => void save()} loading={loading}>保存</Button>
        </Space>
      </div>

      {guidance?.field_mapping?.length ? (
        <Alert type="info" showIcon message="配置引导" description={guidance.field_mapping.join("；")} />
      ) : null}

      <Card className="leave-audit-toolbar-card">
        <Table
          rowKey="canonical_field"
          columns={columns}
          dataSource={mappings}
          loading={loading}
          pagination={false}
        />
      </Card>
    </div>
  );
}
