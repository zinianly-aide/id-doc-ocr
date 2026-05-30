import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Collapse,
  Descriptions,
  Divider,
  Drawer,
  Empty,
  Form,
  Input,
  message,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  CheckCircleOutlined,
  CloudSyncOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  RollbackOutlined,
  SearchOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";

import { leaveAuditApi } from "@/api/leaveAuditApi";
import type {
  AutoPassReadiness,
  LeaveAuditDetailResponse,
  LeaveAuditResult,
  LeaveAuditStatus,
  LeaveAuditTableRow,
  LeaveAuditTask,
  RuleResult,
} from "@/types/leaveAudit";

const { Title, Text, Paragraph } = Typography;

const STATUS_OPTIONS: LeaveAuditStatus[] = [
  "PENDING",
  "PULLED",
  "PROCESSING",
  "PASS",
  "REVIEW",
  "REJECT",
  "ERROR",
  "IGNORED",
  "SYNCED",
];

const REVIEW_DECISIONS: LeaveAuditStatus[] = ["PASS", "REVIEW", "REJECT"];

function statusColor(status?: string): string {
  switch (status) {
    case "PASS":
    case "SYNCED":
      return "success";
    case "REVIEW":
    case "PENDING":
    case "PULLED":
    case "PROCESSING":
      return "warning";
    case "REJECT":
      return "error";
    case "ERROR":
      return "volcano";
    default:
      return "default";
  }
}

function readinessColor(status?: string): string {
  switch (status) {
    case "ready":
      return "success";
    case "blocked":
      return "warning";
    default:
      return "default";
  }
}

function riskColor(riskLevel?: string): string {
  switch (riskLevel) {
    case "LOW":
      return "success";
    case "MEDIUM":
      return "warning";
    case "HIGH":
      return "error";
    default:
      return "default";
  }
}

function formatTime(value?: string | null): string {
  if (!value) {
    return "-";
  }
  const parsed = dayjs(value);
  return parsed.isValid() ? parsed.format("YYYY-MM-DD HH:mm") : value;
}

function getLeaveRequestId(task: LeaveAuditTask): string {
  const raw = task.raw_payload ?? {};
  return String(raw.leave_request_id ?? raw.request_id ?? task.request_id);
}

function getAttachmentName(task: LeaveAuditTask): string {
  const first = task.attachments?.[0];
  return first?.filename ?? first?.attachment_id ?? "-";
}

function toRows(tasks: LeaveAuditTask[], details: Record<string, LeaveAuditDetailResponse | undefined>): LeaveAuditTableRow[] {
  return tasks.map((task) => {
    const detail = details[task.request_id];
    const result = detail?.result ?? null;
    const verification = result?.verification_json;
    return {
      key: task.request_id,
      task,
      result,
      request_id: task.request_id,
      leave_request_id: getLeaveRequestId(task),
      employee_name: task.employee_name,
      leave_type: task.leave_type,
      attachment_name: getAttachmentName(task),
      matched_attachment_type: verification?.matched_attachment_type,
      status: task.status,
      risk_level: verification?.risk_level,
      verify_status: verification?.verify_status,
      updated_at: result?.updated_at ?? task.updated_at,
    };
  });
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="leave-audit-json-block">{JSON.stringify(value ?? {}, null, 2)}</pre>;
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (Array.isArray(value)) {
    return value.length ? value.map(renderValue).join("、") : "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function AutoPassReadinessView({ readiness }: { readiness?: AutoPassReadiness }) {
  if (!readiness) {
    return <Tag>未生成</Tag>;
  }
  return (
    <Space direction="vertical" size={8} className="leave-audit-full-width">
      <Tag color={readinessColor(readiness.status)}>{readiness.label || readiness.status}</Tag>
      {readiness.reasons?.length ? <Alert type="warning" showIcon message="原因" description={readiness.reasons.join("；")} /> : null}
      {readiness.blockers?.length ? <Alert type="error" showIcon message="阻断项" description={readiness.blockers.join("；")} /> : null}
    </Space>
  );
}

function RuleResultsView({ rules }: { rules?: RuleResult[] }) {
  if (!rules?.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无规则结果" />;
  }
  return (
    <Space direction="vertical" size={8} className="leave-audit-full-width">
      {rules.map((rule) => (
        <Card size="small" key={rule.rule_code} className={rule.passed ? undefined : "leave-audit-rule-card--failed"}>
          <Space direction="vertical" size={4} className="leave-audit-full-width">
            <Space wrap>
              <Tag color={rule.passed ? "success" : statusColor(rule.severity === "error" ? "REJECT" : "REVIEW")}>
                {rule.passed ? "通过" : "未通过"}
              </Tag>
              <Tag>{rule.rule_code}</Tag>
              <Tag color={rule.severity === "error" ? "error" : rule.severity === "warning" ? "warning" : "default"}>{rule.severity}</Tag>
              <Text type="secondary">score_delta: {rule.score_delta}</Text>
            </Space>
            <Text strong>{rule.display_message ?? rule.message_zh ?? rule.message ?? "-"}</Text>
            <JsonBlock value={rule.evidence} />
          </Space>
        </Card>
      ))}
    </Space>
  );
}

function getFieldParserBackend(result?: LeaveAuditResult | null): string {
  const analysis = result?.analysis_json;
  const classification = analysis?.classification_evidence ?? {};
  const artifacts = analysis?.raw_artifacts ?? {};
  return String(classification.field_parser_backend ?? artifacts.field_parser_backend ?? "-");
}

function AnalysisExplanation({ result }: { result?: LeaveAuditResult | null }) {
  const analysis = result?.analysis_json;
  const verification = result?.verification_json;
  const parserBackend = getFieldParserBackend(result);
  const fieldCount = Array.isArray(analysis?.extracted_fields) ? analysis.extracted_fields.length : 0;
  const ruleCount = Array.isArray(verification?.rule_results) ? verification.rule_results.length : 0;
  const failedRuleCount = Array.isArray(verification?.rule_results)
    ? verification.rule_results.filter((rule) => !rule.passed).length
    : 0;

  if (result?.error_message) {
    return (
      <Alert
        type="error"
        showIcon
        message="解析或核验失败"
        description={result.error_message}
      />
    );
  }

  return (
    <Space direction="vertical" size={12} className="leave-audit-full-width">
      <Alert
        type="info"
        showIcon
        message="说明"
        description="analysis_json 是 OCR/解析器输出与质量判断；verification_json 是把解析结果和请假申请规则比对后的核验结论。下面已按业务视角拆成摘要、字段和规则，原始 JSON 仅保留在调试区。"
      />
      <Descriptions column={2} size="small">
        <Descriptions.Item label="解析方式">
          <Tag color={parserBackend === "dify" ? "purple" : "blue"}>{parserBackend === "dify" ? "Dify 解析" : "传统解析"}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="文档类型">{analysis?.doc_type ?? "-"}</Descriptions.Item>
        <Descriptions.Item label="材料类型">{String((analysis?.classification_evidence ?? {}).attachment_label ?? verification?.matched_attachment_type ?? "-")}</Descriptions.Item>
        <Descriptions.Item label="提取字段数">{fieldCount}</Descriptions.Item>
        <Descriptions.Item label="核验规则数">{ruleCount}</Descriptions.Item>
        <Descriptions.Item label="未通过规则">{failedRuleCount}</Descriptions.Item>
      </Descriptions>
    </Space>
  );
}

function ExtractedFieldsView({ result }: { result?: LeaveAuditResult | null }) {
  const analysisFields = Array.isArray(result?.analysis_json?.extracted_fields)
    ? result?.analysis_json?.extracted_fields ?? []
    : [];
  const verificationFields = result?.verification_json?.extracted_fields;
  const rows = analysisFields.length
    ? analysisFields.map((field, index) => ({
        key: String(field.name ?? index),
        name: renderValue(field.name),
        value: renderValue(field.value),
        confidence: typeof field.confidence === "number" ? field.confidence.toFixed(2) : "-",
        source: renderValue(field.source),
        matched: field.matched === undefined ? "-" : field.matched ? "已匹配" : "未匹配",
      }))
    : Object.entries((verificationFields ?? {}) as Record<string, unknown>).map(([name, value]) => ({
        key: name,
        name,
        value: renderValue(value),
        confidence: "-",
        source: "verification",
        matched: "-",
      }));

  if (!rows.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无提取字段" />;
  }

  return (
    <Table
      size="small"
      pagination={false}
      dataSource={rows}
      columns={[
        { title: "字段", dataIndex: "name", width: 150 },
        { title: "值", dataIndex: "value" },
        { title: "置信度", dataIndex: "confidence", width: 90 },
        { title: "来源", dataIndex: "source", width: 120 },
        { title: "证据匹配", dataIndex: "matched", width: 100 },
      ]}
    />
  );
}

function VerificationSummaryView({ result }: { result?: LeaveAuditResult | null }) {
  const verification = result?.verification_json;
  if (!verification || !Object.keys(verification).length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无核验结论" />;
  }
  return (
    <Descriptions column={1} size="small">
      <Descriptions.Item label="核验结果">{verification.verify_status ? <Tag color={statusColor(String(verification.verify_status))}>{String(verification.verify_status)}</Tag> : "-"}</Descriptions.Item>
      <Descriptions.Item label="风险等级">{verification.risk_level ? <Tag color={riskColor(String(verification.risk_level))}>{String(verification.risk_level)}</Tag> : "-"}</Descriptions.Item>
      <Descriptions.Item label="风险分">{verification.risk_score ?? "-"}</Descriptions.Item>
      <Descriptions.Item label="识别材料类型">{verification.matched_attachment_type ?? "-"}</Descriptions.Item>
      <Descriptions.Item label="是否需要人工复核">{verification.needs_manual_review === undefined ? "-" : verification.needs_manual_review ? "是" : "否"}</Descriptions.Item>
      <Descriptions.Item label="结论说明">{verification.summary_message ?? "-"}</Descriptions.Item>
    </Descriptions>
  );
}

export function LeaveAuditWorkbench() {
  const [tasks, setTasks] = useState<LeaveAuditTask[]>([]);
  const [detailsById, setDetailsById] = useState<Record<string, LeaveAuditDetailResponse | undefined>>({});
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [leaveTypeFilter, setLeaveTypeFilter] = useState<string | undefined>();
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionLoadingKey, setActionLoadingKey] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [reviewForm] = Form.useForm<{ review_result: LeaveAuditStatus; review_comment?: string; reviewer: string }>();

  const selectedDetail = selectedRequestId ? detailsById[selectedRequestId] : undefined;

  const fetchDetail = async (requestId: string): Promise<LeaveAuditDetailResponse> => {
    const detail = await leaveAuditApi.getTask(requestId);
    setDetailsById((current) => ({ ...current, [requestId]: detail }));
    return detail;
  };

  const refresh = async () => {
    setLoading(true);
    try {
      const response = await leaveAuditApi.listTasks(statusFilter ? { status: statusFilter } : undefined);
      setTasks(response.tasks);
      const detailResponses = await Promise.allSettled(response.tasks.map((task) => leaveAuditApi.getTask(task.request_id)));
      const nextDetails: Record<string, LeaveAuditDetailResponse> = {};
      detailResponses.forEach((item) => {
        if (item.status === "fulfilled") {
          nextDetails[item.value.task.request_id] = item.value;
        }
      });
      setDetailsById(nextDetails);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "刷新失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const rows = useMemo(() => toRows(tasks, detailsById), [tasks, detailsById]);

  const leaveTypeOptions = useMemo(
    () => Array.from(new Set(tasks.map((task) => task.leave_type).filter(Boolean))).map((value) => ({ label: value, value })),
    [tasks],
  );

  const filteredRows = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();
    return rows.filter((row) => {
      const leaveTypeMatch = !leaveTypeFilter || row.leave_type === leaveTypeFilter;
      const keywordMatch =
        !normalizedKeyword ||
        [row.request_id, row.leave_request_id, row.attachment_name, row.employee_name]
          .filter(Boolean)
          .some((item) => String(item).toLowerCase().includes(normalizedKeyword));
      return leaveTypeMatch && keywordMatch;
    });
  }, [rows, leaveTypeFilter, keyword]);

  const stats = useMemo(() => {
    const total = rows.length;
    const pending = rows.filter((row) => ["PENDING", "PULLED", "PROCESSING"].includes(row.status)).length;
    const pass = rows.filter((row) => row.status === "PASS" || row.verify_status === "PASS").length;
    const review = rows.filter((row) => row.status === "REVIEW" || row.verify_status === "REVIEW").length;
    const reject = rows.filter((row) => row.status === "REJECT" || row.verify_status === "REJECT").length;
    const autoPassRate = total > 0 ? Math.round((pass / total) * 1000) / 10 : 0;
    return { pending, pass, review, reject, autoPassRate };
  }, [rows]);

  const syncTasks = async () => {
    setLoading(true);
    try {
      const response = await leaveAuditApi.syncTasks();
      message.success(`已同步 ${response.synced} 条待审核任务`);
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "同步失败");
    } finally {
      setLoading(false);
    }
  };

  const runTask = async (requestId: string, fieldParserBackend: "plugin" | "dify") => {
    const loadingKey = `${requestId}:${fieldParserBackend}`;
    setActionLoadingKey(loadingKey);
    try {
      const response = await leaveAuditApi.runTask(requestId, fieldParserBackend);
      message.success(`${fieldParserBackend === "dify" ? "Dify解析" : "传统解析"}完成：${response.result.status}`);
      await fetchDetail(requestId);
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "运行核验失败");
    } finally {
      setActionLoadingKey(null);
    }
  };

  const openDetail = async (requestId: string) => {
    setSelectedRequestId(requestId);
    setDrawerOpen(true);
    await fetchDetail(requestId);
    reviewForm.setFieldsValue({ reviewer: "hr01", review_result: "REVIEW", review_comment: "" });
  };

  const submitReview = async () => {
    if (!selectedRequestId) {
      return;
    }
    const values = await reviewForm.validateFields();
    setActionLoadingKey(`${selectedRequestId}:review`);
    try {
      await leaveAuditApi.submitReview(selectedRequestId, {
        decision: values.review_result,
        reviewer: values.reviewer,
        comment: values.review_comment,
      });
      message.success("人工复核已提交");
      await fetchDetail(selectedRequestId);
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "提交复核失败");
    } finally {
      setActionLoadingKey(null);
    }
  };

  const callbackTask = async (requestId: string) => {
    const loadingKey = `${requestId}:callback`;
    setActionLoadingKey(loadingKey);
    try {
      await leaveAuditApi.callbackTask(requestId);
      message.success("已回写假勤系统");
      await fetchDetail(requestId);
      await refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "回写失败");
    } finally {
      setActionLoadingKey(null);
    }
  };

  const columns: ColumnsType<LeaveAuditTableRow> = [
    { title: "任务编号", dataIndex: "request_id", width: 210, fixed: "left" },
    { title: "申请单号", dataIndex: "leave_request_id", width: 190 },
    { title: "员工姓名", dataIndex: "employee_name", width: 130 },
    { title: "假别", dataIndex: "leave_type", width: 120, render: (value: string) => <Tag>{value}</Tag> },
    { title: "附件名称", dataIndex: "attachment_name", width: 180 },
    { title: "识别材料类型", dataIndex: "matched_attachment_type", width: 220, render: (value?: string) => value ? <Tag color="blue">{value}</Tag> : "-" },
    { title: "任务状态", dataIndex: "status", width: 120, render: (value: string) => <Tag color={statusColor(value)}>{value}</Tag> },
    { title: "风险等级", dataIndex: "risk_level", width: 120, render: (value?: string) => value ? <Tag color={riskColor(value)}>{value}</Tag> : "-" },
    { title: "核验结果", dataIndex: "verify_status", width: 140, render: (value?: string) => value ? <Tag color={statusColor(value)}>{value}</Tag> : "-" },
    { title: "更新时间", dataIndex: "updated_at", width: 170, render: formatTime },
    {
      title: "操作",
      key: "actions",
      fixed: "right",
      width: 300,
      render: (_, row) => (
        <Space size={6} wrap>
          <Button size="small" type="primary" icon={<SyncOutlined />} loading={actionLoadingKey === `${row.request_id}:plugin`} onClick={() => void runTask(row.request_id, "plugin")}>
            传统解析
          </Button>
          <Button size="small" icon={<SyncOutlined />} loading={actionLoadingKey === `${row.request_id}:dify`} onClick={() => void runTask(row.request_id, "dify")}>
            Dify解析
          </Button>
          <Button size="small" onClick={() => void openDetail(row.request_id)}>详情</Button>
          <Button size="small" icon={<RollbackOutlined />} loading={actionLoadingKey === `${row.request_id}:callback`} onClick={() => void callbackTask(row.request_id)}>
            回写
          </Button>
        </Space>
      ),
    },
  ];

  const selectedTask = selectedDetail?.task;
  const selectedResult = selectedDetail?.result;
  const verification = selectedResult?.verification_json;
  const analysis = selectedResult?.analysis_json;
  const readiness = verification?.autoPassReadiness;

  return (
    <div className="leave-audit-workbench">
      <div className="leave-audit-header">
        <div>
          <Text className="leave-audit-eyebrow">Leave Audit Sidecar</Text>
          <Title level={2}>假勤材料旁路审核工作台</Title>
          <Paragraph>用于同步、核验、复核和回写 leave_audit 旁路审核任务。</Paragraph>
        </div>
        <Badge status="processing" text="Connected to /leave-audit API" />
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={4}>
          <Card><Statistic title="待核验" value={stats.pending} prefix={<CloudSyncOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={4}>
          <Card><Statistic title="自动通过" value={stats.pass} valueStyle={{ color: "#16a34a" }} prefix={<CheckCircleOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={5}>
          <Card><Statistic title="待人工复核" value={stats.review} valueStyle={{ color: "#d97706" }} prefix={<ExclamationCircleOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={4}>
          <Card><Statistic title="建议驳回" value={stats.reject} valueStyle={{ color: "#dc2626" }} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={4}>
          <Card><Statistic title="自动通过率" value={stats.autoPassRate} suffix="%" precision={1} /></Card>
        </Col>
      </Row>

      <Card className="leave-audit-toolbar-card">
        <Space wrap>
          <Button type="primary" icon={<CloudSyncOutlined />} onClick={() => void syncTasks()} loading={loading}>同步待审核任务</Button>
          <Button icon={<ReloadOutlined />} onClick={() => void refresh()} loading={loading}>刷新</Button>
          <Select allowClear placeholder="状态筛选" value={statusFilter} onChange={setStatusFilter} style={{ width: 160 }} options={STATUS_OPTIONS.map((value) => ({ label: value, value }))} />
          <Select allowClear placeholder="假别筛选" value={leaveTypeFilter} onChange={setLeaveTypeFilter} style={{ width: 160 }} options={leaveTypeOptions} />
          <Input prefix={<SearchOutlined />} allowClear placeholder="文件名/申请单号搜索" value={keyword} onChange={(event) => setKeyword(event.target.value)} style={{ width: 260 }} />
        </Space>
      </Card>

      <Card>
        <Table
          rowClassName={(row) => row.status === "REVIEW" || row.status === "REJECT" ? "leave-audit-row-highlight" : ""}
          columns={columns}
          dataSource={filteredRows}
          loading={loading}
          scroll={{ x: 1680 }}
          pagination={{ pageSize: 10, showSizeChanger: true }}
        />
      </Card>

      <Drawer
        title="旁路审核详情"
        width={760}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={selectedRequestId ? (
          <Space>
            <Button icon={<SyncOutlined />} onClick={() => void runTask(selectedRequestId, "plugin")} loading={actionLoadingKey === `${selectedRequestId}:plugin`}>传统解析</Button>
            <Button icon={<SyncOutlined />} onClick={() => void runTask(selectedRequestId, "dify")} loading={actionLoadingKey === `${selectedRequestId}:dify`}>Dify解析</Button>
            <Button type="primary" icon={<RollbackOutlined />} onClick={() => void callbackTask(selectedRequestId)} loading={actionLoadingKey === `${selectedRequestId}:callback`}>回写</Button>
          </Space>
        ) : null}
      >
        {!selectedTask ? (
          <Empty description="请选择任务" />
        ) : (
          <Space direction="vertical" size={18} className="leave-audit-full-width">
            <Card title="申请信息" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="request_id">{selectedTask.request_id}</Descriptions.Item>
                <Descriptions.Item label="leave_request_id">{getLeaveRequestId(selectedTask)}</Descriptions.Item>
                <Descriptions.Item label="employee_name">{selectedTask.employee_name}</Descriptions.Item>
                <Descriptions.Item label="employee_id">{selectedTask.employee_id ?? "-"}</Descriptions.Item>
                <Descriptions.Item label="leave_type"><Tag>{selectedTask.leave_type}</Tag></Descriptions.Item>
                <Descriptions.Item label="leave_date">{selectedTask.leave_start_date ?? "-"} ~ {selectedTask.leave_end_date ?? "-"}</Descriptions.Item>
                <Descriptions.Item label="status"><Tag color={statusColor(selectedTask.status)}>{selectedTask.status}</Tag></Descriptions.Item>
              </Descriptions>
            </Card>

            <Card title="附件信息" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="attachment_name">{getAttachmentName(selectedTask)}</Descriptions.Item>
                <Descriptions.Item label="attachment_url">{selectedTask.attachments?.[0]?.attachment_url ?? "-"}</Descriptions.Item>
                <Descriptions.Item label="plugin_name">{selectedTask.attachments?.[0]?.plugin_name ?? selectedResult?.plugin_name ?? "-"}</Descriptions.Item>
                <Descriptions.Item label="content_type">{selectedTask.attachments?.[0]?.content_type ?? "-"}</Descriptions.Item>
              </Descriptions>
            </Card>

            <Card title="解析说明" size="small">
              <AnalysisExplanation result={selectedResult} />
            </Card>

            <Card title="核验结论" size="small">
              <VerificationSummaryView result={selectedResult} />
            </Card>

            <Card title="自动通过判断" size="small">
              <AutoPassReadinessView readiness={readiness} />
            </Card>

            <Card title="提取字段" size="small">
              <ExtractedFieldsView result={selectedResult} />
            </Card>

            <Card title="规则核验" size="small">
              <RuleResultsView rules={verification?.rule_results} />
            </Card>

            <Card title="人工复核 Panel" size="small">
              <Form form={reviewForm} layout="vertical" initialValues={{ reviewer: "hr01", review_result: "REVIEW" }}>
                <Form.Item name="review_result" label="review_result" rules={[{ required: true }]}>
                  <Select options={REVIEW_DECISIONS.map((value) => ({ label: value, value }))} />
                </Form.Item>
                <Form.Item name="reviewer" label="reviewer" rules={[{ required: true, message: "请输入复核人" }]}>
                  <Input placeholder="hr01" />
                </Form.Item>
                <Form.Item name="review_comment" label="review_comment">
                  <Input.TextArea rows={3} placeholder="请输入复核说明" />
                </Form.Item>
                <Button type="primary" onClick={() => void submitReview()} loading={actionLoadingKey === `${selectedRequestId}:review`}>提交复核按钮</Button>
              </Form>
              {selectedDetail.reviews?.length ? (
                <>
                  <Divider />
                  <Space direction="vertical" className="leave-audit-full-width">
                    {selectedDetail.reviews.map((review) => (
                      <Alert
                        key={`${review.request_id}-${review.created_at}`}
                        type={review.decision === "PASS" ? "success" : review.decision === "REJECT" ? "error" : "warning"}
                        message={`${review.decision} / ${review.reviewer} / ${formatTime(review.created_at)}`}
                        description={review.comment || "无备注"}
                      />
                    ))}
                  </Space>
                </>
              ) : null}
            </Card>

            <Card title="原始数据（调试）" size="small">
              <Collapse
                size="small"
                items={[
                  {
                    key: "analysis_json",
                    label: "analysis_json：解析与质量判断原始数据",
                    children: <JsonBlock value={analysis} />,
                  },
                  {
                    key: "verification_json",
                    label: "verification_json：规则核验原始数据",
                    children: <JsonBlock value={verification} />,
                  },
                ]}
              />
            </Card>
          </Space>
        )}
      </Drawer>
    </div>
  );
}
