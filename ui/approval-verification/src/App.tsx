import { ConfigProvider, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import dayjs from "dayjs";
import "dayjs/locale/zh-cn";

import { DifyOcrChatbot } from "@/components/DifyOcrChatbot";
import { LeaveAuditWorkbench } from "@/components/LeaveAuditWorkbench";

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
      <LeaveAuditWorkbench />
      <DifyOcrChatbot />
    </ConfigProvider>
  );
}
