import { ConfigProvider, Tabs, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import dayjs from "dayjs";
import "dayjs/locale/zh-cn";

import { DifyOcrChatbot } from "@/components/DifyOcrChatbot";
import { FieldMappingConfigPage } from "@/components/FieldMappingConfigPage";
import { LeaveAuditWorkbench } from "@/components/LeaveAuditWorkbench";
import { RuleConfigPage } from "@/components/RuleConfigPage";

dayjs.locale("zh-cn");

export default function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#2563eb",
          borderRadius: 12,
          fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
      }}
    >
      <Tabs
        className="leave-audit-app-tabs"
        defaultActiveKey="workbench"
        items={[
          { key: "workbench", label: "审核工作台", children: <LeaveAuditWorkbench /> },
          { key: "field-mapping", label: "字段映射", children: <FieldMappingConfigPage /> },
          { key: "rules", label: "规则配置", children: <RuleConfigPage /> },
        ]}
      />
      <DifyOcrChatbot />
    </ConfigProvider>
  );
}
